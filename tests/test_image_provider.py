from hashlib import sha256
from io import BytesIO

import pytest

from cultureshift.contracts import BackgroundRequest, ExecutionMode, Locale
from cultureshift.domain import LocalizationDirection
from cultureshift.image_provider import (
    FixtureImageProvider,
    ImageProviderError,
    ImageProviderErrorCode,
)


def _request(scene: str, *, direction: LocalizationDirection | None = None) -> BackgroundRequest:
    selected = direction or LocalizationDirection.CHINA_TO_UK
    return BackgroundRequest(
        direction=selected,
        target_locale=(
            Locale.EN_GB
            if selected is LocalizationDirection.CHINA_TO_UK
            else Locale.ZH_CN
        ),
        narrative=scene,
        use_scenario="A calm, abstract workspace with open space for locked layers.",
    )


@pytest.mark.parametrize(
    "protected",
    [
        "Orbit AI logo",
        "brand name",
        "product UI screenshot",
        "show 98%",
        "statistics dashboard",
        "render a product claim",
        "add long text",
        "add typography",
        "caption area",
    ],
)
def test_background_provider_rejects_protected_content(protected: str) -> None:
    with pytest.raises(ImageProviderError) as caught:
        FixtureImageProvider().generate_background(_request(protected))
    assert caught.value.code is ImageProviderErrorCode.INVALID_REQUEST
    assert str(caught.value) == "image provider failed"


@pytest.mark.parametrize("direction", list(LocalizationDirection))
def test_fixture_provider_is_deterministic_valid_png_and_offline(
    direction: LocalizationDirection,
) -> None:
    provider = FixtureImageProvider()
    first = provider.generate_background(_request("quiet abstract workspace", direction=direction))
    second = provider.generate_background(_request("quiet abstract workspace", direction=direction))

    assert first == second
    assert first.execution_mode is ExecutionMode.FIXTURE
    assert first.width == 1600 and first.height == 900
    assert first.sha256 == sha256(first.png_bytes).hexdigest()
    assert first.provenance_ref.startswith("fixture:")
    assert first.png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    from PIL import Image

    with Image.open(BytesIO(first.png_bytes)) as image:
        assert image.size == (1600, 900)
        assert image.mode == "RGBA"


def test_background_request_requires_directional_locale() -> None:
    with pytest.raises(ValueError):
        BackgroundRequest(
            direction=LocalizationDirection.CHINA_TO_UK,
            target_locale=Locale.ZH_CN,
            narrative="quiet abstract workspace",
            use_scenario="reserved layout",
        )


def test_generated_background_bytes_are_not_a_public_contract_field() -> None:
    result = FixtureImageProvider().generate_background(_request("quiet abstract workspace"))
    assert "png_bytes" not in BackgroundRequest.model_json_schema()["properties"]
    assert "png_bytes" not in result.public_metadata()
