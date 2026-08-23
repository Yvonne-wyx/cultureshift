from uuid import UUID, uuid4

import pytest

from cultureshift.contracts import AssetKind
from cultureshift.fixture_assets import FixtureAssetError, fixture_asset_registry


def test_fixture_registry_resolves_only_registered_brand_assets() -> None:
    registry = fixture_asset_registry()
    logo = registry.resolve(UUID("a1111111-1111-4111-8111-111111111111"))
    product_ui = registry.resolve(UUID("a2222222-2222-4222-8222-222222222222"))
    assert logo.kind is AssetKind.LOGO
    assert product_ui.kind is AssetKind.PRODUCT_UI
    assert logo.png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert product_ui.png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_fixture_registry_rejects_unregistered_asset_id_without_leaking_it() -> None:
    missing = uuid4()
    with pytest.raises(FixtureAssetError) as caught:
        fixture_asset_registry().resolve(missing)
    assert str(caught.value) == "fixture asset unavailable"
    assert str(missing) not in str(caught.value)
