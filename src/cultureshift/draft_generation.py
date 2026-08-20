from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from cultureshift.contracts import (
    AdAnalysis,
    AdCopy,
    BrandLock,
    CreativeBrief,
    Locale,
)
from cultureshift.domain import LocalizationDirection


class DraftErrorCode(StrEnum):
    BRAND_LOCK_UNCONFIRMED = "brand_lock_unconfirmed"
    OUTPUT_INVALID = "draft_output_invalid"


class DraftGenerationError(ValueError):
    def __init__(self, code: DraftErrorCode) -> None:
        self.code = code
        super().__init__("draft generation failed")


@dataclass(frozen=True)
class CopywriterResult:
    ad_copy: AdCopy
    fact_references: tuple[str, ...]
    rule_ids: tuple[str, ...]


class Copywriter(Protocol):
    def write(
        self,
        brief: CreativeBrief,
        rule_ids: tuple[str, ...],
    ) -> CopywriterResult: ...


@dataclass(frozen=True)
class DraftArtifacts:
    brief: CreativeBrief
    ad_copy: AdCopy
    fact_references: tuple[str, ...]
    rule_ids: tuple[str, ...]


@dataclass(frozen=True)
class _DirectionFixture:
    target_locale: Locale
    source_locale: Locale
    rule_ids: tuple[str, str]
    narrative: str
    use_scenario: str
    headline: str
    body: str
    cta_label: str


_FIXTURES = {
    LocalizationDirection.CHINA_TO_UK: _DirectionFixture(
        target_locale=Locale.EN_GB,
        source_locale=Locale.ZH_CN,
        rule_ids=("ZEU-S1", "ZEU-S3"),
        narrative="Present approved-note summarisation as a clear, reviewable workflow.",
        use_scenario=(
            "A UK team reviews approved meeting notes before organising task summaries."
        ),
        headline="Turn approved notes into clear task summaries",
        body=(
            "Orbit AI helps teams organise approved meeting notes into task summaries."
        ),
        cta_label="Try the fixture demo",
    ),
    LocalizationDirection.UK_TO_CHINA: _DirectionFixture(
        target_locale=Locale.ZH_CN,
        source_locale=Locale.EN_GB,
        rule_ids=("EZC-S1", "EZC-S3"),
        narrative="以清晰、可复核的工作流程呈现已批准笔记的整理过程。",
        use_scenario="中国团队在整理任务摘要前复核已批准的会议笔记。",
        headline="把已批准笔记整理成清晰任务摘要",
        body="Orbit AI 帮助团队将已批准的会议笔记整理为任务摘要。",
        cta_label="体验示例演示",
    ),
}


class FixtureCopywriter:
    def write(
        self,
        brief: CreativeBrief,
        rule_ids: tuple[str, ...],
    ) -> CopywriterResult:
        fixture = _FIXTURES[brief.direction]
        return CopywriterResult(
            ad_copy=AdCopy(
                locale=fixture.target_locale,
                headline=fixture.headline,
                body=fixture.body,
                cta_label=fixture.cta_label,
                cta_action_meaning=brief.brand_lock.cta_action_meaning,
            ),
            fact_references=brief.brand_lock.verified_product_facts,
            rule_ids=rule_ids,
        )


class DraftGenerator:
    def __init__(self, copywriter: Copywriter) -> None:
        self._copywriter = copywriter

    def generate(
        self,
        analysis: AdAnalysis,
        confirmed_brand_lock: BrandLock,
    ) -> DraftArtifacts:
        if analysis.brand_lock != confirmed_brand_lock:
            raise DraftGenerationError(DraftErrorCode.BRAND_LOCK_UNCONFIRMED)

        fixture = _FIXTURES.get(self._direction_for_analysis(analysis))
        if fixture is None or analysis.detected_locale is not fixture.source_locale:
            raise DraftGenerationError(DraftErrorCode.OUTPUT_INVALID)
        if any(item.review_status != "pending" for item in analysis.hypotheses):
            raise DraftGenerationError(DraftErrorCode.OUTPUT_INVALID)

        brief = CreativeBrief(
            direction=self._direction_for_analysis(analysis),
            target_locale=fixture.target_locale,
            brand_lock=confirmed_brand_lock,
            hypotheses=analysis.hypotheses,
            narrative=fixture.narrative,
            use_scenario=fixture.use_scenario,
            trust_information="Fixture Demo / 非实时模型",
        )
        result = self._copywriter.write(brief, fixture.rule_ids)
        if (
            result.ad_copy.locale is not fixture.target_locale
            or result.ad_copy.cta_action_meaning
            != confirmed_brand_lock.cta_action_meaning
            or result.rule_ids != fixture.rule_ids
            or result.fact_references != confirmed_brand_lock.verified_product_facts
        ):
            raise DraftGenerationError(DraftErrorCode.OUTPUT_INVALID)
        return DraftArtifacts(
            brief=brief,
            ad_copy=result.ad_copy,
            fact_references=result.fact_references,
            rule_ids=result.rule_ids,
        )

    @staticmethod
    def _direction_for_analysis(analysis: AdAnalysis) -> LocalizationDirection:
        if analysis.detected_locale is Locale.ZH_CN:
            return LocalizationDirection.CHINA_TO_UK
        if analysis.detected_locale is Locale.EN_GB:
            return LocalizationDirection.UK_TO_CHINA
        raise DraftGenerationError(DraftErrorCode.OUTPUT_INVALID)
