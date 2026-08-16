from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4

from pydantic import TypeAdapter, ValidationError

from cultureshift.contracts import AssetKind, PublicReference, SourceAdAssetRef

MAX_ASSET_BYTES = 10 * 1024 * 1024
ASSET_TTL = timedelta(hours=24)
TOMBSTONE_TTL = timedelta(days=7)
_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg"}
_PUBLIC_REFERENCE = TypeAdapter(PublicReference)


class AssetUploadError(ValueError):
    pass


class AssetEmptyError(AssetUploadError):
    pass


class AssetTooLargeError(AssetUploadError):
    pass


class UnsupportedAssetTypeError(AssetUploadError):
    pass


class AssetTypeMismatchError(AssetUploadError):
    pass


class AssetMetadataError(AssetUploadError):
    pass


class AssetLifecycleClosedError(AssetUploadError):
    pass


class AssetStorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredAsset:
    asset: SourceAdAssetRef
    size_bytes: int
    created_at: datetime


def detect_media_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
        return "image/jpeg"
    return None


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("time must use UTC")
    return value


class TemporaryAssetStore:
    def __init__(self, root: str | Path) -> None:
        value = str(root).strip()
        if not value:
            raise ValueError("temporary asset root is required")
        self._root = Path(value)
        self._lock = Lock()

    def _tombstone_path(self, asset_id: UUID) -> Path:
        digest = hashlib.sha256(str(asset_id).encode("ascii")).hexdigest()
        return self._root / "tombstones" / f"{digest}.json"

    def _is_closed(self, asset_id: UUID) -> bool:
        return self._tombstone_path(asset_id).is_file()

    @staticmethod
    def _write_exclusive(path: Path, data: bytes) -> None:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

    def store(
        self,
        data: bytes,
        *,
        declared_media_type: str,
        provenance_ref: str,
        rights_ref: str,
        now: datetime | None = None,
        asset_id: UUID | None = None,
    ) -> StoredAsset:
        if declared_media_type not in _EXTENSIONS:
            raise UnsupportedAssetTypeError("unsupported asset type")
        if not data:
            raise AssetEmptyError("asset is empty")
        if len(data) > MAX_ASSET_BYTES:
            raise AssetTooLargeError("asset exceeds size limit")
        detected = detect_media_type(data)
        if detected != declared_media_type:
            raise AssetTypeMismatchError("declared and detected asset types differ")
        try:
            safe_provenance = _PUBLIC_REFERENCE.validate_python(provenance_ref)
            safe_rights = _PUBLIC_REFERENCE.validate_python(rights_ref)
        except ValidationError as error:
            raise AssetMetadataError("invalid asset metadata") from error

        created_at = _require_utc(now or datetime.now(UTC))
        identifier = asset_id or uuid4()
        extension = _EXTENSIONS[detected]
        expires_at = created_at + ASSET_TTL
        stored = StoredAsset(
            asset=SourceAdAssetRef(
                asset_id=identifier,
                kind=AssetKind.SOURCE_AD,
                media_type=detected,
                sha256=hashlib.sha256(data).hexdigest(),
                provenance_ref=safe_provenance,
                rights_ref=safe_rights,
                expires_at=expires_at,
            ),
            size_bytes=len(data),
            created_at=created_at,
        )
        metadata = {
            "asset": stored.asset.model_dump(mode="json"),
            "created_at": created_at.isoformat(),
            "size_bytes": stored.size_bytes,
        }
        encoded_metadata = (
            json.dumps(metadata, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"
        ).encode("utf-8")
        part_path = self._root / f"{identifier}.part"
        metadata_part_path = self._root / f"{identifier}.meta.part"
        final_path = self._root / f"{identifier}.{extension}"
        metadata_path = self._root / f"{identifier}.meta.json"

        with self._lock:
            if self._is_closed(identifier):
                raise AssetLifecycleClosedError("asset lifecycle is closed")
            try:
                self._root.mkdir(parents=True, exist_ok=True)
                self._write_exclusive(part_path, data)
                self._write_exclusive(metadata_part_path, encoded_metadata)
                if self._is_closed(identifier):
                    raise AssetLifecycleClosedError("asset lifecycle is closed")
                os.replace(part_path, final_path)
                if self._is_closed(identifier):
                    raise AssetLifecycleClosedError("asset lifecycle is closed")
                os.replace(metadata_part_path, metadata_path)
                if self._is_closed(identifier):
                    raise AssetLifecycleClosedError("asset lifecycle is closed")
            except AssetLifecycleClosedError:
                for path in (part_path, metadata_part_path, final_path, metadata_path):
                    path.unlink(missing_ok=True)
                raise
            except OSError as error:
                for path in (part_path, metadata_part_path, final_path, metadata_path):
                    path.unlink(missing_ok=True)
                raise AssetStorageError("temporary asset write failed") from error
        return stored

    def delete(
        self,
        asset_id: UUID,
        *,
        now: datetime | None = None,
        reason: str = "deleted",
    ) -> bool:
        deleted_at = _require_utc(now or datetime.now(UTC))
        tombstone = self._tombstone_path(asset_id)
        with self._lock:
            active_paths = list(self._root.glob(f"{asset_id}.*")) if self._root.exists() else []
            existed = any(path.is_file() for path in active_paths)
            if not tombstone.exists():
                tombstone.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "deleted_at": deleted_at.isoformat(),
                    "reason": reason,
                    "result": "removed" if existed else "already_absent",
                }
                part = tombstone.with_suffix(".part")
                try:
                    self._write_exclusive(
                        part,
                        (
                            json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
                        ).encode("utf-8"),
                    )
                    os.replace(part, tombstone)
                except OSError as error:
                    part.unlink(missing_ok=True)
                    raise AssetStorageError("asset deletion failed") from error
            try:
                for path in active_paths:
                    path.unlink(missing_ok=True)
            except OSError as error:
                raise AssetStorageError("asset deletion failed") from error
        return existed

    def purge_expired(self, now: datetime | None = None) -> int:
        purge_at = _require_utc(now or datetime.now(UTC))
        if not self._root.exists():
            return 0
        expired: list[UUID] = []
        try:
            for metadata_path in self._root.glob("*.meta.json"):
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                asset = SourceAdAssetRef.model_validate(metadata["asset"])
                if asset.expires_at is not None and asset.expires_at <= purge_at:
                    expired.append(asset.asset_id)
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
            raise AssetStorageError("temporary asset metadata is invalid") from error

        removed = sum(self.delete(asset_id, now=purge_at, reason="expired") for asset_id in expired)
        tombstone_cutoff = purge_at - TOMBSTONE_TTL
        for tombstone in (self._root / "tombstones").glob("*.json"):
            try:
                payload = json.loads(tombstone.read_text(encoding="utf-8"))
                deleted_at = datetime.fromisoformat(payload["deleted_at"])
                if _require_utc(deleted_at) <= tombstone_cutoff:
                    tombstone.unlink(missing_ok=True)
            except (OSError, KeyError, ValueError, json.JSONDecodeError):
                continue
        return removed
