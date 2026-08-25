from __future__ import annotations

import re
from datetime import timedelta
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    WithJsonSchema,
    model_validator,
)
from typing_extensions import TypeAliasType

from cultureshift.domain import LocalizationDirection

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
PUBLIC_REFERENCE_PATTERN = r"^(?:fixture|rights|evidence):[A-Za-z0-9][A-Za-z0-9._/-]*$"


def _validate_public_reference(value: str) -> str:
    if re.fullmatch(PUBLIC_REFERENCE_PATTERN, value) is None:
        raise ValueError("public references must not contain a local path or unapproved scheme")
    return value


PublicReference = TypeAliasType(
    "PublicReference",
    Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=256,
        ),
        AfterValidator(_validate_public_reference),
        WithJsonSchema(
            {
                "type": "string",
                "minLength": 1,
                "maxLength": 256,
                "pattern": PUBLIC_REFERENCE_PATTERN,
            },
            mode="validation",
        ),
    ],
)
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
MediaType = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$"),
]
LocalizableField = Literal["narrative", "use_scenario", "trust_information", "language"]


def _require_utc(value: AwareDatetime) -> AwareDatetime:
    if value.utcoffset() != timedelta(0):
        raise ValueError("public timestamps must use UTC")
    return value


UtcDatetime = TypeAliasType(
    "UtcDatetime",
    Annotated[
        AwareDatetime,
        AfterValidator(_require_utc),
        WithJsonSchema(
            {
                "type": "string",
                "format": "date-time",
                "pattern": r"(?:Z|\+00:00)$",
            },
            mode="validation",
        ),
    ],
)


class ContractModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class Market(StrEnum):
    CHINA = "china"
    UNITED_KINGDOM = "united_kingdom"


class Locale(StrEnum):
    ZH_CN = "zh-CN"
    EN_GB = "en-GB"


class ExecutionMode(StrEnum):
    FIXTURE = "fixture"
    LIVE = "live"


class AssetKind(StrEnum):
    SOURCE_AD = "source_ad"
    LOGO = "logo"
    PRODUCT_UI = "product_ui"
    LAYOUT_TEMPLATE = "layout_template"
    BACKGROUND = "background"
    RENDERED_AD = "rendered_ad"


class RunStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_BRAND_LOCK = "awaiting_brand_lock"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    READY = "ready"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_FINAL = "failed_final"


class AssetRef(ContractModel):
    asset_id: UUID
    kind: AssetKind
    media_type: MediaType
    sha256: Sha256
    provenance_ref: PublicReference
    rights_ref: PublicReference
    expires_at: UtcDatetime | None = None


class SourceAdAssetRef(AssetRef):
    kind: Literal[AssetKind.SOURCE_AD] = Field(title="SourceAssetKind")


class AssetUploaded(ContractModel):
    asset: SourceAdAssetRef
    size_bytes: int = Field(ge=1, le=10 * 1024 * 1024)
    created_at: UtcDatetime
    delete_capability_token: Annotated[
        str, StringConstraints(min_length=16, max_length=4096)
    ]


class CulturalHypothesis(ContractModel):
    hypothesis_id: UUID
    target_market: Market
    claim: LongText
    evidence_refs: tuple[PublicReference, ...] = Field(min_length=1, max_length=32)
    uncertainty: Literal["low", "medium", "high"]
    rationale: LongText
    validation_requirements: tuple[ShortText, ...] = Field(min_length=1, max_length=16)
    review_status: Literal["pending", "accepted", "rejected"] = "pending"


class BrandLock(ContractModel):
    logo_asset_id: UUID
    product_name: ShortText
    verified_product_facts: tuple[ShortText, ...] = Field(min_length=1, max_length=32)
    product_ui_asset_ids: tuple[UUID, ...] = Field(min_length=1, max_length=16)
    benefit_order: tuple[ShortText, ...] = Field(min_length=1, max_length=16)
    cta_action_meaning: ShortText
    layout_template_asset_id: UUID
    localizable_fields: tuple[LocalizableField, ...] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def require_unique_sequences(self) -> Self:
        for values in (
            self.verified_product_facts,
            self.product_ui_asset_ids,
            self.benefit_order,
            self.localizable_fields,
        ):
            if len(values) != len(set(values)):
                raise ValueError("Brand Lock sequences must contain unique values")
        return self


