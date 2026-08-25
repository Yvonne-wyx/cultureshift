from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from cultureshift.contracts import (
    AdAnalysis,
    BrandLock,
    CompositionGenerated,
    CritiqueCategory,
    CritiqueIssue,
    CritiqueReport,
    CritiqueSeverity,
    CritiqueStatus,
)
from cultureshift.repository import DraftRecord

_SAFETY_REFUSALS = frozenset(
    {"prohibited_content", "instruction_like_content", "safety_refusal"}
)
_ABSOLUTE_CULTURAL_PHRASES = (
    "all british people",
    "british people always",
    "all chinese people",
    "chinese people always",
    "所有英国人",
    "英国人都",
    "所有中国人",
    "中国人都",
)
_STEREOTYPE_PHRASES = (
    "british people are reserved",
    "chinese users only like red",
    "英国人很保守",
    "中国用户只喜欢红色",
)


@dataclass(frozen=True, slots=True)
class CriticRequest:
    analysis: AdAnalysis
    confirmed_brand_lock: BrandLock
    draft: DraftRecord
    composition: CompositionGenerated
    warning_codes: tuple[str, ...] = ()


class Critic:
    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or (lambda: datetime.now(UTC))

    @staticmethod
    def _issue(
        code: str,
        category: CritiqueCategory,
        severity: CritiqueSeverity,
        message: str,
        *,
        requires_human_review: bool = False,
    ) -> CritiqueIssue:
        return CritiqueIssue(
            code=code,
            category=category,
            severity=severity,
            message=message,
            requires_human_review=requires_human_review,
        )

    def review(self, request: CriticRequest) -> CritiqueReport:
        issues: list[CritiqueIssue] = []
        warnings = tuple(dict.fromkeys((*request.analysis.warnings, *request.warning_codes)))
        if _SAFETY_REFUSALS.intersection(warnings):
            issues.append(
                self._issue(
                    "safety_refusal",
                    CritiqueCategory.SAFETY,
                    CritiqueSeverity.BLOCKING,
                    "Persisted safety evidence blocks this concept.",
                )
            )

        layer_sources = {
            layer.kind: layer.source_asset_id
            for layer in request.composition.layers
            if layer.source_asset_id is not None
        }
        lock = request.confirmed_brand_lock
        brand_lock_preserved = (
            request.analysis.brand_lock == lock
            and request.draft.brief.brand_lock == lock
            and request.draft.ad_copy.cta_action_meaning == lock.cta_action_meaning
            and layer_sources.get("logo") == lock.logo_asset_id
            and layer_sources.get("product_ui") in lock.product_ui_asset_ids
        )
        if not brand_lock_preserved:
            issues.append(
                self._issue(
                    "brand_lock_mismatch",
                    CritiqueCategory.BRAND_LOCK,
                    CritiqueSeverity.BLOCKING,
                    "Protected Brand Lock evidence does not match the confirmation.",
                )
            )

        fact_references = request.draft.fact_references
        if not fact_references or not set(fact_references).issubset(
            lock.verified_product_facts
        ):
            issues.append(
                self._issue(
                    "unsupported_fact",
                    CritiqueCategory.FACT,
                    CritiqueSeverity.BLOCKING,
                    "Copy evidence includes an unsupported product fact.",
                )
            )

        copy = request.draft.ad_copy
        if len(copy.headline) > 80 or len(copy.body) > 220 or len(copy.cta_label) > 32:
            issues.append(
                self._issue(
                    "copy_unreadable",
                    CritiqueCategory.READABILITY,
                    CritiqueSeverity.WARNING,
                    "Copy exceeds the deterministic fixture readability limit.",
                )
            )

        for hypothesis in request.analysis.hypotheses:
            claim = hypothesis.claim.casefold()
            if any(phrase in claim for phrase in _ABSOLUTE_CULTURAL_PHRASES):
                issues.append(
                    self._issue(
                        "absolute_cultural_claim",
                        CritiqueCategory.CULTURE,
                        CritiqueSeverity.WARNING,
                        "A population-wide cultural claim must be rewritten as a hypothesis.",
                    )
                )
            elif any(phrase in claim for phrase in _STEREOTYPE_PHRASES):
                issues.append(
                    self._issue(
                        "possible_stereotype",
                        CritiqueCategory.CULTURE,
                        CritiqueSeverity.WARNING,
                        "A possible stereotype requires accountable human review.",
                        requires_human_review=True,
                    )
                )
            elif hypothesis.review_status == "pending":
                issues.append(
                    self._issue(
                        "cultural_hypothesis_pending",
                        CritiqueCategory.CULTURE,
                        CritiqueSeverity.WARNING,
                        "A cultural hypothesis remains pending human review.",
                        requires_human_review=True,
                    )
                )

        if any(issue.severity is CritiqueSeverity.BLOCKING for issue in issues):
            status = CritiqueStatus.REJECT
        elif any(issue.requires_human_review for issue in issues):
            status = CritiqueStatus.NEEDS_HUMAN_REVIEW
        elif issues:
            status = CritiqueStatus.REVISE
        else:
            status = CritiqueStatus.PASS
        requires_human_review = any(issue.requires_human_review for issue in issues)
        return CritiqueReport(
            status=status,
            issues=tuple(issues),
            warnings=warnings,
            brand_lock_preserved=brand_lock_preserved,
            requires_human_review=requires_human_review,
            reviewed_at=self._now(),
        )
