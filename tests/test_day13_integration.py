from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from cultureshift.app import create_app
from cultureshift.asset_storage import TemporaryAssetStore
from cultureshift.capability_tokens import CapabilityTokenService
from cultureshift.composition import PillowCompositor
from cultureshift.composition_export import CompositionExportService
from cultureshift.composition_service import CompositionService
from cultureshift.composition_storage import CompositionArtifactStore
from cultureshift.fixture_assets import FixtureAssetRegistry
from cultureshift.image_provider import FixtureImageProvider
from cultureshift.repository import SQLiteProjectRunRepository

LOGO_ID = "a1111111-1111-4111-8111-111111111111"
UI_ID = "a2222222-2222-4222-8222-222222222222"
LAYOUT_ID = "a3333333-3333-4333-8333-333333333333"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _source_png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (64, 48), "#e8f0f6").save(output, "PNG", compress_level=9)
    return output.getvalue()


def _client(tmp_path) -> TestClient:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"d" * 32, audience="cultureshift-api")
    compositions = CompositionArtifactStore(tmp_path / "compositions")
    return TestClient(
        create_app(
            repository=repository,
            token_service=tokens,
            asset_store=TemporaryAssetStore(tmp_path / "assets"),
            composition_service=CompositionService(
                repository,
                FixtureImageProvider(),
                FixtureAssetRegistry(),
                PillowCompositor(),
                compositions,
                Path("assets/fonts/NotoSansCJKsc-Regular.otf"),
            ),
            composition_export_service=CompositionExportService(
                repository, compositions
            ),
        )
    )


@pytest.mark.parametrize(
    ("direction", "expected_locale", "expected_rules"),
    [
        ("china_to_uk", "en-GB", ["ZEU-S1", "ZEU-S3"]),
        ("uk_to_china", "zh-CN", ["EZC-S1", "EZC-S3"]),
    ],
)
def test_day13_bilateral_public_upload_to_export_is_repeatable(
    tmp_path,
    valid_run_payload,
    direction: str,
    expected_locale: str,
    expected_rules: list[str],
) -> None:
    client = _client(tmp_path)
    with client:
        uploaded = client.post(
            "/api/v1/assets",
            content=_source_png(),
            headers={
                "Content-Type": "image/png",
                "X-Provenance-Ref": f"fixture:day13/{direction}/source",
                "X-Rights-Ref": "rights:authorized-fixture/day13",
            },
        )
        assert uploaded.status_code == 201
        brand_lock = {
            **valid_run_payload["brand_lock"],
            "logo_asset_id": LOGO_ID,
            "product_ui_asset_ids": [UI_ID],
            "layout_template_asset_id": LAYOUT_ID,
        }
        created = client.post(
            "/api/v1/runs",
            json={
                **valid_run_payload,
                "direction": direction,
                "source_asset": uploaded.json()["asset"],
                "brand_lock": brand_lock,
            },
        )
        assert created.status_code == 201
        run_id = created.json()["run_id"]
        token = created.json()["capability_token"]

        analyzed = client.post(f"/api/v1/runs/{run_id}/analyze", headers=_auth(token))
        confirmed = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": brand_lock},
            headers=_auth(token),
        )
        drafted = client.post(f"/api/v1/runs/{run_id}/draft", headers=_auth(token))
        generated = client.post(
            f"/api/v1/runs/{run_id}/composition", headers=_auth(token)
        )
        first_png = client.get(
            f"/api/v1/runs/{run_id}/composition.png", headers=_auth(token)
        )
        second_png = client.get(
            f"/api/v1/runs/{run_id}/composition.png", headers=_auth(token)
        )
        first_json = client.get(
            f"/api/v1/runs/{run_id}/composition.json", headers=_auth(token)
        )
        second_json = client.get(
            f"/api/v1/runs/{run_id}/composition.json", headers=_auth(token)
        )
        snapshot = client.get(f"/api/v1/runs/{run_id}", headers=_auth(token))

    assert analyzed.status_code == confirmed.status_code == drafted.status_code == 200
    assert generated.status_code == first_png.status_code == first_json.status_code == 200
    assert first_png.content == second_png.content
    assert first_json.content == second_json.content
    assert first_json.json() == generated.json()
    assert first_json.json()["disclosure"] == "Fixture Demo / 非实时模型"
    assert hashlib.sha256(first_png.content).hexdigest() == generated.json()[
        "rendered_sha256"
    ]
    with Image.open(BytesIO(first_png.content)) as exported:
        assert exported.format == "PNG"
        assert exported.size == (1600, 900)
    assert drafted.json()["copy"]["locale"] == expected_locale
    assert drafted.json()["rule_ids"] == expected_rules
    assert [layer["kind"] for layer in generated.json()["layers"]][1:3] == [
        "product_ui",
        "logo",
    ]
    assert generated.json()["layers"][1]["source_asset_id"] == UI_ID
    assert generated.json()["layers"][2]["source_asset_id"] == LOGO_ID
    assert snapshot.json()["status"] == "in_progress"
    assert token not in first_json.text
