import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest

from cultureshift.contracts import (
    AdAnalysis,
    BrandLock,
    CompositionGenerated,
    CompositionLayer,
    RunCreate,
)
from cultureshift.domain import LocalizationDirection, ProjectRun, ProjectRunStatus
from cultureshift.draft_generation import DraftGenerator, FixtureCopywriter
from cultureshift.repository import (
    BrandLockImmutableError,
    CompositionImmutableError,
    DraftImmutableError,
    InvalidRunStateError,
    ProjectRunNotFoundError,
    SQLiteProjectRunRepository,
)


def analyzed_run(repository, valid_run_payload):
    request = RunCreate.model_validate(valid_run_payload)
    run = repository.create(ProjectRun(direction=request.direction), request=request)
    repository.update_status(run.id, ProjectRunStatus.IN_PROGRESS)
    repository.complete_analysis(
        run.id,
        AdAnalysis(
            source_asset=request.source_asset,
            detected_locale="zh-CN",
            brand_lock=request.brand_lock,
        ),
    )
    return run, request.brand_lock


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


def test_initialize_migrates_day9_context_for_brand_lock_confirmation(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE project_run_contexts (
                run_id TEXT PRIMARY KEY,
                request_json TEXT NOT NULL,
                analysis_json TEXT,
                repair_attempted INTEGER NOT NULL DEFAULT 0
            )
            """
        )

    SQLiteProjectRunRepository(database).initialize()

    with sqlite3.connect(database) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(project_run_contexts)")
        }
    assert {"confirmed_brand_lock_json", "brand_lock_confirmed_at"} <= columns


def test_initialize_migrates_context_for_day11_draft(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE project_run_contexts (
                run_id TEXT PRIMARY KEY,
                request_json TEXT NOT NULL,
                analysis_json TEXT,
                repair_attempted INTEGER NOT NULL DEFAULT 0,
                confirmed_brand_lock_json TEXT,
                brand_lock_confirmed_at TEXT
            )
            """
        )

    SQLiteProjectRunRepository(database).initialize()

    with sqlite3.connect(database) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(project_run_contexts)")
        }
    assert {
        "creative_brief_json",
        "ad_copy_json",
        "draft_rule_ids_json",
        "draft_generated_at",
    } <= columns


