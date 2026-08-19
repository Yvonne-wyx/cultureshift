import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from cultureshift.contracts import AdAnalysis, RunCreate
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


def test_repository_binds_validated_request_and_analysis(
    tmp_path, valid_run_payload
) -> None:
    database = tmp_path / "runs.sqlite3"
    repository = SQLiteProjectRunRepository(database)
    repository.initialize()
    request = RunCreate.model_validate(valid_run_payload)
    analysis = AdAnalysis(
        source_asset=request.source_asset,
        detected_locale="zh-CN",
        brand_lock=request.brand_lock,
        warnings=("fixture_provider",),
    )
    run = ProjectRun(direction=request.direction)

    repository.create(run, request=request)
    repository.update_status(run.id, ProjectRunStatus.IN_PROGRESS)
    completed = repository.complete_analysis(run.id, analysis, repair_attempted=True)

    assert completed.status is ProjectRunStatus.AWAITING_BRAND_LOCK
    assert repository.get_request(run.id) == request
    assert repository.get_analysis(run.id) == analysis
    assert repository.get_repair_attempted(run.id) is True
    with sqlite3.connect(database) as connection:
        request_json, analysis_json = connection.execute(
            "SELECT request_json, analysis_json FROM project_run_contexts WHERE run_id = ?",
            (str(run.id),),
        ).fetchone()
    persisted = request_json + analysis_json
    assert "capability_token" not in persisted
    assert "storage_path" not in persisted
    assert "image_bytes" not in persisted


def test_repository_records_only_bounded_failure_code(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    request = RunCreate.model_validate(valid_run_payload)
    run = repository.create(ProjectRun(direction=request.direction), request=request)
    repository.update_status(run.id, ProjectRunStatus.IN_PROGRESS)

    failed = repository.record_failure(
        run.id,
        ProjectRunStatus.FAILED,
        "provider_output_invalid",
    )

    assert failed.status is ProjectRunStatus.FAILED
    assert failed.warning_codes == ("provider_output_invalid",)
    assert repository.get_analysis(run.id) is None


def test_analysis_completion_without_context_leaves_status_unchanged(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    request = RunCreate.model_validate(valid_run_payload)
    analysis = AdAnalysis(
        source_asset=request.source_asset,
        detected_locale="zh-CN",
        brand_lock=request.brand_lock,
    )
    run = repository.create(ProjectRun(direction=request.direction))
    repository.update_status(run.id, ProjectRunStatus.IN_PROGRESS)

    with pytest.raises(ProjectRunNotFoundError):
        repository.complete_analysis(run.id, analysis)

    assert repository.get(run.id).status is ProjectRunStatus.IN_PROGRESS


def test_only_one_concurrent_analysis_claim_wins(tmp_path, valid_run_payload) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    request = RunCreate.model_validate(valid_run_payload)
    run = repository.create(ProjectRun(direction=request.direction), request=request)
    barrier = Barrier(2)

    def claim():
        barrier.wait()
        return repository.claim_analysis(run.id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: claim(), range(2)))

    assert sum(result is not None for result in results) == 1
    assert repository.get(run.id).status is ProjectRunStatus.IN_PROGRESS


def test_completion_rolls_back_if_in_progress_claim_is_lost(
    tmp_path, valid_run_payload
) -> None:
    database = tmp_path / "runs.sqlite3"
    repository = SQLiteProjectRunRepository(database)
    repository.initialize()
    request = RunCreate.model_validate(valid_run_payload)
    analysis = AdAnalysis(
        source_asset=request.source_asset,
        detected_locale="zh-CN",
        brand_lock=request.brand_lock,
    )
    run = repository.create(ProjectRun(direction=request.direction), request=request)
    assert repository.claim_analysis(run.id) is not None
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TRIGGER lose_analysis_claim
            AFTER UPDATE OF analysis_json ON project_run_contexts
            BEGIN
                UPDATE project_runs SET status = 'blocked' WHERE id = NEW.run_id;
            END
            """
        )

    with pytest.raises(ProjectRunNotFoundError):
        repository.complete_analysis(run.id, analysis)

    assert repository.get(run.id).status is ProjectRunStatus.IN_PROGRESS
    assert repository.get_analysis(run.id) is None