WarningCode = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class AdAnalysis(ContractModel):
    source_asset: SourceAdAssetRef
    detected_locale: Locale
    brand_lock: BrandLock
    hypotheses: tuple[CulturalHypothesis, ...] = Field(default=(), max_length=32)
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)


class CreativeBrief(ContractModel):
    direction: LocalizationDirection
    target_locale: Locale
    brand_lock: BrandLock
    hypotheses: tuple[CulturalHypothesis, ...] = Field(default=(), max_length=32)
    narrative: LongText
    use_scenario: LongText
    trust_information: LongText


class AdCopy(ContractModel):
    locale: Locale
    headline: ShortText
    body: LongText
    cta_label: ShortText
    cta_action_meaning: ShortText


class CritiqueStatus(StrEnum):
    PASS = "pass"
    REVISE = "revise"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    REJECT = "reject"


class CritiqueCategory(StrEnum):
    BRAND_LOCK = "brand_lock"
    FACT = "fact"
    READABILITY = "readability"
    CULTURE = "culture"
    SAFETY = "safety"


class CritiqueSeverity(StrEnum):
    WARNING = "warning"
    BLOCKING = "blocking"


class CritiqueIssue(ContractModel):
    code: WarningCode
    category: CritiqueCategory
    severity: CritiqueSeverity
    message: ShortText
    requires_human_review: bool = False


class CritiqueReport(ContractModel):
    status: CritiqueStatus
    issues: tuple[CritiqueIssue, ...] = Field(default=(), max_length=32)
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    brand_lock_preserved: bool
    requires_human_review: bool
    reviewed_at: UtcDatetime

    @model_validator(mode="after")
    def require_consistent_status(self) -> Self:
        blocking = any(
            issue.severity is CritiqueSeverity.BLOCKING for issue in self.issues
        )
        if not self.brand_lock_preserved and not any(
            issue.category is CritiqueCategory.BRAND_LOCK
            and issue.severity is CritiqueSeverity.BLOCKING
            for issue in self.issues
        ):
            raise ValueError("Brand Lock changes require a blocking issue")
        if blocking != (self.status is CritiqueStatus.REJECT):
            raise ValueError("blocking issues require reject status")
        if self.status is CritiqueStatus.PASS and (
            self.issues or self.requires_human_review
        ):
            raise ValueError("pass status requires no issues or human review")
        if (
            self.status is CritiqueStatus.NEEDS_HUMAN_REVIEW
            and not self.requires_human_review
        ):
            raise ValueError("human-review status requires human review")
        return self


class ResultVersion(ContractModel):
    version: int = Field(ge=1)
    analysis: AdAnalysis
    brief: CreativeBrief
    ad_copy: AdCopy = Field(alias="copy")
    rendered_asset: AssetRef | None = None
    critique: CritiqueReport
    created_at: UtcDatetime

    @model_validator(mode="after")
    def preserve_cross_artifact_brand_lock(self) -> Self:
        if self.analysis.brand_lock != self.brief.brand_lock:
            raise ValueError("Brand Lock must match across result artifacts")
        if self.ad_copy.cta_action_meaning != self.brief.brand_lock.cta_action_meaning:
            raise ValueError("CTA action meaning must preserve Brand Lock")
        if (
            self.rendered_asset is not None
            and self.rendered_asset.kind is not AssetKind.RENDERED_AD
        ):
            raise ValueError("rendered_asset must use the rendered_ad asset kind")
        return self


class RunCreate(ContractModel):
    direction: LocalizationDirection
    execution_mode: Annotated[
        ExecutionMode,
        Field(title="FixtureExecutionMode", json_schema_extra={"const": "fixture"}),
    ]
    source_asset: SourceAdAssetRef
    brand_lock: BrandLock
    product_category: Literal["ai_software", "ai_application"]
    creative_format: Literal["static_ad"]

    @model_validator(mode="after")
    def fixture_only_on_day_four(self) -> Self:
        if self.execution_mode is not ExecutionMode.FIXTURE:
            raise ValueError("live execution is not enabled in the Day 4 MVP")
        return self


