import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
RUBRIC = ROOT / "docs/evaluation/rubric-v0.1.json"
PROTOCOL = ROOT / "docs/evaluation/protocol-v0.1.md"
RECRUITMENT_PACK = ROOT / "docs/evaluation/recruitment-pack-v0.1.md"
RECRUITMENT_STATUS = ROOT / "docs/evaluation/recruitment-status.json"


def test_frozen_rubric_has_bilateral_five_point_six_criterion_structure() -> None:
    rubric = json.loads(RUBRIC.read_text(encoding="utf-8"))

    assert rubric["protocol_version"] == "0.2"
    assert rubric["status"] == "frozen"
    assert rubric["directions"] == ["china_to_uk", "uk_to_china"]
    assert [item["value"] for item in rubric["scale"]] == [1, 2, 3, 4, 5]
    assert {criterion["id"] for criterion in rubric["criteria"]} == {
        "brand_lock_preservation",
        "language_naturalness",
        "task_clarity",
        "evidence_traceability",
        "safety_and_non_misleadingness",
        "overall_preference",
    }
    brand_lock = next(
        criterion
        for criterion in rubric["criteria"]
        if criterion["id"] == "brand_lock_preservation"
    )
    assert brand_lock["blocking"] is True
    assert all(criterion["reviewer_observation"] is True for criterion in rubric["criteria"])
    assert len(rubric["severe_risk_flags"]) == 5
    assert all(item["type"] == "boolean" for item in rubric["severe_risk_flags"])


def test_protocol_freezes_blinded_balanced_ab_flow_and_decision_rules() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    for heading in (
        "## Status and version",
        "## Blinded A/B procedure",
        "## Evaluation rubric",
        "## Decision rules",
        "## Consent and withdrawal",
        "## Recruitment structure",
        "## Privacy and data handling",
        "## Limitations",
    ):
        assert heading in text
    assert "China to UK" in normalized
    assert "UK to China" in normalized
    assert "randomized A/B labels" in text
    assert "Balance left/right presentation order" in text
    assert "Analyze each direction separately" in text
    assert "Brand Lock failure blocks preference selection" in text


def test_protocol_finalizes_sampling_and_keeps_human_judgment_bounded() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "Protocol version: 0.2" in text
    assert "Status: frozen" in text
    assert "12 cases" in normalized
    assert "six per direction" in normalized
    assert "at least three independent" in normalized
    assert "6-8 reviewers" in normalized
    assert "language-only baseline" in normalized
    assert "Participation is voluntary" in text
    assert "withdraw before the stated aggregate-freeze" in normalized
    assert "Reviewer observations are not cultural facts" in text
    assert "does not provide automated cultural validation" in normalized
    assert "does not establish legal compliance or" in normalized
    assert "performance uplift" in normalized


def test_recruitment_materials_are_public_safe_and_truthful() -> None:
    text = RECRUITMENT_PACK.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    status = json.loads(RECRUITMENT_STATUS.read_text(encoding="utf-8"))

    for phrase in (
        "adult reviewers",
        "relevant language or target-context experience",
        "Nationality is not an eligibility requirement",
        "participation",
        "anonymized aggregate reporting",
        "public attribution",
        "quotation",
        "withdrawal deadline",
        "approved private contact route",
    ):
        assert phrase in normalized
    assert status == {
        "protocol_version": "0.2",
        "status": "pending_human_activation",
        "opened_at": None,
        "real_reviewers_confirmed": 0,
        "activation_requirements": [
            "named_human_coordinator",
            "approved_private_contact_route",
            "protected_consent_vault",
        ],
        "public_claim": "Recruitment materials are ready; no outreach evidence is recorded.",
    }
