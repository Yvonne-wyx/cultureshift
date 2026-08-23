import type {
  AdCopy,
  BrandLock,
  CompositionLayer,
  CulturalHypothesis,
  RunCreate,
} from "../generated/contracts";
import { FIXTURE_DISCLOSURE, type FixtureBundle, type FixtureId } from "./types";

type JsonObject = Record<string, unknown>;

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SHA256 = /^[a-f0-9]{64}$/;
const PUBLIC_REFERENCE = /^(?:fixture|rights|evidence):[A-Za-z0-9][A-Za-z0-9._/-]*$/;
const APPROVED_BRAND_LOCK: Readonly<BrandLock> = deepFreeze<BrandLock>({
  logo_asset_id: "a1111111-1111-4111-8111-111111111111",
  product_name: "Orbit AI",
  verified_product_facts: ["Turns approved notes into task summaries"],
  product_ui_asset_ids: ["a2222222-2222-4222-8222-222222222222"],
  benefit_order: ["Summarize", "Organize"],
  cta_action_meaning: "Start a fixture demo",
  layout_template_asset_id: "a3333333-3333-4333-8333-333333333333",
  localizable_fields: ["narrative", "use_scenario", "trust_information", "language"],
});
const APPROVED_SOURCE_BY_FIXTURE = deepFreeze({
  "china-to-uk": {
    direction: "china_to_uk",
    source_asset: {
      asset_id: "b1111111-1111-4111-8111-111111111111",
      kind: "source_ad",
      media_type: "image/svg+xml",
      sha256: "58c22343c4cc16ee3ba25bdeed5c897dce442426d9b500a7a2704edeac3ccc39",
      provenance_ref: "fixture:orbit-ai-source-zh-cn-001",
      rights_ref: "rights:demo-assets-manifest",
    },
    source_asset_path: "/fixtures/orbit-ai/source-zh-cn.svg",
  },
  "uk-to-china": {
    direction: "uk_to_china",
    source_asset: {
      asset_id: "b2222222-2222-4222-8222-222222222222",
      kind: "source_ad",
      media_type: "image/svg+xml",
      sha256: "f85f732a435126690b2908508597cc800e7b99fc07b98c9a035bddd0b9091d68",
      provenance_ref: "fixture:orbit-ai-source-en-gb-001",
      rights_ref: "rights:demo-assets-manifest",
    },
    source_asset_path: "/fixtures/orbit-ai/source-en-gb.svg",
  },
} as const);
const APPROVED_COMPOSITION_BY_FIXTURE = deepFreeze({
  "china-to-uk": {
    preview_path: "/fixtures/orbit-ai/composed-china-to-uk.png",
    rendered_sha256: "39d3233aa64533558579a5d9ad0ff345105555ea4ae69dfd8c26f5faaddb0d15",
    background_provenance: "fixture:day12-background-china_to_uk",
  },
  "uk-to-china": {
    preview_path: "/fixtures/orbit-ai/composed-uk-to-china.png",
    rendered_sha256: "e64f1342a728d561c141accf9cf78b5d43f251b5f550cf7be616a00da049517f",
    background_provenance: "fixture:day12-background-uk_to_china",
  },
} as const);
const FONT_SHA256 = "2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b";
const FONT_COMMIT = "f8d157532fbfaeda587e826d4cd5b21a49186f7c";

function invalid(code: string): never {
  throw new Error(`Invalid fixture: ${code}`);
}

function object(value: unknown, code: string): JsonObject {
  if (value === null || typeof value !== "object" || Array.isArray(value)) invalid(code);
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) invalid(code);
  return value as JsonObject;
}

function text(value: unknown, code: string): string {
  if (typeof value !== "string" || value.trim() === "") invalid(code);
  return value;
}

function strings(value: unknown, code: string): string[] {
  if (!Array.isArray(value) || value.length === 0) invalid(code);
  return value.map((item) => text(item, code));
}

function uuid(value: unknown, code: string): string {
  const result = text(value, code);
  if (!UUID_V4.test(result)) invalid(code);
  return result;
}

function publicReference(value: unknown, code = "rights_missing"): string {
  const result = text(value, code);
  if (!PUBLIC_REFERENCE.test(result)) invalid(code);
  return result;
}

