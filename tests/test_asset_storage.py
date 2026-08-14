from datetime import UTC, datetime, timedelta

import pytest

from cultureshift.asset_storage import (
    MAX_ASSET_BYTES,
    AssetEmptyError,
    AssetMetadataError,
    AssetTooLargeError,
    AssetTypeMismatchError,
    TemporaryAssetStore,
    UnsupportedAssetTypeError,
)

PNG = b"\x89PNG\r\n\x1a\nfixture"
JPEG = b"\xff\xd8\xfffixture\xff\xd9"


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
    files = list(tmp_path.iterdir())
    assert files == [tmp_path / f"{uploaded.asset.asset_id}.png"]
    assert files[0].read_bytes() == PNG
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
