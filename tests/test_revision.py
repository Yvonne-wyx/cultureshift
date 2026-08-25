from datetime import UTC, datetime
from uuid import uuid4

import pytest

from cultureshift.contracts import AdCopy, BrandLock, CreativeBrief, Locale, RevisionChange
from cultureshift.domain import LocalizationDirection
from cultureshift.repository import DraftRecord
from cultureshift.revision import FixtureRevisionEngine


def _draft(direction: LocalizationDirection) -> DraftRecord:
    brand_lock = BrandLock(
        logo_asset_id=uuid4(),
        product_name="Orbit AI",
        verified_product_facts=("Turns approved notes into task summaries",),
        product_ui_asset_ids=(uuid4(),),
        benefit_order=("Summarize", "Organize"),
        cta_action_meaning="Start a fixture demo",
        layout_template_asset_id=uuid4(),
        localizable_fields=("narrative", "use_scenario", "trust_information", "language"),
    )
    if direction is LocalizationDirection.CHINA_TO_UK:
        locale = Locale.EN_GB
        headline = "Turn approved notes into clear task summaries"
        body = "Orbit AI helps teams organise approved meeting notes into task summaries."
        cta_label = "Try the fixture demo"
        rule_ids = ("ZEU-S1", "ZEU-S3")
    else:
        locale = Locale.ZH_CN
        headline = "把已批准笔记整理成清晰任务摘要"
        body = "Orbit AI 帮助团队将已批准的会议笔记整理为任务摘要。"
        cta_label = "体验示例演示"
        rule_ids = ("EZC-S1", "EZC-S3")
    brief = CreativeBrief(
        direction=direction,
        target_locale=locale,
        brand_lock=brand_lock,
        narrative="A reviewable fixture narrative.",
        use_scenario="An authorized fictional workflow.",
        trust_information="Fixture Demo / 非实时模型",
    )
    return DraftRecord(
        brief=brief,
        ad_copy=AdCopy(
            locale=locale,
            headline=headline,
            body=body,
            cta_label=cta_label,
            cta_action_meaning=brand_lock.cta_action_meaning,
        ),
        fact_references=brand_lock.verified_product_facts,
        rule_ids=rule_ids,
        generated_at=datetime(2026, 8, 25, tzinfo=UTC),
    )


@pytest.mark.parametrize("direction", tuple(LocalizationDirection))
def test_fixture_revision_changes_only_selected_headline(
    direction: LocalizationDirection,
) -> None:
    original = _draft(direction)
    revised = FixtureRevisionEngine().revise(
        direction, original, (RevisionChange.SHORTEN_HEADLINE,)
    )

    assert revised.ad_copy.headline != original.ad_copy.headline
    assert len(revised.ad_copy.headline) < len(original.ad_copy.headline)
    assert revised.ad_copy.body == original.ad_copy.body
    assert revised.ad_copy.cta_label == original.ad_copy.cta_label
    assert revised.ad_copy.cta_action_meaning == original.ad_copy.cta_action_meaning
    assert revised.brief == original.brief
    assert revised.fact_references == original.fact_references
    assert revised.rule_ids == original.rule_ids


@pytest.mark.parametrize("direction", tuple(LocalizationDirection))
def test_fixture_revision_changes_only_selected_body(
    direction: LocalizationDirection,
) -> None:
    original = _draft(direction)
    revised = FixtureRevisionEngine().revise(
        direction, original, (RevisionChange.SHORTEN_BODY,)
    )

    assert revised.ad_copy.headline == original.ad_copy.headline
    assert revised.ad_copy.body != original.ad_copy.body
    assert len(revised.ad_copy.body) < len(original.ad_copy.body)
    assert revised.brief.trust_information == "Fixture Demo / 非实时模型"
    assert revised.ad_copy.cta_action_meaning == original.ad_copy.cta_action_meaning


@pytest.mark.parametrize("direction", tuple(LocalizationDirection))
def test_fixture_revision_can_apply_both_supported_changes_once(
    direction: LocalizationDirection,
) -> None:
    original = _draft(direction)
    revised = FixtureRevisionEngine().revise(
        direction,
        original,
        (RevisionChange.SHORTEN_HEADLINE, RevisionChange.SHORTEN_BODY),
    )

    assert len(revised.ad_copy.headline) < len(original.ad_copy.headline)
    assert len(revised.ad_copy.body) < len(original.ad_copy.body)
    assert revised.fact_references == original.fact_references
    assert revised.rule_ids == original.rule_ids
