from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from cultureshift.contracts import (
    AdAnalysis,
    AnalysisCompleted,
    AssetKind,
    AssetRef,
    BrandLock,
    ContractRegistry,
    CulturalHypothesis,
    ExecutionMode,
    Locale,
    Market,
    ProjectRunContract,
    ResultVersion,
    RunCreate,
    RunSnapshot,
    RunStatus,
)
from cultureshift.domain import LocalizationDirection, ProjectRun, ProjectRunStatus


def _valid_result_payload(request: RunCreate) -> dict[str, object]:
    return {
        "version": 1,
        "analysis": {
            "source_asset": request.source_asset,
            "detected_locale": "zh-CN",
            "brand_lock": request.brand_lock,
        },
        "brief": {
            "direction": request.direction,
            "target_locale": "en-GB",
            "brand_lock": request.brand_lock,
            "narrative": "A reviewable fixture narrative.",
            "use_scenario": "An authorized fictional workflow.",
            "trust_information": "Fixture demo; not a live model.",
        },
        "copy": {
            "locale": "en-GB",
            "headline": "Organize approved notes",
            "body": "Fixture copy for review.",
            "cta_label": "Try fixture",
            "cta_action_meaning": request.brand_lock.cta_action_meaning,
        },
        "critique": {"brand_lock_preserved": True},
        "created_at": datetime(2026, 8, 10, tzinfo=UTC),
    }


def test_contract_enums_have_stable_public_values() -> None:
    assert [item.value for item in Market] == ["china", "united_kingdom"]
    assert [item.value for item in Locale] == ["zh-CN", "en-GB"]
    assert [item.value for item in ExecutionMode] == ["fixture", "live"]
    assert AssetKind.RENDERED_AD.value == "rendered_ad"
    assert RunStatus.PENDING.value == "pending"


def test_analysis_completed_requires_awaiting_brand_lock(
    valid_run_payload: dict[str, object],
) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    analysis = AdAnalysis(
        source_asset=request.source_asset,
        detected_locale="zh-CN",
        brand_lock=request.brand_lock,
    )
    completed = AnalysisCompleted(
        run_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        status="awaiting_brand_lock",
        analysis=analysis,
        repair_attempted=False,
        completed_at=datetime(2026, 8, 19, tzinfo=UTC),
    )

    assert completed.status is RunStatus.AWAITING_BRAND_LOCK
    with pytest.raises(ValidationError):
        AnalysisCompleted.model_validate({**completed.model_dump(), "status": "completed"})


def test_asset_ref_is_serializable_and_rejects_local_paths() -> None:
    asset = AssetRef(
        asset_id="11111111-1111-4111-8111-111111111111",
        kind="source_ad",
        media_type="image/png",
        sha256="a" * 64,
        provenance_ref="fixture:ai-app/source-ad",
        rights_ref="rights:fixture-synthetic-v1",
        expires_at=datetime(2026, 8, 11, tzinfo=UTC),
    )
    assert AssetRef.model_validate_json(asset.model_dump_json()) == asset

    with pytest.raises(ValidationError, match="local path"):
        AssetRef(
            asset_id="11111111-1111-4111-8111-111111111111",
            kind="source_ad",
            media_type="image/png",
            sha256="a" * 64,
            provenance_ref=r"C:\\private\\source.png",
            rights_ref="rights:fixture-synthetic-v1",
        )


@pytest.mark.parametrize("reference_field", ["provenance_ref", "rights_ref"])
def test_asset_ref_rejects_local_file_uris(reference_field: str) -> None:
    values = {
        "asset_id": "11111111-1111-4111-8111-111111111111",
        "kind": "source_ad",
        "media_type": "image/png",
        "sha256": "a" * 64,
        "provenance_ref": "fixture:ai-app/source-ad",
        "rights_ref": "rights:fixture-synthetic-v1",
    }
    values[reference_field] = "file:///C:/private/source.png"

    with pytest.raises(ValidationError, match="local path"):
        AssetRef.model_validate(values)


def test_cultural_hypothesis_defaults_to_pending_review() -> None:
    hypothesis = CulturalHypothesis(
        hypothesis_id="55555555-5555-4555-8555-555555555555",
        target_market="united_kingdom",
        claim="A concise proof point may reduce interpretation effort.",
        evidence_refs=("evidence:public-study-1",),
        uncertainty="high",
        rationale="This is a testable localization hypothesis, not a fact.",
        validation_requirements=("Qualified UK reviewer",),
    )
    assert hypothesis.review_status == "pending"


