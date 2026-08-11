from typing import Any

import pytest


@pytest.fixture
def valid_run_payload() -> dict[str, Any]:
    return {
        "direction": "china_to_uk",
        "execution_mode": "fixture",
        "product_category": "ai_application",
        "creative_format": "static_ad",
        "source_asset": {
            "asset_id": "11111111-1111-4111-8111-111111111111",
            "kind": "source_ad",
            "media_type": "image/png",
            "sha256": "a" * 64,
            "provenance_ref": "fixture:ai-app/source-ad",
            "rights_ref": "rights:fixture-synthetic-v1",
        },
        "brand_lock": {
            "logo_asset_id": "22222222-2222-4222-8222-222222222222",
            "product_name": "Orbit AI",
            "verified_product_facts": ["Turns approved notes into task summaries"],
            "product_ui_asset_ids": ["33333333-3333-4333-8333-333333333333"],
            "benefit_order": ["Summarize", "Organize"],
            "cta_action_meaning": "Start a fixture demo",
            "layout_template_asset_id": "44444444-4444-4444-8444-444444444444",
            "localizable_fields": [
                "narrative",
                "use_scenario",
                "trust_information",
                "language",
            ],
        },
    }
