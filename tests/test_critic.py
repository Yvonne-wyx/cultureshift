from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from cultureshift.contracts import (
    AdAnalysis,
    AdCopy,
    CompositionGenerated,
    CompositionLayer,
    CreativeBrief,
    CulturalHypothesis,
    RunCreate,
)
from cultureshift.critic import Critic, CriticRequest
from cultureshift.repository import DraftRecord

REVIEWED_AT = datetime(2026, 8, 25, 9, 0, tzinfo=UTC)


def _hypothesis(claim: str) -> CulturalHypothesis:
    return CulturalHypothesis(
        hypothesis_id=uuid4(),
        target_market="united_kingdom",
        claim=claim,
        evidence_refs=("evidence:day14-fixture",),
        uncertainty="high",
        rationale="A fixture hypothesis that is not a cultural finding.",
        validation_requirements=("Accountable target-market review",),
        review_status="pending",
    )


def _composition(run_id, logo_id, ui_id) -> CompositionGenerated:
    specs = (
        ("background", None, (0, 0, 1600, 900), "1"),
        ("product_ui", ui_id, (850, 150, 1480, 720), "2"),
        ("logo", logo_id, (100, 70, 320, 166), "3"),
        ("headline", None, (100, 240, 760, 360), "4"),
        ("body", None, (100, 400, 760, 510), "5"),
        ("cta", None, (100, 600, 420, 680), "6"),
        ("disclosure", None, (100, 820, 530, 864), "7"),
    )
    layers = tuple(
        CompositionLayer(
            kind=kind,
            source_asset_id=source,
            rgba_sha256=digit * 64,
            bounds=bounds,
            width=bounds[2] - bounds[0],
            height=bounds[3] - bounds[1],
        )
        for kind, source, bounds, digit in specs
    )
    return CompositionGenerated(
        run_id=run_id,
        status="in_progress",
        execution_mode="fixture",
        width=1600,
        height=900,
        media_type="image/png",
        rendered_sha256="a" * 64,
        artifact_id=uuid4(),
        layers=layers,
        disclosure="Fixture Demo / 非实时模型",
        generated_at=REVIEWED_AT,
    )


def _request(valid_run_payload, *, hypotheses=(), warnings=()) -> CriticRequest:
    run_request = RunCreate.model_validate(valid_run_payload)
    lock = run_request.brand_lock
    analysis = AdAnalysis(
        source_asset=run_request.source_asset,
        detected_locale="zh-CN",
        brand_lock=lock,
        hypotheses=hypotheses,
        warnings=warnings,
    )
    brief = CreativeBrief(
        direction=run_request.direction,
        target_locale="en-GB",
        brand_lock=lock,
        hypotheses=hypotheses,
        narrative="Present a clear, reviewable workflow.",
        use_scenario="A team reviews approved notes before organising summaries.",
        trust_information="Fixture Demo / 非实时模型",
    )
    ad_copy = AdCopy(
        locale="en-GB",
        headline="Turn approved notes into task summaries",
        body="Orbit AI helps teams organise approved notes into task summaries.",
        cta_label="Try the fixture demo",
        cta_action_meaning=lock.cta_action_meaning,
    )
    draft = DraftRecord(
        brief=brief,
        ad_copy=ad_copy,
        fact_references=lock.verified_product_facts,
        rule_ids=("ZEU-S1", "ZEU-S3"),
        generated_at=REVIEWED_AT,
    )
    return CriticRequest(
        analysis=analysis,
        confirmed_brand_lock=lock,
        draft=draft,
        composition=_composition(
            uuid4(),
            lock.logo_asset_id,
            lock.product_ui_asset_ids[0],
        ),
        warning_codes=(),
    )


def _codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


def test_critic_rejects_brand_mismatch(valid_run_payload) -> None:
    request = _request(valid_run_payload)
    request = replace(
        request,
        composition=_composition(
            request.composition.run_id,
            uuid4(),
            request.confirmed_brand_lock.product_ui_asset_ids[0],
        ),
    )

    report = Critic(now=lambda: REVIEWED_AT).review(request)

    assert report.status.value == "reject"
    assert "brand_lock_mismatch" in _codes(report)


def test_critic_rejects_unsupported_fact_reference(valid_run_payload) -> None:
    request = _request(valid_run_payload)
    changed_draft = replace(
        request.draft,
        fact_references=("Guaranteed perfect output",),
    )
    request = replace(request, draft=changed_draft)

    report = Critic(now=lambda: REVIEWED_AT).review(request)

    assert report.status.value == "reject"
    assert "unsupported_fact" in _codes(report)


def test_critic_requests_revision_for_unreadable_copy(valid_run_payload) -> None:
    request = _request(valid_run_payload)
    unreadable = request.draft.ad_copy.model_copy(update={"headline": "x" * 81})
    changed_draft = replace(request.draft, ad_copy=unreadable)
    request = replace(request, draft=changed_draft)

    report = Critic(now=lambda: REVIEWED_AT).review(request)

    assert report.status.value == "revise"
    assert "copy_unreadable" in _codes(report)


def test_critic_requests_revision_for_absolute_cultural_claim(
    valid_run_payload,
) -> None:
    hypothesis = _hypothesis("All British people prefer minimal advertising.")
    request = _request(valid_run_payload, hypotheses=(hypothesis,))

    report = Critic(now=lambda: REVIEWED_AT).review(request)

    assert report.status.value == "revise"
    assert "absolute_cultural_claim" in _codes(report)
    assert hypothesis.review_status == "pending"


def test_critic_requires_review_for_possible_stereotype(valid_run_payload) -> None:
    hypothesis = _hypothesis("British people are reserved.")
    request = _request(valid_run_payload, hypotheses=(hypothesis,))

    report = Critic(now=lambda: REVIEWED_AT).review(request)

    assert report.status.value == "needs_human_review"
    assert "possible_stereotype" in _codes(report)


def test_critic_rejects_persisted_safety_refusal(valid_run_payload) -> None:
    request = _request(valid_run_payload, warnings=("prohibited_content",))

    report = Critic(now=lambda: REVIEWED_AT).review(request)

    assert report.status.value == "reject"
    assert "safety_refusal" in _codes(report)


def test_critic_clean_request_passes(valid_run_payload) -> None:
    report = Critic(now=lambda: REVIEWED_AT).review(_request(valid_run_payload))

    assert report.status.value == "pass"
    assert report.issues == ()
    assert report.requires_human_review is False
    assert report.reviewed_at == REVIEWED_AT


def test_critic_keeps_pending_hypothesis_for_human_review(valid_run_payload) -> None:
    hypothesis = _hypothesis("A reviewable workflow may be useful to test.")
    request = _request(valid_run_payload, hypotheses=(hypothesis,))

    report = Critic(now=lambda: REVIEWED_AT).review(request)

    assert report.status.value == "needs_human_review"
    assert "cultural_hypothesis_pending" in _codes(report)
    assert request.analysis.hypotheses[0].review_status == "pending"
