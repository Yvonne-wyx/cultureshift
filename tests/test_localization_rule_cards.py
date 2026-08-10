import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RULE_CARDS = (
    ROOT / "docs" / "localization" / "zh-to-en-uk-rule-card-v1.md",
    ROOT / "docs" / "localization" / "en-to-zh-cn-rule-card-v1.md",
)


@pytest.mark.parametrize("rule_card", RULE_CARDS)
def test_rule_card_keeps_evidence_separate_from_hypotheses(rule_card: Path) -> None:
    content = rule_card.read_text(encoding="utf-8")

    assert "## Source-backed rules" in content
    assert "## Hypotheses requiring validation" in content
    assert "## Source register" in content
    assert "Retrieved: 2026-08-10" in content
    assert "CulturalHypothesis" in content
    assert "Human review" in content

    source_section, hypothesis_section = content.split("## Hypotheses requiring validation")
    source_rows = [line for line in source_section.splitlines() if re.match(r"\| \w+-S\d+ ", line)]
    hypothesis_rows = [
        line for line in hypothesis_section.splitlines() if re.match(r"\| \w+-H\d+ ", line)
    ]
    assert source_rows
    assert hypothesis_rows
    for row in source_rows:
        references = re.findall(r"\[S\d+\]", row)
        assert references
        assert all(f"**{reference}**" in content for reference in references)
    assert all("CulturalHypothesis" in hypothesis_section for _ in hypothesis_rows)


@pytest.mark.parametrize("rule_card", RULE_CARDS)
def test_rule_card_preserves_brand_lock(rule_card: Path) -> None:
    content = rule_card.read_text(encoding="utf-8")

    for locked_field in (
        "logo",
        "product name",
        "verified product facts",
        "real UI",
        "benefit order",
        "CTA action meaning",
        "layout template",
    ):
        assert locked_field in content
