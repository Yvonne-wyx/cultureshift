import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPARISON = ROOT / "docs/research/vision-provider-comparison-2026-08-16.json"

REQUIRED_DIMENSIONS = {
    "training_use",
    "retention",
    "regional_storage_and_processing",
    "public_pricing_unit",
    "structured_multimodal_suitability",
    "unresolved_approval_requirements",
}
OFFICIAL_SOURCES = {
    "https://platform.openai.com/docs/models/default-usage-policies-by-endpoint",
    "https://openai.com/api/pricing/",
    "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention",
    "https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations",
    "https://cloud.google.com/vertex-ai/generative-ai/pricing",
    "https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html",
    "https://docs.aws.amazon.com/bedrock/latest/userguide/models-region-compatibility.html",
    "https://aws.amazon.com/bedrock/pricing/",
}


def test_provider_comparison_uses_official_sources_and_required_dimensions() -> None:
    comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))

    assert comparison["accessed_at"] == "2026-08-16"
    assert comparison["decision"] == "no_live_provider_approved"
    assert {item["provider"] for item in comparison["providers"]} == {
        "OpenAI API",
        "Google Vertex AI",
        "Amazon Bedrock",
    }
    assert all(
        set(item["dimensions"]) == REQUIRED_DIMENSIONS
        for item in comparison["providers"]
    )
    sources = {
        source
        for item in comparison["providers"]
        for source in item["sources"]
    }
    assert sources == OFFICIAL_SOURCES
    assert all(
        set(dimension) == {"verified", "inference"}
        for item in comparison["providers"]
        for dimension in item["dimensions"].values()
    )
