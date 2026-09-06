from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from uuid import UUID

from cultureshift.cloud_storage import ObjectNotFoundError, ObjectStorageError, ObjectStore


class CompositionArtifactError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredCompositionArtifact:
    artifact_id: UUID
    sha256: str
    size_bytes: int
    expires_at: datetime


@dataclass(frozen=True)
class LoadedCompositionArtifact:
    record: StoredCompositionArtifact
    png_bytes: bytes


class CompositionArtifactStore:
    def __init__(self, root: str | Path, *, max_bytes: int = 10 * 1024 * 1024) -> None:
        self._root = Path(root)
        self._max_bytes = max_bytes
        self._lock = Lock()

    def _png_path(self, artifact_id: UUID) -> Path:
        return self._root / f"{artifact_id}.png"

    def _metadata_path(self, artifact_id: UUID) -> Path:
        return self._root / f"{artifact_id}.json"

    @staticmethod
    def _require_utc(value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise CompositionArtifactError("composition artifact unavailable")
        return value

    @staticmethod
    def _exclusive_write(path: Path, data: bytes) -> None:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

    def save(
        self, artifact_id: UUID, png_bytes: bytes, *, expires_at: datetime
    ) -> StoredCompositionArtifact:
        expiration = self._require_utc(expires_at)
        if (
            not png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
            or len(png_bytes) < 9
            or len(png_bytes) > self._max_bytes
        ):
            raise CompositionArtifactError("composition artifact unavailable")
        digest = hashlib.sha256(png_bytes).hexdigest()
        record = StoredCompositionArtifact(artifact_id, digest, len(png_bytes), expiration)
        encoded = json.dumps(
            {
                "artifact_id": str(artifact_id),
                "expires_at": expiration.isoformat(),
                "sha256": digest,
                "size_bytes": len(png_bytes),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        self._root.mkdir(parents=True, exist_ok=True)
        png_path = self._png_path(artifact_id)
        metadata_path = self._metadata_path(artifact_id)
        with self._lock:
            if png_path.exists() or metadata_path.exists():
                existing = self._load_unlocked(
                    artifact_id, now=datetime.now(UTC), check_expiry=False
                )
                if existing.record == record and existing.png_bytes == png_bytes:
                    return record
                raise CompositionArtifactError("composition artifact unavailable")
            png_part = png_path.with_suffix(".png.part")
            metadata_part = metadata_path.with_suffix(".json.part")
            try:
                self._exclusive_write(png_part, png_bytes)
                self._exclusive_write(metadata_part, encoded)
                os.replace(png_part, png_path)
                os.replace(metadata_part, metadata_path)
            except OSError as error:
                for path in (png_part, metadata_part, png_path, metadata_path):
                    path.unlink(missing_ok=True)
                raise CompositionArtifactError("composition artifact unavailable") from error
        return record

    def _load_unlocked(
        self, artifact_id: UUID, *, now: datetime, check_expiry: bool
    ) -> LoadedCompositionArtifact:
        try:
            metadata = json.loads(self._metadata_path(artifact_id).read_text(encoding="ascii"))
            content = self._png_path(artifact_id).read_bytes()
            record = StoredCompositionArtifact(
                artifact_id=UUID(metadata["artifact_id"]),
                sha256=metadata["sha256"],
                size_bytes=metadata["size_bytes"],
                expires_at=self._require_utc(datetime.fromisoformat(metadata["expires_at"])),
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise CompositionArtifactError("composition artifact unavailable") from error
        if (
            record.artifact_id != artifact_id
            or record.size_bytes != len(content)
            or record.size_bytes < 9
            or record.size_bytes > self._max_bytes
            or hashlib.sha256(content).hexdigest() != record.sha256
            or not content.startswith(b"\x89PNG\r\n\x1a\n")
            or (check_expiry and record.expires_at <= now)
        ):
            raise CompositionArtifactError("composition artifact unavailable")
        return LoadedCompositionArtifact(record, content)

    def load(self, artifact_id: UUID, *, now: datetime | None = None) -> LoadedCompositionArtifact:
        checked_at = self._require_utc(now or datetime.now(UTC))
        with self._lock:
            return self._load_unlocked(artifact_id, now=checked_at, check_expiry=True)

    def delete(self, artifact_id: UUID) -> bool:
        removed = False
        with self._lock:
            for path in (self._png_path(artifact_id), self._metadata_path(artifact_id)):
                if path.exists():
                    path.unlink()
                    removed = True
        return removed


class CloudCompositionArtifactStore:
    def __init__(
        self,
        objects: ObjectStore,
        prefix: str = "compositions/",
        *,
        max_bytes: int = 10 * 1024 * 1024,
    ) -> None:
        self._objects = objects
        self._prefix = prefix.strip("/") + "/"
        self._max_bytes = max_bytes

    def _key(self, artifact_id: UUID, suffix: str) -> str:
        return f"{self._prefix}{artifact_id}.{suffix}"

    def save(
        self, artifact_id: UUID, png_bytes: bytes, *, expires_at: datetime
    ) -> StoredCompositionArtifact:
        expiration = CompositionArtifactStore._require_utc(expires_at)
        if not png_bytes.startswith(b"\x89PNG\r\n\x1a\n") or len(png_bytes) > self._max_bytes:
            raise CompositionArtifactError("composition artifact unavailable")
        digest = hashlib.sha256(png_bytes).hexdigest()
        record = StoredCompositionArtifact(artifact_id, digest, len(png_bytes), expiration)
        metadata = json.dumps(
            {
                "artifact_id": str(artifact_id),
                "sha256": digest,
                "size_bytes": len(png_bytes),
                "expires_at": expiration.isoformat(),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        try:
            existing = self.load(artifact_id, now=datetime.now(UTC), check_expiry=False)
            if existing.record == record and existing.png_bytes == png_bytes:
                return record
            raise CompositionArtifactError("composition artifact unavailable")
        except CompositionArtifactError:
            try:
                self._objects.put(
                    self._key(artifact_id, "png"),
                    png_bytes,
                    content_type="image/png",
                    create_only=True,
                )
                self._objects.put(
                    self._key(artifact_id, "json"),
                    metadata,
                    content_type="application/json",
                    create_only=True,
                )
            except (ObjectStorageError, FileExistsError) as error:
                raise CompositionArtifactError("composition artifact unavailable") from error
        return record

    def load(
        self, artifact_id: UUID, *, now: datetime | None = None, check_expiry: bool = True
    ) -> LoadedCompositionArtifact:
        checked_at = CompositionArtifactStore._require_utc(now or datetime.now(UTC))
        try:
            metadata = json.loads(
                self._objects.get(self._key(artifact_id, "json"), max_bytes=64 * 1024)
            )
            content = self._objects.get(self._key(artifact_id, "png"), max_bytes=self._max_bytes)
            record = StoredCompositionArtifact(
                UUID(metadata["artifact_id"]),
                metadata["sha256"],
                metadata["size_bytes"],
                CompositionArtifactStore._require_utc(
                    datetime.fromisoformat(metadata["expires_at"])
                ),
            )
        except (ObjectNotFoundError, ObjectStorageError, KeyError, TypeError, ValueError) as error:
            raise CompositionArtifactError("composition artifact unavailable") from error
        if (
            record.artifact_id != artifact_id
            or record.size_bytes != len(content)
            or hashlib.sha256(content).hexdigest() != record.sha256
            or (check_expiry and record.expires_at <= checked_at)
        ):
            raise CompositionArtifactError("composition artifact unavailable")
        return LoadedCompositionArtifact(record, content)

    def delete(self, artifact_id: UUID) -> bool:
        return bool(
            self._objects.delete((self._key(artifact_id, "png"), self._key(artifact_id, "json")))
        )
