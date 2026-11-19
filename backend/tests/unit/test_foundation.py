from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.clock import BusinessClock
from app.core.security import hash_password, verify_password, token_hash, new_token
from app.main import create_app


def test_clock_uses_wita_at_utc_day_boundary():
    clock = BusinessClock(lambda: datetime(2026, 10, 30, 17, tzinfo=timezone.utc))
    assert clock.today().isoformat() == "2026-10-31"


def test_password_hash_and_wrong_password():
    password = "frasa sandi aman untuk pengelola"
    hashed = hash_password(password)
    assert hashed.startswith("$argon2id$")
    assert password not in hashed
    assert verify_password(password, hashed)
    assert not verify_password("password salah", hashed)


@pytest.mark.parametrize("password", ["a" * 7, "a" * 129])
def test_password_length(password):
    with pytest.raises(ValueError):
        hash_password(password)


@pytest.mark.parametrize('password', ['a' * 8, 'a' * 128])
def test_password_length_boundaries_accepted(password):
    assert verify_password(password, hash_password(password))


def test_opaque_tokens_are_random_and_only_hash_is_stored():
    first, second = new_token(), new_token()
    assert first != second
    assert len(first) >= 43
    assert len(token_hash(first)) == 64
    assert token_hash(first) != first


def test_health_requires_no_database_and_hides_configuration():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["data"] == {"status": "ok"}
        assert response.json()["request_id"] == response.headers["x-request-id"]
        assert response.headers["cache-control"] == "no-store"
        assert "database" not in response.text.lower()


def test_not_found_has_standard_error_envelope():
    with TestClient(create_app()) as client:
        response = client.get("/missing")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
        assert response.json()["request_id"]


def test_production_documentation_is_not_public():
    from app.core.config import Settings

    settings = Settings(environment="production", app_profile="supabase",
                        app_origin="https://kos.example",
                        database_url=(
                            "postgresql+psycopg://kamartha_runtime:pw@example.test:5432/kamartha"
                            "?sslmode=require"),
                        _env_file=None,
                        supabase_url="https://storage.example.test",
                        supabase_service_key="test-only-storage-key")
    with TestClient(create_app(settings)) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_unhandled_errors_do_not_expose_secrets(caplog):
    app = create_app()

    @app.get("/test-error")
    def fail():
        raise RuntimeError("database password must not appear")

    with TestClient(app) as client:
        response = client.get("/test-error")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"
        assert "database password" not in response.text
        assert "database password" not in caplog.text
        assert response.headers["x-request-id"] in caplog.text
