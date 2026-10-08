from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoints_report_ready():
    assert client.get("/health/live").json() == {"status": "ok"}
    readiness = client.get("/health/ready")
    assert readiness.status_code == 200
    assert readiness.json()["registered_tools"] == 2


def test_invalid_task_is_rejected_before_execution():
    response = client.post("/api/runs", json={"task": "short"})
    assert response.status_code == 422


def test_missing_run_returns_not_found():
    response = client.get("/api/runs/AO-MISSING")
    assert response.status_code == 404
