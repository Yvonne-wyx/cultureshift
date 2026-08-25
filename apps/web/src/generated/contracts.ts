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
export type RepairAttempted = boolean;
export type RunId = string;
export type Status = "awaiting_brand_lock";
export type AssetId1 = string;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "AssetKind".
 */
export type AssetKind = "source_ad" | "logo" | "product_ui" | "layout_template" | "background" | "rendered_ad";
export type MediaType1 = string;
export type Sha2561 = string;
export type DeleteCapabilityToken = string;
export type SizeBytes = number;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "LocalizationDirection".
 */
export type LocalizationDirection = "china_to_uk" | "uk_to_china";
export type Height = 900;
export type Narrative = string;
export type ProhibitedContent = ("logo" | "brand_name" | "product_ui" | "statistics" | "claims" | "long_text")[];
export type UseScenario = string;
export type Width = 1600;
export type RunId1 = string;
export type Status1 = "in_progress";
export type ArtifactId = string;
export type Disclosure = "Fixture Demo / 非实时模型";
export type FixtureCompositionExecutionMode = "fixture";
export type Height1 = 900;
/**
 * @minItems 6
 * @maxItems 7
 */
export type Layers =
  | [CompositionLayer, CompositionLayer, CompositionLayer, CompositionLayer, CompositionLayer, CompositionLayer]
  | [
      CompositionLayer,
      CompositionLayer,
      CompositionLayer,
      CompositionLayer,
      CompositionLayer,
      CompositionLayer,
      CompositionLayer
    ];
/**
 * @minItems 4
 * @maxItems 4
 */
export type Bounds = [unknown, unknown, unknown, unknown];
export type Height2 = number;
export type Kind = "background" | "product_ui" | "logo" | "headline" | "body" | "cta" | "disclosure";
export type RgbaSha256 = string;
export type SourceAssetId = string | null;
export type Width1 = number;
export type MediaType2 = "image/png";
export type RenderedSha256 = string;
export type RunId2 = string;
export type Status2 = "in_progress";
export type Width2 = 1600;
/**
 * @maxItems 32
 */
export type Hypotheses1 = CulturalHypothesis[];
export type Narrative1 = string;
export type TrustInformation = string;
export type UseScenario1 = string;
export type BrandLockPreserved = boolean;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CritiqueCategory".
 */
export type CritiqueCategory = "brand_lock" | "fact" | "readability" | "culture" | "safety";
export type Code = string;
export type Message = string;
export type RequiresHumanReview = boolean;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CritiqueSeverity".
 */
export type CritiqueSeverity = "warning" | "blocking";
/**
 * @maxItems 32
 */
export type Issues = CritiqueIssue[];
export type RequiresHumanReview1 = boolean;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CritiqueStatus".
 */
export type CritiqueStatus = "pass" | "revise" | "needs_human_review" | "reject";
/**
 * @maxItems 32
 */
export type Warnings1 = string[];
export type HumanRevisionCount = number;
export type InitialGenerationCount = number;
export type RunId3 = string;
export type Status3 = "ready" | "failed_final";
export type TechnicalAttemptCount = number;
/**
 * @minItems 2
 * @maxItems 2
 */
export type RuleIds = [string, string];
export type RunId4 = string;
export type Status4 = "in_progress";
export type ApprovalStatus = "pending" | "approved" | "rejected";
export type ExportResultVersion = number;
export type RunId5 = string;
/**
 * @maxItems 32
 */
export type Warnings2 = string[];
export type Feedback = string;
/**
 * @minItems 1
 * @maxItems 2
 */
export type RequestedChanges = [RevisionChange] | [RevisionChange, RevisionChange];
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RevisionChange".
 */
export type RevisionChange = "shorten_headline" | "shorten_body";
export type RunId6 = string;
export type RunId7 = string;
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RunStatus".
 */
export type RunStatus =
  | "pending"
  | "in_progress"
  | "awaiting_brand_lock"
  | "blocked"
  | "completed"
  | "failed"
  | "ready"
  | "failed_retryable"
  | "failed_final";
export type CreativeFormat = "static_ad";
export type FixtureExecutionMode = "fixture";
export type ProductCategory = "ai_software" | "ai_application";
export type Version = number;
/**
 * @maxItems 64
 */
export type ResultVersions = ResultVersion[];
export type RunId8 = string;
/**
 * @maxItems 32
 */
export type WarningCodes = string[];
export type ReasonCategory = "validation" | "generation" | "review";
export type RunId9 = string;
export type HumanRevisionCount1 = 1;
export type InitialGenerationCount1 = 1;
export type RevisionResultVersion = 2;
export type RunId10 = string;
export type Status5 = "ready" | "failed_final";
export type TechnicalAttemptCount1 = number;
export type CapabilityToken = string;
export type RunId11 = string;
export type RunId12 = string;
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
  analysis_completed: AnalysisCompleted;
  asset_ref: AssetRef;
  asset_uploaded: AssetUploaded;
  background_request: BackgroundRequest;
  brand_lock: BrandLock;
  brand_lock_confirmation: BrandLockConfirmation;
  brand_lock_confirmed: BrandLockConfirmed;
  composition_generated: CompositionGenerated;
  creative_brief: CreativeBrief;
  critique_completed: CritiqueCompleted;
  critique_issue: CritiqueIssue;
  critique_report: CritiqueReport;
  cultural_hypothesis: CulturalHypothesis;
  draft_generated: DraftGenerated;
  export_summary: ExportSummary;
  feedback_request: FeedbackRequest;
  job_accepted: JobAccepted;
  project_run: ProjectRunContract;
  result_version: ResultVersion;
  retry_request: RetryRequest;
  revision_change: RevisionChange;
  revision_completed: RevisionCompleted;
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
 * via the `definition` "AnalysisCompleted".
 */
