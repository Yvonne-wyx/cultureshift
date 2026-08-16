from dataclasses import replace
from typing import Any

import pytest
from pydantic import ValidationError

from cultureshift.analysis_provider import (
    FakeProvider,
    VisionAnalysisRequest,
    VisionProvider,
    VisionProviderResult,
)
from cultureshift.contracts import Locale, RunCreate


@pytest.fixture
def analysis_request(valid_run_payload: dict[str, Any]) -> VisionAnalysisRequest:
    run = RunCreate.model_validate(valid_run_payload)
    return VisionAnalysisRequest(
        content=b"\x89PNG\r\n\x1a\nfixture",
        source_asset=run.source_asset,
        direction=run.direction,
        brand_lock=run.brand_lock,
        product_category=run.product_category,
        creative_format=run.creative_format,
    )


def test_fake_provider_is_deterministic_and_does_not_derive_from_private_bytes(
    analysis_request: VisionAnalysisRequest,
) -> None:
    result = VisionProviderResult(
        detected_locale=Locale.ZH_CN,
        hypotheses=(),
        warnings=("fixture_provider",),
    )
    provider = FakeProvider(result)

    first = provider.analyze(analysis_request)
    second = provider.analyze(
        replace(analysis_request, content=b"\x89PNG\r\n\x1a\nanother-fixture")
    )

    assert first == second == result
    assert provider.call_count == 2


def test_provider_result_is_closed() -> None:
    with pytest.raises(ValidationError):
        VisionProviderResult.model_validate(
            {
                "detected_locale": "zh-CN",
                "private_reasoning": "must not cross the provider boundary",
            }
        )


def test_runtime_protocol_accepts_analyze_implementation(
    analysis_request: VisionAnalysisRequest,
) -> None:
    class MinimalProvider:
        def analyze(self, request: VisionAnalysisRequest) -> VisionProviderResult:
            assert request is analysis_request
            return VisionProviderResult(detected_locale=Locale.ZH_CN)

    provider = MinimalProvider()
    assert isinstance(provider, VisionProvider)
    assert provider.analyze(analysis_request).detected_locale is Locale.ZH_CN
