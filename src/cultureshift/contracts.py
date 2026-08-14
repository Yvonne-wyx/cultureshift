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
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


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


class CritiqueReport(ContractModel):
    warnings: tuple[WarningCode, ...] = Field(default=(), max_length=32)
    brand_lock_preserved: bool
    requires_human_review: bool = True

    @model_validator(mode="after")
    def fail_closed_on_lock_change(self) -> Self:
        if not self.brand_lock_preserved and not self.requires_human_review:
            raise ValueError("Brand Lock changes require human review")
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
    critique_report: CritiqueReport
    result_version: ResultVersion
    run_create: RunCreate
    run_created: RunCreated
    run_snapshot: RunSnapshot
    job_accepted: JobAccepted
    feedback_request: FeedbackRequest
    retry_request: RetryRequest
    export_summary: ExportSummary
    project_run: ProjectRunContract
