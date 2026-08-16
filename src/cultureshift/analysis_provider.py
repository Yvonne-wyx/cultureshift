from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from pydantic import Field

from cultureshift.contracts import (
    BrandLock,
    ContractModel,
    CulturalHypothesis,
    Locale,
    SourceAdAssetRef,
    WarningCode,
)
from cultureshift.domain import LocalizationDirection


@dataclass(frozen=True, slots=True)
class VisionAnalysisRequest:
    content: bytes
    source_asset: SourceAdAssetRef
    direction: LocalizationDirection
    brand_lock: BrandLock
    product_category: Literal["ai_software", "ai_application"]
    creative_format: Literal["static_ad"] = "static_ad"


class VisionProviderResult(ContractModel):
    detected_locale: Locale
    hypotheses: tuple[CulturalHypothesis, ...] = Field(default=(), max_length=32)
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    instruction_like_content_detected: bool = False
    prohibited_content_detected: bool = False


@runtime_checkable
class VisionProvider(Protocol):
    def analyze(
        self, request: VisionAnalysisRequest
    ) -> VisionProviderResult | Mapping[str, object]: ...


class FakeProvider:
    def __init__(self, result: VisionProviderResult) -> None:
        self._result = result
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def analyze(self, request: VisionAnalysisRequest) -> VisionProviderResult:
        del request
        self._call_count += 1
        return self._result