function publicPath(value: unknown): string {
  const result = text(value, "unsafe_asset_path");
  const segments = result.split("/");
  if (
    !result.startsWith("/fixtures/orbit-ai/") ||
    result.includes("\\") ||
    /[a-z][a-z0-9+.-]*:/i.test(result) ||
    result.includes("?") ||
    result.includes("#") ||
    segments.some((segment) => segment === "." || segment === "..") ||
    !result.endsWith(".svg")
  ) {
    invalid("unsafe_asset_path");
  }
  return result;
}

function publicPngPath(value: unknown): string {
  const result = text(value, "unsafe_asset_path");
  if (
    !result.startsWith("/fixtures/orbit-ai/composed-") ||
    !result.endsWith(".png") ||
    result.includes("\\") ||
    result.includes("..") ||
    result.includes("?") ||
    result.includes("#")
  ) invalid("unsafe_asset_path");
  return result;
}

function exactKeys(value: JsonObject, expected: readonly string[], code: string): void {
  if (!structuralEqual(Object.keys(value).sort(), [...expected].sort())) invalid(code);
}

function compositionEvidence(
  value: unknown,
  fixtureId: FixtureId,
  lock: BrandLock,
): FixtureBundle["composition"] {
  const composition = object(value, "invalid_composition");
  exactKeys(composition, [
    "execution_mode", "width", "height", "media_type", "preview_path",
    "rendered_sha256", "background_provenance", "layers", "font", "disclosure",
    "limitation",
  ], "invalid_composition");
  const approved = APPROVED_COMPOSITION_BY_FIXTURE[fixtureId];
  if (
    composition.execution_mode !== "fixture" || composition.width !== 1600 ||
    composition.height !== 900 || composition.media_type !== "image/png" ||
    publicPngPath(composition.preview_path) !== approved.preview_path ||
    text(composition.rendered_sha256, "invalid_composition") !== approved.rendered_sha256 ||
    publicReference(composition.background_provenance, "invalid_composition") !== approved.background_provenance ||
    composition.disclosure !== FIXTURE_DISCLOSURE
  ) invalid("invalid_composition");
  if (!Array.isArray(composition.layers) || composition.layers.length !== 7) {
    invalid("invalid_composition");
  }
  const expectedKinds = [
    "background", "product_ui", "logo", "headline", "body", "cta", "disclosure",
  ] as const;
  const layers = composition.layers.map((rawLayer, index): CompositionLayer => {
    const layer = object(rawLayer, "invalid_composition");
    exactKeys(layer, ["kind", "source_asset_id", "rgba_sha256", "bounds", "width", "height"], "invalid_composition");
    if (layer.kind !== expectedKinds[index] || !SHA256.test(text(layer.rgba_sha256, "invalid_composition"))) {
      invalid("invalid_composition");
    }
    if (!Array.isArray(layer.bounds) || layer.bounds.length !== 4 || !layer.bounds.every(Number.isInteger)) {
      invalid("invalid_composition");
    }
    const [left, top, right, bottom] = layer.bounds as number[];
    if (
      !Number.isInteger(layer.width) || !Number.isInteger(layer.height) ||
      left < 0 || top < 0 || right > 1600 || bottom > 900 ||
      right - left !== layer.width || bottom - top !== layer.height
    ) invalid("invalid_composition");
    const expectedSource = layer.kind === "logo"
      ? lock.logo_asset_id
      : layer.kind === "product_ui" ? lock.product_ui_asset_ids[0] : null;
    if (layer.source_asset_id !== expectedSource) invalid("invalid_composition");
    return {
      kind: layer.kind as CompositionLayer["kind"],
      source_asset_id: expectedSource,
      rgba_sha256: layer.rgba_sha256 as string,
      bounds: layer.bounds as CompositionLayer["bounds"],
      width: layer.width as number,
      height: layer.height as number,
    };
  });
  const font = object(composition.font, "invalid_composition");
  exactKeys(font, ["path", "sha256", "upstream_commit"], "invalid_composition");
  if (
    font.path !== "assets/fonts/NotoSansCJKsc-Regular.otf" ||
    font.sha256 !== FONT_SHA256 || font.upstream_commit !== FONT_COMMIT
  ) invalid("invalid_composition");
  const limitation = text(composition.limitation, "invalid_composition");
  if (!/fixture-only composition; human review required/i.test(limitation)) {
    invalid("invalid_composition");
  }
  return {
    execution_mode: "fixture",
    width: 1600,
    height: 900,
    media_type: "image/png",
    preview_path: approved.preview_path,
    rendered_sha256: approved.rendered_sha256,
    background_provenance: approved.background_provenance,
    layers,
    font: {
      path: "assets/fonts/NotoSansCJKsc-Regular.otf",
      sha256: FONT_SHA256,
      upstream_commit: FONT_COMMIT,
    },
    disclosure: FIXTURE_DISCLOSURE,
    limitation,
  };
}

