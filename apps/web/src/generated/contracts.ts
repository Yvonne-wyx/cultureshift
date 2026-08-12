/* AUTO-GENERATED FROM PYDANTIC JSON SCHEMA. DO NOT EDIT. */

/**
 * @minItems 1
 * @maxItems 16
 */
export type BenefitOrder =
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ];
export type CtaActionMeaning = string;
export type LayoutTemplateAssetId = string;
/**
 * @minItems 1
 * @maxItems 4
 */
export type LocalizableFields =
  | ["narrative" | "use_scenario" | "trust_information" | "language"]
  | [
      "narrative" | "use_scenario" | "trust_information" | "language",
      "narrative" | "use_scenario" | "trust_information" | "language"
    ]
  | [
      "narrative" | "use_scenario" | "trust_information" | "language",
      "narrative" | "use_scenario" | "trust_information" | "language",
      "narrative" | "use_scenario" | "trust_information" | "language"
    ]
  | [
      "narrative" | "use_scenario" | "trust_information" | "language",
      "narrative" | "use_scenario" | "trust_information" | "language",
      "narrative" | "use_scenario" | "trust_information" | "language",
      "narrative" | "use_scenario" | "trust_information" | "language"
    ];
export type LogoAssetId = string;
export type ProductName = string;
/**
 * @minItems 1
 * @maxItems 16
 */
export type ProductUiAssetIds =
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ];
/**
 * @minItems 1
 * @maxItems 32
 */
export type VerifiedProductFacts = [string, ...string[]];
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "Locale".
 */
export type Locale = "zh-CN" | "en-GB";
export type Claim = string;
/**
 * @minItems 1
 * @maxItems 32
 */
export type EvidenceRefs = [PublicReference, ...PublicReference[]];
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "PublicReference".
 */
export type PublicReference = string;
export type HypothesisId = string;
export type Rationale = string;
export type ReviewStatus = "pending" | "accepted" | "rejected";
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "Market".
 */
export type Market = "china" | "united_kingdom";
export type Uncertainty = "low" | "medium" | "high";
/**
 * @minItems 1
 * @maxItems 16
 */
export type ValidationRequirements =
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ];
/**
 * @maxItems 32
 */
export type Hypotheses = CulturalHypothesis[];
export type AssetId = string;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "UtcDatetime".
 */
export type UtcDatetime = string;
export type SourceAssetKind = "source_ad";
export type MediaType = string;
export type Sha256 = string;
/**
 * @maxItems 32
 */
export type Warnings = string[];
export type Body = string;
export type CtaActionMeaning1 = string;
export type CtaLabel = string;
export type Headline = string;
export type AssetId1 = string;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "AssetKind".
 */
export type AssetKind = "source_ad" | "logo" | "product_ui" | "layout_template" | "background" | "rendered_ad";
export type MediaType1 = string;
export type Sha2561 = string;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "LocalizationDirection".
 */
export type LocalizationDirection = "china_to_uk" | "uk_to_china";
/**
 * @maxItems 32
 */
export type Hypotheses1 = CulturalHypothesis[];
export type Narrative = string;
export type TrustInformation = string;
export type UseScenario = string;
export type BrandLockPreserved = boolean;
export type RequiresHumanReview = boolean;
/**
 * @maxItems 32
 */
export type Warnings1 = string[];
export type ApprovalStatus = "pending" | "approved" | "rejected";
export type ExportResultVersion = number;
export type RunId = string;
/**
 * @maxItems 32
 */
export type Warnings2 = string[];
export type Feedback = string;
/**
 * @minItems 1
 * @maxItems 16
 */
export type RequestedChanges =
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ];
export type RunId1 = string;
export type RunId2 = string;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RunStatus".
 */
export type RunStatus = "pending" | "in_progress" | "blocked" | "completed" | "failed";
export type CreativeFormat = "static_ad";
export type FixtureExecutionMode = "fixture";
export type ProductCategory = "ai_software" | "ai_application";
export type Version = number;
/**
 * @maxItems 64
 */
export type ResultVersions = ResultVersion[];
export type RunId3 = string;
/**
 * @maxItems 32
 */
export type WarningCodes = string[];
export type ReasonCategory = "validation" | "generation" | "review";
export type RunId4 = string;
export type CapabilityToken = string;
export type RunId5 = string;
export type RunId6 = string;
/**
 * @maxItems 32
 */
export type WarningCodes1 = string[];
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "ExecutionMode".
 */
export type ExecutionMode = "fixture" | "live";

