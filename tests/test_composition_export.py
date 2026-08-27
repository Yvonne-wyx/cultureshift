from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from io import BytesIO
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from PIL import Image

from cultureshift.composition_export import (
    CompositionExportError,
    CompositionExportErrorCode,
    CompositionExportService,
)
from cultureshift.composition_storage import CompositionArtifactStore
from cultureshift.contracts import CompositionGenerated, CompositionLayer
from cultureshift.repository import ProjectRunNotFoundError


class SummaryRepository:
    def __init__(
        self,
        summary: CompositionGenerated | None,
        *,
        revision: object | None = None,
        run_exists: bool = True,
    ) -> None:
        self._summary = summary
        self._revision = revision
        self._run_exists = run_exists

    def get_composition(self, run_id: UUID) -> CompositionGenerated | None:
        if not self._run_exists:
            raise ProjectRunNotFoundError(str(run_id))
        return self._summary

    def get_revision(self, run_id: UUID) -> object | None:
        if not self._run_exists:
            raise ProjectRunNotFoundError(str(run_id))
        return self._revision


def _png(size: tuple[int, int] = (1600, 900), color: str = "#e8f0f6") -> bytes:
    output = BytesIO()
    Image.new("RGBA", size, color).save(output, "PNG", compress_level=9)
    return output.getvalue()


def _summary(run_id: UUID, artifact_id: UUID, png_bytes: bytes) -> CompositionGenerated:
    specs = (
        ("background", None, (0, 0, 1600, 900), "1"),
        ("product_ui", "a2222222-2222-4222-8222-222222222222", (850, 170, 1500, 615), "2"),
        ("logo", "a1111111-1111-4111-8111-111111111111", (100, 70, 320, 143), "3"),
        ("headline", None, (100, 220, 760, 344), "4"),
        ("body", None, (100, 390, 780, 476), "5"),
        ("cta", None, (100, 560, 430, 636), "6"),
        ("disclosure", None, (100, 820, 530, 864), "7"),
    )
    layers = tuple(
        CompositionLayer(
            kind=kind,
            source_asset_id=source,
            rgba_sha256=digit * 64,
            bounds=bounds,
            width=bounds[2] - bounds[0],
            height=bounds[3] - bounds[1],
        )
        for kind, source, bounds, digit in specs
    )
    return CompositionGenerated(
        run_id=run_id,
        status="in_progress",
        execution_mode="fixture",
        width=1600,
        height=900,
        media_type="image/png",
        rendered_sha256=hashlib.sha256(png_bytes).hexdigest(),
        artifact_id=artifact_id,
        layers=layers,
        disclosure="Fixture Demo / 非实时模型",
        generated_at=datetime(2026, 8, 23, 9, 0, tzinfo=UTC),
    )


def test_export_service_returns_verified_png_and_canonical_json(tmp_path) -> None:
    run_id, artifact_id = uuid4(), uuid4()
    png_bytes = _png()
    summary = _summary(run_id, artifact_id, png_bytes)
    store = CompositionArtifactStore(tmp_path / "compositions")
    store.save(artifact_id, png_bytes, expires_at=datetime.now(UTC) + timedelta(hours=1))
    service = CompositionExportService(SummaryRepository(summary), store)

    exported = service.export_png(run_id)
    encoded = service.export_json(run_id)

    assert exported.png_bytes == png_bytes
    assert exported.sha256 == summary.rendered_sha256
    assert exported.size_bytes == len(png_bytes)
    assert encoded.endswith(b"\n")
    assert json.loads(encoded) == summary.model_dump(mode="json")
    assert encoded == json.dumps(
        summary.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8") + b"\n"


def test_export_service_selects_immutable_version_one_and_two(tmp_path) -> None:
    run_id = uuid4()
    initial_bytes = _png()
    revised_bytes = _png(color="#d9e7dc")
    initial = _summary(run_id, uuid4(), initial_bytes)
    revised = _summary(run_id, uuid4(), revised_bytes).model_copy(
        update={"rendered_sha256": hashlib.sha256(revised_bytes).hexdigest()}
    )
    store = CompositionArtifactStore(tmp_path / "compositions")
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    store.save(initial.artifact_id, initial_bytes, expires_at=expires_at)
    store.save(revised.artifact_id, revised_bytes, expires_at=expires_at)
    service = CompositionExportService(
        SummaryRepository(initial, revision=SimpleNamespace(composition=revised)),
        store,
    )

    assert json.loads(service.export_json(run_id, 1))["artifact_id"] == str(
        initial.artifact_id
    )
    assert json.loads(service.export_json(run_id, 2))["artifact_id"] == str(
        revised.artifact_id
    )
    assert service.export_png(run_id, 1).png_bytes == initial_bytes
    assert service.export_png(run_id, 2).png_bytes == revised_bytes


def test_export_service_rejects_absent_or_unknown_version(tmp_path) -> None:
    run_id = uuid4()
    initial_bytes = _png()
    initial = _summary(run_id, uuid4(), initial_bytes)
    store = CompositionArtifactStore(tmp_path / "compositions")
    store.save(
        initial.artifact_id,
        initial_bytes,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    service = CompositionExportService(SummaryRepository(initial), store)

    with pytest.raises(CompositionExportError) as missing:
        service.export_png(run_id, 2)
    assert missing.value.code is CompositionExportErrorCode.COMPOSITION_UNAVAILABLE
    with pytest.raises(ValueError, match="unsupported result version"):
        service.export_json(run_id, 3)


def test_export_service_distinguishes_missing_run_and_composition(tmp_path) -> None:
    run_id = uuid4()
    store = CompositionArtifactStore(tmp_path / "compositions")
    with pytest.raises(CompositionExportError) as missing_run:
        CompositionExportService(SummaryRepository(None, run_exists=False), store).export_json(
            run_id
        )
    assert missing_run.value.code is CompositionExportErrorCode.RUN_NOT_FOUND
    assert str(missing_run.value) == "composition export failed"

    with pytest.raises(CompositionExportError) as missing_composition:
        CompositionExportService(SummaryRepository(None), store).export_png(run_id)
    assert missing_composition.value.code is CompositionExportErrorCode.COMPOSITION_UNAVAILABLE


@pytest.mark.parametrize("mutation", ["missing", "expired", "hash", "dimensions"])
def test_export_service_fails_closed_for_unavailable_or_inconsistent_artifact(
    tmp_path,
    mutation: str,
) -> None:
    run_id, artifact_id = uuid4(), uuid4()
    png_bytes = _png((1, 1) if mutation == "dimensions" else (1600, 900))
    summary = _summary(run_id, artifact_id, png_bytes)
    if mutation == "hash":
        summary = summary.model_copy(update={"rendered_sha256": "f" * 64})
    store = CompositionArtifactStore(tmp_path / mutation)
    if mutation != "missing":
        expires_at = datetime.now(UTC) + (
            timedelta(seconds=-1) if mutation == "expired" else timedelta(hours=1)
        )
        store.save(artifact_id, png_bytes, expires_at=expires_at)
    service = CompositionExportService(SummaryRepository(summary), store)

    with pytest.raises(CompositionExportError) as caught:
        service.export_png(run_id)

    assert caught.value.code is CompositionExportErrorCode.ARTIFACT_UNAVAILABLE
    assert str(caught.value) == "composition export failed"
