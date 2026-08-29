import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "docs" / "evaluation"


def test_day17_status_freezes_zero_state_and_closed_gate() -> None:
    status = json.loads((EVALUATION / "day17-reviewer-readiness-status-v1.0.json").read_text())

    assert status["version"] == "1.0"
    assert status["dated"] == "2026-08-29"
    assert status["recruitment"] == "not_open"
    assert status["real_reviewers_confirmed"] == 0
    assert status["responses_collected"] == 0
    assert status["findings_produced"] == 0
    assert status["cultural_approval"] == "not_granted"
    assert status["production_or_campaign_approval"] == "not_granted"
    assert status["activation_gate"] == "closed"


def test_day17_study_package_is_bilateral_complete_and_truthful() -> None:
    package = (EVALUATION / "day17-reviewer-study-package-v1.0.md").read_text()
    required = [
        "China → UK",
        "UK → China",
        "inclusion criteria",
        "exclusion criteria",
        "participant information",
        "consent",
        "withdraw",
        "data minimisation",
        "screening questions",
        "counterbalanced",
        "clarity and readability",
        "factual accuracy",
        "Brand Lock preservation",
        "perceived cultural appropriateness",
        "possible stereotyping",
        "trust and credibility",
        "CTA comprehension",
        "overall preference",
        "reason for preference",
        "discomfort",
        "escalation",
        "stopping rules",
        "not yet approved",
        "decision rule",
        "limitations",
        "reviewer observations",
    ]
    for phrase in required:
        assert phrase.casefold() in package.casefold()

    forbidden = [
        "recruitment is open",
        "culturally approved",
        "validated cultural truth",
        "responses were collected",
    ]
    for phrase in forbidden:
        assert phrase.casefold() not in package.casefold()


def test_day17_activation_checklist_keeps_every_gate_closed() -> None:
    checklist = (EVALUATION / "day17-reviewer-activation-checklist-v1.0.md").read_text()
    gates = [
        "research owner",
        "target reviewer profile",
        "sample-size rationale",
        "recruitment channel",
        "compensation",
        "consent wording",
        "privacy and retention",
        "contact and withdrawal route",
        "data-access permissions",
        "adverse-event escalation",
        "cultural expert involvement",
        "final study materials",
        "explicit user authorization",
    ]
    for gate in gates:
        assert gate.casefold() in checklist.casefold()

    assert checklist.count("- [ ]") >= len(gates)
    assert "Activation gate: CLOSED" in checklist
