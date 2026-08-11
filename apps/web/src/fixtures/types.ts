import type {
  BrandLock,
  CulturalHypothesis,
  RunCreate,
} from "../generated/contracts";

export const FIXTURE_DISCLOSURE = "Fixture Demo / 非实时模型" as const;

export type FixtureId = "china-to-uk" | "uk-to-china";

export interface FixtureBundle {
  fixture_id: FixtureId;
  disclosure: typeof FIXTURE_DISCLOSURE;
  source_locale: "zh-CN" | "en-GB";
  target_locale: "zh-CN" | "en-GB";
  request: RunCreate;
  preview: {
    source_asset_path: string;
    logo_asset_path: string;
    product_ui_asset_path: string;
    source_copy: { headline: string; body: string };
    localized_copy: {
      locale: "zh-CN" | "en-GB";
      headline: string;
      body: string;
      cta_label: string;
      cta_action_meaning: string;
    };
    brand_lock: BrandLock;
    rule_ids: string[];
    hypotheses: CulturalHypothesis[];
    warnings: string[];
    limitation: string;
  };
}
