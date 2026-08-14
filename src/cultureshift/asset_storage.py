from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from cultureshift.contracts import AssetKind, AssetUploaded, PublicReference, SourceAdAssetRef

MAX_ASSET_BYTES = 10 * 1024 * 1024
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


class AssetStorageError(RuntimeError):
    pass


def _detected_media_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
        return "image/jpeg"
    return None


class TemporaryAssetStore:
    def __init__(self, root: str | Path) -> None:
        value = str(root).strip()
        if not value:
            raise ValueError("temporary asset root is required")
        self._root = Path(value)

    def store(
        self,
        data: bytes,
        *,
        declared_media_type: str,
        provenance_ref: str,
        rights_ref: str,
        now: datetime | None = None,
    ) -> AssetUploaded:
        if declared_media_type not in _EXTENSIONS:
            raise UnsupportedAssetTypeError("unsupported asset type")
        if not data:
            raise AssetEmptyError("asset is empty")
        if len(data) > MAX_ASSET_BYTES:
            raise AssetTooLargeError("asset exceeds size limit")
        detected = _detected_media_type(data)
        if detected != declared_media_type:
            raise AssetTypeMismatchError("declared and detected asset types differ")
        try:
            safe_provenance = _PUBLIC_REFERENCE.validate_python(provenance_ref)
            safe_rights = _PUBLIC_REFERENCE.validate_python(rights_ref)
        except ValidationError as error:
            raise AssetMetadataError("invalid asset metadata") from error

        created_at = now or datetime.now(UTC)
        if created_at.tzinfo is None or created_at.utcoffset() != timedelta(0):
            raise ValueError("now must use UTC")
        asset_id = uuid4()
        extension = _EXTENSIONS[detected]
        expires_at = created_at + timedelta(hours=24)
        uploaded = AssetUploaded(
            asset=SourceAdAssetRef(
                asset_id=asset_id,
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
        part_path = self._root / f"{asset_id}.part"
        final_path = self._root / f"{asset_id}.{extension}"
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(part_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(part_path, final_path)
        except OSError as error:
            part_path.unlink(missing_ok=True)
            raise AssetStorageError("temporary asset write failed") from error

        return uploaded
