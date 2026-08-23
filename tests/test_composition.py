from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image, ImageDraw, ImageFont

from cultureshift.composition import (
    ComposeRequest,
    CompositionError,
    CompositionErrorCode,
    PillowCompositor,
)
from cultureshift.contracts import AdCopy, AssetKind, BrandLock, Locale
from cultureshift.domain import LocalizationDirection
from cultureshift.fixture_assets import RegisteredFixtureAsset
from cultureshift.image_provider import BackgroundRequest, FixtureImageProvider

FONT_PATH = Path("assets/fonts/NotoSansCJKsc-Regular.otf")
LOGO_ID = "a1111111-1111-4111-8111-111111111111"
UI_ID = "a2222222-2222-4222-8222-222222222222"
LAYOUT_ID = "a3333333-3333-4333-8333-333333333333"


def _png(size: tuple[int, int], color: tuple[int, int, int, int]) -> bytes:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(image).rounded_rectangle(
        (4, 4, size[0] - 5, size[1] - 5), radius=12, fill=color
    )
    output = BytesIO()
    image.save(output, "PNG", compress_level=9)
    return output.getvalue()


def _asset(asset_id: str, kind: AssetKind, data: bytes) -> RegisteredFixtureAsset:
    return RegisteredFixtureAsset(
        asset_id=asset_id,
        kind=kind,
        png_bytes=data,
        sha256=sha256(data).hexdigest(),
        provenance_ref="fixture:day12-test-asset",
    )


def _request(*, product_ui: RegisteredFixtureAsset | None = None) -> ComposeRequest:
    brand_lock = BrandLock(
        logo_asset_id=LOGO_ID,
        product_name="Orbit AI",
        verified_product_facts=("Turns approved notes into task summaries",),
        product_ui_asset_ids=(UI_ID,),
        benefit_order=("Summarize", "Organize"),
        cta_action_meaning="Start a fixture demo",
        layout_template_asset_id=LAYOUT_ID,
        localizable_fields=("narrative", "use_scenario", "trust_information", "language"),
    )
    background = FixtureImageProvider().generate_background(
        BackgroundRequest(
            direction=LocalizationDirection.CHINA_TO_UK,
            target_locale=Locale.EN_GB,
            narrative="quiet abstract workspace",
            use_scenario="open space reserved for deterministic locked layers",
        )
    )
    return ComposeRequest(
        run_id=uuid4(),
        background=background,
        brand_lock=brand_lock,
        ad_copy=AdCopy(
            locale=Locale.EN_GB,
            headline="Turn approved notes into clear task summaries",
            body="Orbit AI helps teams organise approved meeting notes into task summaries.",
            cta_label="Try the fixture demo",
            cta_action_meaning="Start a fixture demo",
        ),
        logo=_asset(LOGO_ID, AssetKind.LOGO, _png((480, 160), (22, 74, 123, 255))),
        product_ui=product_ui or _asset(
            UI_ID, AssetKind.PRODUCT_UI, _png((760, 520), (236, 242, 247, 255))
        ),
        font_path=FONT_PATH,
    )


def _decoded_rgba(data: bytes) -> Image.Image:
    with Image.open(BytesIO(data)) as image:
        return image.convert("RGBA")


def _approved_contain(data: bytes, maximum: tuple[int, int]) -> Image.Image:
    image = _decoded_rgba(data)
    image.thumbnail(maximum, Image.Resampling.LANCZOS)
    return image


def test_compositor_preserves_locked_logo_and_ui_decoded_pixels() -> None:
    request = _request()
    result = PillowCompositor().compose(request)

    logo = _decoded_rgba(result.layer_png("logo"))
    expected_logo = _approved_contain(request.logo.png_bytes, (220, 96))
    assert logo.size == expected_logo.size
    assert logo.getbbox() == expected_logo.getbbox()
    assert sha256(logo.tobytes()).hexdigest() == sha256(expected_logo.tobytes()).hexdigest()
    assert result.layer("logo").source_asset_id == request.brand_lock.logo_asset_id

    ui = _decoded_rgba(result.layer_png("product_ui"))
    expected_ui = _approved_contain(request.product_ui.png_bytes, (650, 520))
    assert ui.size == expected_ui.size
    assert ui.getbbox() == expected_ui.getbbox()
    assert sha256(ui.tobytes()).hexdigest() == sha256(expected_ui.tobytes()).hexdigest()
    assert result.layer("product_ui").source_asset_id == request.brand_lock.product_ui_asset_ids[0]


def test_compositor_is_deterministic_fixed_size_and_fixed_order() -> None:
    request = _request()
    first = PillowCompositor().compose(request)
    second = PillowCompositor().compose(request)
    assert first.png_bytes == second.png_bytes
    assert first.sha256 == sha256(first.png_bytes).hexdigest()
    assert _decoded_rgba(first.png_bytes).size == (1600, 900)
    assert tuple(layer.kind for layer in first.layers) == (
        "background",
        "product_ui",
        "logo",
        "headline",
        "body",
        "cta",
        "disclosure",
    )
    for kind in ("headline", "body"):
        rendered = _decoded_rgba(first.layer_png(kind))
        alpha_bounds = rendered.getchannel("A").getbbox()
        assert alpha_bounds is not None
        assert alpha_bounds[2] < rendered.width - 8


def test_compositor_fails_closed_for_missing_or_drifted_locked_input() -> None:
    wrong_ui = _asset(str(uuid4()), AssetKind.PRODUCT_UI, _png((760, 520), (1, 2, 3, 255)))
    with pytest.raises(CompositionError) as caught:
        PillowCompositor().compose(_request(product_ui=wrong_ui))
    assert caught.value.code is CompositionErrorCode.LOCKED_ASSET_MISSING
    assert str(caught.value) == "composition failed"


def test_pinned_font_covers_every_bilingual_fixture_character() -> None:
    font = ImageFont.truetype(str(FONT_PATH), 48)
    text = (
        "Turn approved notes into clear task summaries "
        "Orbit AI helps teams organise approved meeting notes into task summaries. "
        "Try the fixture demo Fixture Demo / 非实时模型 "
        "把已批准笔记整理成清晰任务摘要 "
        "Orbit AI 帮助团队将已批准的会议笔记整理为任务摘要。 体验示例演示"
    )
    for character in set(text) - {" "}:
        assert font.getmask(character).getbbox() is not None, character


def test_compositor_rejects_cta_meaning_drift() -> None:
    request = _request()
    drifted = request.ad_copy.model_copy(update={"cta_action_meaning": "Buy now"})
    with pytest.raises(CompositionError) as caught:
        PillowCompositor().compose(
            ComposeRequest(
                run_id=request.run_id,
                background=request.background,
                brand_lock=request.brand_lock,
                ad_copy=drifted,
                logo=request.logo,
                product_ui=request.product_ui,
                font_path=request.font_path,
            )
        )
    assert caught.value.code is CompositionErrorCode.LOCKED_CONTENT_DRIFT
