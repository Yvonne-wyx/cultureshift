import sqlite3

from fastapi.testclient import TestClient

from cultureshift.app import create_app
from cultureshift.capability_tokens import CapabilityTokenService
from cultureshift.repository import SQLiteProjectRunRepository


def make_client(tmp_path) -> tuple[TestClient, SQLiteProjectRunRepository]:
    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    return TestClient(create_app(repository=repository, token_service=tokens)), repository


def test_health_contracts_and_openapi(tmp_path) -> None:
    client, _ = make_client(tmp_path)
    with client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/healthz").json() == {"status": "ok"}
        openapi = client.get("/openapi.json").json()
    assert "RunCreate" in openapi["components"]["schemas"]
    assert "RunCreated" in openapi["components"]["schemas"]


def test_create_run_returns_one_time_token_without_persisting_it(
    tmp_path, valid_run_payload
) -> None:
    client, repository = make_client(tmp_path)
    with client:
        response = client.post("/api/v1/runs", json=valid_run_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert len(body["capability_token"]) >= 16
    assert repository.get(body["run_id"]).direction.value == "china_to_uk"

    with sqlite3.connect(tmp_path / "runs.sqlite3") as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(project_runs)")}
    assert "capability_token" not in columns


def test_create_run_rejects_live_and_unknown_input(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    invalid = {**valid_run_payload, "execution_mode": "live", "private_note": "do not echo"}
    with client:
        response = client.post("/api/v1/runs", json=invalid)
    assert response.status_code == 422
    assert "do not echo" not in response.text


def test_create_run_does_not_echo_unknown_field_locations(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    private_key = r"C:\private\source.png"
    with client:
        response = client.post("/api/v1/runs", json={**valid_run_payload, private_key: "x"})
    assert response.status_code == 422
    assert private_key not in response.json()["detail"][0]["loc"]
    assert private_key not in response.text


def test_create_run_returns_generic_error_without_exception_text(
    tmp_path, valid_run_payload
) -> None:
    class FailingRepository(SQLiteProjectRunRepository):
        def create(self, run):
            raise RuntimeError("private repository detail")

    repository = FailingRepository(tmp_path / "runs.sqlite3")
    tokens = CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with TestClient(create_app(repository=repository, token_service=tokens)) as client:
        response = client.post("/api/v1/runs", json=valid_run_payload)
    assert response.status_code == 500
    assert response.json() == {"detail": {"code": "run_creation_failed"}}
    assert "private repository detail" not in response.text


def test_token_failure_returns_generic_error_without_orphan_run(
    tmp_path, valid_run_payload
) -> None:
    class FailingTokenService(CapabilityTokenService):
        def issue(self, **kwargs):
            raise RuntimeError("private token detail")

    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = FailingTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with TestClient(create_app(repository=repository, token_service=tokens)) as client:
        response = client.post("/api/v1/runs", json=valid_run_payload)

    assert response.status_code == 500
    assert response.json() == {"detail": {"code": "run_creation_failed"}}
    assert "private token detail" not in response.text
    with sqlite3.connect(tmp_path / "runs.sqlite3") as connection:
        count = connection.execute("SELECT COUNT(*) FROM project_runs").fetchone()[0]
    assert count == 0


def test_invalid_token_value_returns_generic_error_without_orphan_run(
    tmp_path, valid_run_payload
) -> None:
    class InvalidTokenService(CapabilityTokenService):
        def issue(self, **kwargs):
            return "short"

    repository = SQLiteProjectRunRepository(tmp_path / "runs.sqlite3")
    tokens = InvalidTokenService(secret=b"a" * 32, audience="cultureshift-api")
    with TestClient(create_app(repository=repository, token_service=tokens)) as client:
        response = client.post("/api/v1/runs", json=valid_run_payload)

    assert response.status_code == 500
    assert response.json() == {"detail": {"code": "run_creation_failed"}}
    with sqlite3.connect(tmp_path / "runs.sqlite3") as connection:
        count = connection.execute("SELECT COUNT(*) FROM project_runs").fetchone()[0]
    assert count == 0
