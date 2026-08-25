from __future__ import annotations

from dataclasses import dataclass

from cultureshift.contracts import AdCopy, CreativeBrief, RevisionChange
from cultureshift.domain import LocalizationDirection
from cultureshift.repository import DraftRecord


@dataclass(frozen=True, slots=True)
class RevisionArtifacts:
    brief: CreativeBrief
    ad_copy: AdCopy
    fact_references: tuple[str, ...]
    rule_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _RevisionFixture:
    headline: str
    body: str


_REVISIONS = {
    LocalizationDirection.CHINA_TO_UK: _RevisionFixture(
        headline="Turn approved notes into task summaries",
        body="Orbit AI organises approved notes into task summaries.",
    ),
    LocalizationDirection.UK_TO_CHINA: _RevisionFixture(
        headline="把已批准笔记整理为任务摘要",
        body="Orbit AI 将已批准笔记整理为任务摘要。",
    ),
}


class FixtureRevisionEngine:
    def revise(
        self,
        direction: LocalizationDirection,
        draft: DraftRecord,
        requested_changes: tuple[RevisionChange, ...],
    ) -> RevisionArtifacts:
        if draft.brief.direction is not direction:
            raise ValueError("revision direction must match persisted draft")
        fixture = _REVISIONS[direction]
        selected = frozenset(requested_changes)
        revised_copy = AdCopy(
            locale=draft.ad_copy.locale,
            headline=(
                fixture.headline
                if RevisionChange.SHORTEN_HEADLINE in selected
                else draft.ad_copy.headline
            ),
            body=(
                fixture.body
                if RevisionChange.SHORTEN_BODY in selected
                else draft.ad_copy.body
            ),
            cta_label=draft.ad_copy.cta_label,
            cta_action_meaning=draft.ad_copy.cta_action_meaning,
        )
        return RevisionArtifacts(
            brief=draft.brief,
            ad_copy=revised_copy,
            fact_references=draft.fact_references,
            rule_ids=draft.rule_ids,
        )
