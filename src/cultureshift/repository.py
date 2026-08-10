from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

from cultureshift.domain import ProjectRun, ProjectRunStatus


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

    def create(self, run: ProjectRun) -> ProjectRun:
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
        except sqlite3.IntegrityError as error:
            raise DuplicateProjectRunError(str(run.id)) from error
        return run

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
