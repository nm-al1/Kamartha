import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app(Settings(environment="test", database_url=None, _env_file=None))) as value:
        yield value


def test_me_without_session_is_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_forged_session_with_no_configured_database_fails_closed(client):
    client.cookies.set("kamartha_session", "forged")
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 503
    assert "DATABASE_URL" not in response.text


@pytest.mark.parametrize("path", ["setup", "login"])
def test_public_mutations_reject_missing_or_foreign_origin(client, path):
    for headers in ({}, {"Origin": "https://attacker.invalid"}):
        response = client.post(f"/api/v1/auth/{path}", json={}, headers=headers)
        assert response.status_code == 403


@pytest.mark.parametrize("path", ["logout", "change-password"])
def test_session_mutations_require_authentication(client, path):
    response = client.post(
        f"/api/v1/auth/{path}", json={}, headers={"Origin": "http://localhost:8080"},
    )
    assert response.status_code == 401


def test_validation_errors_never_echo_password(client):
    response = client.post(
        "/api/v1/auth/login", headers={"Origin": "http://localhost:8080"},
        json={"username": "x", "password": "never-echo-this"},
    )
    assert response.status_code == 422
    assert "never-echo-this" not in response.text
