from dataclasses import replace
from typing import Any

import pytest

from cultureshift.contracts import AdAnalysis, AdCopy, CulturalHypothesis, RunCreate
from cultureshift.domain import LocalizationDirection
from cultureshift.draft_generation import (
    CopywriterResult,
    DraftErrorCode,
    DraftGenerationError,
    DraftGenerator,
    FixtureCopywriter,
)


def _hypothesis(direction: LocalizationDirection) -> CulturalHypothesis:
    china_to_uk = direction is LocalizationDirection.CHINA_TO_UK
    return CulturalHypothesis.model_validate(
        {
            "hypothesis_id": (
                "c1111111-1111-4111-8111-111111111111"
                if china_to_uk
                else "c2222222-2222-4222-8222-222222222222"
            ),
            "target_market": "united_kingdom" if china_to_uk else "china",
            "claim": "A reviewable directional drafting hypothesis.",
            "evidence_refs": [
                "evidence:day3-zeu-h1" if china_to_uk else "evidence:day3-ezc-h1"
            ],
            "uncertainty": "high",
            "rationale": "This is not a cultural finding.",
            "validation_requirements": ["Accountable target-market review"],
            "review_status": "pending",
        }
    )


def _analysis(
    valid_run_payload: dict[str, Any], direction: LocalizationDirection
) -> AdAnalysis:
    payload = dict(valid_run_payload)
    payload["direction"] = direction.value
    request = RunCreate.model_validate(payload)
    return AdAnalysis(
        source_asset=request.source_asset,
        detected_locale="zh-CN" if direction is LocalizationDirection.CHINA_TO_UK else "en-GB",
        brand_lock=request.brand_lock,
        hypotheses=(_hypothesis(direction),),
        warnings=("human_review_required",),
    )


@pytest.mark.parametrize(
    ("direction", "locale", "rules", "headline"),
    [
        (
            LocalizationDirection.CHINA_TO_UK,
            "en-GB",
            ("ZEU-S1", "ZEU-S3"),
            "Turn approved notes into clear task summaries",
        ),
        (
            LocalizationDirection.UK_TO_CHINA,
            "zh-CN",
            ("EZC-S1", "EZC-S3"),
            "把已批准笔记整理成清晰任务摘要",
        ),
    ],
)
def test_generator_returns_deterministic_bilateral_factual_draft(
    valid_run_payload: dict[str, Any],
    direction: LocalizationDirection,
    locale: str,
    rules: tuple[str, str],
    headline: str,
) -> None:
    analysis = _analysis(valid_run_payload, direction)

    result = DraftGenerator(FixtureCopywriter()).generate(analysis, analysis.brand_lock)

    assert result.brief.direction is direction
    assert result.ad_copy.locale == locale
    assert result.ad_copy.headline == headline
    assert result.brief.brand_lock == analysis.brand_lock
    assert result.brief.hypotheses == analysis.hypotheses
    assert result.rule_ids == rules
    assert result.fact_references == analysis.brand_lock.verified_product_facts
    assert result.brief.trust_information == "Fixture Demo / 非实时模型"


class RecordingWriter:
    def __init__(self, result: CopywriterResult) -> None:
        self.result = result
        self.calls = 0

    def write(self, brief, rule_ids):
        del brief, rule_ids
        self.calls += 1
        return self.result


def _safe_writer_result(analysis: AdAnalysis) -> CopywriterResult:
    return CopywriterResult(
        ad_copy=AdCopy(
            locale="en-GB",
            headline="Turn approved notes into task summaries",
            body="Orbit AI turns approved notes into task summaries.",
            cta_label="Try the fixture demo",
            cta_action_meaning=analysis.brand_lock.cta_action_meaning,
        ),
        fact_references=analysis.brand_lock.verified_product_facts,
        rule_ids=("ZEU-S1", "ZEU-S3"),
    )


def test_generator_rejects_unconfirmed_brand_lock_before_writer_call(
    valid_run_payload: dict[str, Any],
) -> None:
    analysis = _analysis(valid_run_payload, LocalizationDirection.CHINA_TO_UK)
    writer = RecordingWriter(_safe_writer_result(analysis))
    changed = analysis.brand_lock.model_copy(update={"product_name": "Changed"})

    with pytest.raises(DraftGenerationError) as caught:
        DraftGenerator(writer).generate(analysis, changed)

    assert caught.value.code is DraftErrorCode.BRAND_LOCK_UNCONFIRMED
    assert writer.calls == 0


@pytest.mark.parametrize(
    "change",
    ["unsupported_fact", "wrong_rule", "wrong_locale", "cta_drift"],
)
def test_generator_rejects_unsafe_copywriter_output(
    valid_run_payload: dict[str, Any], change: str
) -> None:
    analysis = _analysis(valid_run_payload, LocalizationDirection.CHINA_TO_UK)
    safe = _safe_writer_result(analysis)
    if change == "unsupported_fact":
        forged = replace(safe, fact_references=("Guarantees perfect summaries",))
    elif change == "wrong_rule":
        forged = replace(safe, rule_ids=("EZC-S1", "EZC-S3"))
    elif change == "wrong_locale":
        forged = replace(safe, ad_copy=safe.ad_copy.model_copy(update={"locale": "zh-CN"}))
    else:
        forged = replace(
            safe,
            ad_copy=safe.ad_copy.model_copy(update={"cta_action_meaning": "Download a file"}),
        )

    with pytest.raises(DraftGenerationError) as caught:
        DraftGenerator(RecordingWriter(forged)).generate(analysis, analysis.brand_lock)

    assert caught.value.code is DraftErrorCode.OUTPUT_INVALID


def test_generator_never_promotes_a_hypothesis_to_fact(
    valid_run_payload: dict[str, Any],
) -> None:
    analysis = _analysis(valid_run_payload, LocalizationDirection.CHINA_TO_UK)
    accepted = analysis.hypotheses[0].model_copy(update={"review_status": "accepted"})
    analysis = analysis.model_copy(update={"hypotheses": (accepted,)})

    with pytest.raises(DraftGenerationError) as caught:
        DraftGenerator(FixtureCopywriter()).generate(analysis, analysis.brand_lock)

    assert caught.value.code is DraftErrorCode.OUTPUT_INVALID
