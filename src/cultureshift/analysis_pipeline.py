from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ValidationError

from cultureshift.analysis_provider import (
    VisionAnalysisRequest,
    VisionProvider,
    VisionProviderResult,
)
from cultureshift.asset_storage import detect_media_type
from cultureshift.contracts import AdAnalysis, Market
from cultureshift.domain import LocalizationDirection


class AnalysisErrorCode(StrEnum):
    INVALID_INPUT = "invalid_analysis_input"
    UNSUPPORTED_SCOPE = "unsupported_analysis_scope"
    ASSET_CLOSED = "asset_lifecycle_closed"
    PROVIDER_FAILED = "provider_failed"
    PROVIDER_OUTPUT_INVALID = "provider_output_invalid"
    INSTRUCTION_LIKE_CONTENT = "instruction_like_content"
    PROHIBITED_CONTENT = "prohibited_content"
    UNSAFE_HYPOTHESIS = "unsafe_hypothesis"


class AnalysisPipelineError(RuntimeError):
    def __init__(self, code: AnalysisErrorCode) -> None:
        self.code = code
        super().__init__(code.value)


class SafetyGate:
    _supported_media_types = frozenset({"image/png", "image/jpeg"})
    _supported_categories = frozenset({"ai_software", "ai_application"})

    def validate_request(self, request: VisionAnalysisRequest, now: datetime) -> None:
        detected = detect_media_type(request.content)
        if (
            detected is None
            or detected not in self._supported_media_types
            or detected != request.source_asset.media_type
        ):
            raise AnalysisPipelineError(AnalysisErrorCode.INVALID_INPUT)
        if (
            request.product_category not in self._supported_categories
            or request.creative_format != "static_ad"
        ):
            raise AnalysisPipelineError(AnalysisErrorCode.UNSUPPORTED_SCOPE)
        expires_at = request.source_asset.expires_at
        if expires_at is not None and expires_at <= now:
            raise AnalysisPipelineError(AnalysisErrorCode.ASSET_CLOSED)

    def validate_result(
        self, request: VisionAnalysisRequest, result: VisionProviderResult
    ) -> None:
        if result.instruction_like_content_detected:
            raise AnalysisPipelineError(AnalysisErrorCode.INSTRUCTION_LIKE_CONTENT)
        if result.prohibited_content_detected:
            raise AnalysisPipelineError(AnalysisErrorCode.PROHIBITED_CONTENT)
        expected_market = {
            LocalizationDirection.CHINA_TO_UK: Market.UNITED_KINGDOM,
            LocalizationDirection.UK_TO_CHINA: Market.CHINA,
        }[request.direction]
        if any(
            hypothesis.review_status != "pending" or hypothesis.target_market is not expected_market
            for hypothesis in result.hypotheses
        ):
            raise AnalysisPipelineError(AnalysisErrorCode.UNSAFE_HYPOTHESIS)


class AnalysisPipeline:
    def __init__(
        self,
        provider: VisionProvider,
        *,
        gate: SafetyGate | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._provider = provider
        self._gate = gate or SafetyGate()
        self._now = now or (lambda: datetime.now(UTC))

    def analyze(self, request: VisionAnalysisRequest) -> AdAnalysis:
        self._gate.validate_request(request, now=self._now())
        try:
            raw_result = self._provider.analyze(request)
        except Exception:
            raise AnalysisPipelineError(AnalysisErrorCode.PROVIDER_FAILED) from None
        try:
            result = VisionProviderResult.model_validate(raw_result)
        except (TypeError, ValidationError):
            raise AnalysisPipelineError(
                AnalysisErrorCode.PROVIDER_OUTPUT_INVALID
            ) from None
        self._gate.validate_result(request, result)
        return AdAnalysis(
            source_asset=request.source_asset,
            detected_locale=result.detected_locale,
            brand_lock=request.brand_lock,
            hypotheses=result.hypotheses,
            warnings=result.warnings,
        )
