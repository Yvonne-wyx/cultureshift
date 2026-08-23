from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from cultureshift.contracts import AssetKind

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_ROOT = _REPOSITORY_ROOT / "apps" / "web" / "public" / "fixtures" / "orbit-ai"


class FixtureAssetError(LookupError):
    pass


@dataclass(frozen=True)
class RegisteredFixtureAsset:
    asset_id: UUID
    kind: AssetKind
    png_bytes: bytes
    sha256: str
    provenance_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "asset_id", UUID(str(self.asset_id)))
        if hashlib.sha256(self.png_bytes).hexdigest() != self.sha256:
            raise ValueError("fixture asset hash mismatch")


class FixtureAssetRegistry:
    def __init__(self, root: Path = _FIXTURE_ROOT) -> None:
        self._root = root
        self._definitions = {
            UUID("a1111111-1111-4111-8111-111111111111"): (
                AssetKind.LOGO,
                "orbit-ai-logo.png",
                "fixture:orbit-ai-logo-day12-raster",
            ),
            UUID("a2222222-2222-4222-8222-222222222222"): (
                AssetKind.PRODUCT_UI,
                "orbit-ai-product-ui.png",
                "fixture:orbit-ai-product-ui-day12-raster",
            ),
        }

    def resolve(self, asset_id: UUID) -> RegisteredFixtureAsset:
        definition = self._definitions.get(asset_id)
        if definition is None:
            raise FixtureAssetError("fixture asset unavailable")
        kind, relative_path, provenance_ref = definition
        try:
            content = (self._root / relative_path).read_bytes()
        except OSError as error:
            raise FixtureAssetError("fixture asset unavailable") from error
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise FixtureAssetError("fixture asset unavailable")
        return RegisteredFixtureAsset(
            asset_id=asset_id,
            kind=kind,
            png_bytes=content,
            sha256=hashlib.sha256(content).hexdigest(),
            provenance_ref=provenance_ref,
        )


def fixture_asset_registry() -> FixtureAssetRegistry:
    return FixtureAssetRegistry()