export interface AnalysisCompleted {
  analysis: AdAnalysis;
  completed_at: UtcDatetime;
  repair_attempted: RepairAttempted;
  run_id: RunId;
  status: Status;
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
 * via the `definition` "AssetUploaded".
 */
export interface AssetUploaded {
  asset: SourceAdAssetRef;
  created_at: UtcDatetime;
  delete_capability_token: DeleteCapabilityToken;
  size_bytes: SizeBytes;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "BackgroundRequest".
 */
export interface BackgroundRequest {
  direction: LocalizationDirection;
  height?: Height;
  narrative: Narrative;
  prohibited_content?: ProhibitedContent;
  target_locale: Locale;
  use_scenario: UseScenario;
  width?: Width;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "BrandLockConfirmation".
 */
export interface BrandLockConfirmation {
  brand_lock: BrandLock;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "BrandLockConfirmed".
 */
export interface BrandLockConfirmed {
  brand_lock: BrandLock;
  confirmed_at: UtcDatetime;
  run_id: RunId1;
  status: Status1;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CompositionGenerated".
 */
export interface CompositionGenerated {
  artifact_id: ArtifactId;
  disclosure: Disclosure;
  execution_mode: FixtureCompositionExecutionMode;
  generated_at: UtcDatetime;
  height: Height1;
  layers: Layers;
  media_type: MediaType2;
  rendered_sha256: RenderedSha256;
  run_id: RunId2;
  status: Status2;
  width: Width2;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CompositionLayer".
 */
export interface CompositionLayer {
  bounds: Bounds;
  height: Height2;
  kind: Kind;
  rgba_sha256: RgbaSha256;
  source_asset_id?: SourceAssetId;
  width: Width1;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CreativeBrief".
 */
export interface CreativeBrief {
  brand_lock: BrandLock;
  direction: LocalizationDirection;
  hypotheses?: Hypotheses1;
  narrative: Narrative1;
  target_locale: Locale;
  trust_information: TrustInformation;
  use_scenario: UseScenario1;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CritiqueCompleted".
 */
export interface CritiqueCompleted {
  critique: CritiqueReport;
  human_revision_count: HumanRevisionCount;
  initial_generation_count: InitialGenerationCount;
  reviewed_at: UtcDatetime;
  run_id: RunId3;
  status: Status3;
  technical_attempt_count: TechnicalAttemptCount;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CritiqueReport".
 */
export interface CritiqueReport {
  brand_lock_preserved: BrandLockPreserved;
  issues?: Issues;
  requires_human_review: RequiresHumanReview1;
  reviewed_at: UtcDatetime;
  status: CritiqueStatus;
  warnings?: Warnings1;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "CritiqueIssue".
 */
export interface CritiqueIssue {
  category: CritiqueCategory;
  code: Code;
  message: Message;
  requires_human_review?: RequiresHumanReview;
  severity: CritiqueSeverity;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "DraftGenerated".
 */
export interface DraftGenerated {
  brief: CreativeBrief;
  copy: AdCopy;
  generated_at: UtcDatetime;
  rule_ids: RuleIds;
  run_id: RunId4;
  status: Status4;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "ExportSummary".
 */
export interface ExportSummary {
  approval_status: ApprovalStatus;
  exported_at: UtcDatetime;
  result_version: ExportResultVersion;
  run_id: RunId5;
  warnings?: Warnings2;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "FeedbackRequest".
 */
export interface FeedbackRequest {
  feedback: Feedback;
  requested_changes: RequestedChanges;
  run_id: RunId6;
  submitted_at: UtcDatetime;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "JobAccepted".
 */
export interface JobAccepted {
  accepted_at: UtcDatetime;
  run_id: RunId7;
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
  run_id: RunId8;
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
  run_id: RunId9;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RevisionCompleted".
 */
export interface RevisionCompleted {
  brief: CreativeBrief;
  composition: CompositionGenerated;
  copy: AdCopy;
  critique: CritiqueReport;
  human_revision_count: HumanRevisionCount1;
  initial_generation_count: InitialGenerationCount1;
  previous_composition: CompositionGenerated;
  result_version: RevisionResultVersion;
  revised_at: UtcDatetime;
  run_id: RunId10;
  status: Status5;
  technical_attempt_count: TechnicalAttemptCount1;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RunCreated".
 */
export interface RunCreated {
  capability_token: CapabilityToken;
  created_at: UtcDatetime;
  run_id: RunId11;
  status: RunStatus;
}
/**
 * This interface was referenced by `ContractRegistry`'s JSON-Schema
 * via the `definition` "RunSnapshot".
 */
export interface RunSnapshot {
  created_at: UtcDatetime;
  direction: LocalizationDirection;
  run_id: RunId12;
  status: RunStatus;
  updated_at: UtcDatetime;
  warning_codes?: WarningCodes1;
}