def test_brand_lock_forbids_unknown_and_unapproved_localizable_fields(
    valid_run_payload: dict[str, object],
) -> None:
    brand_lock = valid_run_payload["brand_lock"]
    assert isinstance(brand_lock, dict)
    BrandLock.model_validate(brand_lock)

    with pytest.raises(ValidationError):
        BrandLock.model_validate({**brand_lock, "logo_can_change": True})

    with pytest.raises(ValidationError):
        BrandLock.model_validate({**brand_lock, "localizable_fields": ["product_name"]})


def test_run_create_accepts_only_fixture_mvp_payload(
    valid_run_payload: dict[str, object],
) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    assert request.execution_mode is ExecutionMode.FIXTURE

    with pytest.raises(ValidationError, match="live execution"):
        RunCreate.model_validate({**valid_run_payload, "execution_mode": "live"})

    with pytest.raises(ValidationError):
        RunCreate.model_validate({**valid_run_payload, "creative_format": "video"})

    with pytest.raises(ValidationError):
        RunCreate.model_validate({**valid_run_payload, "product_category": "medical"})

    wrong_kind = dict(valid_run_payload["source_asset"])
    wrong_kind["kind"] = "logo"
    with pytest.raises(ValidationError):
        RunCreate.model_validate({**valid_run_payload, "source_asset": wrong_kind})


def test_run_snapshot_is_public_serializable_and_closed() -> None:
    run = ProjectRun(
        direction=LocalizationDirection.CHINA_TO_UK,
        status=ProjectRunStatus.PENDING,
        warning_codes=("human_review_required",),
    )
    snapshot = RunSnapshot(
        run_id=run.id,
        direction=run.direction,
        status=run.status,
        warning_codes=run.warning_codes,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )

    assert RunSnapshot.model_validate_json(snapshot.model_dump_json()) == snapshot
    assert snapshot.model_dump(mode="json")["direction"] == "china_to_uk"
    with pytest.raises(ValidationError):
        RunSnapshot.model_validate({**snapshot.model_dump(), "capability_token": "private"})


def test_asset_uploaded_contract_is_public_serializable_and_closed() -> None:
    from datetime import UTC, datetime, timedelta
    from uuid import uuid4

    from cultureshift.contracts import AssetUploaded, SourceAdAssetRef

    created_at = datetime(2026, 8, 14, tzinfo=UTC)
    uploaded = AssetUploaded(
        asset=SourceAdAssetRef(
            asset_id=uuid4(),
            kind="source_ad",
            media_type="image/png",
            sha256="a" * 64,
            provenance_ref="fixture:user-upload/day6",
            rights_ref="rights:authorized-upload/day6",
            expires_at=created_at + timedelta(hours=24),
        ),
        size_bytes=1024,
        created_at=created_at,
        delete_capability_token="fixture-delete-capability",
    )
    assert AssetUploaded.model_validate_json(uploaded.model_dump_json()) == uploaded
    assert uploaded.delete_capability_token == "fixture-delete-capability"
    with pytest.raises(ValidationError):
        AssetUploaded.model_validate({**uploaded.model_dump(), "storage_path": "private"})


def test_ad_analysis_requires_source_ad_asset(
    valid_run_payload: dict[str, object],
) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    wrong_kind = {**request.source_asset.model_dump(), "kind": "logo"}

    with pytest.raises(ValidationError):
        AdAnalysis(
            source_asset=wrong_kind,
            detected_locale="zh-CN",
            brand_lock=request.brand_lock,
        )


@pytest.mark.parametrize(
    "reference",
    [
        r"C:\\private\\source.png",
        "/private/source.png",
        r"fixture:folder\\source.png",
        "https://example.test/evidence",
        "fixture:C:/private/source.png",
        "file:///private/source.png",
        "file%3A///private/source.png",
        "%66%69%6C%65%3A///private/source.png",
    ],
)
def test_public_references_reject_paths_and_unapproved_schemes(reference: str) -> None:
    with pytest.raises(ValidationError):
        CulturalHypothesis(
            hypothesis_id="55555555-5555-4555-8555-555555555555",
            target_market="united_kingdom",
            claim="A testable claim.",
            evidence_refs=(reference,),
            uncertainty="high",
            rationale="A fixture rationale.",
            validation_requirements=("Qualified reviewer",),
        )


