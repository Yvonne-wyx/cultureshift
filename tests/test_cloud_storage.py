from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from cultureshift.app import _stores_from_environment
from cultureshift.asset_storage import AssetLifecycleClosedError, CloudAssetStore
from cultureshift.cloud_storage import ObjectNotFoundError
from cultureshift.composition_storage import (
    CloudCompositionArtifactStore,
    CompositionArtifactError,
)

PNG = b"\x89PNG\r\n\x1a\ncloud-fixture"


class MemoryObjects:
    def __init__(self) -> None:
        self.values: dict[str, tuple[bytes, str]] = {}

    def put(self, key: str, content: bytes, *, content_type: str, create_only: bool) -> None:
        if create_only and key in self.values:
            raise FileExistsError(key)
        self.values[key] = (content, content_type)

    def get(self, key: str, *, max_bytes: int) -> bytes:
        try:
            value = self.values[key][0]
        except KeyError as error:
            raise ObjectNotFoundError from error
        if len(value) > max_bytes:
            raise ValueError("bounded read exceeded")
        return value

    def delete(self, keys: tuple[str, ...]) -> int:
        removed = 0
        for key in keys:
            removed += self.values.pop(key, None) is not None
        return removed

    def list(self, prefix: str) -> tuple[str, ...]:
        return tuple(key for key in self.values if key.startswith(prefix))


def test_cloud_asset_store_preserves_integrity_expiry_and_deletion() -> None:
    objects = MemoryObjects()
    store = CloudAssetStore(objects)
    now = datetime(2026, 9, 6, 10, 0, tzinfo=UTC)

    stored = store.store(
        PNG,
        declared_media_type="image/png",
        provenance_ref="fixture:cloud/source",
        rights_ref="rights:authorized/cloud",
        now=now,
    )

    assert store.load(stored.asset.asset_id, now=now + timedelta(hours=1)).content == PNG
    assert store.delete(stored.asset.asset_id, now=now + timedelta(hours=2)) is True
    with pytest.raises(AssetLifecycleClosedError):
        store.load(stored.asset.asset_id, now=now + timedelta(hours=3))


def test_cloud_composition_store_is_immutable_and_bounded() -> None:
    objects = MemoryObjects()
    store = CloudCompositionArtifactStore(objects)
    artifact_id = uuid4()
    now = datetime(2026, 9, 6, 10, 0, tzinfo=UTC)

    first = store.save(artifact_id, PNG, expires_at=now + timedelta(hours=1))
    assert store.save(artifact_id, PNG, expires_at=now + timedelta(hours=1)) == first
    assert store.load(artifact_id, now=now).png_bytes == PNG

    with pytest.raises(CompositionArtifactError):
        store.save(artifact_id, PNG + b"changed", expires_at=now + timedelta(hours=1))


def test_production_storage_configuration_fails_closed_when_incomplete(monkeypatch) -> None:
    monkeypatch.delenv("CULTURESHIFT_TEMP_ASSET_DIR", raising=False)
    monkeypatch.setenv("CULTURESHIFT_OBJECT_STORAGE_URL", "https://example.supabase.co")
    monkeypatch.delenv("CULTURESHIFT_OBJECT_STORAGE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    with pytest.raises(RuntimeError, match="object storage configuration is incomplete"):
        _stores_from_environment()


def test_storage_accepts_vercel_supabase_environment(monkeypatch) -> None:
    monkeypatch.delenv("CULTURESHIFT_OBJECT_STORAGE_URL", raising=False)
    monkeypatch.delenv("CULTURESHIFT_OBJECT_STORAGE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")

    asset_store, composition_store = _stores_from_environment()

    assert isinstance(asset_store, CloudAssetStore)
    assert isinstance(composition_store, CloudCompositionArtifactStore)


def test_storage_prefers_service_role_key_for_legacy_storage_api(monkeypatch) -> None:
    monkeypatch.delenv("CULTURESHIFT_OBJECT_STORAGE_URL", raising=False)
    monkeypatch.delenv("CULTURESHIFT_OBJECT_STORAGE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "new-secret-key")

    asset_store, _ = _stores_from_environment()

    assert asset_store._objects._service_key == "service-role-key"


def test_storage_normalizes_platform_wrapped_supabase_url(monkeypatch) -> None:
    monkeypatch.delenv("CULTURESHIFT_OBJECT_STORAGE_URL", raising=False)
    monkeypatch.delenv("CULTURESHIFT_OBJECT_STORAGE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_URL", '"https://example.supabase.co"')
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")

    asset_store, composition_store = _stores_from_environment()

    assert isinstance(asset_store, CloudAssetStore)
    assert isinstance(composition_store, CloudCompositionArtifactStore)


def test_storage_uses_private_bucket_when_optional_variable_is_blank(monkeypatch) -> None:
    monkeypatch.setenv("CULTURESHIFT_OBJECT_STORAGE_URL", "https://example.supabase.co")
    monkeypatch.setenv("CULTURESHIFT_OBJECT_STORAGE_KEY", "service-role-key")
    monkeypatch.setenv("CULTURESHIFT_OBJECT_STORAGE_BUCKET", "")

    asset_store, composition_store = _stores_from_environment()

    assert isinstance(asset_store, CloudAssetStore)
    assert isinstance(composition_store, CloudCompositionArtifactStore)
