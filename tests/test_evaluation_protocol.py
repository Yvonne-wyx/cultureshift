import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
RUBRIC = ROOT / "docs/evaluation/rubric-v0.1.json"
PROTOCOL = ROOT / "docs/evaluation/protocol-v0.1.md"


def test_frozen_rubric_has_bilateral_five_point_six_criterion_structure() -> None:
    rubric = json.loads(RUBRIC.read_text(encoding="utf-8"))

    assert rubric["protocol_version"] == "0.1"
    assert rubric["status"] == "frozen_draft"
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


def test_protocol_freezes_blinded_balanced_ab_flow_and_decision_rules() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")

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
    assert "China → UK" in text
    assert "UK → China" in text
    assert "randomized A/B labels" in text
    assert "balanced presentation order" in text
    assert "analyze each direction separately" in text.casefold()
    assert "Brand Lock failure blocks preference selection" in text


def test_protocol_keeps_recruitment_inactive_and_human_judgment_bounded() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")

    assert "Recruitment status: not active in Day 6" in text
    assert "No personal data is collected by this draft" in text
    assert "Participation is voluntary" in text
    assert "withdraw before anonymized aggregation" in text
    assert "reviewer observations, not cultural facts" in text
    assert "does not provide automated cultural validation" in text
    assert "does not establish legal compliance or performance uplift" in text