class RunCreated(ContractModel):
    run_id: UUID
    status: RunStatus
    capability_token: Annotated[str, StringConstraints(min_length=16, max_length=4096)]
    created_at: UtcDatetime


class RunSnapshot(ContractModel):
    run_id: UUID
    direction: LocalizationDirection
    status: RunStatus
    warning_codes: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    created_at: UtcDatetime
    updated_at: UtcDatetime


class AnalysisCompleted(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.AWAITING_BRAND_LOCK]
    analysis: AdAnalysis
    repair_attempted: bool
    completed_at: UtcDatetime


class BrandLockConfirmation(ContractModel):
    brand_lock: BrandLock


class BrandLockConfirmed(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.IN_PROGRESS]
    brand_lock: BrandLock
    confirmed_at: UtcDatetime


class DraftGenerated(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.IN_PROGRESS]
    brief: CreativeBrief
    ad_copy: AdCopy = Field(alias="copy")
    rule_ids: tuple[ShortText, ...] = Field(min_length=2, max_length=2)
    generated_at: UtcDatetime

    @model_validator(mode="after")
    def preserve_directional_constraints(self) -> Self:
        expected = {
            LocalizationDirection.CHINA_TO_UK: (
                Locale.EN_GB,
                ("ZEU-S1", "ZEU-S3"),
            ),
            LocalizationDirection.UK_TO_CHINA: (
                Locale.ZH_CN,
                ("EZC-S1", "EZC-S3"),
            ),
        }
        locale, rule_ids = expected[self.brief.direction]
        if self.brief.target_locale is not locale or self.ad_copy.locale is not locale:
            raise ValueError("draft locale must match direction")
        if self.ad_copy.cta_action_meaning != self.brief.brand_lock.cta_action_meaning:
            raise ValueError("CTA action meaning must preserve Brand Lock")
        if self.rule_ids != rule_ids:
            raise ValueError("draft rule IDs must match direction")
        return self


class CritiqueCompleted(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.READY, RunStatus.FAILED_FINAL]
    critique: CritiqueReport
    initial_generation_count: int = Field(ge=0, le=1)
    human_revision_count: int = Field(ge=0, le=1)
    technical_attempt_count: int = Field(ge=0)
    reviewed_at: UtcDatetime

    @model_validator(mode="after")
    def match_review_timestamp(self) -> Self:
        if self.reviewed_at != self.critique.reviewed_at:
            raise ValueError("review timestamp must match Critic report")
        return self


class BackgroundRequest(ContractModel):
    direction: LocalizationDirection
    target_locale: Locale
    narrative: LongText
    use_scenario: LongText
    width: Literal[1600] = 1600
    height: Literal[900] = 900
    prohibited_content: tuple[
        Literal["logo", "brand_name", "product_ui", "statistics", "claims", "long_text"],
        ...,
    ] = ("logo", "brand_name", "product_ui", "statistics", "claims", "long_text")

    @model_validator(mode="after")
    def require_directional_locale_and_guardrails(self) -> Self:
        expected_locale = {
            LocalizationDirection.CHINA_TO_UK: Locale.EN_GB,
            LocalizationDirection.UK_TO_CHINA: Locale.ZH_CN,
        }[self.direction]
        if self.target_locale is not expected_locale:
            raise ValueError("background locale must match direction")
        required = ("logo", "brand_name", "product_ui", "statistics", "claims", "long_text")
        if self.prohibited_content != required:
            raise ValueError("background guardrails are fixed")
        return self


CompositionLayerKind = Literal[
    "background", "product_ui", "logo", "headline", "body", "cta", "disclosure"
]


