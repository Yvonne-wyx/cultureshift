from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from uuid import UUID

from PIL import Image, UnidentifiedImageError

from cultureshift.composition_storage import (
    CompositionArtifactError,
    CompositionArtifactStore,
)
from cultureshift.contracts import CompositionGenerated
from cultureshift.repository import ProjectRunNotFoundError, SQLiteProjectRunRepository


class CompositionExportErrorCode(StrEnum):
    RUN_NOT_FOUND = "run_not_found"
    COMPOSITION_UNAVAILABLE = "composition_unavailable"
    ARTIFACT_UNAVAILABLE = "composition_artifact_unavailable"


class CompositionExportError(RuntimeError):
    def __init__(self, code: CompositionExportErrorCode) -> None:
        self.code = code
        super().__init__("composition export failed")


@dataclass(frozen=True)
class ExportedComposition:
    png_bytes: bytes
    sha256: str
    size_bytes: int


class CompositionExportService:
    def __init__(
        self,
        repository: SQLiteProjectRunRepository,
        artifact_store: CompositionArtifactStore,
    ) -> None:
        self._repository = repository
        self._artifact_store = artifact_store

    def _summary(self, run_id: UUID) -> CompositionGenerated:
        try:
            summary = self._repository.get_composition(run_id)
        except ProjectRunNotFoundError:
            raise CompositionExportError(CompositionExportErrorCode.RUN_NOT_FOUND) from None
        if summary is None:
            raise CompositionExportError(
                CompositionExportErrorCode.COMPOSITION_UNAVAILABLE
            )
        return summary

    def export_png(self, run_id: UUID) -> ExportedComposition:
        summary = self._summary(run_id)
        try:
            loaded = self._artifact_store.load(summary.artifact_id)
            if (
                loaded.record.artifact_id != summary.artifact_id
                or loaded.record.sha256 != summary.rendered_sha256
                or loaded.record.size_bytes != len(loaded.png_bytes)
            ):
                raise CompositionArtifactError("composition artifact unavailable")
            with Image.open(BytesIO(loaded.png_bytes)) as image:
                if image.format != "PNG" or image.size != (summary.width, summary.height):
                    raise CompositionArtifactError("composition artifact unavailable")
                image.load()
        except (CompositionArtifactError, OSError, UnidentifiedImageError):
            raise CompositionExportError(
                CompositionExportErrorCode.ARTIFACT_UNAVAILABLE
            ) from None
        return ExportedComposition(
            png_bytes=loaded.png_bytes,
            sha256=loaded.record.sha256,
            size_bytes=loaded.record.size_bytes,
        )

    def export_json(self, run_id: UUID) -> bytes:
        summary = self._summary(run_id)
        return (
            json.dumps(
                summary.model_dump(mode="json"),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )
