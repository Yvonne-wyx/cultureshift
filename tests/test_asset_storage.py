from datetime import UTC, datetime, timedelta

import pytest

from cultureshift.asset_storage import (
    MAX_ASSET_BYTES,
    AssetEmptyError,
    AssetLifecycleClosedError,
    AssetMetadataError,
    AssetTooLargeError,
    AssetTypeMismatchError,
    TemporaryAssetStore,
    UnsupportedAssetTypeError,
    detect_media_type,
)

PNG = b"\x89PNG\r\n\x1a\nfixture"
JPEG = b"\xff\xd8\xfffixture\xff\xd9"


@pytest.mark.parametrize(
    ("data", "expected"),
    [(PNG, "image/png"), (JPEG, "image/jpeg"), (b"not-an-image", None)],
)
def test_shared_media_detector_matches_upload_signatures(data, expected) -> None:
    assert detect_media_type(data) == expected


def test_store_writes_private_uuid_asset_atomically_with_public_metadata(tmp_path) -> None:
    store = TemporaryAssetStore(tmp_path)
    now = datetime(2026, 8, 14, 8, 0, tzinfo=UTC)

    uploaded = store.store(
        PNG,
        declared_media_type="image/png",
        provenance_ref="fixture:user-upload/day6",
        rights_ref="rights:authorized-upload/day6",
        now=now,
    )

    assert uploaded.asset.kind == "source_ad"
    assert uploaded.asset.media_type == "image/png"
    assert uploaded.asset.expires_at == now + timedelta(hours=24)
    assert uploaded.created_at == now
    assert uploaded.size_bytes == len(PNG)
    asset_path = tmp_path / f"{uploaded.asset.asset_id}.png"
    metadata_path = tmp_path / f"{uploaded.asset.asset_id}.meta.json"
    assert asset_path.read_bytes() == PNG
    assert metadata_path.is_file()
    assert not list(tmp_path.glob("*.part"))


@pytest.mark.parametrize(
    ("data", "media_type", "error"),
    [
        (b"", "image/png", AssetEmptyError),
        (PNG, "image/svg+xml", UnsupportedAssetTypeError),
        (PNG, "image/jpeg", AssetTypeMismatchError),
        (JPEG, "image/png", AssetTypeMismatchError),
    ],
)
def test_store_rejects_invalid_content_without_writing(tmp_path, data, media_type, error) -> None:
    store = TemporaryAssetStore(tmp_path)
    with pytest.raises(error):
        store.store(
            data,
            declared_media_type=media_type,
            provenance_ref="fixture:user-upload/day6",
            rights_ref="rights:authorized-upload/day6",
        )
    assert list(tmp_path.iterdir()) == []


def test_purge_expired_removes_bytes_and_metadata_idempotently(tmp_path) -> None:
    store = TemporaryAssetStore(tmp_path)
    created_at = datetime(2026, 8, 13, 8, 0, tzinfo=UTC)
    uploaded = store.store(
        PNG,
        declared_media_type="image/png",
        provenance_ref="fixture:user-upload/day7",
        rights_ref="rights:authorized-upload/day7",
        now=created_at,
    )

    assert store.purge_expired(created_at + timedelta(hours=24)) == 1
    assert store.purge_expired(created_at + timedelta(hours=25)) == 0
    assert not (tmp_path / f"{uploaded.asset.asset_id}.png").exists()
    assert not (tmp_path / f"{uploaded.asset.asset_id}.meta.json").exists()


def test_delete_is_idempotent_and_tombstone_blocks_late_write(tmp_path) -> None:
    store = TemporaryAssetStore(tmp_path)
    asset_id = uploaded_id = store.store(
        PNG,
        declared_media_type="image/png",
        provenance_ref="fixture:user-upload/day7",
        rights_ref="rights:authorized-upload/day7",
    ).asset.asset_id

    assert store.delete(asset_id) is True
    assert store.delete(asset_id) is False
    with pytest.raises(AssetLifecycleClosedError):
        store.store(
            PNG,
            declared_media_type="image/png",
            provenance_ref="fixture:user-upload/day7",
            rights_ref="rights:authorized-upload/day7",
            asset_id=uploaded_id,
        )
    assert not list(tmp_path.glob(f"{asset_id}.*"))
    tombstones = list((tmp_path / "tombstones").glob("*.json"))
    assert len(tombstones) == 1
    assert str(asset_id) not in tombstones[0].name
    assert str(asset_id) not in tombstones[0].read_text(encoding="utf-8")


def test_tombstone_is_retained_for_seven_days_then_removed(tmp_path) -> None:
    store = TemporaryAssetStore(tmp_path)
    deleted_at = datetime(2026, 8, 14, 9, 0, tzinfo=UTC)
    asset_id = store.store(
        PNG,
        declared_media_type="image/png",
        provenance_ref="fixture:user-upload/day7",
        rights_ref="rights:authorized-upload/day7",
        now=deleted_at,
    ).asset.asset_id
    store.delete(asset_id, now=deleted_at)
    tombstone = next((tmp_path / "tombstones").glob("*.json"))

    store.purge_expired(deleted_at + timedelta(days=7) - timedelta(seconds=1))
    assert tombstone.exists()
    store.purge_expired(deleted_at + timedelta(days=7))
    assert not tombstone.exists()


def test_store_rejects_oversize_and_private_metadata_before_writing(tmp_path) -> None:
    store = TemporaryAssetStore(tmp_path)
    with pytest.raises(AssetTooLargeError):
        store.store(
            PNG + b"x" * MAX_ASSET_BYTES,
            declared_media_type="image/png",
            provenance_ref="fixture:user-upload/day6",
            rights_ref="rights:authorized-upload/day6",
        )
    with pytest.raises(AssetMetadataError):
        store.store(
            PNG,
            declared_media_type="image/png",
            provenance_ref=r"C:\private\source.png",
            rights_ref="rights:authorized-upload/day6",
        )
    assert list(tmp_path.iterdir()) == []
