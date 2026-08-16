from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest

from cultureshift.analysis_pipeline import (
    AnalysisErrorCode,
    AnalysisPipeline,
    AnalysisPipelineError,
)
from cultureshift.analysis_provider import VisionAnalysisRequest, VisionProviderResult
from cultureshift.contracts import CulturalHypothesis, RunCreate

PNG = b"\x89PNG\r\n\x1a\nprivate-marker"
NOW = datetime(2026, 8, 16, 8, 0, tzinfo=UTC)


class RecordingProvider:
    def __init__(self, result: VisionProviderResult | dict[str, object]) -> None:
        self.result = result
        self.call_count = 0

    def analyze(self, request: VisionAnalysisRequest) -> VisionProviderResult | dict[str, object]:
        del request
        self.call_count += 1
        return self.result


class FailingProvider:
    def analyze(self, request: VisionAnalysisRequest) -> VisionProviderResult:
        del request
        raise RuntimeError("provider-private-message")


@pytest.fixture
def analysis_request(valid_run_payload: dict[str, Any]) -> VisionAnalysisRequest:
    run = RunCreate.model_validate(valid_run_payload)
    source_asset = run.source_asset.model_copy(update={"expires_at": NOW + timedelta(hours=1)})
    return VisionAnalysisRequest(
        content=PNG,
        source_asset=source_asset,
        direction=run.direction,
        brand_lock=run.brand_lock,
        product_category=run.product_category,
        creative_format=run.creative_format,
    )


def _hypothesis(*, target_market: str = "united_kingdom", status: str = "pending"):
    return CulturalHypothesis.model_validate(
        {
            "hypothesis_id": UUID("55555555-5555-4555-8555-555555555555"),
            "target_market": target_market,
            "claim": "Reviewers may prefer a concise workflow proof point.",
            "evidence_refs": ["evidence:fixture/day8"],
            "uncertainty": "high",
            "rationale": "A reviewable fixture hypothesis, not a cultural fact.",
            "validation_requirements": ["Qualified target-market reviewer"],
            "review_status": status,
        }
    )


def _safe_result(**changes: object) -> VisionProviderResult:
    values: dict[str, object] = {
        "detected_locale": "zh-CN",
        "hypotheses": (_hypothesis(),),
        "warnings": ("fixture_provider",),
    }
    values.update(changes)
    return VisionProviderResult.model_validate(values)


@pytest.mark.parametrize(
    ("request_change", "expected_code"),
    [
        ({"content": b""}, AnalysisErrorCode.INVALID_INPUT),
        ({"content": b"not-a-png"}, AnalysisErrorCode.INVALID_INPUT),
        ({"product_category": "medical"}, AnalysisErrorCode.UNSUPPORTED_SCOPE),
        ({"creative_format": "video"}, AnalysisErrorCode.UNSUPPORTED_SCOPE),
    ],
)
def test_preflight_blocks_before_provider(
    request_change: dict[str, object],
    expected_code: AnalysisErrorCode,
    analysis_request: VisionAnalysisRequest,
) -> None:
    provider = RecordingProvider(_safe_result())
    with pytest.raises(AnalysisPipelineError) as caught:
        AnalysisPipeline(provider, now=lambda: NOW).analyze(
            replace(analysis_request, **request_change)
        )
    assert caught.value.code is expected_code
    assert provider.call_count == 0


def test_expired_asset_is_blocked_before_provider(
    analysis_request: VisionAnalysisRequest,
) -> None:
    provider = RecordingProvider(_safe_result())
    expired = analysis_request.source_asset.model_copy(update={"expires_at": NOW})
    with pytest.raises(AnalysisPipelineError) as caught:
        AnalysisPipeline(provider, now=lambda: NOW).analyze(
            replace(analysis_request, source_asset=expired)
        )
    assert caught.value.code is AnalysisErrorCode.ASSET_CLOSED
    assert provider.call_count == 0


@pytest.mark.parametrize(
    ("result", "expected_code"),
    [
        ({"detected_locale": "not-a-locale"}, AnalysisErrorCode.PROVIDER_OUTPUT_INVALID),
        (
            _safe_result(instruction_like_content_detected=True),
            AnalysisErrorCode.INSTRUCTION_LIKE_CONTENT,
        ),
        (_safe_result(prohibited_content_detected=True), AnalysisErrorCode.PROHIBITED_CONTENT),
        (
            _safe_result(hypotheses=(_hypothesis(target_market="china"),)),
            AnalysisErrorCode.UNSAFE_HYPOTHESIS,
        ),
        (
            _safe_result(hypotheses=(_hypothesis(status="accepted"),)),
            AnalysisErrorCode.UNSAFE_HYPOTHESIS,
        ),
    ],
)
def test_provider_output_fails_closed(
    result: VisionProviderResult | dict[str, object],
    expected_code: AnalysisErrorCode,
    analysis_request: VisionAnalysisRequest,
) -> None:
    with pytest.raises(AnalysisPipelineError) as caught:
        AnalysisPipeline(RecordingProvider(result), now=lambda: NOW).analyze(analysis_request)
    assert caught.value.code is expected_code


def test_provider_exception_is_sanitized(
    analysis_request: VisionAnalysisRequest, caplog: pytest.LogCaptureFixture
) -> None:
    with pytest.raises(AnalysisPipelineError) as caught:
        AnalysisPipeline(FailingProvider(), now=lambda: NOW).analyze(analysis_request)
    surface = f"{caught.value!r} {caught.value} {caplog.text}"
    assert caught.value.code is AnalysisErrorCode.PROVIDER_FAILED
    for secret in (
        "private-marker",
        r"C:\private\source.png",
        "rejected private claim",
        "provider-private-message",
    ):
        assert secret not in surface


def test_safe_success_preserves_trusted_request_objects(
    analysis_request: VisionAnalysisRequest,
) -> None:
    provider_result = _safe_result()
    analysis = AnalysisPipeline(
        RecordingProvider(provider_result), now=lambda: NOW
    ).analyze(analysis_request)

    assert analysis.source_asset is analysis_request.source_asset
    assert analysis.brand_lock is analysis_request.brand_lock
    assert analysis.hypotheses == provider_result.hypotheses


def test_safe_success_supports_uk_to_china(
    analysis_request: VisionAnalysisRequest,
) -> None:
    request = replace(analysis_request, direction="uk_to_china")
    result = _safe_result(detected_locale="en-GB", hypotheses=(_hypothesis(target_market="china"),))

    analysis = AnalysisPipeline(RecordingProvider(result), now=lambda: NOW).analyze(request)

    assert analysis.detected_locale == "en-GB"
    assert analysis.hypotheses[0].target_market == "china"
