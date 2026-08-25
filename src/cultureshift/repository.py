from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from cultureshift.brand_lock_confirmation import validate_brand_lock_confirmation
from cultureshift.contracts import (
    AdAnalysis,
    AdCopy,
    BrandLock,
    CompositionGenerated,
    CreativeBrief,
    CritiqueReport,
    CritiqueStatus,
    RunCreate,
)
from cultureshift.domain import ProjectRun, ProjectRunStatus, utc_now


class ProjectRunNotFoundError(LookupError):
    pass


class DuplicateProjectRunError(ValueError):
    pass


class BrandLockImmutableError(ValueError):
    pass


class InvalidRunStateError(ValueError):
    pass


class DraftImmutableError(ValueError):
    pass


class CompositionImmutableError(ValueError):
    pass


class CritiqueImmutableError(ValueError):
    pass


@dataclass(frozen=True)
class BrandLockConfirmationRecord:
    brand_lock: BrandLock
    confirmed_at: datetime


@dataclass(frozen=True)
class DraftRecord:
    brief: CreativeBrief
    ad_copy: AdCopy
    fact_references: tuple[str, ...]
    rule_ids: tuple[str, ...]
    generated_at: datetime


@dataclass(frozen=True)
class CritiqueRecord:
    report: CritiqueReport
    reviewed_at: datetime


