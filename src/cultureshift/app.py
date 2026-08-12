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

from cultureshift.capability_tokens import (
    Capability,
    CapabilityTokenError,
    CapabilityTokenService,
)
from cultureshift.contracts import RunCreate, RunCreated, RunSnapshot, RunStatus
from cultureshift.domain import ProjectRun
from cultureshift.repository import ProjectRunNotFoundError, SQLiteProjectRunRepository


def _capability_service_from_environment() -> CapabilityTokenService:
    configured = os.environ.get("CULTURESHIFT_CAPABILITY_SECRET")
    if configured is None:
        raise RuntimeError("CULTURESHIFT_CAPABILITY_SECRET is required")
    secret = configured.encode("utf-8")
    if len(secret) < 32:
        raise RuntimeError("CULTURESHIFT_CAPABILITY_SECRET must be at least 32 UTF-8 bytes")
    return CapabilityTokenService(secret=secret, audience="cultureshift-api")


def create_app(
    *,
    repository: SQLiteProjectRunRepository | None = None,
    token_service: CapabilityTokenService | None = None,
) -> FastAPI:
    runs = repository or SQLiteProjectRunRepository(Path(".cultureshift/runs.sqlite3"))
    tokens = token_service or _capability_service_from_environment()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        runs.initialize()
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
