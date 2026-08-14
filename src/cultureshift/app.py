from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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
from cultureshift.capability_tokens import (
    Capability,
    CapabilityTokenError,
    CapabilityTokenService,
)
from cultureshift.contracts import AssetUploaded, RunCreate, RunCreated, RunSnapshot, RunStatus
from cultureshift.domain import ProjectRun
from cultureshift.rate_limits import FixedWindowRateLimiter
from cultureshift.repository import ProjectRunNotFoundError, SQLiteProjectRunRepository


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
) -> FastAPI:
    runs = repository or SQLiteProjectRunRepository(Path(".cultureshift/runs.sqlite3"))
    tokens = token_service or _capability_service_from_environment()
    assets = asset_store or _asset_store_from_environment()
    upload_limit = upload_rate_limiter or FixedWindowRateLimiter(
        limit=10, window=timedelta(minutes=1)
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        runs.initialize()
        assets.purge_expired()
        yield

    application = FastAPI(title="CultureShift API", version="0.1.0", lifespan=lifespan)

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
                capabilities={Capability.READ_PROJECT_RUN},
                ttl=timedelta(minutes=15),
            )
            response = RunCreated(
                run_id=run.id,
                status=RunStatus(run.status.value),
                capability_token=token,
                created_at=run.created_at,
            )
            runs.create(run)
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

    return application


app = create_app()
