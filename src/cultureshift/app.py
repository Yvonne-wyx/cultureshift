from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cultureshift.capability_tokens import Capability, CapabilityTokenService
from cultureshift.contracts import RunCreate, RunCreated, RunStatus
from cultureshift.domain import ProjectRun
from cultureshift.repository import SQLiteProjectRunRepository


def create_app(
    *,
    repository: SQLiteProjectRunRepository | None = None,
    token_service: CapabilityTokenService | None = None,
) -> FastAPI:
    runs = repository or SQLiteProjectRunRepository(Path(".cultureshift/runs.sqlite3"))
    tokens = token_service or CapabilityTokenService(
        secret=secrets.token_bytes(32),
        audience="cultureshift-api",
    )

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

    return application


app = create_app()
