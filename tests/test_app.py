import hashlib
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cultureshift.analysis_provider import FakeProvider, VisionProvider, VisionProviderResult
from cultureshift.app import create_app
from cultureshift.asset_storage import TemporaryAssetStore
from cultureshift.capability_tokens import Capability, CapabilityTokenService
from cultureshift.composition import PillowCompositor
from cultureshift.composition_export import CompositionExportService
from cultureshift.composition_service import CompositionService
from cultureshift.composition_storage import CompositionArtifactStore
from cultureshift.contracts import RevisionChange
from cultureshift.critic import Critic
from cultureshift.draft_generation import (
    DraftErrorCode,
    DraftGenerationError,
    DraftGenerator,
    FixtureCopywriter,
)
from cultureshift.fixture_assets import FixtureAssetRegistry
from cultureshift.image_provider import FixtureImageProvider
from cultureshift.rate_limits import FixedWindowRateLimiter
from cultureshift.repository import RevisionLimitReachedError, SQLiteProjectRunRepository
from cultureshift.revision import FixtureRevisionEngine
from cultureshift.revision_service import RevisionService
from cultureshift.workflow import RetryAction, RetryCondition


def make_client(
    tmp_path,
    *,
    upload_rate_limiter: FixedWindowRateLimiter | None = None,
    analysis_provider: VisionProvider | None = None,
    draft_generator: DraftGenerator | None = None,
    composition_service: CompositionService | None = None,
    composition_export_service: CompositionExportService | None = None,
    revision_service_factory=None,
) -> tuple[TestClient, SQLiteProjectRunRepository]:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    composition_store = CompositionArtifactStore(tmp_path / "compositions")
    compositions = composition_service or CompositionService(
        repository,
        FixtureImageProvider(),
        FixtureAssetRegistry(),
        PillowCompositor(),
        composition_store,
        Path("assets/fonts/NotoSansCJKsc-Regular.otf"),
    )
    exports = composition_export_service or CompositionExportService(
        repository, composition_store
    )
    return (
        TestClient(
            create_app(
                repository=repository,
                token_service=tokens,
                asset_store=TemporaryAssetStore(tmp_path / "assets"),
                upload_rate_limiter=upload_rate_limiter,
                analysis_provider=analysis_provider,
                draft_generator=draft_generator,
                composition_service=compositions,
                composition_export_service=exports,
                revision_service=(
                    revision_service_factory(repository, composition_store)
                    if revision_service_factory is not None
                    else None
                ),
            )
        ),
        repository,
    )


