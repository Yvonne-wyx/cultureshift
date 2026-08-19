from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

from cultureshift.contracts import AdAnalysis, RunCreate
from cultureshift.domain import ProjectRun, ProjectRunStatus, utc_now


class ProjectRunNotFoundError(LookupError):
    pass


class DuplicateProjectRunError(ValueError):
    pass


class SQLiteProjectRunRepository:
    """SQLite storage for non-sensitive ProjectRun state only."""

    def __init__(self, database: str | Path) -> None:
        self._database = Path(database)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database)
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
                    repair_attempted INTEGER NOT NULL DEFAULT 0
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

    def get(self, run_id: UUID | str) -> ProjectRun:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, direction, status, warning_codes_json, created_at, updated_at
                FROM project_runs
                WHERE id = ?
                """,
                (str(run_id),),
            ).fetchone()
        if row is None:
            raise ProjectRunNotFoundError(str(run_id))
        values = dict(row)
        values["warning_codes"] = json.loads(values.pop("warning_codes_json"))
        return ProjectRun.model_validate(values)

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
