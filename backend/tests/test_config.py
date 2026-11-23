import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


def test_environment_overrides_local_origins(monkeypatch):
    from app.core.config import Settings
    from app.main import create_app

    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:5199"]')
    settings = Settings(_env_file=None)
    with TestClient(create_app(settings)) as client:
        response = client.get("/health", headers={"Origin": "http://localhost:5199"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5199"
        blocked = client.get("/health", headers={"Origin": "http://localhost:5173"})
        assert "access-control-allow-origin" not in blocked.headers


@pytest.mark.parametrize("origin", ["*", "not-a-url", "http://localhost:5173/path", "ftp://localhost"])
def test_rejects_invalid_cors_origin(origin):
    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(cors_origins=[origin], _env_file=None)