function structuralEqual(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (typeof left !== typeof right || left === null || right === null) return false;
  if (Array.isArray(left) || Array.isArray(right)) {
    return Array.isArray(left) && Array.isArray(right) && left.length === right.length && left.every((item, index) => structuralEqual(item, right[index]));
  }
  if (typeof left === "object") {
    const leftObject = left as JsonObject;
    const rightObject = right as JsonObject;
    const leftKeys = Object.keys(leftObject).sort();
    const rightKeys = Object.keys(rightObject).sort();
    return leftKeys.length === rightKeys.length && leftKeys.every((key, index) => key === rightKeys[index] && structuralEqual(leftObject[key], rightObject[key]));
  }
  return false;
}

function brandLock(value: unknown): BrandLock {
  const lock = object(value, "brand_lock_mismatch");
  if (!structuralEqual(lock, APPROVED_BRAND_LOCK)) invalid("brand_lock_mismatch");
  const localizable = strings(lock.localizable_fields, "brand_lock_mismatch");
  const allowed = new Set(["narrative", "use_scenario", "trust_information", "language"]);
  if (localizable.some((field) => !allowed.has(field))) invalid("brand_lock_mismatch");
  return {
    logo_asset_id: uuid(lock.logo_asset_id, "brand_lock_mismatch"),
    product_name: text(lock.product_name, "brand_lock_mismatch"),
    verified_product_facts: strings(lock.verified_product_facts, "brand_lock_mismatch") as BrandLock["verified_product_facts"],
    product_ui_asset_ids: strings(lock.product_ui_asset_ids, "brand_lock_mismatch").map((id) => uuid(id, "brand_lock_mismatch")) as BrandLock["product_ui_asset_ids"],
    benefit_order: strings(lock.benefit_order, "brand_lock_mismatch") as BrandLock["benefit_order"],
    cta_action_meaning: text(lock.cta_action_meaning, "brand_lock_mismatch"),
    layout_template_asset_id: uuid(lock.layout_template_asset_id, "brand_lock_mismatch"),
    localizable_fields: localizable as BrandLock["localizable_fields"],
  };
}

function runCreate(value: unknown): RunCreate {
  const request = object(value, "invalid_request");
  if (request.execution_mode !== "fixture") invalid("live_execution");
  if (request.direction !== "china_to_uk" && request.direction !== "uk_to_china") invalid("invalid_direction");
  if (request.product_category !== "ai_software" && request.product_category !== "ai_application") invalid("invalid_request");
  if (request.creative_format !== "static_ad") invalid("invalid_request");
  const asset = object(request.source_asset, "invalid_request");
  if (asset.kind !== "source_ad") invalid("invalid_request");
  if (!SHA256.test(text(asset.sha256, "invalid_request"))) invalid("invalid_request");
  if (!/^[a-z0-9][a-z0-9.+-]*\/[a-z0-9][a-z0-9.+-]*$/.test(text(asset.media_type, "invalid_request"))) invalid("invalid_request");
  return {
    direction: request.direction,
    execution_mode: "fixture",
    product_category: request.product_category,
    creative_format: "static_ad",
    source_asset: {
      asset_id: uuid(asset.asset_id, "invalid_request"),
      kind: "source_ad",
      media_type: asset.media_type as string,
      sha256: asset.sha256 as string,
      provenance_ref: publicReference(asset.provenance_ref),
      rights_ref: publicReference(asset.rights_ref),
    },
    brand_lock: brandLock(request.brand_lock),
  };
}

