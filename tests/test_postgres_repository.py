from pathlib import Path

import pytest

from cultureshift.app import _repository_from_environment
from cultureshift.postgres_repository import _postgres_sql
from cultureshift.repository import SQLiteProjectRunRepository


def test_postgres_sql_adapts_parameters_and_operation_identity() -> None:
    query = "INSERT INTO project_run_operations (run_id, state) VALUES (?, ?)"

    assert _postgres_sql(query) == (
        "INSERT INTO project_run_operations (run_id, state) VALUES (%s, %s) RETURNING id"
    )
    assert _postgres_sql("SELECT * FROM project_runs WHERE id = ?") == (
        "SELECT * FROM project_runs WHERE id = %s"
    )


def test_local_repository_remains_sqlite(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("CULTURESHIFT_DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.setenv("CULTURESHIFT_SQLITE_PATH", str(tmp_path / "runs.sqlite3"))

    repository = _repository_from_environment()

    assert isinstance(repository, SQLiteProjectRunRepository)
    assert repository._database == Path(tmp_path / "runs.sqlite3")


def test_vercel_never_silently_falls_back_to_sqlite(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("CULTURESHIFT_DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)

    with pytest.raises(RuntimeError, match="CULTURESHIFT_DATABASE_URL or POSTGRES_URL is required"):
        _repository_from_environment()


def test_vercel_accepts_supabase_postgres_url(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("CULTURESHIFT_DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_URL", "postgresql://user:password@localhost/database")

    repository = _repository_from_environment()

    assert repository._database_url == "postgresql://user:password@localhost/database"