def test_initialize_migrates_context_for_day12_composition(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE project_run_contexts (
                run_id TEXT PRIMARY KEY,
                request_json TEXT NOT NULL,
                analysis_json TEXT,
                repair_attempted INTEGER NOT NULL DEFAULT 0,
                confirmed_brand_lock_json TEXT,
                brand_lock_confirmed_at TEXT,
                creative_brief_json TEXT,
                ad_copy_json TEXT,
                draft_rule_ids_json TEXT,
                draft_generated_at TEXT
            )
            """
        )

    SQLiteProjectRunRepository(database).initialize()

    with sqlite3.connect(database) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(project_run_contexts)")
        }
    assert "composition_json" in columns


def _composition_summary(run_id, brand_lock: BrandLock) -> CompositionGenerated:
    specs = (
        ("background", None, (0, 0, 1600, 900), "1"),
        ("product_ui", str(brand_lock.product_ui_asset_ids[0]), (850, 170, 1500, 690), "2"),
        ("logo", str(brand_lock.logo_asset_id), (100, 70, 320, 166), "3"),
        ("headline", None, (100, 220, 760, 344), "4"),
        ("body", None, (100, 390, 780, 476), "5"),
        ("cta", None, (100, 560, 430, 636), "6"),
        ("disclosure", None, (100, 820, 530, 864), "7"),
    )
    layers = tuple(
        CompositionLayer(
            kind=kind,
            source_asset_id=source,
            rgba_sha256=digit * 64,
            bounds=bounds,
            width=bounds[2] - bounds[0],
            height=bounds[3] - bounds[1],
        )
        for kind, source, bounds, digit in specs
    )
    return CompositionGenerated(
        run_id=run_id,
        status="in_progress",
        execution_mode="fixture",
        width=1600,
        height=900,
        media_type="image/png",
        rendered_sha256="a" * 64,
        artifact_id=uuid4(),
        layers=layers,
        disclosure="Fixture Demo / 非实时模型",
        generated_at=datetime(2026, 8, 23, 9, 0, tzinfo=UTC),
    )


def test_repository_saves_and_replays_one_immutable_composition(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    run, analyzed = analyzed_run(repository, valid_run_payload)
    repository.confirm_brand_lock(run.id, analyzed)
    analysis = repository.get_analysis(run.id)
    assert analysis is not None
    draft = DraftGenerator(FixtureCopywriter()).generate(
        analysis, analyzed, direction=run.direction
    )
    repository.save_draft(run.id, draft.brief, draft.ad_copy, draft.rule_ids)
    summary = _composition_summary(run.id, analyzed)

    first = repository.save_composition(run.id, summary)
    retry = repository.save_composition(run.id, summary)
    assert retry == first
    assert repository.get_composition(run.id) == first

    changed = summary.model_copy(update={"artifact_id": uuid4()})
    with pytest.raises(CompositionImmutableError):
        repository.save_composition(run.id, changed)


def test_repository_saves_and_replays_one_immutable_draft(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    run, analyzed = analyzed_run(repository, valid_run_payload)
    repository.confirm_brand_lock(run.id, analyzed)
    analysis = repository.get_analysis(run.id)
    assert analysis is not None
    draft = DraftGenerator(FixtureCopywriter()).generate(
        analysis,
        analyzed,
        direction=run.direction,
    )
    generated_at = datetime(2026, 8, 20, 10, 0, tzinfo=UTC)

    first = repository.save_draft(
        run.id,
        draft.brief,
        draft.ad_copy,
        draft.rule_ids,
        generated_at=generated_at,
    )
    retry = repository.save_draft(
        run.id,
        draft.brief,
        draft.ad_copy,
        draft.rule_ids,
        generated_at=generated_at + timedelta(hours=1),
    )

    assert first.generated_at == generated_at
    assert retry == first
    assert repository.get_draft(run.id) == first
    with pytest.raises(DraftImmutableError):
        repository.save_draft(
            run.id,
            draft.brief,
            draft.ad_copy.model_copy(update={"headline": "Changed"}),
            draft.rule_ids,
        )


def test_repository_rejects_draft_before_brand_lock_confirmation(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    run, analyzed = analyzed_run(repository, valid_run_payload)
    analysis = repository.get_analysis(run.id)
    assert analysis is not None
    draft = DraftGenerator(FixtureCopywriter()).generate(
        analysis,
        analyzed,
        direction=run.direction,
    )

    with pytest.raises(InvalidRunStateError):
        repository.save_draft(
            run.id,
            draft.brief,
            draft.ad_copy,
            draft.rule_ids,
        )

    assert repository.get_draft(run.id) is None


def test_repository_confirms_brand_lock_and_returns_run_to_in_progress(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    run, analyzed = analyzed_run(repository, valid_run_payload)
    proposed = BrandLock.model_validate(
        {
            **analyzed.model_dump(),
            "benefit_order": tuple(reversed(analyzed.benefit_order)),
            "localizable_fields": ("narrative", "language"),
        }
    )
    confirmed_at = run.created_at + timedelta(seconds=1)

    record = repository.confirm_brand_lock(
        run.id,
        proposed,
        confirmed_at=confirmed_at,
    )

    assert record.brand_lock == proposed
    assert record.confirmed_at == confirmed_at
    assert repository.get_confirmed_brand_lock(run.id) == record
    assert repository.get(run.id).status is ProjectRunStatus.IN_PROGRESS


def test_confirmation_retry_is_idempotent_but_different_value_is_immutable(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    run, analyzed = analyzed_run(repository, valid_run_payload)
    first_time = run.created_at + timedelta(seconds=1)
    first = repository.confirm_brand_lock(run.id, analyzed, confirmed_at=first_time)

    retry = repository.confirm_brand_lock(
        run.id,
        analyzed,
        confirmed_at=first_time + timedelta(hours=1),
    )
    changed = BrandLock.model_validate(
        {**analyzed.model_dump(), "benefit_order": tuple(reversed(analyzed.benefit_order))}
    )

    assert retry == first
    with pytest.raises(BrandLockImmutableError):
        repository.confirm_brand_lock(run.id, changed)
    assert repository.get_confirmed_brand_lock(run.id) == first


def test_confirmation_rejects_timestamp_before_run_creation(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    run, analyzed = analyzed_run(repository, valid_run_payload)

    with pytest.raises(ValueError, match="confirmed_at cannot precede run creation"):
        repository.confirm_brand_lock(
            run.id,
            analyzed,
            confirmed_at=run.created_at - timedelta(seconds=1),
        )

    assert repository.get_confirmed_brand_lock(run.id) is None
    assert repository.get(run.id).status is ProjectRunStatus.AWAITING_BRAND_LOCK


def test_concurrent_different_confirmations_store_exactly_one_value(
    tmp_path, valid_run_payload
) -> None:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    repository.initialize()
    run, analyzed = analyzed_run(repository, valid_run_payload)
    reversed_lock = BrandLock.model_validate(
        {**analyzed.model_dump(), "benefit_order": tuple(reversed(analyzed.benefit_order))}
    )
    barrier = Barrier(2)

    def confirm(proposed):
        barrier.wait()
        try:
            return repository.confirm_brand_lock(run.id, proposed).brand_lock
        except (BrandLockImmutableError, InvalidRunStateError):
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(confirm, (analyzed, reversed_lock)))

    winner = repository.get_confirmed_brand_lock(run.id)
    assert winner is not None
    assert sum(result is not None for result in results) == 1
    assert winner.brand_lock in (analyzed, reversed_lock)


def test_confirmation_rolls_back_when_awaiting_claim_is_lost(
    tmp_path, valid_run_payload
) -> None:
    database = tmp_path / "runs.sqlite3"
    repository = SQLiteProjectRunRepository(database)
    repository.initialize()
    run, analyzed = analyzed_run(repository, valid_run_payload)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TRIGGER lose_brand_lock_claim
            AFTER UPDATE OF confirmed_brand_lock_json ON project_run_contexts
            BEGIN
                UPDATE project_runs SET status = 'blocked' WHERE id = NEW.run_id;
            END
            """
        )

    with pytest.raises(InvalidRunStateError):
        repository.confirm_brand_lock(run.id, analyzed)

    assert repository.get_confirmed_brand_lock(run.id) is None
    assert repository.get(run.id).status is ProjectRunStatus.AWAITING_BRAND_LOCK