def test_all_public_timestamps_require_utc() -> None:
    request = RunCreate.model_validate_json(
        RunCreate.model_validate(
            {
                "direction": "china_to_uk",
                "execution_mode": "fixture",
                "source_asset": {
                    "asset_id": "11111111-1111-4111-8111-111111111111",
                    "kind": "source_ad",
                    "media_type": "image/png",
                    "sha256": "a" * 64,
                    "provenance_ref": "fixture:source-ad",
                    "rights_ref": "rights:fixture-v1",
                    "expires_at": "2026-08-10T12:00:00Z",
                },
                "brand_lock": {
                    "logo_asset_id": "22222222-2222-4222-8222-222222222222",
                    "product_name": "Orbit AI",
                    "verified_product_facts": ["Approved fact"],
                    "product_ui_asset_ids": ["33333333-3333-4333-8333-333333333333"],
                    "benefit_order": ["Summarize"],
                    "cta_action_meaning": "Start a fixture demo",
                    "layout_template_asset_id": "44444444-4444-4444-8444-444444444444",
                    "localizable_fields": ["language"],
                },
                "product_category": "ai_application",
                "creative_format": "static_ad",
            }
        ).model_dump_json()
    )
    result = _valid_result_payload(request)
    result["created_at"] = "2026-08-10T13:00:00+01:00"
    with pytest.raises(ValidationError, match="UTC"):
        ResultVersion.model_validate(result)


@pytest.mark.parametrize("drift", ["brand_lock", "source_asset", "direction", "cta"])
def test_project_run_rejects_results_that_drift_from_request(
    valid_run_payload: dict[str, object], drift: str
) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    result = _valid_result_payload(request)
    if drift == "brand_lock":
        changed = {**request.brand_lock.model_dump(), "product_name": "Drifted name"}
        result["analysis"] = {**result["analysis"], "brand_lock": changed}
        result["brief"] = {**result["brief"], "brand_lock": changed}
        result["copy"] = {**result["copy"], "cta_action_meaning": changed["cta_action_meaning"]}
    elif drift == "source_asset":
        result["analysis"] = {
            **result["analysis"],
            "source_asset": {**request.source_asset.model_dump(), "sha256": "b" * 64},
        }
    elif drift == "direction":
        result["brief"] = {**result["brief"], "direction": "uk_to_china"}
    else:
        changed = {**request.brand_lock.model_dump(), "cta_action_meaning": "Drifted action"}
        result["analysis"] = {**result["analysis"], "brand_lock": changed}
        result["brief"] = {**result["brief"], "brand_lock": changed}
        result["copy"] = {**result["copy"], "cta_action_meaning": "Drifted action"}

    with pytest.raises(ValidationError, match="original request"):
        ProjectRunContract(
            run_id="66666666-6666-4666-8666-666666666666",
            request=request,
            status="completed",
            result_versions=(result,),
            created_at="2026-08-10T12:00:00Z",
            updated_at="2026-08-10T12:00:00Z",
        )


def test_project_run_accepts_result_identical_to_request_after_json_round_trip(
    valid_run_payload: dict[str, object],
) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    project = ProjectRunContract(
        run_id="66666666-6666-4666-8666-666666666666",
        request=request,
        status="completed",
        result_versions=(_valid_result_payload(request),),
        created_at="2026-08-10T12:00:00Z",
        updated_at="2026-08-10T12:00:00Z",
    )

    serialized = project.model_dump_json(by_alias=True)
    restored = ProjectRunContract.model_validate_json(serialized)
    assert restored.run_id == project.run_id


