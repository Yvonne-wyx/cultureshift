from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from cultureshift.domain import (
    LocalizationDirection,
    ProjectRun,
    ProjectRunStatus,
)


def test_project_run_defaults_are_safe_and_serializable() -> None:
    run = ProjectRun(direction=LocalizationDirection.CHINA_TO_UK)

    assert isinstance(run.id, UUID)
    assert run.status is ProjectRunStatus.PENDING
    assert run.created_at.tzinfo is UTC
    assert run.updated_at == run.created_at
    assert ProjectRun.model_validate_json(run.model_dump_json()) == run


def test_project_run_rejects_unsupported_direction() -> None:
    with pytest.raises(ValidationError):
        ProjectRun(direction="us_to_uk")


def test_project_run_rejects_updated_at_before_created_at() -> None:
    created_at = datetime.now(UTC)
    with pytest.raises(ValidationError):
        ProjectRun(
            direction=LocalizationDirection.UK_TO_CHINA,
            created_at=created_at,
            updated_at=created_at - timedelta(seconds=1),
        )


def test_project_run_status_transition_updates_timestamp() -> None:
    run = ProjectRun(direction=LocalizationDirection.UK_TO_CHINA)
    started = run.with_status(ProjectRunStatus.IN_PROGRESS)

    assert started.status is ProjectRunStatus.IN_PROGRESS
    assert started.updated_at >= run.updated_at
    assert run.status is ProjectRunStatus.PENDING


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ProjectRunStatus.PENDING, ProjectRunStatus.IN_PROGRESS),
        (ProjectRunStatus.PENDING, ProjectRunStatus.BLOCKED),
        (ProjectRunStatus.PENDING, ProjectRunStatus.FAILED),
        (ProjectRunStatus.IN_PROGRESS, ProjectRunStatus.BLOCKED),
        (ProjectRunStatus.IN_PROGRESS, ProjectRunStatus.AWAITING_BRAND_LOCK),
        (ProjectRunStatus.IN_PROGRESS, ProjectRunStatus.COMPLETED),
        (ProjectRunStatus.IN_PROGRESS, ProjectRunStatus.FAILED),
        (ProjectRunStatus.BLOCKED, ProjectRunStatus.IN_PROGRESS),
        (ProjectRunStatus.BLOCKED, ProjectRunStatus.FAILED),
        (ProjectRunStatus.AWAITING_BRAND_LOCK, ProjectRunStatus.IN_PROGRESS),
        (ProjectRunStatus.AWAITING_BRAND_LOCK, ProjectRunStatus.FAILED),
    ],
)
def test_project_run_accepts_legal_status_transitions(
    current: ProjectRunStatus, target: ProjectRunStatus
) -> None:
    run = ProjectRun(direction=LocalizationDirection.CHINA_TO_UK, status=current)

    assert run.with_status(target).status is target


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ProjectRunStatus.PENDING, ProjectRunStatus.COMPLETED),
        (ProjectRunStatus.PENDING, ProjectRunStatus.AWAITING_BRAND_LOCK),
        (ProjectRunStatus.IN_PROGRESS, ProjectRunStatus.PENDING),
        (ProjectRunStatus.BLOCKED, ProjectRunStatus.COMPLETED),
        (ProjectRunStatus.COMPLETED, ProjectRunStatus.IN_PROGRESS),
        (ProjectRunStatus.FAILED, ProjectRunStatus.IN_PROGRESS),
    ],
)
def test_project_run_rejects_invalid_status_transitions(
    current: ProjectRunStatus, target: ProjectRunStatus
) -> None:
    run = ProjectRun(direction=LocalizationDirection.CHINA_TO_UK, status=current)

    with pytest.raises(ValueError, match="transition"):
        run.with_status(target)


def test_project_run_rejects_transition_timestamp_moving_backwards() -> None:
    run = ProjectRun(direction=LocalizationDirection.CHINA_TO_UK)

    with pytest.raises(ValidationError, match="updated_at"):
        run.with_status(
            ProjectRunStatus.IN_PROGRESS,
            updated_at=run.updated_at - timedelta(microseconds=1),
        )


def test_project_run_rejects_sensitive_or_unstructured_warning_codes() -> None:
    with pytest.raises(ValidationError, match="warning_codes"):
        ProjectRun(
            direction=LocalizationDirection.CHINA_TO_UK,
            warning_codes=("raw user content",),
        )
