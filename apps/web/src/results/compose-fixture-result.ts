import type { BrandLock, CulturalHypothesis } from "../generated/contracts";
import type { FixtureBundle, FixtureId } from "../fixtures/types";

const DIRECTION_LABELS: Readonly<Record<FixtureId, string>> = {
  "china-to-uk": "China to UK",
  "uk-to-china": "UK to China",
};

function deepFreeze<T>(value: T): Readonly<T> {
  if (value !== null && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const nested of Object.values(value)) {
      deepFreeze(nested);
    }
  }
  return value;
}

export interface FixtureResult {
  fixture_id: FixtureId;
  direction_label: string;
  source_locale: FixtureBundle["source_locale"];
  target_locale: FixtureBundle["target_locale"];
  watermark: FixtureBundle["disclosure"];
  source: FixtureBundle["preview"]["source_copy"] & { asset_path: string };
  proposal: FixtureBundle["preview"]["localized_copy"] & {
    logo_asset_path: string;
    product_ui_asset_path: string;
  };
  brand_lock: BrandLock;
  rule_ids: string[];
  hypotheses: CulturalHypothesis[];
  warnings: string[];
  limitation: string;
  draft: FixtureBundle["draft"];
  composition: FixtureBundle["composition"];
  walkthrough: { title: string; description: string }[];
}

export function composeFixtureResult(
  fixture: Readonly<FixtureBundle>,
): Readonly<FixtureResult> {
  const preview = fixture.preview;
  const result: FixtureResult = {
    fixture_id: fixture.fixture_id,
    direction_label: DIRECTION_LABELS[fixture.fixture_id],
    source_locale: fixture.source_locale,
    target_locale: fixture.target_locale,
    watermark: fixture.disclosure,
    source: {
      asset_path: preview.source_asset_path,
      headline: preview.source_copy.headline,
      body: preview.source_copy.body,
    },
    proposal: {
      ...preview.localized_copy,
      logo_asset_path: preview.logo_asset_path,
      product_ui_asset_path: preview.product_ui_asset_path,
    },
    brand_lock: structuredClone(preview.brand_lock),
    rule_ids: [...preview.rule_ids],
    hypotheses: structuredClone(preview.hypotheses),
    warnings: [...preview.warnings],
    limitation: preview.limitation,
    draft: structuredClone(fixture.draft),
    composition: structuredClone(fixture.composition),
    walkthrough: [
      { title: "1. Review source", description: "Confirm the supplied creative and direction." },
      { title: "2. Inspect proposal", description: "Compare the fixture-only localized composition." },
      { title: "3. Verify traceability", description: "Check Brand Lock, rules, and pending evidence." },
    ],
  };
  return deepFreeze(result);
}
