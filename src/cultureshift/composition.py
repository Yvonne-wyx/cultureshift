from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from pathlib import Path
from uuid import UUID

from PIL import Image, ImageDraw, ImageFont

from cultureshift.contracts import AdCopy, AssetKind, BrandLock, CompositionLayer
from cultureshift.fixture_assets import RegisteredFixtureAsset
from cultureshift.image_provider import GeneratedBackground

CANVAS_SIZE = (1600, 900)
FONT_SHA256 = "2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b"
DISCLOSURE = "Fixture Demo / 非实时模型"


class CompositionErrorCode(StrEnum):
    LOCKED_ASSET_MISSING = "locked_asset_missing"
    LOCKED_CONTENT_DRIFT = "locked_content_drift"
    INVALID_OUTPUT = "composition_output_invalid"


class CompositionError(ValueError):
    def __init__(self, code: CompositionErrorCode) -> None:
        self.code = code
        super().__init__("composition failed")


@dataclass(frozen=True)
class ComposeRequest:
    run_id: UUID
    background: GeneratedBackground
    brand_lock: BrandLock
    ad_copy: AdCopy
    logo: RegisteredFixtureAsset
    product_ui: RegisteredFixtureAsset
    font_path: Path


@dataclass(frozen=True)
class _RenderedLayer:
    evidence: CompositionLayer
    png_bytes: bytes


@dataclass(frozen=True)
class ComposedAd:
    png_bytes: bytes
    sha256: str
    layers: tuple[CompositionLayer, ...]
    _rendered_layers: tuple[_RenderedLayer, ...]

    def layer(self, kind: str) -> CompositionLayer:
        for layer in self.layers:
            if layer.kind == kind:
                return layer
        raise KeyError(kind)

    def layer_png(self, kind: str) -> bytes:
        for layer in self._rendered_layers:
            if layer.evidence.kind == kind:
                return layer.png_bytes
        raise KeyError(kind)


def _decode_rgba(data: bytes, expected_size: tuple[int, int] | None = None) -> Image.Image:
    try:
        with Image.open(BytesIO(data)) as source:
            image = source.convert("RGBA")
    except (OSError, ValueError) as error:
        raise CompositionError(CompositionErrorCode.INVALID_OUTPUT) from error
    if expected_size is not None and image.size != expected_size:
        raise CompositionError(CompositionErrorCode.INVALID_OUTPUT)
    return image


def _encode_png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, "PNG", optimize=False, compress_level=9)
    return output.getvalue()


def _contain(data: bytes, maximum: tuple[int, int]) -> Image.Image:
    image = _decode_rgba(data)
    image.thumbnail(maximum, Image.Resampling.LANCZOS)
    return image


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != FONT_SHA256:
            raise CompositionError(CompositionErrorCode.INVALID_OUTPUT)
        return ImageFont.truetype(str(path), size)
    except (OSError, ValueError) as error:
        if isinstance(error, CompositionError):
            raise
        raise CompositionError(CompositionErrorCode.INVALID_OUTPUT) from error


def _is_cjk(character: str) -> bool:
    codepoint = ord(character)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def _text_units(text: str) -> tuple[tuple[str, bool], ...]:
    normalized = " ".join(text.split())
    if not normalized:
        raise CompositionError(CompositionErrorCode.INVALID_OUTPUT)
    units: list[tuple[str, bool]] = []
    index = 0
    separated = False
    while index < len(normalized):
        character = normalized[index]
        if character == " ":
            separated = True
            index += 1
            continue
        if _is_cjk(character):
            units.append((character, separated))
            separated = False
            index += 1
            continue
        end = index + 1
        while end < len(normalized) and normalized[end] != " " and not _is_cjk(normalized[end]):
            end += 1
        units.append((normalized[index:end], separated))
        separated = False
        index = end
    return tuple(units)


def _wrap_text(
    font: ImageFont.FreeTypeFont,
    text: str,
    maximum_width: int,
    maximum_lines: int,
) -> tuple[str, ...]:
    if maximum_width <= 0 or maximum_lines <= 0:
        raise CompositionError(CompositionErrorCode.INVALID_OUTPUT)
    lines: list[str] = []
    current = ""
    for unit, separated in _text_units(text):
        prefix = " " if current and separated else ""
        candidate = f"{current}{prefix}{unit}"
        if font.getlength(candidate) <= maximum_width:
            current = candidate
            continue
        if not current or font.getlength(unit) > maximum_width:
            raise CompositionError(CompositionErrorCode.INVALID_OUTPUT)
        lines.append(current)
        if len(lines) >= maximum_lines:
            raise CompositionError(CompositionErrorCode.INVALID_OUTPUT)
        current = unit
    if current:
        lines.append(current)
    if not lines or len(lines) > maximum_lines:
        raise CompositionError(CompositionErrorCode.INVALID_OUTPUT)
    return tuple(lines)


