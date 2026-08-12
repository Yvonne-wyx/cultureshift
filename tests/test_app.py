import sqlite3
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cultureshift.app import create_app
from cultureshift.capability_tokens import Capability, CapabilityTokenService
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


def create_run(client: TestClient, valid_run_payload) -> tuple[str, str]:
    response = client.post("/api/v1/runs", json=valid_run_payload)
    assert response.status_code == 201
    body = response.json()
    return body["run_id"], body["capability_token"]


def test_get_run_returns_public_snapshot_for_read_capability(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, token = create_run(client, valid_run_payload)
        response = client.get(
            f"/api/v1/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "run_id": run_id,
        "direction": "china_to_uk",
        "status": "pending",
        "warning_codes": [],
        "created_at": response.json()["created_at"],
        "updated_at": response.json()["updated_at"],
    }
    assert token not in response.text
    assert "capability_token" not in response.text


@pytest.mark.parametrize("authorization", [None, "Basic private-value", "Bearer malformed"])
def test_get_run_rejects_missing_or_malformed_authorization_without_echo(
    tmp_path, valid_run_payload, authorization
) -> None:
    client, _ = make_client(tmp_path)
    with client:
        run_id, _ = create_run(client, valid_run_payload)
        headers = {} if authorization is None else {"Authorization": authorization}
        response = client.get(f"/api/v1/runs/{run_id}", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "invalid_capability"}}
    if authorization:
        assert authorization not in response.text


def test_get_run_rejects_expired_wrong_audience_and_wrong_scope_tokens(
    tmp_path, valid_run_payload
) -> None:
    client, _ = make_client(tmp_path)
    now = datetime.now(UTC)
    with client:
        run_id, _ = create_run(client, valid_run_payload)
        tokens = [
            CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api").issue(
                subject=run_id,
                capabilities={Capability.READ_PROJECT_RUN},
                ttl=timedelta(seconds=1),
                now=now - timedelta(seconds=2),
            ),
            CapabilityTokenService(secret=b"a" * 32, audience="other-api").issue(
                subject=run_id,
                capabilities={Capability.READ_PROJECT_RUN},
                ttl=timedelta(minutes=5),
            ),
            CapabilityTokenService(secret=b"a" * 32, audience="cultureshift-api").issue(
                subject=run_id,
                capabilities={Capability.UPDATE_PROJECT_RUN},
                ttl=timedelta(minutes=5),
            ),
        ]
        responses = [
            client.get(
                f"/api/v1/runs/{run_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            for token in tokens
        ]

    for response, token in zip(responses, tokens, strict=True):
        assert response.status_code == 401
        assert response.json() == {"detail": {"code": "invalid_capability"}}
        assert token not in response.text


def test_get_run_isolates_subject_and_missing_run(tmp_path, valid_run_payload) -> None:
    client, _ = make_client(tmp_path)
    with client:
        first_id, first_token = create_run(client, valid_run_payload)
        second_id, second_token = create_run(client, valid_run_payload)
        mismatch = client.get(
            f"/api/v1/runs/{second_id}",
            headers={"Authorization": f"Bearer {first_token}"},
        )
        missing_id = str(uuid4())
        missing_token = CapabilityTokenService(
            secret=b"a" * 32, audience="cultureshift-api"
        ).issue(
            subject=missing_id,
            capabilities={Capability.READ_PROJECT_RUN},
            ttl=timedelta(minutes=5),
        )
        absent = client.get(
            f"/api/v1/runs/{missing_id}",
            headers={"Authorization": f"Bearer {missing_token}"},
        )

    assert first_id != second_id
    assert second_token not in mismatch.text
    assert mismatch.status_code == 403
    assert mismatch.json() == {"detail": {"code": "capability_subject_mismatch"}}
    assert absent.status_code == 404
    assert absent.json() == {"detail": {"code": "run_not_found"}}


def test_run_recovery_survives_restart_with_same_database_and_secret(
    tmp_path, valid_run_payload
) -> None:
    database = tmp_path / "runs.sqlite3"
    first_tokens = CapabilityTokenService(secret=b"s" * 32, audience="cultureshift-api")
    first_app = create_app(
        repository=SQLiteProjectRunRepository(database), token_service=first_tokens
    )
    with TestClient(first_app) as first_client:
        run_id, token = create_run(first_client, valid_run_payload)

    second_tokens = CapabilityTokenService(secret=b"s" * 32, audience="cultureshift-api")
    second_app = create_app(
        repository=SQLiteProjectRunRepository(database), token_service=second_tokens
    )
    with TestClient(second_app) as second_client:
        recovered = second_client.get(
            f"/api/v1/runs/{run_id}", headers={"Authorization": f"Bearer {token}"}
        )
    assert recovered.status_code == 200
    assert recovered.json()["run_id"] == run_id

    different_tokens = CapabilityTokenService(secret=b"x" * 32, audience="cultureshift-api")
    different_app = create_app(
        repository=SQLiteProjectRunRepository(database), token_service=different_tokens
    )
    with TestClient(different_app) as different_client:
        rejected = different_client.get(
            f"/api/v1/runs/{run_id}", headers={"Authorization": f"Bearer {token}"}
        )
    assert rejected.status_code == 401

    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(project_runs)")}
    assert not {"token", "capability_token", "secret"} & columns


def test_default_app_requires_non_secret_environment_configuration(monkeypatch) -> None:
    monkeypatch.delenv("CULTURESHIFT_CAPABILITY_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="CULTURESHIFT_CAPABILITY_SECRET") as missing:
        create_app()
    assert "secret=" not in str(missing.value)

    private_value = "private-short-value"
    monkeypatch.setenv("CULTURESHIFT_CAPABILITY_SECRET", private_value)
    with pytest.raises(RuntimeError, match="32 UTF-8 bytes") as short:
        create_app()
    assert private_value not in str(short.value)
