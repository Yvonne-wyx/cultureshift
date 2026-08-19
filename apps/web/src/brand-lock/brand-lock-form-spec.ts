import type { BrandLock } from "../generated/contracts";

export interface BrandLockFieldSpec {
  key: keyof BrandLock;
  label: string;
  help: string;
  control:
    | "asset_preview"
    | "text"
    | "ordered_text"
    | "ordered_assets"
    | "reorder"
    | "multi_select";
  preview: boolean;
  required: true;
  constraints: {
    ordered?: boolean;
    repeatable?: boolean;
    minItems?: number;
    maxItems?: number;
    allowedValues?: readonly string[];
  };
}

export const BRAND_LOCK_FORM_SPEC = [
  {
    key: "logo_asset_id",
    label: "Logo asset",
    help: "Review the approved logo asset; replacement is a Day 10 decision.",
    control: "asset_preview",
    preview: true,
    required: true,
    constraints: {},
  },
  {
    key: "product_name",
    label: "Product name",
    help: "Review the canonical product name that localized copy must preserve.",
    control: "text",
    preview: false,
    required: true,
    constraints: {},
  },
  {
    key: "verified_product_facts",
    label: "Verified product facts",
    help: "Review only approved factual claims and their intended order.",
    control: "ordered_text",
    preview: false,
    required: true,
    constraints: { ordered: true, repeatable: true, minItems: 1, maxItems: 32 },
  },
  {
    key: "product_ui_asset_ids",
    label: "Product UI assets",
    help: "Review the approved product-interface assets shown in the proposal.",
    control: "ordered_assets",
    preview: true,
    required: true,
    constraints: { ordered: true, repeatable: true, minItems: 1, maxItems: 16 },
  },
  {
    key: "benefit_order",
    label: "Benefit order",
    help: "Review the priority order without changing it before confirmation.",
    control: "reorder",
    preview: false,
    required: true,
    constraints: { ordered: true, repeatable: true, minItems: 1, maxItems: 16 },
  },
  {
    key: "cta_action_meaning",
    label: "CTA action meaning",
    help: "Review the invariant action meaning, separate from its localized label.",
    control: "text",
    preview: false,
    required: true,
    constraints: {},
  },
  {
    key: "layout_template_asset_id",
    label: "Layout template",
    help: "Review the approved layout represented by the target preview.",
    control: "asset_preview",
    preview: true,
    required: true,
    constraints: {},
  },
  {
    key: "localizable_fields",
    label: "Localizable fields",
    help: "Review the only fields that Day 10 may allow for localization.",
    control: "multi_select",
    preview: false,
    required: true,
    constraints: {
      repeatable: true,
      minItems: 1,
      maxItems: 4,
      allowedValues: ["narrative", "use_scenario", "trust_information", "language"],
    },
  },
] as const satisfies readonly BrandLockFieldSpec[];