def _fit_font(
    path: Path,
    text: str,
    width: int,
    height: int,
    start: int,
    minimum: int,
    maximum_lines: int,
) -> tuple[ImageFont.FreeTypeFont, tuple[str, ...], int]:
    for size in range(start, minimum - 1, -2):
        candidate = _font(path, size)
        try:
            lines = _wrap_text(candidate, text, width, maximum_lines)
        except CompositionError:
            continue
        spacing = max(2, size // 6)
        probe = ImageDraw.Draw(Image.new("L", (1, 1)))
        bounds = probe.multiline_textbbox(
            (0, 0), "\n".join(lines), font=candidate, spacing=spacing
        )
        if bounds[2] - bounds[0] <= width and bounds[3] - bounds[1] <= height:
            return candidate, lines, spacing
    raise CompositionError(CompositionErrorCode.INVALID_OUTPUT)


def _text_layer(
    path: Path,
    text: str,
    size: tuple[int, int],
    *,
    start_font: int,
    minimum_font: int,
    maximum_lines: int,
    colour: str,
    background: str | None = None,
) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if background is not None:
        draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=18, fill=background)
    font, lines, spacing = _fit_font(
        path,
        text,
        size[0] - 24,
        size[1],
        start_font,
        minimum_font,
        maximum_lines,
    )
    rendered = "\n".join(lines)
    box = draw.multiline_textbbox((0, 0), rendered, font=font, spacing=spacing)
    y = (size[1] - (box[3] - box[1])) // 2 - box[1]
    draw.multiline_text((12, y), rendered, font=font, spacing=spacing, fill=colour)
    return image


def _rendered_layer(
    kind: str,
    image: Image.Image,
    origin: tuple[int, int],
    *,
    source_asset_id: UUID | None = None,
) -> _RenderedLayer:
    width, height = image.size
    left, top = origin
    evidence = CompositionLayer(
        kind=kind,
        source_asset_id=source_asset_id,
        rgba_sha256=hashlib.sha256(image.tobytes()).hexdigest(),
        bounds=(left, top, left + width, top + height),
        width=width,
        height=height,
    )
    return _RenderedLayer(evidence=evidence, png_bytes=_encode_png(image))


def _validate_request(request: ComposeRequest) -> None:
    if (
        request.logo.asset_id != request.brand_lock.logo_asset_id
        or request.logo.kind is not AssetKind.LOGO
        or request.product_ui.asset_id not in request.brand_lock.product_ui_asset_ids
        or request.product_ui.kind is not AssetKind.PRODUCT_UI
    ):
        raise CompositionError(CompositionErrorCode.LOCKED_ASSET_MISSING)
    if request.ad_copy.cta_action_meaning != request.brand_lock.cta_action_meaning:
        raise CompositionError(CompositionErrorCode.LOCKED_CONTENT_DRIFT)


class PillowCompositor:
    def compose(self, request: ComposeRequest) -> ComposedAd:
        _validate_request(request)
        background = _decode_rgba(request.background.png_bytes, CANVAS_SIZE)
        product_ui = _contain(request.product_ui.png_bytes, (650, 520))
        logo = _contain(request.logo.png_bytes, (220, 96))
        headline = _text_layer(
            request.font_path,
            request.ad_copy.headline,
            (660, 124),
            start_font=58,
            minimum_font=24,
            maximum_lines=2,
            colour="#102f4a",
        )
        body = _text_layer(
            request.font_path,
            request.ad_copy.body,
            (680, 86),
            start_font=34,
            minimum_font=16,
            maximum_lines=3,
            colour="#27475f",
        )
        cta = _text_layer(
            request.font_path,
            request.ad_copy.cta_label,
            (330, 76),
            start_font=34,
            minimum_font=24,
            maximum_lines=2,
            colour="#ffffff",
            background="#164a7b",
        )
        disclosure = _text_layer(
            request.font_path,
            DISCLOSURE,
            (430, 44),
            start_font=22,
            minimum_font=18,
            maximum_lines=1,
            colour="#5d1600",
            background="#ffe3d9",
        )
        rendered = (
            _rendered_layer("background", background, (0, 0)),
            _rendered_layer(
                "product_ui",
                product_ui,
                (850, 170),
                source_asset_id=request.product_ui.asset_id,
            ),
            _rendered_layer("logo", logo, (100, 70), source_asset_id=request.logo.asset_id),
            _rendered_layer("headline", headline, (100, 220)),
            _rendered_layer("body", body, (100, 390)),
            _rendered_layer("cta", cta, (100, 560)),
            _rendered_layer("disclosure", disclosure, (100, 820)),
        )
        output = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        for layer in rendered:
            image = _decode_rgba(layer.png_bytes)
            output.alpha_composite(image, (layer.evidence.bounds[0], layer.evidence.bounds[1]))
        png_bytes = _encode_png(output)
        return ComposedAd(
            png_bytes=png_bytes,
            sha256=hashlib.sha256(png_bytes).hexdigest(),
            layers=tuple(layer.evidence for layer in rendered),
            _rendered_layers=rendered,
        )
