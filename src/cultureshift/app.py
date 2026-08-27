from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.middleware.cors import CORSMiddleware

from cultureshift.analysis_pipeline import (
    AnalysisErrorCode,
    AnalysisPipeline,
    AnalysisPipelineError,
)
from cultureshift.analysis_provider import (
    FixtureProvider,
    VisionAnalysisRequest,
    VisionProvider,
)
from cultureshift.asset_storage import (
    MAX_ASSET_BYTES,
    AssetEmptyError,
    AssetLifecycleClosedError,
    AssetMetadataError,
    AssetStorageError,
    AssetTooLargeError,
    AssetTypeMismatchError,
    TemporaryAssetStore,
    UnsupportedAssetTypeError,
)
from cultureshift.brand_lock_confirmation import BrandLockConfirmationError
from cultureshift.capability_tokens import (
    Capability,
    CapabilityTokenError,
    CapabilityTokenService,
)
from cultureshift.composition import PillowCompositor
from cultureshift.composition_export import (
    CompositionExportError,
    CompositionExportErrorCode,
    CompositionExportService,
)
from cultureshift.composition_service import (
    CompositionService,
    CompositionServiceError,
    CompositionServiceErrorCode,
)
from cultureshift.composition_storage import CompositionArtifactStore
from cultureshift.contracts import (
    AnalysisCompleted,
    AssetUploaded,
    BrandLockConfirmation,
    BrandLockConfirmed,
    CompositionGenerated,
    CritiqueCompleted,
    DraftGenerated,
    FeedbackRequest,
    RetryRequest,
    RevisionCompleted,
    RunCreate,
    RunCreated,
    RunSnapshot,
    RunStatus,
)
from cultureshift.critic import Critic, CriticRequest
from cultureshift.domain import ProjectRun, ProjectRunStatus
from cultureshift.draft_generation import (
    DraftErrorCode,
    DraftGenerationError,
    DraftGenerator,
    FixtureCopywriter,
)
from cultureshift.fixture_assets import FixtureAssetRegistry
from cultureshift.image_provider import FixtureImageProvider
from cultureshift.rate_limits import FixedWindowRateLimiter
from cultureshift.repository import (
    BrandLockImmutableError,
    CritiqueImmutableError,
    DraftImmutableError,
    InvalidRunStateError,
    ProjectRunNotFoundError,
    SQLiteProjectRunRepository,
)
from cultureshift.revision import FixtureRevisionEngine
from cultureshift.revision_service import (
    RevisionService,
    RevisionServiceError,
    RevisionServiceErrorCode,
)

DEFAULT_STUDIO_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


def _cors_origins_from_environment() -> tuple[str, ...]:
    configured = os.environ.get("CULTURESHIFT_STUDIO_ORIGINS", "")
    origins = tuple(value.strip() for value in configured.split(",") if value.strip())
    selected = tuple(dict.fromkeys(origins or DEFAULT_STUDIO_ORIGINS))
    if any(
        origin == "*" or not origin.startswith(("http://", "https://"))
        for origin in selected
    ):
        raise RuntimeError("CULTURESHIFT_STUDIO_ORIGINS must contain exact origins")
    return selected


def _capability_service_from_environment() -> CapabilityTokenService:
    configured = os.environ.get("CULTURESHIFT_CAPABILITY_SECRET")
    if configured is None:
        raise RuntimeError("CULTURESHIFT_CAPABILITY_SECRET is required")
    secret = configured.encode("utf-8")
    if len(secret) < 32:
        raise RuntimeError("CULTURESHIFT_CAPABILITY_SECRET must be at least 32 UTF-8 bytes")
    return CapabilityTokenService(secret=secret, audience="cultureshift-api")


def _asset_store_from_environment() -> TemporaryAssetStore:
    configured = os.environ.get("CULTURESHIFT_TEMP_ASSET_DIR", "")
    if not configured.strip():
        raise RuntimeError("CULTURESHIFT_TEMP_ASSET_DIR is required")
    return TemporaryAssetStore(configured)


