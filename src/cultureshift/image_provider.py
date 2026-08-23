from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from typing import Protocol

from PIL import Image, ImageDraw

from cultureshift.contracts import BackgroundRequest, ExecutionMode
from cultureshift.domain import LocalizationDirection


class ImageProviderErrorCode(StrEnum):
    INVALID_REQUEST = "background_request_invalid"
    INVALID_OUTPUT = "background_output_invalid"


class ImageProviderError(ValueError):
    def __init__(self, code: ImageProviderErrorCode) -> None:
        self.code = code
        super().__init__("image provider failed")


@dataclass(frozen=True)
class GeneratedBackground:
    execution_mode: ExecutionMode
    width: int
    height: int
    media_type: str
    sha256: str
    provenance_ref: str
    png_bytes: bytes

    def public_metadata(self) -> dict[str, str | int]:
        return {
            "execution_mode": self.execution_mode.value,
            "width": self.width,
            "height": self.height,
            "media_type": self.media_type,
            "sha256": self.sha256,
            "provenance_ref": self.provenance_ref,
        }


class ImageProvider(Protocol):
    def generate_background(self, request: BackgroundRequest) -> GeneratedBackground: ...


_PROTECTED_PATTERNS = (
    r"\borbit\s+ai\b",
    r"\blogo\b",
    r"\bbrand\s+name\b",
    r"\bproduct\s+ui\b",
    r"\bscreenshot\b",
    r"\bclaim\b",
    r"\bstatistic(?:s)?\b",
    r"\blong\s+text\b",
    r"\btypograph(?:y|ic)\b",
    r"\bcaption\b",
    r"\brender\b.*\btext\b",
    r"\d+(?:\.\d+)?%",
)


def _validate_request(request: BackgroundRequest) -> None:
    combined = f"{request.narrative}\n{request.use_scenario}".casefold()
    if any(re.search(pattern, combined) for pattern in _PROTECTED_PATTERNS):
        raise ImageProviderError(ImageProviderErrorCode.INVALID_REQUEST)


def _encode_png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def _render_direction_background(direction: LocalizationDirection) -> Image.Image:
    if direction is LocalizationDirection.CHINA_TO_UK:
        base, accent = "#eaf2f8", "#bfd6e6"
    else:
        base, accent = "#f5eee2", "#e0c9a8"
    image = Image.new("RGBA", (1600, 900), base)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((980, -180, 1700, 540), fill=accent + "b8")
    draw.rounded_rectangle((760, 130, 1510, 790), radius=48, fill="#ffffff8a")
    draw.polygon(((0, 760), (690, 500), (930, 900), (0, 900)), fill="#ffffff73")
    return image


class FixtureImageProvider:
    def generate_background(self, request: BackgroundRequest) -> GeneratedBackground:
        _validate_request(request)
        png_bytes = _encode_png(_render_direction_background(request.direction))
        digest = hashlib.sha256(png_bytes).hexdigest()
        return GeneratedBackground(
            execution_mode=ExecutionMode.FIXTURE,
            width=1600,
            height=900,
            media_type="image/png",
            sha256=digest,
            provenance_ref=f"fixture:day12-background-{request.direction.value}",
            png_bytes=png_bytes,
        )
