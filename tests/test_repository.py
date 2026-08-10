import sqlite3

import pytest

from cultureshift.domain import LocalizationDirection, ProjectRun, ProjectRunStatus
from cultureshift.repository import ProjectRunNotFoundError, SQLiteProjectRunRepository


def test_repository_initializes_and_round_trips_project_run(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    repository = SQLiteProjectRunRepository(database)
    run = ProjectRun(
        direction=LocalizationDirection.CHINA_TO_UK,
        warning_codes=("evidence_gap", "human_review_required"),
    )

    repository.initialize()
    repository.create(run)

    assert repository.get(run.id) == run

    with sqlite3.connect(database) as connection:
        stored = connection.execute(
            "SELECT direction, status, created_at, updated_at, warning_codes_json "
            "FROM project_runs WHERE id = ?",
            (str(run.id),),
        ).fetchone()

    assert stored == (
        "china_to_uk",
        "pending",
        run.created_at.isoformat(),
        run.updated_at.isoformat(),
        '["evidence_gap","human_review_required"]',
    )


def test_repository_updates_only_status_and_timestamp(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    repository = SQLiteProjectRunRepository(database)
    original = ProjectRun(direction=LocalizationDirection.UK_TO_CHINA)
    repository.initialize()
    repository.create(original)

    updated = repository.update_status(original.id, ProjectRunStatus.IN_PROGRESS)

    assert updated.status is ProjectRunStatus.IN_PROGRESS
    assert updated.direction is original.direction
    assert updated.warning_codes == original.warning_codes
    assert updated.updated_at >= original.updated_at


def test_repository_missing_run_fails_explicitly(tmp_path) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()

    with pytest.raises(ProjectRunNotFoundError):
        repository.get("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def test_repository_does_not_persist_capability_tokens(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    repository = SQLiteProjectRunRepository(database)
    repository.initialize()

    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(project_runs)")}

    assert "token" not in columns
    assert "capability_token" not in columns