class CompositionLayer(ContractModel):
    kind: CompositionLayerKind
    source_asset_id: UUID | None = None
    rgba_sha256: Sha256
    bounds: tuple[int, int, int, int]
    width: int = Field(ge=1, le=1600)
    height: int = Field(ge=1, le=900)

    @model_validator(mode="after")
    def require_valid_source_and_bounds(self) -> Self:
        if (self.kind in {"logo", "product_ui"}) != (self.source_asset_id is not None):
            raise ValueError("only protected visual layers require source asset IDs")
        left, top, right, bottom = self.bounds
        if (
            left < 0
            or top < 0
            or right > 1600
            or bottom > 900
            or right <= left
            or bottom <= top
            or right - left != self.width
            or bottom - top != self.height
        ):
            raise ValueError("composition layer bounds must match the fixed canvas")
        return self


class CompositionGenerated(ContractModel):
    run_id: UUID
    status: Literal[RunStatus.IN_PROGRESS]
    execution_mode: Annotated[
        Literal[ExecutionMode.FIXTURE],
        Field(title="FixtureCompositionExecutionMode"),
    ]
    width: Literal[1600]
    height: Literal[900]
    media_type: Literal["image/png"]
    rendered_sha256: Sha256
    artifact_id: UUID
    layers: tuple[CompositionLayer, ...] = Field(min_length=6, max_length=7)
    disclosure: Literal["Fixture Demo / 非实时模型"]
    generated_at: UtcDatetime

    @model_validator(mode="after")
    def require_fixed_layer_order(self) -> Self:
        kinds = tuple(layer.kind for layer in self.layers)
        expected = (
            "background",
            "product_ui",
            "logo",
            "headline",
            "body",
            "cta",
            "disclosure",
        )
        without_ui = ("background", "logo", "headline", "body", "cta", "disclosure")
        if kinds not in {expected, without_ui}:
            raise ValueError("composition layers must use fixed semantic order")
        return self


class JobAccepted(ContractModel):
    run_id: UUID
    status: RunStatus
    accepted_at: UtcDatetime


class FeedbackRequest(ContractModel):
    run_id: UUID
    feedback: LongText
    requested_changes: tuple[ShortText, ...] = Field(min_length=1, max_length=16)
    submitted_at: UtcDatetime


class RetryRequest(ContractModel):
    run_id: UUID
    reason_category: Literal["validation", "generation", "review"]


class ExportSummary(ContractModel):
    run_id: UUID
    result_version: int = Field(ge=1, title="ExportResultVersion")
    approval_status: Literal["pending", "approved", "rejected"]
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    exported_at: UtcDatetime


class ProjectRunContract(ContractModel):
    run_id: UUID
    request: RunCreate
    status: RunStatus
    result_versions: tuple[ResultVersion, ...] = Field(default=(), max_length=64)
    warning_codes: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @model_validator(mode="after")
    def tie_results_to_original_request(self) -> Self:
        for result in self.result_versions:
            if (
                result.analysis.brand_lock != self.request.brand_lock
                or result.analysis.source_asset.model_dump()
                != self.request.source_asset.model_dump()
                or result.brief.direction != self.request.direction
                or result.ad_copy.cta_action_meaning
                != self.request.brand_lock.cta_action_meaning
            ):
                raise ValueError("result artifacts must match the original request")
        return self


class ContractRegistry(ContractModel):
    asset_ref: AssetRef
    asset_uploaded: AssetUploaded
    cultural_hypothesis: CulturalHypothesis
    brand_lock: BrandLock
    ad_analysis: AdAnalysis
    creative_brief: CreativeBrief
    ad_copy: AdCopy
    critique_issue: CritiqueIssue
    critique_report: CritiqueReport
    critique_completed: CritiqueCompleted
    result_version: ResultVersion
    run_create: RunCreate
    run_created: RunCreated
    run_snapshot: RunSnapshot
    analysis_completed: AnalysisCompleted
    brand_lock_confirmation: BrandLockConfirmation
    brand_lock_confirmed: BrandLockConfirmed
    draft_generated: DraftGenerated
    background_request: BackgroundRequest
    composition_generated: CompositionGenerated
    job_accepted: JobAccepted
    feedback_request: FeedbackRequest
    retry_request: RetryRequest
    export_summary: ExportSummary
    project_run: ProjectRunContract