function hypotheses(
  value: unknown,
  targetMarket: "china" | "united_kingdom",
  requiredId: string,
  requiredEvidence: string,
): CulturalHypothesis[] {
  if (!Array.isArray(value) || value.length !== 1) invalid("hypothesis_mapping");
  return value.map((item) => {
    const hypothesis = object(item, "hypothesis_mapping");
    if (hypothesis.review_status !== "pending") invalid("hypothesis_not_pending");
    if (hypothesis.target_market !== targetMarket || hypothesis.hypothesis_id !== requiredId) invalid("hypothesis_mapping");
    const evidence = strings(hypothesis.evidence_refs, "hypothesis_mapping").map((reference) => publicReference(reference, "hypothesis_mapping"));
    if (evidence.length !== 1 || evidence[0] !== requiredEvidence) invalid("hypothesis_mapping");
    const requirements = strings(hypothesis.validation_requirements, "hypothesis_not_pending");
    if (hypothesis.uncertainty !== "low" && hypothesis.uncertainty !== "medium" && hypothesis.uncertainty !== "high") invalid("hypothesis_not_pending");
    return {
      hypothesis_id: uuid(hypothesis.hypothesis_id, "hypothesis_not_pending"),
      target_market: hypothesis.target_market as CulturalHypothesis["target_market"],
      claim: text(hypothesis.claim, "hypothesis_not_pending"),
      evidence_refs: evidence as CulturalHypothesis["evidence_refs"],
      uncertainty: hypothesis.uncertainty,
      rationale: text(hypothesis.rationale, "hypothesis_not_pending"),
      validation_requirements: requirements as CulturalHypothesis["validation_requirements"],
      review_status: "pending",
    };
  });
}

export function deepFreeze<T>(value: T): Readonly<T> {
  if (value !== null && typeof value === "object" && !Object.isFrozen(value)) {
    for (const child of Object.values(value as Record<string, unknown>)) deepFreeze(child);
    Object.freeze(value);
  }
  return value as Readonly<T>;
}

