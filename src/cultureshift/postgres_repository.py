from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from cultureshift.repository import SQLiteProjectRunRepository


def _postgres_sql(query: str) -> str:
    adapted = query.replace("?", "%s")
    if "INSERT INTO project_run_operations" in adapted and "RETURNING id" not in adapted:
        adapted = adapted.rstrip() + " RETURNING id"
    return adapted


class _PostgresCursor:
    def __init__(self, cursor: Any, *, lastrowid: int | None = None) -> None:
        self._cursor = cursor
        self.lastrowid = lastrowid

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()

    def __iter__(self):
        return iter(self._cursor)


class _PostgresConnection:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> _PostgresCursor:
        if query.strip().upper() == "BEGIN IMMEDIATE":
            # Serialize the small demo's state-transition transactions across instances.
            cursor = self._connection.execute("SELECT pg_advisory_xact_lock(2147483001)")
            return _PostgresCursor(cursor)
        adapted = _postgres_sql(query)
        cursor = self._connection.execute(adapted, parameters)
        if adapted.rstrip().endswith("RETURNING id"):
            row = cursor.fetchone()
            return _PostgresCursor(cursor, lastrowid=row["id"])
        return _PostgresCursor(cursor)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()


class PostgresProjectRunRepository(SQLiteProjectRunRepository):
    """PostgreSQL implementation preserving the validated repository behavior."""

    def __init__(self, database_url: str) -> None:
        if not database_url.startswith(("postgresql://", "postgres://")):
            raise ValueError("PostgreSQL connection URL is required")
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("PostgreSQL driver is unavailable") from error
        self._database_url = database_url
        self._psycopg = psycopg
        self._integrity_error = psycopg.IntegrityError

    @contextmanager
    def _connect(self) -> Iterator[_PostgresConnection]:
        from psycopg.rows import dict_row

        raw = self._psycopg.connect(self._database_url, row_factory=dict_row)
        connection = _PostgresConnection(raw)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        statements = (
            """
            CREATE TABLE IF NOT EXISTS project_runs (
                id TEXT PRIMARY KEY,
                direction TEXT NOT NULL,
                status TEXT NOT NULL,
                warning_codes_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS project_run_contexts (
                run_id TEXT PRIMARY KEY REFERENCES project_runs(id) ON DELETE CASCADE,
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
            """,
            """
            CREATE TABLE IF NOT EXISTS project_run_revisions (
                run_id TEXT PRIMARY KEY REFERENCES project_runs(id) ON DELETE CASCADE,
                result_version INTEGER NOT NULL CHECK(result_version = 2),
                requested_changes_json TEXT NOT NULL,
                feedback_digest TEXT NOT NULL,
                creative_brief_json TEXT NOT NULL,
                ad_copy_json TEXT NOT NULL,
                fact_references_json TEXT NOT NULL,
                rule_ids_json TEXT NOT NULL,
                composition_json TEXT NOT NULL,
                critique_json TEXT NOT NULL,
                revised_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS project_run_operations (
                id BIGSERIAL PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES project_runs(id) ON DELETE CASCADE,
                operation_kind TEXT NOT NULL CHECK(operation_kind IN ('feedback', 'retry')),
                idempotency_key_digest TEXT NOT NULL,
                request_fingerprint TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN (
                    'in_progress', 'succeeded', 'failed_retryable', 'failed_final'
                )),
                requested_changes_json TEXT,
                feedback_digest TEXT,
                retry_condition TEXT,
                retry_action TEXT,
                public_response_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(run_id, operation_kind, idempotency_key_digest)
            )
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_feedback_per_run
            ON project_run_operations (run_id)
            WHERE operation_kind = 'feedback' AND state = 'in_progress'
            """,
        )
        with self._connect() as connection:
            for statement in statements:
                connection.execute(statement)
