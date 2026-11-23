import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_returns_the_public_contract(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "FraudGuard AI",
        "version": "0.1.0",
    }
    assert response.headers["content-type"] == "application/json"


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
def test_local_frontend_can_read_health(client, origin):
    response = client.get("/health", headers={"Origin": origin})

    assert response.headers.get("access-control-allow-origin") == origin


def test_unlisted_origin_has_no_cors_permission(client):
    response = client.get("/health", headers={"Origin": "https://example.org"})

    assert "access-control-allow-origin" not in response.headers


def test_local_cors_preflight(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_health_is_read_only(client):
    assert client.post("/health").status_code == 405