export function validateFixture(raw: unknown, expectedId: FixtureId): Readonly<FixtureBundle> {
  const fixture = object(raw, "invalid_shape");
  if (fixture.fixture_id !== expectedId) invalid("id_mismatch");
  if (fixture.disclosure !== FIXTURE_DISCLOSURE) invalid("invalid_disclosure");
  const chinaToUk = expectedId === "china-to-uk";
  const sourceLocale = chinaToUk ? "zh-CN" : "en-GB";
  const targetLocale = chinaToUk ? "en-GB" : "zh-CN";
  const approvedSource = APPROVED_SOURCE_BY_FIXTURE[expectedId];
  const targetMarket = chinaToUk ? "united_kingdom" : "china";
  const ruleIds = chinaToUk ? ["ZEU-S1", "ZEU-S3"] : ["EZC-S1", "EZC-S3"];
  const hypothesisId = chinaToUk
    ? "c1111111-1111-4111-8111-111111111111"
    : "c2222222-2222-4222-8222-222222222222";
  const hypothesisEvidence = chinaToUk ? "evidence:day3-zeu-h1" : "evidence:day3-ezc-h1";
  if (fixture.source_locale !== sourceLocale || fixture.target_locale !== targetLocale) invalid("invalid_locale_pair");
  const request = runCreate(fixture.request);
  if (request.direction !== approvedSource.direction) invalid("invalid_direction");
  if (!structuralEqual(request.source_asset, approvedSource.source_asset)) invalid("source_asset_mismatch");
  const preview = object(fixture.preview, "invalid_shape");
  const composition = compositionEvidence(fixture.composition, expectedId, request.brand_lock);
  const sourceAssetPath = publicPath(preview.source_asset_path);
  if (sourceAssetPath !== approvedSource.source_asset_path) invalid("source_asset_mismatch");
  const previewLock = brandLock(preview.brand_lock);
  if (!structuralEqual(request.brand_lock, previewLock)) invalid("brand_lock_mismatch");
  const observedRules = strings(preview.rule_ids, "invalid_rules");
  if (!structuralEqual(observedRules, ruleIds)) invalid("invalid_rules");
  const warningCodes = strings(preview.warnings, "invalid_warning");
  if (!warningCodes.includes("HUMAN_REVIEW_REQUIRED")) invalid("invalid_warning");
  const limitation = text(preview.limitation, "invalid_limitation");
  if (!/not cultural, legal, or performance validation/i.test(limitation)) invalid("invalid_limitation");
  const localized = object(preview.localized_copy, "invalid_shape");
  if (localized.locale !== targetLocale || localized.cta_action_meaning !== request.brand_lock.cta_action_meaning) invalid("brand_lock_mismatch");
  const sourceCopy = object(preview.source_copy, "invalid_shape");
  const observedHypotheses = hypotheses(preview.hypotheses, targetMarket, hypothesisId, hypothesisEvidence);
  const draft = object(fixture.draft, "invalid_draft");
  const draftBrief = object(draft.brief, "invalid_draft");
  const draftCopy = object(draft.copy, "invalid_draft");
  const rawDraftLock = object(draftBrief.brand_lock, "invalid_draft");
  if (!structuralEqual(rawDraftLock, request.brand_lock)) invalid("invalid_draft");
  const draftLock = brandLock(rawDraftLock);
  const draftHypotheses = draftBrief.hypotheses;
  const draftRules = strings(draft.rule_ids, "invalid_draft");
  const requiredPrompt = chinaToUk
    ? "Use verified facts and ZEU-S1/ZEU-S3; preserve Brand Lock."
    : "仅使用已验证事实与 EZC-S1/EZC-S3；保持品牌锁定。";
  if (
    draftBrief.direction !== request.direction ||
    draftBrief.target_locale !== targetLocale ||
    !structuralEqual(draftLock, request.brand_lock) ||
    !structuralEqual(draftHypotheses, observedHypotheses) ||
    !structuralEqual(draftRules, ruleIds) ||
    !structuralEqual(draftRules, observedRules) ||
    draftCopy.locale !== targetLocale ||
    draftCopy.cta_action_meaning !== request.brand_lock.cta_action_meaning ||
    draft.prompt_summary !== requiredPrompt
  ) invalid("invalid_draft");
  const validatedBrief: FixtureBundle["draft"]["brief"] = {
    direction: request.direction,
    target_locale: targetLocale,
    brand_lock: draftLock,
    hypotheses: observedHypotheses,
    narrative: text(draftBrief.narrative, "invalid_draft"),
    use_scenario: text(draftBrief.use_scenario, "invalid_draft"),
    trust_information: text(draftBrief.trust_information, "invalid_draft"),
  };
  if (validatedBrief.trust_information !== FIXTURE_DISCLOSURE) invalid("invalid_draft");
  const validatedCopy: AdCopy = {
    locale: targetLocale,
    headline: text(draftCopy.headline, "invalid_draft"),
    body: text(draftCopy.body, "invalid_draft"),
    cta_label: text(draftCopy.cta_label, "invalid_draft"),
    cta_action_meaning: request.brand_lock.cta_action_meaning,
  };
  if (!structuralEqual(validatedCopy, {
    locale: targetLocale,
    headline: localized.headline,
    body: localized.body,
    cta_label: localized.cta_label,
    cta_action_meaning: localized.cta_action_meaning,
  })) invalid("invalid_draft");
  const bundle: FixtureBundle = {
    fixture_id: expectedId,
    disclosure: FIXTURE_DISCLOSURE,
    source_locale: sourceLocale,
    target_locale: targetLocale,
    request,
    draft: {
      brief: validatedBrief,
      copy: validatedCopy,
      rule_ids: draftRules,
      prompt_summary: requiredPrompt,
    },
    composition,
    preview: {
      source_asset_path: sourceAssetPath,
      logo_asset_path: publicPath(preview.logo_asset_path),
      product_ui_asset_path: publicPath(preview.product_ui_asset_path),
      source_copy: { headline: text(sourceCopy.headline, "invalid_shape"), body: text(sourceCopy.body, "invalid_shape") },
      localized_copy: {
        locale: targetLocale,
        headline: text(localized.headline, "invalid_shape"),
        body: text(localized.body, "invalid_shape"),
        cta_label: text(localized.cta_label, "invalid_shape"),
        cta_action_meaning: request.brand_lock.cta_action_meaning,
      },
      brand_lock: previewLock,
      rule_ids: observedRules,
      hypotheses: observedHypotheses,
      warnings: warningCodes,
      limitation,
    },
  };
  return deepFreeze(bundle);
}
