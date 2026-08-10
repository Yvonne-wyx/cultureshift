from fastapi.testclient import TestClient

from cultureshift.app import create_app


def test_application_starts_and_reports_readiness() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