def test_result_version_fails_when_cta_meaning_changes(
    valid_run_payload: dict[str, object],
) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    values = {
        "version": 1,
        "analysis": {
            "source_asset": request.source_asset,
            "detected_locale": "zh-CN",
            "brand_lock": request.brand_lock,
            "hypotheses": [],
            "warnings": ["human_review_required"],
        },
        "brief": {
            "direction": request.direction,
            "target_locale": "en-GB",
            "brand_lock": request.brand_lock,
            "hypotheses": [],
            "narrative": "A reviewable fixture narrative.",
            "use_scenario": "An authorized fictional workflow.",
            "trust_information": "Fixture demo; not a live model.",
        },
        "copy": {
            "locale": "en-GB",
            "headline": "Organize approved notes",
            "body": "Fixture copy for review.",
            "cta_label": "Try fixture",
            "cta_action_meaning": "A different action",
        },
        "critique": {
            "warnings": ["human_review_required"],
            "brand_lock_preserved": True,
            "requires_human_review": True,
        },
        "created_at": datetime(2026, 8, 10, tzinfo=UTC),
    }
    with pytest.raises(ValidationError, match="CTA action meaning"):
        ResultVersion.model_validate(values)


def test_result_version_fails_when_analysis_brand_lock_changes(
    valid_run_payload: dict[str, object],
) -> None:
    request = RunCreate.model_validate(valid_run_payload)
    values = {
        "version": 1,
        "analysis": {
            "source_asset": request.source_asset,
            "detected_locale": "zh-CN",
            "brand_lock": {
                **request.brand_lock.model_dump(),
                "product_name": "Changed product name",
            },
            "hypotheses": [],
            "warnings": ["human_review_required"],
        },
        "brief": {
            "direction": request.direction,
            "target_locale": "en-GB",
            "brand_lock": request.brand_lock,
            "hypotheses": [],
            "narrative": "A reviewable fixture narrative.",
            "use_scenario": "An authorized fictional workflow.",
            "trust_information": "Fixture demo; not a live model.",
        },
        "copy": {
            "locale": "en-GB",
            "headline": "Organize approved notes",
            "body": "Fixture copy for review.",
            "cta_label": "Try fixture",
            "cta_action_meaning": request.brand_lock.cta_action_meaning,
        },
        "critique": {
            "warnings": ["human_review_required"],
            "brand_lock_preserved": True,
            "requires_human_review": True,
        },
        "created_at": datetime(2026, 8, 10, tzinfo=UTC),
    }

    with pytest.raises(ValidationError, match="Brand Lock"):
        ResultVersion.model_validate(values)


def test_registry_schema_contains_every_public_contract() -> None:
    definitions = ContractRegistry.model_json_schema(by_alias=True)["$defs"]
    for name in (
        "AssetRef",
        "AssetUploaded",
        "BrandLock",
        "CulturalHypothesis",
        "AdAnalysis",
        "CreativeBrief",
        "AdCopy",
        "CritiqueReport",
        "ResultVersion",
        "RunCreate",
        "RunCreated",
        "RunSnapshot",
        "JobAccepted",
        "FeedbackRequest",
        "RetryRequest",
        "ExportSummary",
        "ProjectRunContract",
    ):
        assert name in definitions
    assert "copy" in definitions["ResultVersion"]["properties"]
    assert "ad_copy" not in definitions["ResultVersion"]["properties"]
    run_create = definitions["RunCreate"]["properties"]
    assert run_create["execution_mode"]["const"] == "fixture"
    source_asset_name = run_create["source_asset"]["$ref"].rsplit("/", 1)[-1]
    assert definitions[source_asset_name]["properties"]["kind"]["const"] == "source_ad"
    assert definitions["AdAnalysis"]["properties"]["source_asset"]["$ref"].endswith(
        "/SourceAdAssetRef"
    )
    public_ref = definitions["PublicReference"]
    assert public_ref["pattern"]
    for definition, field in (
        ("AssetRef", "expires_at"),
        ("AssetUploaded", "created_at"),
        ("ResultVersion", "created_at"),
        ("RunCreated", "created_at"),
        ("JobAccepted", "accepted_at"),
        ("FeedbackRequest", "submitted_at"),
        ("ExportSummary", "exported_at"),
        ("ProjectRunContract", "created_at"),
        ("ProjectRunContract", "updated_at"),
    ):
        timestamp = definitions[definition]["properties"][field]
        if field == "expires_at":
            timestamp = next(item for item in timestamp["anyOf"] if "$ref" in item)
        if "$ref" in timestamp:
            timestamp = definitions[timestamp["$ref"].rsplit("/", 1)[-1]]
        assert timestamp["format"] == "date-time"
        assert timestamp["pattern"] == r"(?:Z|\+00:00)$"