class SQLiteProjectRunRepository:
    """SQLite storage for non-sensitive ProjectRun state only."""

    def __init__(self, database: str | Path) -> None:
        self._database = Path(database)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self._database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_runs (
                    id TEXT PRIMARY KEY,
                    direction TEXT NOT NULL,
                    status TEXT NOT NULL,
                    warning_codes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_run_contexts (
                    run_id TEXT PRIMARY KEY,
                    request_json TEXT NOT NULL,
                    analysis_json TEXT,
                    repair_attempted INTEGER NOT NULL DEFAULT 0,
                    confirmed_brand_lock_json TEXT,
                    brand_lock_confirmed_at TEXT,
                    creative_brief_json TEXT,
                    ad_copy_json TEXT,
                    draft_fact_references_json TEXT,
                    draft_rule_ids_json TEXT,
                    draft_generated_at TEXT,
                    composition_json TEXT,
                    critique_json TEXT,
                    critic_reviewed_at TEXT,
                    initial_generation_count INTEGER NOT NULL DEFAULT 0,
                    human_revision_count INTEGER NOT NULL DEFAULT 0,
                    technical_attempt_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(project_run_contexts)")
            }
            if "repair_attempted" not in columns:
                connection.execute(
                    """
                    ALTER TABLE project_run_contexts
                    ADD COLUMN repair_attempted INTEGER NOT NULL DEFAULT 0
                    """
                )
            if "confirmed_brand_lock_json" not in columns:
                connection.execute(
                    "ALTER TABLE project_run_contexts ADD COLUMN confirmed_brand_lock_json TEXT"
                )
            if "brand_lock_confirmed_at" not in columns:
                connection.execute(
                    "ALTER TABLE project_run_contexts ADD COLUMN brand_lock_confirmed_at TEXT"
                )
            draft_columns = {
                "creative_brief_json": "TEXT",
                "ad_copy_json": "TEXT",
                "draft_fact_references_json": "TEXT",
                "draft_rule_ids_json": "TEXT",
                "draft_generated_at": "TEXT",
            }
            for name, sql_type in draft_columns.items():
                if name not in columns:
                    connection.execute(
                        f"ALTER TABLE project_run_contexts ADD COLUMN {name} {sql_type}"
                    )
            if "composition_json" not in columns:
                connection.execute(
                    "ALTER TABLE project_run_contexts ADD COLUMN composition_json TEXT"
                )
            critique_columns = {
                "critique_json": "TEXT",
                "critic_reviewed_at": "TEXT",
            }
            for name, sql_type in critique_columns.items():
                if name not in columns:
                    connection.execute(
                        f"ALTER TABLE project_run_contexts ADD COLUMN {name} {sql_type}"
                    )
            counter_columns = {
                "initial_generation_count": "INTEGER NOT NULL DEFAULT 0",
                "human_revision_count": "INTEGER NOT NULL DEFAULT 0",
                "technical_attempt_count": "INTEGER NOT NULL DEFAULT 0",
            }
            for name, sql_type in counter_columns.items():
                if name not in columns:
                    connection.execute(
                        f"ALTER TABLE project_run_contexts ADD COLUMN {name} {sql_type}"
                    )
            connection.execute(
                """
                UPDATE project_run_contexts
                SET initial_generation_count = 1
                WHERE composition_json IS NOT NULL AND initial_generation_count = 0
                """
            )
            legacy_drafts = connection.execute(
                """
                SELECT run_id, confirmed_brand_lock_json
                FROM project_run_contexts
                WHERE draft_generated_at IS NOT NULL
                  AND draft_fact_references_json IS NULL
                """
            ).fetchall()
            for row in legacy_drafts:
                if row["confirmed_brand_lock_json"] is None:
                    raise ValueError("legacy draft is missing confirmed Brand Lock")
                lock = BrandLock.model_validate_json(row["confirmed_brand_lock_json"])
                connection.execute(
                    """
                    UPDATE project_run_contexts
                    SET draft_fact_references_json = ?
                    WHERE run_id = ?
                    """,
                    (
                        json.dumps(lock.verified_product_facts, separators=(",", ":")),
                        row["run_id"],
                    ),
                )

    def create(self, run: ProjectRun, *, request: RunCreate | None = None) -> ProjectRun:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO project_runs (
                        id, direction, status, warning_codes_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(run.id),
                        run.direction.value,
                        run.status.value,
                        json.dumps(run.warning_codes, separators=(",", ":")),
                        run.created_at.isoformat(),
                        run.updated_at.isoformat(),
                    ),
                )
                if request is not None:
                    if request.direction is not run.direction:
                        raise ValueError("run direction must match request direction")
                    connection.execute(
                        """
                        INSERT INTO project_run_contexts (run_id, request_json, analysis_json)
                        VALUES (?, ?, NULL)
                        """,
                        (str(run.id), request.model_dump_json()),
                    )
        except sqlite3.IntegrityError as error:
            raise DuplicateProjectRunError(str(run.id)) from error
        return run

    def get_request(self, run_id: UUID | str) -> RunCreate:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT request_json FROM project_run_contexts WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        return RunCreate.model_validate_json(row["request_json"])

    def get_analysis(self, run_id: UUID | str) -> AdAnalysis | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT analysis_json FROM project_run_contexts WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        if row["analysis_json"] is None:
            return None
        return AdAnalysis.model_validate_json(row["analysis_json"])

    def get_repair_attempted(self, run_id: UUID | str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT repair_attempted FROM project_run_contexts WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        value = row["repair_attempted"]
        if value not in (0, 1):
            raise ValueError("invalid repair attempt state")
        return bool(value)

    def get_confirmed_brand_lock(
        self,
        run_id: UUID | str,
    ) -> BrandLockConfirmationRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT confirmed_brand_lock_json, brand_lock_confirmed_at
                FROM project_run_contexts
                WHERE run_id = ?
                """,
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        return self._confirmation_record(row)

    def get_draft(self, run_id: UUID | str) -> DraftRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT creative_brief_json, ad_copy_json,
                       draft_fact_references_json, draft_rule_ids_json,
                       draft_generated_at
                FROM project_run_contexts
                WHERE run_id = ?
                """,
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        return self._draft_record(row)

    def get_composition(self, run_id: UUID | str) -> CompositionGenerated | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT composition_json FROM project_run_contexts WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        encoded = row["composition_json"]
        return None if encoded is None else CompositionGenerated.model_validate_json(encoded)

    def get_critique(self, run_id: UUID | str) -> CritiqueRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT critique_json, critic_reviewed_at "
                "FROM project_run_contexts WHERE run_id = ?",
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        return self._critique_record(row)

    @staticmethod
    def _confirmation_record(row: sqlite3.Row) -> BrandLockConfirmationRecord | None:
        encoded = row["confirmed_brand_lock_json"]
        timestamp = row["brand_lock_confirmed_at"]
        if encoded is None and timestamp is None:
            return None
        if encoded is None or timestamp is None:
            raise ValueError("invalid Brand Lock confirmation state")
        confirmed_at = datetime.fromisoformat(timestamp)
        if confirmed_at.tzinfo is None or confirmed_at.utcoffset() != timedelta(0):
            raise ValueError("invalid Brand Lock confirmation state")
        return BrandLockConfirmationRecord(
            brand_lock=BrandLock.model_validate_json(encoded),
            confirmed_at=confirmed_at,
        )

    @staticmethod
    def _draft_record(row: sqlite3.Row) -> DraftRecord | None:
        values = (
            row["creative_brief_json"],
            row["ad_copy_json"],
            row["draft_fact_references_json"],
            row["draft_rule_ids_json"],
            row["draft_generated_at"],
        )
        if all(value is None for value in values):
            return None
        if any(value is None for value in values):
            raise ValueError("invalid draft persistence state")
        generated_at = datetime.fromisoformat(row["draft_generated_at"])
        if generated_at.tzinfo is None or generated_at.utcoffset() != timedelta(0):
            raise ValueError("invalid draft persistence state")
        fact_references = json.loads(row["draft_fact_references_json"])
        rule_ids = json.loads(row["draft_rule_ids_json"])
        if not isinstance(fact_references, list) or not all(
            isinstance(value, str) for value in fact_references
        ):
            raise ValueError("invalid draft persistence state")
        if not isinstance(rule_ids, list) or not all(isinstance(value, str) for value in rule_ids):
            raise ValueError("invalid draft persistence state")
        return DraftRecord(
            brief=CreativeBrief.model_validate_json(row["creative_brief_json"]),
            ad_copy=AdCopy.model_validate_json(row["ad_copy_json"]),
            fact_references=tuple(fact_references),
            rule_ids=tuple(rule_ids),
            generated_at=generated_at,
        )

    @staticmethod
    def _critique_record(row: sqlite3.Row) -> CritiqueRecord | None:
        encoded = row["critique_json"]
        timestamp = row["critic_reviewed_at"]
        if encoded is None and timestamp is None:
            return None
        if encoded is None or timestamp is None:
            raise ValueError("invalid Critic persistence state")
        report = CritiqueReport.model_validate_json(encoded)
        reviewed_at = datetime.fromisoformat(timestamp)
        if (
            reviewed_at.tzinfo is None
            or reviewed_at.utcoffset() != timedelta(0)
            or reviewed_at != report.reviewed_at
        ):
            raise ValueError("invalid Critic persistence state")
        return CritiqueRecord(report=report, reviewed_at=reviewed_at)

    def save_draft(
        self,
        run_id: UUID | str,
        brief: CreativeBrief,
        ad_copy: AdCopy,
        fact_references: tuple[str, ...],
        rule_ids: tuple[str, ...],
        *,
        generated_at: datetime | None = None,
    ) -> DraftRecord:
        generation_time = generated_at or utc_now()
        if generation_time.tzinfo is None or generation_time.utcoffset() != timedelta(0):
            raise ValueError("generated_at must use UTC")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT r.status, c.confirmed_brand_lock_json,
                       c.creative_brief_json, c.ad_copy_json,
                       c.draft_fact_references_json, c.draft_rule_ids_json,
                       c.draft_generated_at
                FROM project_runs AS r
                LEFT JOIN project_run_contexts AS c ON c.run_id = r.id
                WHERE r.id = ?
                """,
                (str(run_id),),
            ).fetchone()
            if row is None:
                raise ProjectRunNotFoundError(str(run_id))
            existing = self._draft_record(row)
            if existing is not None:
                if (
                    existing.brief == brief
                    and existing.ad_copy == ad_copy
                    and existing.fact_references == fact_references
                    and existing.rule_ids == rule_ids
                ):
                    return existing
                raise DraftImmutableError("draft is immutable")
            if (
                row["status"] != ProjectRunStatus.IN_PROGRESS.value
                or row["confirmed_brand_lock_json"] is None
            ):
                raise InvalidRunStateError("confirmed in-progress run required")
            confirmed = BrandLock.model_validate_json(row["confirmed_brand_lock_json"])
            if brief.brand_lock != confirmed:
                raise InvalidRunStateError("draft Brand Lock must match confirmation")
            if not fact_references or not set(fact_references).issubset(
                confirmed.verified_product_facts
            ):
                raise InvalidRunStateError("draft fact references must be verified")
            cursor = connection.execute(
                """
                UPDATE project_run_contexts
                SET creative_brief_json = ?, ad_copy_json = ?,
                    draft_fact_references_json = ?, draft_rule_ids_json = ?,
                    draft_generated_at = ?
                WHERE run_id = ?
                  AND creative_brief_json IS NULL
                  AND ad_copy_json IS NULL
                  AND draft_fact_references_json IS NULL
                  AND draft_rule_ids_json IS NULL
                  AND draft_generated_at IS NULL
                """,
                (
                    brief.model_dump_json(),
                    ad_copy.model_dump_json(),
                    json.dumps(fact_references, separators=(",", ":")),
                    json.dumps(rule_ids, separators=(",", ":")),
                    generation_time.isoformat(),
                    str(run_id),
                ),
            )
            if cursor.rowcount != 1:
                raise DraftImmutableError("draft is immutable")
        return DraftRecord(brief, ad_copy, fact_references, rule_ids, generation_time)

    def save_composition(
        self,
        run_id: UUID | str,
        composition: CompositionGenerated,
    ) -> CompositionGenerated:
        if str(composition.run_id) != str(run_id):
            raise InvalidRunStateError("composition run mismatch")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT r.status, c.confirmed_brand_lock_json, c.draft_generated_at,
                       c.composition_json, c.initial_generation_count
                FROM project_runs AS r
                LEFT JOIN project_run_contexts AS c ON c.run_id = r.id
                WHERE r.id = ?
                """,
                (str(run_id),),
            ).fetchone()
            if row is None:
                raise ProjectRunNotFoundError(str(run_id))
            if row["composition_json"] is not None:
                existing = CompositionGenerated.model_validate_json(row["composition_json"])
                if existing == composition:
                    return existing
                raise CompositionImmutableError("composition is immutable")
            if (
                row["status"] != ProjectRunStatus.IN_PROGRESS.value
                or row["confirmed_brand_lock_json"] is None
                or row["draft_generated_at"] is None
            ):
                raise InvalidRunStateError("confirmed drafted run required")
            confirmed = BrandLock.model_validate_json(row["confirmed_brand_lock_json"])
            layer_sources = {
                layer.kind: layer.source_asset_id
                for layer in composition.layers
                if layer.source_asset_id is not None
            }
            if (
                layer_sources.get("logo") != confirmed.logo_asset_id
                or layer_sources.get("product_ui") not in confirmed.product_ui_asset_ids
            ):
                raise InvalidRunStateError("composition Brand Lock mismatch")
            cursor = connection.execute(
                """
                UPDATE project_run_contexts
                SET composition_json = ?, initial_generation_count = 1
                WHERE run_id = ? AND composition_json IS NULL
                  AND initial_generation_count = 0
                """,
                (composition.model_dump_json(), str(run_id)),
            )
            if cursor.rowcount != 1:
                raise CompositionImmutableError("composition is immutable")
        return composition

    def save_critique(
        self,
        run_id: UUID | str,
        report: CritiqueReport,
    ) -> CritiqueRecord:
        target_status = (
            ProjectRunStatus.FAILED_FINAL
            if report.status is CritiqueStatus.REJECT
            else ProjectRunStatus.READY
        )
        record = CritiqueRecord(report=report, reviewed_at=report.reviewed_at)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT r.status, c.confirmed_brand_lock_json,
                       c.draft_generated_at, c.composition_json,
                       c.initial_generation_count,
                       c.critique_json, c.critic_reviewed_at
                FROM project_runs AS r
                LEFT JOIN project_run_contexts AS c ON c.run_id = r.id
                WHERE r.id = ?
                """,
                (str(run_id),),
            ).fetchone()
            if row is None:
                raise ProjectRunNotFoundError(str(run_id))
            existing = self._critique_record(row)
            if existing is not None:
                if existing.report == report:
                    return existing
                raise CritiqueImmutableError("Critic result is immutable")
            if (
                row["status"] != ProjectRunStatus.IN_PROGRESS.value
                or row["confirmed_brand_lock_json"] is None
                or row["draft_generated_at"] is None
                or row["composition_json"] is None
                or row["initial_generation_count"] != 1
            ):
                raise InvalidRunStateError("one composed in-progress run is required")
            context = connection.execute(
                """
                UPDATE project_run_contexts
                SET critique_json = ?, critic_reviewed_at = ?
                WHERE run_id = ?
                  AND critique_json IS NULL
                  AND critic_reviewed_at IS NULL
                """,
                (report.model_dump_json(), report.reviewed_at.isoformat(), str(run_id)),
            )
            if context.rowcount != 1:
                raise CritiqueImmutableError("Critic result is immutable")
            run = connection.execute(
                """
                UPDATE project_runs
                SET status = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    target_status.value,
                    report.reviewed_at.isoformat(),
                    str(run_id),
                    ProjectRunStatus.IN_PROGRESS.value,
                ),
            )
            if run.rowcount != 1:
                raise InvalidRunStateError("one composed in-progress run is required")
        return record

    def get(self, run_id: UUID | str) -> ProjectRun:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT r.id, r.direction, r.status, r.warning_codes_json,
                       r.created_at, r.updated_at,
                       COALESCE(c.initial_generation_count, 0) AS initial_generation_count,
                       COALESCE(c.human_revision_count, 0) AS human_revision_count,
                       COALESCE(c.technical_attempt_count, 0) AS technical_attempt_count
                FROM project_runs AS r
                LEFT JOIN project_run_contexts AS c ON c.run_id = r.id
                WHERE r.id = ?
                """,
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        values = dict(row)
        values["warning_codes"] = json.loads(values.pop("warning_codes_json"))
        return ProjectRun.model_validate(values)

    def increment_technical_attempt(self, run_id: UUID | str) -> ProjectRun:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE project_run_contexts
                SET technical_attempt_count = technical_attempt_count + 1
                WHERE run_id = ?
                """,
                (str(run_id),),
            )
        if cursor.rowcount != 1:
            raise ProjectRunNotFoundError(str(run_id))
        return self.get(run_id)

    def update_status(self, run_id: UUID | str, status: ProjectRunStatus) -> ProjectRun:
        updated = self.get(run_id).with_status(status)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE project_runs
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (updated.status.value, updated.updated_at.isoformat(), str(updated.id)),
            )
        if cursor.rowcount != 1:
            raise ProjectRunNotFoundError(str(run_id))
        return updated

    def claim_analysis(self, run_id: UUID | str) -> ProjectRun | None:
        claimed_at = utc_now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE project_runs
                SET status = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    ProjectRunStatus.IN_PROGRESS.value,
                    claimed_at.isoformat(),
                    str(run_id),
                    ProjectRunStatus.PENDING.value,
                ),
            )
        if cursor.rowcount != 1:
            self.get(run_id)
            return None
        return self.get(run_id)

    def complete_analysis(
        self,
        run_id: UUID | str,
        analysis: AdAnalysis,
        *,
        repair_attempted: bool = False,
    ) -> ProjectRun:
        current = self.get(run_id)
        request = self.get_request(run_id)
        if (
            analysis.source_asset != request.source_asset
            or analysis.brand_lock != request.brand_lock
        ):
            raise ValueError("analysis must match the stored request")
        updated = current.with_status(ProjectRunStatus.AWAITING_BRAND_LOCK)
        with self._connect() as connection:
            context = connection.execute(
                """
                UPDATE project_run_contexts
                SET analysis_json = ?, repair_attempted = ?
                WHERE run_id = ?
                """,
                (analysis.model_dump_json(), int(repair_attempted), str(run_id)),
            )
            if context.rowcount != 1:
                raise ProjectRunNotFoundError(str(run_id))
            run = connection.execute(
                """
                UPDATE project_runs
                SET status = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    updated.status.value,
                    updated.updated_at.isoformat(),
                    str(run_id),
                    ProjectRunStatus.IN_PROGRESS.value,
                ),
            )
            if run.rowcount != 1:
                raise ProjectRunNotFoundError(str(run_id))
        return updated

    def confirm_brand_lock(
        self,
        run_id: UUID | str,
        proposed: BrandLock,
        *,
        confirmed_at: datetime | None = None,
    ) -> BrandLockConfirmationRecord:
        confirmation_time = confirmed_at or utc_now()
        if (
            confirmation_time.tzinfo is None
            or confirmation_time.utcoffset() != timedelta(0)
        ):
            raise ValueError("confirmed_at must use UTC")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT
                    r.status,
                    r.created_at,
                    c.analysis_json,
                    c.confirmed_brand_lock_json,
                    c.brand_lock_confirmed_at
                FROM project_runs AS r
                LEFT JOIN project_run_contexts AS c ON c.run_id = r.id
                WHERE r.id = ?
                """,
                (str(run_id),),
            ).fetchone()
            if row is None:
                raise ProjectRunNotFoundError(str(run_id))
            existing = self._confirmation_record(row)
            if existing is not None:
                if existing.brand_lock == proposed:
                    return existing
                raise BrandLockImmutableError("Brand Lock is immutable")
            if confirmation_time < datetime.fromisoformat(row["created_at"]):
                raise ValueError("confirmed_at cannot precede run creation")
            if row["status"] != ProjectRunStatus.AWAITING_BRAND_LOCK.value:
                raise InvalidRunStateError("run is not awaiting Brand Lock")
            if row["analysis_json"] is None:
                raise InvalidRunStateError("validated analysis is required")
            analysis = AdAnalysis.model_validate_json(row["analysis_json"])
            validated = validate_brand_lock_confirmation(
                proposed,
                analysis.brand_lock,
            )
            context = connection.execute(
                """
                UPDATE project_run_contexts
                SET confirmed_brand_lock_json = ?, brand_lock_confirmed_at = ?
                WHERE run_id = ? AND confirmed_brand_lock_json IS NULL
                """,
                (
                    validated.model_dump_json(),
                    confirmation_time.isoformat(),
                    str(run_id),
                ),
            )
            if context.rowcount != 1:
                raise BrandLockImmutableError("Brand Lock is immutable")
            transitioned = connection.execute(
                """
                UPDATE project_runs
                SET status = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    ProjectRunStatus.IN_PROGRESS.value,
                    confirmation_time.isoformat(),
                    str(run_id),
                    ProjectRunStatus.AWAITING_BRAND_LOCK.value,
                ),
            )
            if transitioned.rowcount != 1:
                raise InvalidRunStateError("run is not awaiting Brand Lock")
        return BrandLockConfirmationRecord(validated, confirmation_time)

    def record_failure(
        self,
        run_id: UUID | str,
        status: ProjectRunStatus,
        code: str,
    ) -> ProjectRun:
        if status not in {ProjectRunStatus.BLOCKED, ProjectRunStatus.FAILED}:
            raise ValueError("failure status must be blocked or failed")
        current = self.get(run_id)
        transitioned = current.with_status(status)
        values = transitioned.model_dump()
        values["warning_codes"] = (*current.warning_codes, code)
        updated = ProjectRun.model_validate(values)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE project_runs
                SET status = ?, warning_codes_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    updated.status.value,
                    json.dumps(updated.warning_codes, separators=(",", ":")),
                    updated.updated_at.isoformat(),
                    str(updated.id),
                ),
            )
        if cursor.rowcount != 1:
            raise ProjectRunNotFoundError(str(run_id))
        return updated