def create_app(
    *,
    repository: SQLiteProjectRunRepository | None = None,
    token_service: CapabilityTokenService | None = None,
    asset_store: TemporaryAssetStore | None = None,
    upload_rate_limiter: FixedWindowRateLimiter | None = None,
    analysis_provider: VisionProvider | None = None,
    draft_generator: DraftGenerator | None = None,
    composition_service: CompositionService | None = None,
    composition_export_service: CompositionExportService | None = None,
    critic: Critic | None = None,
    revision_service: RevisionService | None = None,
) -> FastAPI:
    runs = repository or SQLiteProjectRunRepository(Path(".cultureshift/runs.sqlite3"))
    tokens = token_service or _capability_service_from_environment()
    assets = asset_store or _asset_store_from_environment()
    upload_limit = upload_rate_limiter or FixedWindowRateLimiter(
        limit=10, window=timedelta(minutes=1)
    )
    provider = analysis_provider or FixtureProvider()
    drafts = draft_generator or DraftGenerator(FixtureCopywriter())
    temporary_root = Path(os.environ.get("CULTURESHIFT_TEMP_ASSET_DIR", ".cultureshift/assets"))
    composition_store = CompositionArtifactStore(temporary_root / "compositions")
    compositions = composition_service or CompositionService(
        runs,
        FixtureImageProvider(),
        FixtureAssetRegistry(),
        PillowCompositor(),
        composition_store,
        Path(__file__).resolve().parents[2] / "assets" / "fonts" / "NotoSansCJKsc-Regular.otf",
    )
    composition_exports = composition_export_service or CompositionExportService(
        runs, composition_store
    )
    reviews = critic or Critic()
    revisions = revision_service or RevisionService(
        runs,
        FixtureRevisionEngine(),
        FixtureImageProvider(),
        FixtureAssetRegistry(),
        PillowCompositor(),
        composition_store,
        Path(__file__).resolve().parents[2]
        / "assets"
        / "fonts"
        / "NotoSansCJKsc-Regular.otf",
        reviews,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        runs.initialize()
        assets.purge_expired()
        yield

    application = FastAPI(title="CultureShift API", version="0.1.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(_cors_origins_from_environment()),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-Provenance-Ref",
            "X-Rights-Ref",
        ],
    )

    @application.exception_handler(RequestValidationError)
    async def safe_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        details = []
        for item in error.errors():
            location = item["loc"]
            if item["type"] == "extra_forbidden" and location:
                location = (*location[:-1], "unknown_field")
            details.append({"type": item["type"], "loc": location, "msg": item["msg"]})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": details},
        )

    @application.get("/health", tags=["operations"])
    @application.get("/healthz", tags=["operations"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post(
        "/api/v1/assets",
        response_model=AssetUploaded,
        status_code=status.HTTP_201_CREATED,
        tags=["assets"],
    )
    async def upload_asset(request: Request) -> AssetUploaded:
        client_key = request.client.host if request.client is not None else "unknown-client"
        if not upload_limit.allow(client_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "upload_rate_limited"},
            )
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > MAX_ASSET_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail={"code": "asset_too_large"},
                )
        try:
            stored = assets.store(
                bytes(content),
                declared_media_type=request.headers.get("Content-Type", ""),
                provenance_ref=request.headers.get("X-Provenance-Ref", ""),
                rights_ref=request.headers.get("X-Rights-Ref", ""),
            )
            try:
                delete_token = tokens.issue(
                    subject=str(stored.asset.asset_id),
                    capabilities={Capability.DELETE_ASSET},
                    ttl=timedelta(hours=24),
                )
            except Exception:
                assets.delete(stored.asset.asset_id, reason="token_issue_failed")
                raise
            return AssetUploaded(
                asset=stored.asset,
                size_bytes=stored.size_bytes,
                created_at=stored.created_at,
                delete_capability_token=delete_token,
            )
        except AssetEmptyError:
            code, status_code = "asset_empty", status.HTTP_400_BAD_REQUEST
        except UnsupportedAssetTypeError:
            code, status_code = "unsupported_asset_type", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        except AssetTypeMismatchError:
            code, status_code = "asset_type_mismatch", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        except AssetTooLargeError:
            code, status_code = "asset_too_large", status.HTTP_413_CONTENT_TOO_LARGE
        except AssetMetadataError:
            code, status_code = "invalid_asset_metadata", status.HTTP_422_UNPROCESSABLE_CONTENT
        except AssetLifecycleClosedError:
            code, status_code = "asset_lifecycle_closed", status.HTTP_409_CONFLICT
        except AssetStorageError:
            code, status_code = "asset_storage_failed", status.HTTP_500_INTERNAL_SERVER_ERROR
        except Exception:
            code, status_code = "asset_storage_failed", status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail={"code": code}) from None

    @application.delete(
        "/api/v1/assets/{asset_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["assets"],
    )
    def delete_asset(asset_id: UUID, request: Request) -> None:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(token, required=Capability.DELETE_ASSET)
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(asset_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )
        try:
            assets.delete(asset_id)
        except AssetStorageError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "asset_deletion_failed"},
            ) from None

    @application.post(
        "/api/v1/runs",
        response_model=RunCreated,
        status_code=status.HTTP_201_CREATED,
        tags=["runs"],
    )
    def create_run(request: RunCreate) -> RunCreated:
        try:
            run = ProjectRun(direction=request.direction)
            token = tokens.issue(
                subject=str(run.id),
                capabilities={
                    Capability.READ_PROJECT_RUN,
                    Capability.ANALYZE_PROJECT_RUN,
                    Capability.UPDATE_PROJECT_RUN,
                },
                ttl=timedelta(minutes=15),
            )
            response = RunCreated(
                run_id=run.id,
                status=RunStatus(run.status.value),
                capability_token=token,
                created_at=run.created_at,
            )
            runs.create(run, request=request)
            return response
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "run_creation_failed"},
            ) from None

    @application.get(
        "/api/v1/runs/{run_id}",
        response_model=RunSnapshot,
        tags=["runs"],
    )
    def get_run(run_id: UUID, request: Request) -> RunSnapshot:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(
                token,
                required=Capability.READ_PROJECT_RUN,
            )
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(run_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )
        try:
            run = runs.get(run_id)
        except ProjectRunNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "run_not_found"},
            ) from None
        return RunSnapshot(
            run_id=run.id,
            direction=run.direction,
            status=run.status,
            warning_codes=run.warning_codes,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @application.post(
        "/api/v1/runs/{run_id}/analyze",
        response_model=AnalysisCompleted,
        tags=["runs"],
    )
    def analyze_run(run_id: UUID, request: Request) -> AnalysisCompleted:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(token, required=Capability.ANALYZE_PROJECT_RUN)
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(run_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )
        try:
            run = runs.get(run_id)
        except ProjectRunNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "run_not_found"},
            ) from None

        if run.status is ProjectRunStatus.AWAITING_BRAND_LOCK:
            try:
                existing = runs.get_analysis(run_id)
            except Exception:
                existing = None
            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"code": "analysis_state_invalid"},
                )
            return AnalysisCompleted(
                run_id=run.id,
                status=RunStatus.AWAITING_BRAND_LOCK,
                analysis=existing,
                repair_attempted=runs.get_repair_attempted(run_id),
                completed_at=run.updated_at,
            )
        if run.status is not ProjectRunStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "invalid_run_state"},
            )

        try:
            stored_request = runs.get_request(run_id)
            claimed = runs.claim_analysis(run_id)
            if claimed is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "invalid_run_state"},
                )
            loaded = assets.load(stored_request.source_asset.asset_id)
            if loaded.asset != stored_request.source_asset:
                raise AssetStorageError("temporary asset metadata mismatch")
        except AssetLifecycleClosedError:
            runs.record_failure(
                run_id,
                ProjectRunStatus.BLOCKED,
                AnalysisErrorCode.ASSET_CLOSED.value,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": AnalysisErrorCode.ASSET_CLOSED.value},
            ) from None
        except (AssetStorageError, ProjectRunNotFoundError):
            runs.record_failure(run_id, ProjectRunStatus.BLOCKED, "asset_validation_failed")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "asset_validation_failed"},
            ) from None

        analysis_request = VisionAnalysisRequest(
            content=loaded.content,
            source_asset=stored_request.source_asset,
            direction=stored_request.direction,
            brand_lock=stored_request.brand_lock,
            product_category=stored_request.product_category,
            creative_format=stored_request.creative_format,
        )
        try:
            outcome = AnalysisPipeline(provider).analyze(analysis_request)
        except AnalysisPipelineError as error:
            blocked_codes = {
                AnalysisErrorCode.INVALID_INPUT,
                AnalysisErrorCode.UNSUPPORTED_SCOPE,
                AnalysisErrorCode.ASSET_CLOSED,
                AnalysisErrorCode.INSTRUCTION_LIKE_CONTENT,
                AnalysisErrorCode.PROHIBITED_CONTENT,
                AnalysisErrorCode.UNSAFE_HYPOTHESIS,
            }
            failed_status = (
                ProjectRunStatus.BLOCKED
                if error.code in blocked_codes
                else ProjectRunStatus.FAILED
            )
            runs.record_failure(run_id, failed_status, error.code.value)
            status_code = (
                status.HTTP_422_UNPROCESSABLE_CONTENT
                if failed_status is ProjectRunStatus.BLOCKED
                else status.HTTP_502_BAD_GATEWAY
            )
            raise HTTPException(
                status_code=status_code,
                detail={"code": error.code.value},
            ) from None

        try:
            completed = runs.complete_analysis(
                run_id,
                outcome.analysis,
                repair_attempted=outcome.repair_attempted,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "analysis_persistence_failed"},
            ) from None
        return AnalysisCompleted(
            run_id=completed.id,
            status=RunStatus.AWAITING_BRAND_LOCK,
            analysis=outcome.analysis,
            repair_attempted=outcome.repair_attempted,
            completed_at=completed.updated_at,
        )

    @application.post(
        "/api/v1/runs/{run_id}/brand-lock/confirm",
        response_model=BrandLockConfirmed,
        tags=["runs"],
    )
    def confirm_brand_lock(
        run_id: UUID,
        confirmation: BrandLockConfirmation,
        request: Request,
    ) -> BrandLockConfirmed:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(token, required=Capability.UPDATE_PROJECT_RUN)
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(run_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )
        try:
            record = runs.confirm_brand_lock(run_id, confirmation.brand_lock)
        except ProjectRunNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "run_not_found"},
            ) from None
        except InvalidRunStateError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "invalid_run_state"},
            ) from None
        except BrandLockImmutableError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "brand_lock_immutable"},
            ) from None
        except BrandLockConfirmationError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": error.code.value},
            ) from None
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "brand_lock_persistence_failed"},
            ) from None
        return BrandLockConfirmed(
            run_id=run_id,
            status=RunStatus.IN_PROGRESS,
            brand_lock=record.brand_lock,
            confirmed_at=record.confirmed_at,
        )

    @application.post(
        "/api/v1/runs/{run_id}/draft",
        response_model=DraftGenerated,
        tags=["runs"],
    )
    def generate_draft(run_id: UUID, request: Request) -> DraftGenerated:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(token, required=Capability.UPDATE_PROJECT_RUN)
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(run_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )

        try:
            existing = runs.get_draft(run_id)
            run = runs.get(run_id)
        except ProjectRunNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "run_not_found"},
            ) from None
        if existing is not None:
            return DraftGenerated(
                run_id=run.id,
                status=RunStatus.IN_PROGRESS,
                brief=existing.brief,
                copy=existing.ad_copy,
                rule_ids=existing.rule_ids,
                generated_at=existing.generated_at,
            )
        try:
            analysis = runs.get_analysis(run_id)
            confirmation = runs.get_confirmed_brand_lock(run_id)
        except ProjectRunNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "run_not_found"},
            ) from None
        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "invalid_run_state"},
            )
        if confirmation is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "brand_lock_unconfirmed"},
            )
        if run.status is not ProjectRunStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "invalid_run_state"},
            )
        try:
            generated = drafts.generate(
                analysis,
                confirmation.brand_lock,
                direction=run.direction,
            )
        except DraftGenerationError as error:
            status_code = (
                status.HTTP_409_CONFLICT
                if error.code is DraftErrorCode.BRAND_LOCK_UNCONFIRMED
                else status.HTTP_422_UNPROCESSABLE_CONTENT
            )
            raise HTTPException(
                status_code=status_code,
                detail={"code": error.code.value},
            ) from None
        try:
            record = runs.save_draft(
                run_id,
                generated.brief,
                generated.ad_copy,
                generated.fact_references,
                generated.rule_ids,
            )
        except (InvalidRunStateError, DraftImmutableError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "invalid_run_state"},
            ) from None
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "draft_persistence_failed"},
            ) from None
        return DraftGenerated(
            run_id=run.id,
            status=RunStatus.IN_PROGRESS,
            brief=record.brief,
            copy=record.ad_copy,
            rule_ids=record.rule_ids,
            generated_at=record.generated_at,
        )

    @application.post(
        "/api/v1/runs/{run_id}/composition",
        response_model=CompositionGenerated,
        tags=["runs"],
    )
    async def generate_composition(run_id: UUID, request: Request) -> CompositionGenerated:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(token, required=Capability.UPDATE_PROJECT_RUN)
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(run_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )
        if await request.body():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "composition_body_not_allowed"},
            )
        try:
            return compositions.generate(run_id)
        except CompositionServiceError as error:
            if error.code is CompositionServiceErrorCode.RUN_NOT_FOUND:
                status_code = status.HTTP_404_NOT_FOUND
            elif error.code is CompositionServiceErrorCode.OUTPUT_INVALID:
                status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
            elif error.code is CompositionServiceErrorCode.PERSISTENCE_FAILED:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            else:
                status_code = status.HTTP_409_CONFLICT
            raise HTTPException(
                status_code=status_code,
                detail={"code": error.code.value},
            ) from None

    @application.post(
        "/api/v1/runs/{run_id}/critic",
        response_model=CritiqueCompleted,
        tags=["runs"],
    )
    async def run_critic(run_id: UUID, request: Request) -> CritiqueCompleted:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(token, required=Capability.UPDATE_PROJECT_RUN)
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(run_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )
        if await request.body():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "critic_body_not_allowed"},
            )
        try:
            run = runs.get(run_id)
            existing = runs.get_critique(run_id)
            if existing is not None:
                report = existing.report
            else:
                analysis = runs.get_analysis(run_id)
                confirmation = runs.get_confirmed_brand_lock(run_id)
                draft = runs.get_draft(run_id)
                composition = runs.get_composition(run_id)
                if any(
                    value is None
                    for value in (analysis, confirmation, draft, composition)
                ):
                    raise InvalidRunStateError("review prerequisites are incomplete")
                report = reviews.review(
                    CriticRequest(
                        analysis=analysis,
                        confirmed_brand_lock=confirmation.brand_lock,
                        draft=draft,
                        composition=composition,
                        warning_codes=run.warning_codes,
                    )
                )
                runs.save_critique(run_id, report)
                run = runs.get(run_id)
        except ProjectRunNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "run_not_found"},
            ) from None
        except (InvalidRunStateError, CritiqueImmutableError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "invalid_run_state"},
            ) from None
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "critic_failed"},
            ) from None
        return CritiqueCompleted(
            run_id=run.id,
            status=RunStatus(run.status.value),
            critique=report,
            initial_generation_count=run.initial_generation_count,
            human_revision_count=run.human_revision_count,
            technical_attempt_count=run.technical_attempt_count,
            reviewed_at=report.reviewed_at,
        )

    def require_run_update_capability(run_id: UUID, request: Request) -> None:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(token, required=Capability.UPDATE_PROJECT_RUN)
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(run_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )

    def revision_failure(error: RevisionServiceError) -> HTTPException:
        if error.code is RevisionServiceErrorCode.RUN_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif error.code is RevisionServiceErrorCode.INVALID_REVISION_REQUEST:
            status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
        elif error.code in {
            RevisionServiceErrorCode.REVISION_FAILED,
            RevisionServiceErrorCode.RETRY_FAILED,
        }:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            status_code = status.HTTP_409_CONFLICT
        return HTTPException(status_code=status_code, detail={"code": error.code.value})

    @application.post(
        "/api/v1/runs/{run_id}/feedback",
        response_model=RevisionCompleted,
        tags=["runs"],
    )
    async def submit_feedback(
        run_id: UUID, feedback: FeedbackRequest, request: Request
    ) -> RevisionCompleted:
        require_run_update_capability(run_id, request)
        idempotency_key = request.headers.get("Idempotency-Key", "")
        if not idempotency_key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "invalid_revision_request"},
            )
        if feedback.run_id != run_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "invalid_run_state"},
            )
        try:
            return revisions.submit_feedback(feedback, idempotency_key)
        except RevisionServiceError as error:
            raise revision_failure(error) from None

    @application.post(
        "/api/v1/runs/{run_id}/retry",
        response_model=RevisionCompleted,
        tags=["runs"],
    )
    async def retry_revision(
        run_id: UUID, retry: RetryRequest, request: Request
    ) -> RevisionCompleted:
        require_run_update_capability(run_id, request)
        idempotency_key = request.headers.get("Idempotency-Key", "")
        if not idempotency_key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "invalid_revision_request"},
            )
        if retry.run_id != run_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "invalid_run_state"},
            )
        try:
            return revisions.retry(retry, idempotency_key)
        except RevisionServiceError as error:
            raise revision_failure(error) from None

    def require_composition_read_capability(run_id: UUID, request: Request) -> None:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or separator != " " or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            )
        try:
            claims = tokens.verify(token, required=Capability.READ_PROJECT_RUN)
        except CapabilityTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_capability"},
            ) from None
        if claims.subject != str(run_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "capability_subject_mismatch"},
            )

    def export_failure(error: CompositionExportError) -> HTTPException:
        if error.code is CompositionExportErrorCode.RUN_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif error.code is CompositionExportErrorCode.COMPOSITION_UNAVAILABLE:
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_410_GONE
        return HTTPException(status_code=status_code, detail={"code": error.code.value})

    @application.get("/api/v1/runs/{run_id}/composition.png", tags=["runs"])
    def export_composition_png(
        run_id: UUID, request: Request, result_version: Literal["1", "2"] = "1"
    ) -> Response:
        require_composition_read_capability(run_id, request)
        try:
            exported = composition_exports.export_png(run_id, int(result_version))
        except CompositionExportError as error:
            raise export_failure(error) from None
        return Response(
            content=exported.png_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="cultureshift-{run_id}.png"'
                ),
                "X-Content-Type-Options": "nosniff",
            },
        )

    @application.get("/api/v1/runs/{run_id}/composition.json", tags=["runs"])
    def export_composition_json(
        run_id: UUID, request: Request, result_version: Literal["1", "2"] = "1"
    ) -> Response:
        require_composition_read_capability(run_id, request)
        try:
            encoded = composition_exports.export_json(run_id, int(result_version))
        except CompositionExportError as error:
            raise export_failure(error) from None
        return Response(
            content=encoded,
            media_type="application/json",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="cultureshift-{run_id}.json"'
                ),
                "X-Content-Type-Options": "nosniff",
            },
        )

    return application


app = create_app()
