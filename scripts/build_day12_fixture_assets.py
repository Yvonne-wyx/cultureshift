"""Build deterministic, project-owned Day 12 fixture rasters and previews."""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from PIL import Image, ImageDraw, ImageFont

from cultureshift.composition import ComposeRequest, PillowCompositor
from cultureshift.contracts import AdCopy, BackgroundRequest, BrandLock, Locale
from cultureshift.domain import LocalizationDirection
from cultureshift.fixture_assets import FixtureAssetRegistry
from cultureshift.image_provider import FixtureImageProvider

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "apps" / "web" / "public" / "fixtures" / "orbit-ai"
FONT_PATH = ROOT / "assets" / "fonts" / "NotoSansCJKsc-Regular.otf"
LOGO_ID = UUID("a1111111-1111-4111-8111-111111111111")
UI_ID = UUID("a2222222-2222-4222-8222-222222222222")
LAYOUT_ID = UUID("a3333333-3333-4333-8333-333333333333")


def _save_png(image: Image.Image, path: Path) -> None:
    output = BytesIO()
    image.save(output, "PNG", optimize=False, compress_level=9)
    path.write_bytes(output.getvalue())


def _build_logo() -> Image.Image:
    image = Image.new("RGBA", (480, 160), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((18, 20, 132, 134), outline="#164a7b", width=12)
    draw.ellipse((56, 2, 154, 100), outline="#4d86b3", width=8)
    draw.ellipse((92, 28, 116, 52), fill="#f18740")
    font = ImageFont.truetype(str(FONT_PATH), 60)
    draw.text((172, 42), "Orbit AI", font=font, fill="#164a7b")
    return image


def _build_product_ui() -> Image.Image:
    image = Image.new("RGBA", (760, 520), "#f7fafc")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1, 1, 758, 518), radius=30, outline="#7990a6", width=4)
    draw.rectangle((2, 2, 758, 78), fill="#164a7b")
    font = ImageFont.truetype(str(FONT_PATH), 30)
    small = ImageFont.truetype(str(FONT_PATH), 22)
    draw.text((32, 20), "Orbit AI - approved notes", font=font, fill="#ffffff")
    for index, (title, colour) in enumerate(
        (("Review notes", "#e8f0f6"), ("Organise tasks", "#f5eee2"), ("Confirm summary", "#e9f3ea"))
    ):
        top = 112 + index * 120
        draw.rounded_rectangle((38, top, 722, top + 88), radius=18, fill=colour)
        draw.text((68, top + 26), title, font=small, fill="#27475f")
    return image


def _brand_lock() -> BrandLock:
    return BrandLock(
        logo_asset_id=LOGO_ID,
        product_name="Orbit AI",
        verified_product_facts=("Turns approved notes into task summaries",),
        product_ui_asset_ids=(UI_ID,),
        benefit_order=("Summarize", "Organize"),
        cta_action_meaning="Start a fixture demo",
        layout_template_asset_id=LAYOUT_ID,
        localizable_fields=("narrative", "use_scenario", "trust_information", "language"),
    )


def _copy(direction: LocalizationDirection) -> AdCopy:
    if direction is LocalizationDirection.CHINA_TO_UK:
        return AdCopy(
            locale=Locale.EN_GB,
            headline="Turn approved notes into clear task summaries",
            body="Orbit AI helps teams organise approved meeting notes into task summaries.",
            cta_label="Try the fixture demo",
            cta_action_meaning="Start a fixture demo",
        )
    return AdCopy(
        locale=Locale.ZH_CN,
        headline="把已批准笔记整理成清晰任务摘要",
        body="Orbit AI 帮助团队将已批准的会议笔记整理为任务摘要。",
        cta_label="体验示例演示",
        cta_action_meaning="Start a fixture demo",
    )


def main() -> int:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    _save_png(_build_logo(), FIXTURE_DIR / "orbit-ai-logo.png")
    _save_png(_build_product_ui(), FIXTURE_DIR / "orbit-ai-product-ui.png")
    registry = FixtureAssetRegistry(FIXTURE_DIR)
    logo = registry.resolve(LOGO_ID)
    product_ui = registry.resolve(UI_ID)
    provider = FixtureImageProvider()
    compositor = PillowCompositor()
    for direction, filename in (
        (LocalizationDirection.CHINA_TO_UK, "composed-china-to-uk.png"),
        (LocalizationDirection.UK_TO_CHINA, "composed-uk-to-china.png"),
    ):
        locale = Locale.EN_GB if direction is LocalizationDirection.CHINA_TO_UK else Locale.ZH_CN
        background = provider.generate_background(
            BackgroundRequest(
                direction=direction,
                target_locale=locale,
                narrative="quiet abstract workspace",
                use_scenario="open space reserved for deterministic locked layers",
            )
        )
        result = compositor.compose(
            ComposeRequest(
                run_id=uuid4(),
                background=background,
                brand_lock=_brand_lock(),
                ad_copy=_copy(direction),
                logo=logo,
                product_ui=product_ui,
                font_path=FONT_PATH,
            )
        )
        (FIXTURE_DIR / filename).write_bytes(result.png_bytes)
    for path in sorted(FIXTURE_DIR.glob("*.png")):
        print(f"{path.name} {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
