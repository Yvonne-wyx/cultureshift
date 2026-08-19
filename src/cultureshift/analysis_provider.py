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
        self,
        request: VisionAnalysisRequest,
        *,
        attempt: Literal["initial", "repair"] = "initial",
    ) -> VisionProviderResult | Mapping[str, object]: ...


class FakeProvider:
    def __init__(
        self,
        result: VisionProviderResult | Mapping[str, object],
        *,
        repair_result: VisionProviderResult | Mapping[str, object] | None = None,
    ) -> None:
        self._result = result
        self._repair_result = repair_result
        self._call_count = 0
        self._attempts: list[Literal["initial", "repair"]] = []

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def attempts(self) -> tuple[Literal["initial", "repair"], ...]:
        return tuple(self._attempts)

    def analyze(
        self,
        request: VisionAnalysisRequest,
        *,
        attempt: Literal["initial", "repair"] = "initial",
    ) -> VisionProviderResult | Mapping[str, object]:
        del request
        self._call_count += 1
        self._attempts.append(attempt)
        if attempt == "repair" and self._repair_result is not None:
            return self._repair_result
        return self._result


class FixtureProvider:
    """Offline bilateral fixture behavior for local API execution and CI."""

    def analyze(
        self,
        request: VisionAnalysisRequest,
        *,
        attempt: Literal["initial", "repair"] = "initial",
    ) -> VisionProviderResult:
        del attempt
        detected_locale = {
            LocalizationDirection.CHINA_TO_UK: Locale.ZH_CN,
            LocalizationDirection.UK_TO_CHINA: Locale.EN_GB,
        }[request.direction]
        return VisionProviderResult(
            detected_locale=detected_locale,
            warnings=("fixture_provider", "human_review_required"),
        )