export interface ContractRegistry {
  ad_analysis: AdAnalysis;
  ad_copy: AdCopy;
  asset_ref: AssetRef;
  brand_lock: BrandLock;
  creative_brief: CreativeBrief;
  critique_report: CritiqueReport;
  cultural_hypothesis: CulturalHypothesis;
  export_summary: ExportSummary;
  feedback_request: FeedbackRequest;
  job_accepted: JobAccepted;
  project_run: ProjectRunContract;
  result_version: ResultVersion;
  retry_request: RetryRequest;
  run_create: RunCreate;
  run_created: RunCreated;
  run_snapshot: RunSnapshot;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "AdAnalysis".
 */
export interface AdAnalysis {
  brand_lock: BrandLock;
  detected_locale: Locale;
  hypotheses?: Hypotheses;
  source_asset: SourceAdAssetRef;
  warnings?: Warnings;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "BrandLock".
 */
export interface BrandLock {
  benefit_order: BenefitOrder;
  cta_action_meaning: CtaActionMeaning;
  layout_template_asset_id: LayoutTemplateAssetId;
  localizable_fields: LocalizableFields;
  logo_asset_id: LogoAssetId;
  product_name: ProductName;
  product_ui_asset_ids: ProductUiAssetIds;
  verified_product_facts: VerifiedProductFacts;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CulturalHypothesis".
 */
export interface CulturalHypothesis {
  claim: Claim;
  evidence_refs: EvidenceRefs;
  hypothesis_id: HypothesisId;
  rationale: Rationale;
  review_status?: ReviewStatus;
  target_market: Market;
  uncertainty: Uncertainty;
  validation_requirements: ValidationRequirements;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "SourceAdAssetRef".
 */
export interface SourceAdAssetRef {
  asset_id: AssetId;
  expires_at?: UtcDatetime | null;
  kind: SourceAssetKind;
  media_type: MediaType;
  provenance_ref: PublicReference;
  rights_ref: PublicReference;
  sha256: Sha256;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "AdCopy".
 */
export interface AdCopy {
  body: Body;
  cta_action_meaning: CtaActionMeaning1;
  cta_label: CtaLabel;
  headline: Headline;
  locale: Locale;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "AssetRef".
 */
export interface AssetRef {
  asset_id: AssetId1;
  expires_at?: UtcDatetime | null;
  kind: AssetKind;
  media_type: MediaType1;
  provenance_ref: PublicReference;
  rights_ref: PublicReference;
  sha256: Sha2561;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CreativeBrief".
 */
export interface CreativeBrief {
  brand_lock: BrandLock;
  direction: LocalizationDirection;
  hypotheses?: Hypotheses1;
  narrative: Narrative;
  target_locale: Locale;
  trust_information: TrustInformation;
  use_scenario: UseScenario;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CritiqueReport".
 */
export interface CritiqueReport {
  brand_lock_preserved: BrandLockPreserved;
  requires_human_review?: RequiresHumanReview;
  warnings?: Warnings1;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "ExportSummary".
 */
export interface ExportSummary {
  approval_status: ApprovalStatus;
  exported_at: UtcDatetime;
  result_version: ExportResultVersion;
  run_id: RunId;
  warnings?: Warnings2;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "FeedbackRequest".
 */
export interface FeedbackRequest {
  feedback: Feedback;
  requested_changes: RequestedChanges;
  run_id: RunId1;
  submitted_at: UtcDatetime;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "JobAccepted".
 */
export interface JobAccepted {
  accepted_at: UtcDatetime;
  run_id: RunId2;
  status: RunStatus;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "ProjectRunContract".
 */
export interface ProjectRunContract {
  created_at: UtcDatetime;
  request: RunCreate;
  result_versions?: ResultVersions;
  run_id: RunId3;
  status: RunStatus;
  updated_at: UtcDatetime;
  warning_codes?: WarningCodes;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RunCreate".
 */
export interface RunCreate {
  brand_lock: BrandLock;
  creative_format: CreativeFormat;
  direction: LocalizationDirection;
  execution_mode: FixtureExecutionMode;
  product_category: ProductCategory;
  source_asset: SourceAdAssetRef;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "ResultVersion".
 */
export interface ResultVersion {
  analysis: AdAnalysis;
  brief: CreativeBrief;
  copy: AdCopy;
  created_at: UtcDatetime;
  critique: CritiqueReport;
  rendered_asset?: AssetRef | null;
  version: Version;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RetryRequest".
 */
export interface RetryRequest {
  reason_category: ReasonCategory;
  run_id: RunId4;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RunCreated".
 */
export interface RunCreated {
  capability_token: CapabilityToken;
  created_at: UtcDatetime;
  run_id: RunId5;
  status: RunStatus;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RunSnapshot".
 */
export interface RunSnapshot {
  created_at: UtcDatetime;
  direction: LocalizationDirection;
  run_id: RunId6;
  status: RunStatus;
  updated_at: UtcDatetime;
  warning_codes?: WarningCodes1;
}