def test_health_contracts_and_openapi(tmp_path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/healthz").json() == {"status": "ok"}
        openapi = client.get("/openapi.json").json()
    assert "RunCreate" in openapi["components"]["schemas"]
    assert "RunCreated" in openapi["components"]["schemas"]
    assert "BrandLockConfirmation" in openapi["components"]["schemas"]
    assert "BrandLockConfirmed" in openapi["components"]["schemas"]


def test_create_run_returns_one_time_token_without_persisting_it(
    tmp_path, valid_run_payload
) -> None:
    client, repository = make_client(tmp_path)
    with client:
        response = client.post("/api/v1/runs", json=valid_run_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert len(body["capability_token"]) >= 16
    assert repository.get(body["run_id"]).direction.value == "china_to_uk"

    with sqlite3.connect(tmp_path / "runs.sqlite3") as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(project_runs)")}
    assert "capability_token" not in columns


def test_create_run_rejects_live_and_unknown_input(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    invalid = {**valid_run_payload, "execution_mode": "live", "private_note": "do not echo"}
    with client:
        response = client.post("/api/v1/runs", json=invalid)
    assert response.status_code == 422
    assert "do not echo" not in response.text


def test_create_run_does_not_echo_unknown_field_locations(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    private_key = r"C:\private\source.png"
    with client:
        response = client.post("/api/v1/runs", json={**valid_run_payload, private_key: "x"})
    assert response.status_code == 422
    assert private_key not in response.json()["detail"][0]["loc"]
    assert private_key not in response.text


def test_create_run_returns_generic_error_without_exception_text(
    tmp_path, valid_run_payload
) -> None:
    class FailingRepository(SQLiteProjectRunRepository):
        def create(self, run):
            raise RuntimeError("private repository detail")

    repository = FailingRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with TestClient(create_app(repository=repository, token_service=tokens)) as client:
        response = client.post("/api/v1/runs", json=valid_run_payload)
    assert response.status_code == 500
    assert response.json() == {"detail": {"code": "run_creation_failed"}}
    assert "private repository detail" not in response.text


def test_token_failure_returns_generic_error_without_orphan_run(
    tmp_path, valid_run_payload
) -> None:
    class FailingTokenService(CapabilityTokenService):
        def issue(self, **kwargs):
            raise RuntimeError("private token detail")

    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = FailingTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with TestClient(create_app(repository=repository, token_service=tokens)) as client:
        response = client.post("/api/v1/runs", json=valid_run_payload)

    assert response.status_code == 500
    assert response.json() == {"detail": {"code": "run_creation_failed"}}
    assert "private token detail" not in response.text
    with sqlite3.connect(tmp_path / "runs.sqlite3") as connection:
        count = connection.execute("SELECT COUNT(*) FROM project_runs").fetchone()[0]
    assert count == 0


def test_invalid_token_value_returns_generic_error_without_orphan_run(
    tmp_path, valid_run_payload
) -> None:
    class InvalidTokenService(CapabilityTokenService):
        def issue(self, **kwargs):
            return "short"

    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = InvalidTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with TestClient(create_app(repository=repository, token_service=tokens)) as client:
        response = client.post("/api/v1/runs", json=valid_run_payload)

    assert response.status_code == 500
    assert response.json() == {"detail": {"code": "run_creation_failed"}}
    with sqlite3.connect(tmp_path / "runs.sqlite3") as connection:
        count = connection.execute("SELECT COUNT(*) FROM project_runs").fetchone()[0]
    assert count == 0


def create_run(client: TestClient, valid_run_payload) -> tuple[str, str]:
    response = client.post("/api/v1/runs", json=valid_run_payload)
    assert response.status_code == 201
    body = response.json()
    return body["run_id"], body["capability_token"]


def create_uploaded_run(client: TestClient, valid_run_payload) -> tuple[str, str, dict]:
    uploaded = client.post(
        "/api/v1/assets",
        content=b"\x89PNG\r\n\x1a\nfixture-day9",
        headers={
            "Content-Type": "image/png",
            "X-Provenance-Ref": "fixture:user-upload/day9",
            "X-Rights-Ref": "rights:authorized-upload/day9",
        },
    )
    assert uploaded.status_code == 201
    payload = {**valid_run_payload, "source_asset": uploaded.json()["asset"]}
    run_id, token = create_run(client, payload)
    return run_id, token, uploaded.json()


def create_analyzed_run(client: TestClient, valid_run_payload) -> tuple[str, str]:
    run_id, token, _ = create_uploaded_run(client, valid_run_payload)
    analyzed = client.post(
        f"/api/v1/runs/{run_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert analyzed.status_code == 200
    return run_id, token


def create_confirmed_run(client: TestClient, valid_run_payload) -> tuple[str, str]:
    run_id, token = create_analyzed_run(client, valid_run_payload)
    confirmed = client.post(
        f"/api/v1/runs/{run_id}/brand-lock/confirm",
        json={"brand_lock": valid_run_payload["brand_lock"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert confirmed.status_code == 200
    return run_id, token


def create_drafted_fixture_run(client: TestClient, valid_run_payload) -> tuple[str, str]:
    payload = {
        **valid_run_payload,
        "brand_lock": {
            **valid_run_payload["brand_lock"],
            "logo_asset_id": "a1111111-1111-4111-8111-111111111111",
            "product_ui_asset_ids": ["a2222222-2222-4222-8222-222222222222"],
            "layout_template_asset_id": "a3333333-3333-4333-8333-333333333333",
        },
    }
    run_id, token = create_confirmed_run(client, payload)
    drafted = client.post(
        f"/api/v1/runs/{run_id}/draft",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert drafted.status_code == 200
    return run_id, token


def create_ready_fixture_run(client: TestClient, valid_run_payload) -> tuple[str, str]:
    run_id, token = create_drafted_fixture_run(client, valid_run_payload)
    authorization = {"Authorization": f"Bearer {token}"}
    assert client.post(
        f"/api/v1/runs/{run_id}/composition", headers=authorization
    ).status_code == 200
    assert client.post(
        f"/api/v1/runs/{run_id}/critic", headers=authorization
    ).status_code == 200
    return run_id, token


@pytest.mark.parametrize("direction", ["china_to_uk", "uk_to_china"])
def test_feedback_endpoint_creates_one_bilateral_revision_and_replays(
    tmp_path, valid_run_payload, direction: str
) -> None:
    client, repository = make_client(tmp_path)
    payload = {**valid_run_payload, "direction": direction}
    with client:
        run_id, token = create_ready_fixture_run(client, payload)
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "revision_key_1234",
        }
        request = {
            "run_id": run_id,
            "feedback": "Please shorten the body without changing the CTA.",
            "requested_changes": ["shorten_body"],
            "submitted_at": "2026-08-25T12:00:00Z",
        }
        first = client.post(
            f"/api/v1/runs/{run_id}/feedback", headers=headers, json=request
        )
        replay = client.post(
            f"/api/v1/runs/{run_id}/feedback", headers=headers, json=request
        )
        conflict = client.post(
            f"/api/v1/runs/{run_id}/feedback",
            headers=headers,
            json={**request, "requested_changes": ["shorten_headline"]},
        )
        limited = client.post(
            f"/api/v1/runs/{run_id}/feedback",
            headers={**headers, "Idempotency-Key": "revision_key_5678"},
            json=request,
        )

    assert first.status_code == replay.status_code == 200
    assert replay.json() == first.json()
    assert first.json()["result_version"] == 2
    assert first.json()["human_revision_count"] == 1
    assert first.json()["previous_composition"]["artifact_id"] != first.json()[
        "composition"
    ]["artifact_id"]
    assert repository.get(run_id).human_revision_count == 1
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": {"code": "idempotency_conflict"}}
    assert limited.status_code == 409
    assert limited.json() == {"detail": {"code": "revision_limit_reached"}}


def test_feedback_endpoint_requires_capability_key_and_matching_run_without_echo(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    private_feedback = "private feedback must not be echoed"
    with client:
        run_id, token = create_ready_fixture_run(client, valid_run_payload)
        request = {
            "run_id": str(uuid4()),
            "feedback": private_feedback,
            "requested_changes": ["shorten_body"],
            "submitted_at": "2026-08-25T12:00:00Z",
        }
        missing_capability = client.post(
            f"/api/v1/runs/{run_id}/feedback",
            headers={"Idempotency-Key": "revision_key_1234"},
            json=request,
        )
        missing_key = client.post(
            f"/api/v1/runs/{run_id}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json=request,
        )
        mismatch = client.post(
            f"/api/v1/runs/{run_id}/feedback",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "revision_key_1234",
            },
            json=request,
        )

    assert missing_capability.status_code == 401
    assert missing_key.status_code == 422
    assert missing_key.json() == {"detail": {"code": "invalid_revision_request"}}
    assert mismatch.status_code == 409
    assert mismatch.json() == {"detail": {"code": "invalid_run_state"}}
    assert private_feedback not in mismatch.text


def test_retry_endpoint_resumes_server_authorized_revision_once(
    tmp_path, valid_run_payload
) -> None:
    client, repository = make_client(tmp_path)
    with client:
        run_id, token = create_ready_fixture_run(client, valid_run_payload)
        run = repository.get(run_id)
        operation = repository.claim_feedback_operation(
            run_id,
            "a" * 64,
            "f" * 64,
            (RevisionChange.SHORTEN_BODY,),
            "d" * 64,
            run.updated_at + timedelta(seconds=1),
        )
        repository.fail_revision_operation(
            run_id,
            operation.id,
            RetryCondition.CONNECTION_BEFORE_ACCEPTANCE,
            RetryAction.RETRY_ONCE,
            run.updated_at + timedelta(seconds=2),
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "technical_retry_1",
        }
        request = {"run_id": run_id, "reason_category": "generation"}
        first = client.post(
            f"/api/v1/runs/{run_id}/retry", headers=headers, json=request
        )
        replay = client.post(
            f"/api/v1/runs/{run_id}/retry", headers=headers, json=request
        )

    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert first.json()["result_version"] == 2
    assert first.json()["human_revision_count"] == 1
    assert first.json()["technical_attempt_count"] == 1
    persisted = repository.get(run_id)
    assert persisted.human_revision_count == 1
    assert persisted.technical_attempt_count == 1


def test_feedback_deletes_orphan_artifact_after_finalize_conflict(
    tmp_path, valid_run_payload, monkeypatch
) -> None:
    def revision_service(repository, store):
        return RevisionService(
            repository,
            FixtureRevisionEngine(),
            FixtureImageProvider(),
            FixtureAssetRegistry(),
            PillowCompositor(),
            store,
            Path("assets/fonts/NotoSansCJKsc-Regular.otf"),
            Critic(),
        )

    client, repository = make_client(
        tmp_path, revision_service_factory=revision_service
    )
    with client:
        run_id, token = create_ready_fixture_run(client, valid_run_payload)
        before = {path.name for path in (tmp_path / "compositions").glob("*.png")}

        def lose_finalize_race(*args, **kwargs):
            raise RevisionLimitReachedError("simulated race")

        monkeypatch.setattr(repository, "complete_revision", lose_finalize_race)
        response = client.post(
            f"/api/v1/runs/{run_id}/feedback",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "revision_cleanup_1",
            },
            json={
                "run_id": run_id,
                "feedback": "Shorten the body.",
                "requested_changes": ["shorten_body"],
                "submitted_at": "2026-08-25T12:00:00Z",
            },
        )
        after = {path.name for path in (tmp_path / "compositions").glob("*.png")}

    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "revision_limit_reached"}}
    assert after == before


def test_composition_endpoint_is_bodyless_authenticated_and_idempotent(
    tmp_path, valid_run_payload
) -> None:
    client, repository = make_client(tmp_path)
    with client:
        run_id, token = create_drafted_fixture_run(client, valid_run_payload)
        first = client.post(
            f"/api/v1/runs/{run_id}/composition",
            headers={"Authorization": f"Bearer {token}"},
        )
        second = client.post(
            f"/api/v1/runs/{run_id}/composition",
            headers={"Authorization": f"Bearer {token}"},
        )
        body_rejected = client.post(
            f"/api/v1/runs/{run_id}/composition",
            json={"private_prompt": "do not echo"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["status"] == "in_progress"
    assert first.json()["width"] == 1600 and first.json()["height"] == 900
    assert "path" not in first.text.casefold()
    assert repository.get_composition(run_id) is not None
    assert body_rejected.status_code == 422
    assert "do not echo" not in body_rejected.text


def test_composition_endpoint_requires_capability_and_day11_draft(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_confirmed_run(client, valid_run_payload)
        missing = client.post(f"/api/v1/runs/{run_id}/composition")
        no_draft = client.post(
            f"/api/v1/runs/{run_id}/composition",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert missing.status_code == 401
    assert missing.json() == {"detail": {"code": "invalid_capability"}}
    assert no_draft.status_code == 409
    assert no_draft.json() == {"detail": {"code": "draft_unavailable"}}


@pytest.mark.parametrize("direction", ["china_to_uk", "uk_to_china"])
def test_critic_endpoint_is_bodyless_authenticated_atomic_and_idempotent(
    tmp_path, valid_run_payload, direction: str
) -> None:
    client, repository = make_client(tmp_path)
    payload = {**valid_run_payload, "direction": direction}
    with client:
        run_id, token = create_drafted_fixture_run(client, payload)
        composed = client.post(
            f"/api/v1/runs/{run_id}/composition",
            headers={"Authorization": f"Bearer {token}"},
        )
        first = client.post(
            f"/api/v1/runs/{run_id}/critic",
            headers={"Authorization": f"Bearer {token}"},
        )
        retry = client.post(
            f"/api/v1/runs/{run_id}/critic",
            headers={"Authorization": f"Bearer {token}"},
        )
        missing = client.post(f"/api/v1/runs/{run_id}/critic")
        body_rejected = client.post(
            f"/api/v1/runs/{run_id}/critic",
            json={"private_prompt": "do not echo"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert composed.status_code == 200
    assert first.status_code == retry.status_code == 200
    assert first.json() == retry.json()
    assert first.json()["status"] == "ready"
    assert first.json()["critique"]["status"] == "pass"
    assert first.json()["initial_generation_count"] == 1
    assert first.json()["human_revision_count"] == 0
    assert first.json()["technical_attempt_count"] == 0
    assert repository.get_critique(run_id) is not None
    assert missing.status_code == 401
    assert missing.json() == {"detail": {"code": "invalid_capability"}}
    assert body_rejected.status_code == 422
    assert body_rejected.json() == {"detail": {"code": "critic_body_not_allowed"}}
    assert "do not echo" not in body_rejected.text


def test_critic_endpoint_rejects_wrong_run_token_and_missing_composition(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_drafted_fixture_run(client, valid_run_payload)
        _, wrong_token = create_run(client, valid_run_payload)
        wrong_subject = client.post(
            f"/api/v1/runs/{run_id}/critic",
            headers={"Authorization": f"Bearer {wrong_token}"},
        )
        no_composition = client.post(
            f"/api/v1/runs/{run_id}/critic",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert wrong_subject.status_code == 403
    assert wrong_subject.json() == {
        "detail": {"code": "capability_subject_mismatch"}
    }
    assert no_composition.status_code == 409
    assert no_composition.json() == {"detail": {"code": "invalid_run_state"}}


def test_composition_exports_are_authenticated_integrity_checked_attachments(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_drafted_fixture_run(client, valid_run_payload)
        generated = client.post(
            f"/api/v1/runs/{run_id}/composition",
            headers={"Authorization": f"Bearer {token}"},
        )
        png = client.get(
            f"/api/v1/runs/{run_id}/composition.png",
            headers={"Authorization": f"Bearer {token}"},
        )
        metadata = client.get(
            f"/api/v1/runs/{run_id}/composition.json",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert generated.status_code == png.status_code == metadata.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert png.headers["content-disposition"] == (
        f'attachment; filename="cultureshift-{run_id}.png"'
    )
    assert png.headers["x-content-type-options"] == "nosniff"
    assert metadata.headers["content-type"] == "application/json"
    assert metadata.headers["content-disposition"] == (
        f'attachment; filename="cultureshift-{run_id}.json"'
    )
    assert metadata.content.endswith(b"\n")
    assert metadata.json() == generated.json()
    assert hashlib.sha256(png.content).hexdigest() == metadata.json()["rendered_sha256"]
    assert "path" not in metadata.text.casefold()
    assert token not in metadata.text


@pytest.mark.parametrize("suffix", ["composition.png", "composition.json"])
def test_composition_exports_require_read_scope_and_matching_subject(
    tmp_path, valid_run_payload, suffix: str
) -> None:
    client, _ = make_client(tmp_path)
    signing = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with client:
        run_id, _ = create_run(client, valid_run_payload)
        update_only = signing.issue(
            subject=run_id,
            capabilities={Capability.UPDATE_PROJECT_RUN},
            ttl=timedelta(minutes=5),
        )
        wrong_subject = signing.issue(
            subject=str(uuid4()),
            capabilities={Capability.READ_PROJECT_RUN},
            ttl=timedelta(minutes=5),
        )
        wrong_scope = client.get(
            f"/api/v1/runs/{run_id}/{suffix}",
            headers={"Authorization": f"Bearer {update_only}"},
        )
        mismatch = client.get(
            f"/api/v1/runs/{run_id}/{suffix}",
            headers={"Authorization": f"Bearer {wrong_subject}"},
        )

    assert wrong_scope.status_code == 401
    assert wrong_scope.json() == {"detail": {"code": "invalid_capability"}}
    assert mismatch.status_code == 403
    assert mismatch.json() == {"detail": {"code": "capability_subject_mismatch"}}
    assert update_only not in wrong_scope.text
    assert wrong_subject not in mismatch.text


def test_composition_exports_report_missing_composition_without_private_data(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_run(client, valid_run_payload)
        response = client.get(
            f"/api/v1/runs/{run_id}/composition.png",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "composition_unavailable"}}
    assert token not in response.text


def test_composition_png_export_maps_missing_artifact_to_bounded_gone_error(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_drafted_fixture_run(client, valid_run_payload)
        generated = client.post(
            f"/api/v1/runs/{run_id}/composition",
            headers={"Authorization": f"Bearer {token}"},
        )
        artifact_id = generated.json()["artifact_id"]
        (tmp_path / "compositions" / f"{artifact_id}.png").unlink()
        response = client.get(
            f"/api/v1/runs/{run_id}/composition.png",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 410
    assert response.json() == {
        "detail": {"code": "composition_artifact_unavailable"}
    }
    assert token not in response.text


@pytest.mark.parametrize(
    ("direction", "rules", "locale"),
    [
        ("china_to_uk", ["ZEU-S1", "ZEU-S3"], "en-GB"),
        ("uk_to_china", ["EZC-S1", "EZC-S3"], "zh-CN"),
    ],
)
def test_generate_draft_is_authenticated_bilateral_and_idempotent(
    tmp_path, valid_run_payload, direction, rules, locale
) -> None:
    payload = {**valid_run_payload, "direction": direction}
    client, repository = make_client(tmp_path)
    with client:
        run_id, token = create_confirmed_run(client, payload)
        first = client.post(
            f"/api/v1/runs/{run_id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )
        retry = client.post(
            f"/api/v1/runs/{run_id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == 200
    assert retry.json() == first.json()
    assert first.json()["status"] == "in_progress"
    assert first.json()["copy"]["locale"] == locale
    assert first.json()["rule_ids"] == rules
    assert "capability_token" not in first.text
    assert repository.get_draft(run_id) is not None


def test_generate_draft_requires_update_capability_and_confirmation(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_analyzed_run(client, valid_run_payload)
        missing = client.post(f"/api/v1/runs/{run_id}/draft")
        unconfirmed = client.post(
            f"/api/v1/runs/{run_id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert missing.status_code == 401
    assert missing.json() == {"detail": {"code": "invalid_capability"}}
    assert unconfirmed.status_code == 409
    assert unconfirmed.json() == {"detail": {"code": "brand_lock_unconfirmed"}}


def test_generate_draft_sanitizes_generation_failure(tmp_path, valid_run_payload) -> None:
    private_marker = r"C:\private\prompt.txt"

    class FailingGenerator(DraftGenerator):
        def generate(self, analysis, confirmed_brand_lock, *, direction):
            del analysis, confirmed_brand_lock, direction
            error = DraftGenerationError(DraftErrorCode.OUTPUT_INVALID)
            error.add_note(private_marker)
            raise error

    client, repository = make_client(
        tmp_path,
        draft_generator=FailingGenerator(FixtureCopywriter()),
    )
    with client:
        run_id, token = create_confirmed_run(client, valid_run_payload)
        response = client.post(
            f"/api/v1/runs/{run_id}/draft",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "draft_output_invalid"}}
    assert private_marker not in response.text
    assert repository.get_draft(run_id) is None


@pytest.mark.parametrize(
    ("direction", "detected_locale"),
    [("china_to_uk", "zh-CN"), ("uk_to_china", "en-GB")],
)
def test_analyze_reaches_awaiting_brand_lock_for_bilateral_fixtures(
    tmp_path, valid_run_payload, direction, detected_locale
) -> None:
    client, repository = make_client(tmp_path)
    payload = {**valid_run_payload, "direction": direction}
    with client:
        run_id, token, _ = create_uploaded_run(client, payload)
        response = client.post(
            f"/api/v1/runs/{run_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_brand_lock"
    assert response.json()["analysis"]["detected_locale"] == detected_locale
    assert response.json()["analysis"]["brand_lock"] == payload["brand_lock"]
    assert repository.get(run_id).status.value == "awaiting_brand_lock"


def test_analyze_is_idempotent_after_success(tmp_path, valid_run_payload) -> None:
    provider = FakeProvider(VisionProviderResult(detected_locale="zh-CN"))
    client, _ = make_client(tmp_path, analysis_provider=provider)
    with client:
        run_id, token, _ = create_uploaded_run(client, valid_run_payload)
        first = client.post(
            f"/api/v1/runs/{run_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )
        second = client.post(
            f"/api/v1/runs/{run_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == second.status_code == 200
    assert second.json()["analysis"] == first.json()["analysis"]
    assert provider.call_count == 1


def test_analyze_repairs_schema_once_and_fails_when_repair_is_invalid(
    tmp_path, valid_run_payload
) -> None:
    repaired = FakeProvider(
        {"detected_locale": "invalid"},
        repair_result=VisionProviderResult(detected_locale="zh-CN"),
    )
    repaired_client, _ = make_client(tmp_path / "repaired", analysis_provider=repaired)
    with repaired_client:
        run_id, token, _ = create_uploaded_run(repaired_client, valid_run_payload)
        success = repaired_client.post(
            f"/api/v1/runs/{run_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )
        retry = repaired_client.post(
            f"/api/v1/runs/{run_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert success.status_code == 200
    assert success.json()["repair_attempted"] is True
    assert retry.json() == success.json()
    assert repaired.attempts == ("initial", "repair")

    invalid = FakeProvider(
        {"detected_locale": "invalid"},
        repair_result={"detected_locale": "still-invalid"},
    )
    invalid_client, repository = make_client(tmp_path / "invalid", analysis_provider=invalid)
    with invalid_client:
        run_id, token, _ = create_uploaded_run(invalid_client, valid_run_payload)
        failure = invalid_client.post(
            f"/api/v1/runs/{run_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert failure.status_code == 502
    assert failure.json() == {"detail": {"code": "provider_output_invalid"}}
    assert invalid.attempts == ("initial", "repair")
    assert repository.get(run_id).status.value == "failed"


def test_analyze_requires_matching_analyze_capability(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, _, _ = create_uploaded_run(client, valid_run_payload)
        read_only = CapabilityTokenService(
            secret=b"a" * 32, audience="cultureshift-api"
        ).issue(
            subject=run_id,
            capabilities={Capability.READ_PROJECT_RUN},
            ttl=timedelta(minutes=5),
        )
        response = client.post(
            f"/api/v1/runs/{run_id}/analyze",
            headers={"Authorization": f"Bearer {read_only}"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "invalid_capability"}}
    assert read_only not in response.text


def test_confirm_brand_lock_is_idempotent_then_immutable(
    tmp_path, valid_run_payload
) -> None:
    client, repository = make_client(tmp_path)
    proposed = {
        **valid_run_payload["brand_lock"],
        "benefit_order": ["Organize", "Summarize"],
        "localizable_fields": ["narrative", "language"],
    }
    with client:
        run_id, token = create_analyzed_run(client, valid_run_payload)
        first = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": proposed},
            headers={"Authorization": f"Bearer {token}"},
        )
        retry = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": proposed},
            headers={"Authorization": f"Bearer {token}"},
        )
        changed = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": valid_run_payload["brand_lock"]},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == retry.status_code == 200
    assert retry.json() == first.json()
    assert first.json()["status"] == "in_progress"
    assert first.json()["brand_lock"] == proposed
    assert "capability_token" not in first.text
    assert repository.get_confirmed_brand_lock(run_id) is not None
    assert changed.status_code == 409
    assert changed.json() == {"detail": {"code": "brand_lock_immutable"}}


@pytest.mark.parametrize(
    ("change", "expected_code"),
    [
        ({"product_name": "Do not echo private product"}, "locked_field_changed"),
        ({"benefit_order": ["Summarize"]}, "benefit_order_invalid"),
    ],
)
def test_confirm_brand_lock_rejects_semantic_drift_without_echo(
    tmp_path, valid_run_payload, change, expected_code
) -> None:
    client, _ = make_client(tmp_path)
    proposed = {**valid_run_payload["brand_lock"], **change}
    with client:
        run_id, token = create_analyzed_run(client, valid_run_payload)
        response = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": proposed},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 422
    assert response.json() == {"detail": {"code": expected_code}}
    assert "Do not echo private product" not in response.text


def test_confirm_brand_lock_rejects_fields_outside_analysis_allowlist(
    tmp_path, valid_run_payload
) -> None:
    source_lock = {
        **valid_run_payload["brand_lock"],
        "localizable_fields": ["narrative"],
    }
    payload = {**valid_run_payload, "brand_lock": source_lock}
    proposed = {**source_lock, "localizable_fields": ["narrative", "language"]}
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_analyzed_run(client, payload)
        response = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": proposed},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "localizable_fields_invalid"}}


def test_confirm_brand_lock_requires_update_capability_and_matching_subject(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with client:
        run_id, _ = create_analyzed_run(client, valid_run_payload)
        other_run, _ = create_run(client, valid_run_payload)
        read_only = tokens.issue(
            subject=run_id,
            capabilities={Capability.READ_PROJECT_RUN},
            ttl=timedelta(minutes=5),
        )
        wrong_subject = tokens.issue(
            subject=other_run,
            capabilities={Capability.UPDATE_PROJECT_RUN},
            ttl=timedelta(minutes=5),
        )
        unauthorized = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": valid_run_payload["brand_lock"]},
            headers={"Authorization": f"Bearer {read_only}"},
        )
        forbidden = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": valid_run_payload["brand_lock"]},
            headers={"Authorization": f"Bearer {wrong_subject}"},
        )

    assert unauthorized.status_code == 401
    assert unauthorized.json() == {"detail": {"code": "invalid_capability"}}
    assert forbidden.status_code == 403
    assert forbidden.json() == {"detail": {"code": "capability_subject_mismatch"}}


def test_confirm_brand_lock_rejects_pending_run_and_sanitizes_unknown_key(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    private_key = r"C:\private\confirmation.txt"
    with client:
        run_id, token = create_run(client, valid_run_payload)
        pending = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": valid_run_payload["brand_lock"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        invalid = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": valid_run_payload["brand_lock"], private_key: "x"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert pending.status_code == 409
    assert pending.json() == {"detail": {"code": "invalid_run_state"}}
    assert invalid.status_code == 422
    assert private_key not in invalid.text


def test_confirm_brand_lock_returns_not_found_for_unknown_run(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    missing_id = str(uuid4())
    token = CapabilityTokenService(
        secret=b"a" * 32,
        audience="cultureshift-api",
    ).issue(
        subject=missing_id,
        capabilities={Capability.UPDATE_PROJECT_RUN},
        ttl=timedelta(minutes=5),
    )
    with client:
        response = client.post(
            f"/api/v1/runs/{missing_id}/brand-lock/confirm",
            json={"brand_lock": valid_run_payload["brand_lock"]},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "run_not_found"}}


def test_confirm_brand_lock_sanitizes_unexpected_repository_failure(
    tmp_path, valid_run_payload
) -> None:
    private_marker = r"C:\private\brand-lock.sqlite3"

    class FailingConfirmationRepository(SQLiteProjectRunRepository):
        def confirm_brand_lock(self, run_id, proposed, *, confirmed_at=None):
            raise RuntimeError(private_marker)

    repository = FailingConfirmationRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    client = TestClient(
        create_app(
            repository=repository,
            token_service=tokens,
            asset_store=TemporaryAssetStore(tmp_path / "assets"),
        )
    )
    run_id = str(uuid4())
    token = tokens.issue(
        subject=run_id,
        capabilities={Capability.UPDATE_PROJECT_RUN},
        ttl=timedelta(minutes=5),
    )
    with client:
        response = client.post(
            f"/api/v1/runs/{run_id}/brand-lock/confirm",
            json={"brand_lock": valid_run_payload["brand_lock"]},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 500
    assert response.json() == {
        "detail": {"code": "brand_lock_persistence_failed"}
    }
    assert private_marker not in response.text


def test_analyze_blocks_deleted_asset_without_echo(tmp_path, valid_run_payload) -> None:
    client, repository = make_client(tmp_path)
    with client:
        run_id, token, uploaded = create_uploaded_run(client, valid_run_payload)
        client.delete(
            f"/api/v1/assets/{uploaded['asset']['asset_id']}",
            headers={"Authorization": f"Bearer {uploaded['delete_capability_token']}"},
        )
        response = client.post(
            f"/api/v1/runs/{run_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "asset_lifecycle_closed"}}
    assert uploaded["delete_capability_token"] not in response.text
    assert repository.get(run_id).status.value == "blocked"


def test_get_run_returns_public_snapshot_for_read_capability(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_run(client, valid_run_payload)
        response = client.get(
            f"/api/v1/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "run_id": run_id,
        "direction": "china_to_uk",
        "status": "pending",
        "warning_codes": [],
        "created_at": response.json()["created_at"],
        "updated_at": response.json()["updated_at"],
    }
    assert token not in response.text
    assert "capability_token" not in response.text


@pytest.mark.parametrize("authorization", [None, "Basic private-value", "Bearer malformed"])
def test_get_run_rejects_missing_or_malformed_authorization_without_echo(
    tmp_path, valid_run_payload, authorization
) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, _ = create_run(client, valid_run_payload)
        headers = {} if authorization is None else {"Authorization": authorization}
        response = client.get(f"/api/v1/runs/{run_id}", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "invalid_capability"}}
    if authorization:
        assert authorization not in response.text


def test_get_run_rejects_expired_wrong_audience_and_wrong_scope_tokens(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    now = datetime.now(UTC)
    with client:
        run_id, _ = create_run(client, valid_run_payload)
        tokens = [
            CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api").issue(
                subject=run_id,
                capabilities={Capability.READ_PROJECT_RUN},
                ttl=timedelta(seconds=1),
                now=now - timedelta(seconds=2),
            ),
            CapabilityTokenService(secret=b"a" * 32, audience="other-api").issue(
                subject=run_id,
                capabilities={Capability.READ_PROJECT_RUN},
                ttl=timedelta(minutes=5),
            ),
            CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api").issue(
                subject=run_id,
                capabilities={Capability.UPDATE_PROJECT_RUN},
                ttl=timedelta(minutes=5),
            ),
        ]
        responses = [
            client.get(
                f"/api/v1/runs/{run_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            for token in tokens
        ]

    for response, token in zip(responses, tokens, strict=True):
        assert response.status_code == 401
        assert response.json() == {"detail": {"code": "invalid_capability"}}
        assert token not in response.text


def test_get_run_isolates_subject_and_missing_run(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    with client:
        first_id, first_token = create_run(client, valid_run_payload)
        second_id, second_token = create_run(client, valid_run_payload)
        mismatch = client.get(
            f"/api/v1/runs/{second_id}",
            headers={"Authorization": f"Bearer {first_token}"},
        )
        missing_id = str(uuid4())
        missing_token = CapabilityTokenService(
            secret=b"a" * 32, audience="cultureshift-api"
        ).issue(
            subject=missing_id,
            capabilities={Capability.READ_PROJECT_RUN},
            ttl=timedelta(minutes=5),
        )
        absent = client.get(
            f"/api/v1/runs/{missing_id}",
            headers={"Authorization": f"Bearer {missing_token}"},
        )

    assert first_id != second_id
    assert second_token not in mismatch.text
    assert mismatch.status_code == 403
    assert mismatch.json() == {"detail": {"code": "capability_subject_mismatch"}}
    assert absent.status_code == 404
    assert absent.json() == {"detail": {"code": "run_not_found"}}


def test_run_recovery_survives_restart_with_same_database_and_secret(
    tmp_path, valid_run_payload
) -> None:
    database = tmp_path / "runs.sqlite3"
    first_tokens = CapabilityTokenService(secret=b"s" * 32, audience="cultureshift-api")
    first_app = create_app(
        repository=SQLiteProjectRunRepository(database), token_service=first_tokens
    )
    with TestClient(first_app) as first_client:
        run_id, token = create_run(first_client, valid_run_payload)

    second_tokens = CapabilityTokenService(secret=b"s" * 32, audience="cultureshift-api")
    second_app = create_app(
        repository=SQLiteProjectRunRepository(database), token_service=second_tokens
    )
    with TestClient(second_app) as second_client:
        recovered = second_client.get(
            f"/api/v1/runs/{run_id}", headers={"Authorization": f"Bearer {token}"}
        )
    assert recovered.status_code == 200
    assert recovered.json()["run_id"] == run_id

    different_tokens = CapabilityTokenService(secret=b"x" * 32, audience="cultureshift-api")
    different_app = create_app(
        repository=SQLiteProjectRunRepository(database), token_service=different_tokens
    )
    with TestClient(different_app) as different_client:
        rejected = different_client.get(
            f"/api/v1/runs/{run_id}", headers={"Authorization": f"Bearer {token}"}
        )
    assert rejected.status_code == 401

    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(project_runs)")}
    assert not {"token", "capability_token", "secret"} & columns


def test_default_app_requires_non_secret_environment_configuration(monkeypatch) -> None:
    monkeypatch.delenv("CULTURESHIFT_CAPABILITY_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="CULTURESHIFT_CAPABILITY_SECRET") as missing:
        create_app()
    assert "secret=" not in str(missing.value)

    private_value = "private-short-value"
    monkeypatch.setenv("CULTURESHIFT_CAPABILITY_SECRET", private_value)
    with pytest.raises(RuntimeError, match="32 UTF-8 bytes") as short:
        create_app()
    assert private_value not in str(short.value)

    monkeypatch.setenv("CULTURESHIFT_CAPABILITY_SECRET", "s" * 32)
    monkeypatch.delenv("CULTURESHIFT_TEMP_ASSET_DIR", raising=False)
    with pytest.raises(RuntimeError, match="CULTURESHIFT_TEMP_ASSET_DIR"):
        create_app()


def test_upload_asset_returns_public_metadata_and_private_file(tmp_path) -> None:
    client, _ = make_client(tmp_path)
    content = b"\x89PNG\r\n\x1a\nfixture"
    with client:
        response = client.post(
            "/api/v1/assets",
            content=content,
            headers={
                "Content-Type": "image/png",
                "X-Provenance-Ref": "fixture:user-upload/day6",
                "X-Rights-Ref": "rights:authorized-upload/day6",
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["asset"]["kind"] == "source_ad"
    assert body["asset"]["media_type"] == "image/png"
    assert body["size_bytes"] == len(content)
    assert "expires_at" in body["asset"]
    assert len(body["delete_capability_token"]) >= 16
    assert response.text.find(content.hex()) == -1
    stored = list((tmp_path / "assets").glob("*.png"))
    assert len(stored) == 1
    assert stored[0].read_bytes() == content
    metadata = next((tmp_path / "assets").glob("*.meta.json")).read_text(encoding="utf-8")
    assert body["delete_capability_token"] not in metadata


@pytest.mark.parametrize(
    ("content", "media_type", "code"),
    [
        (b"", "image/png", "asset_empty"),
        (b"<svg>private</svg>", "image/svg+xml", "unsupported_asset_type"),
        (b"\x89PNG\r\n\x1a\nprivate", "image/jpeg", "asset_type_mismatch"),
    ],
)
def test_upload_asset_fails_closed_without_echo(tmp_path, content, media_type, code) -> None:
    client, _ = make_client(tmp_path)
    private_reference = r"C:\private\source.png"
    with client:
        response = client.post(
            "/api/v1/assets",
            content=content,
            headers={
                "Content-Type": media_type,
                "X-Provenance-Ref": "fixture:user-upload/day6",
                "X-Rights-Ref": "rights:authorized-upload/day6",
                "X-Original-Filename": private_reference,
            },
        )

    assert response.status_code in {400, 413, 415, 422}
    assert response.json() == {"detail": {"code": code}}
    assert private_reference not in response.text
    assert "private" not in response.text


def test_upload_asset_hides_unexpected_storage_failure(tmp_path) -> None:
    class FailingStore(TemporaryAssetStore):
        def store(self, *args, **kwargs):
            raise RuntimeError("private storage detail")

    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    application = create_app(
        repository=repository,
        token_service=tokens,
        asset_store=FailingStore(tmp_path / "assets"),
    )
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/assets",
            content=b"\x89PNG\r\n\x1a\nfixture",
            headers={
                "Content-Type": "image/png",
                "X-Provenance-Ref": "fixture:user-upload/day6",
                "X-Rights-Ref": "rights:authorized-upload/day6",
            },
        )
    assert response.status_code == 500
    assert response.json() == {"detail": {"code": "asset_storage_failed"}}
    assert "private storage detail" not in response.text


def test_delete_asset_requires_matching_one_time_capability_and_is_idempotent(tmp_path) -> None:
    client, _ = make_client(tmp_path)
    content = b"\x89PNG\r\n\x1a\nfixture"
    headers = {
        "Content-Type": "image/png",
        "X-Provenance-Ref": "fixture:user-upload/day7",
        "X-Rights-Ref": "rights:authorized-upload/day7",
    }
    with client:
        uploaded = client.post("/api/v1/assets", content=content, headers=headers).json()
        asset_id = uploaded["asset"]["asset_id"]
        token = uploaded["delete_capability_token"]
        deleted = client.delete(
            f"/api/v1/assets/{asset_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        repeated = client.delete(
            f"/api/v1/assets/{asset_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert deleted.status_code == repeated.status_code == 204
    assert not list((tmp_path / "assets").glob(f"{asset_id}.*"))


def test_delete_asset_rejects_wrong_subject_without_echo(tmp_path) -> None:
    client, _ = make_client(tmp_path)
    wrong_id = uuid4()
    token = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api").issue(
        subject=str(uuid4()),
        capabilities={Capability.DELETE_ASSET},
        ttl=timedelta(minutes=5),
    )
    with client:
        response = client.delete(
            f"/api/v1/assets/{wrong_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json() == {"detail": {"code": "capability_subject_mismatch"}}
    assert token not in response.text


def test_delete_asset_rejects_missing_capability(tmp_path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        response = client.delete(f"/api/v1/assets/{uuid4()}")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "invalid_capability"}}


def test_upload_rate_limit_is_generic_and_does_not_write_second_asset(tmp_path) -> None:
    limiter = FixedWindowRateLimiter(limit=1, window=timedelta(minutes=1))
    client, _ = make_client(tmp_path, upload_rate_limiter=limiter)
    headers = {
        "Content-Type": "image/png",
        "X-Provenance-Ref": "fixture:user-upload/day7",
        "X-Rights-Ref": "rights:authorized-upload/day7",
    }
    with client:
        first = client.post("/api/v1/assets", content=b"\x89PNG\r\n\x1a\none", headers=headers)
        second = client.post(
            "/api/v1/assets", content=b"\x89PNG\r\n\x1a\nprivate-second", headers=headers
        )

    assert first.status_code == 201
    assert second.status_code == 429
    assert second.json() == {"detail": {"code": "upload_rate_limited"}}
    assert "private-second" not in second.text
    assert len(list((tmp_path / "assets").glob("*.png"))) == 1


def test_startup_purges_expired_assets(tmp_path, valid_run_payload) -> None:
    store = TemporaryAssetStore(tmp_path / "assets")
    old = datetime.now(UTC) - timedelta(hours=25)
    uploaded = store.store(
        b"\x89PNG\r\n\x1a\nold",
        declared_media_type="image/png",
        provenance_ref="fixture:user-upload/day7",
        rights_ref="rights:authorized-upload/day7",
        now=old,
    )
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")

    with TestClient(
        create_app(repository=repository, token_service=tokens, asset_store=store)
    ) as client:
        assert client.get("/healthz").status_code == 200

    assert not list((tmp_path / "assets").glob(f"{uploaded.asset.asset_id}.*"))
