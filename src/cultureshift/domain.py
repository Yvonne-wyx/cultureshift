from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LocalizationDirection(StrEnum):
    CHINA_TO_UK = "china_to_uk"
    UK_TO_CHINA = "uk_to_china"


class ProjectRunStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_BRAND_LOCK = "awaiting_brand_lock"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    READY = "ready"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_FINAL = "failed_final"


_ALLOWED_TRANSITIONS: dict[ProjectRunStatus, frozenset[ProjectRunStatus]] = {
    ProjectRunStatus.PENDING: frozenset(
        {ProjectRunStatus.IN_PROGRESS, ProjectRunStatus.BLOCKED, ProjectRunStatus.FAILED}
    ),
    ProjectRunStatus.IN_PROGRESS: frozenset(
        {
            ProjectRunStatus.AWAITING_BRAND_LOCK,
            ProjectRunStatus.BLOCKED,
            ProjectRunStatus.COMPLETED,
            ProjectRunStatus.FAILED,
            ProjectRunStatus.READY,
            ProjectRunStatus.FAILED_RETRYABLE,
            ProjectRunStatus.FAILED_FINAL,
        }
    ),
    ProjectRunStatus.AWAITING_BRAND_LOCK: frozenset(
        {ProjectRunStatus.IN_PROGRESS, ProjectRunStatus.FAILED}
    ),
    ProjectRunStatus.BLOCKED: frozenset({ProjectRunStatus.IN_PROGRESS, ProjectRunStatus.FAILED}),
    ProjectRunStatus.COMPLETED: frozenset(),
    ProjectRunStatus.FAILED: frozenset(),
    ProjectRunStatus.READY: frozenset({ProjectRunStatus.IN_PROGRESS}),
    ProjectRunStatus.FAILED_RETRYABLE: frozenset({ProjectRunStatus.IN_PROGRESS}),
    ProjectRunStatus.FAILED_FINAL: frozenset(),
}


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProjectRun(BaseModel):
    """Non-sensitive state for one in-scope localization run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    direction: LocalizationDirection
    status: ProjectRunStatus = ProjectRunStatus.PENDING
    warning_codes: tuple[str, ...] = ()
    initial_generation_count: int = Field(default=0, ge=0, le=1)
    human_revision_count: int = Field(default=0, ge=0, le=1)
    technical_attempt_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime | None = None

    @field_validator("warning_codes")
    @classmethod
    def validate_warning_codes(cls, warning_codes: tuple[str, ...]) -> tuple[str, ...]:
        if len(warning_codes) > 32 or len(set(warning_codes)) != len(warning_codes):
            raise ValueError("warning_codes must be unique and contain at most 32 values")
        if any(re.fullmatch(r"[a-z][a-z0-9_]{0,63}", code) is None for code in warning_codes):
            raise ValueError("warning_codes must contain only non-sensitive code identifiers")
        return warning_codes

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        created_at = self.created_at
        updated_at = self.updated_at
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if updated_at is None:
            object.__setattr__(self, "updated_at", created_at)
            return self
        if updated_at.tzinfo is None or updated_at.utcoffset() is None:
            raise ValueError("updated_at must be timezone-aware")
        if updated_at < created_at:
            raise ValueError("updated_at cannot precede created_at")
        return self

    def with_status(
        self, status: ProjectRunStatus, *, updated_at: datetime | None = None
    ) -> ProjectRun:
        if status not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"invalid status transition: {self.status} -> {status}")
        values = self.model_dump()
        values.update({"status": status, "updated_at": updated_at or utc_now()})
        return ProjectRun.model_validate(values)
