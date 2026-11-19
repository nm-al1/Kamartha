import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.modules.auth import router as auth_router
from app.modules.auth import service as auth_service

pytestmark = pytest.mark.integration


def test_production_seed_has_six_packages_and_no_manager(migrated_connection):
    db = migrated_connection
    assert db.scalar(text("SELECT count(*) FROM kamartha.packages")) == 6
    assert db.scalar(text("SELECT count(*) FROM kamartha.managers")) == 0
    assert db.scalar(text("SELECT count(*) FROM kamartha.rooms")) == 0


def test_future_functions_are_not_publicly_executable(migrated_connection):
    db = migrated_connection
    db.execute(text('CREATE FUNCTION kamartha.audit_probe() RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$'))
    assert not db.scalar(text(
        "SELECT has_function_privilege('public', 'kamartha.audit_probe()', 'EXECUTE')"))


def test_singleton_manager_constraint(migrated_connection):
    db = migrated_connection
    db.execute(text("""
        INSERT INTO kamartha.managers(username,username_normalized,password_hash)
        VALUES ('owner','owner','not-an-authentication-test')
    """))
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(text("""
            INSERT INTO kamartha.managers(username,username_normalized,password_hash)
            VALUES ('other','other','not-an-authentication-test')
        """))


def test_setup_login_reload_csrf_and_logout(migrated_connection, monkeypatch):
    def session_for_request(request):
        return Session(migrated_connection, join_transaction_mode="create_savepoint")

    monkeypatch.setattr(auth_router, "open_session", session_for_request)
    monkeypatch.setattr(auth_service, "open_session", session_for_request)
    from app.modules.residents import router as resident_router
    monkeypatch.setattr(resident_router, 'open_session', session_for_request)
    settings = Settings(
        environment="test", _env_file=None, database_url=None,
        setup_code_hash=hash_password("private setup code for test"),
        ip_hash_secret="test-only-secret-with-at-least-32-characters",
    )
    origin = {"Origin": settings.app_origin}
    password = "password phrase for integration test"
    with TestClient(create_app(settings)) as client:
        csrf = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
        response = client.post("/api/v1/auth/setup", headers={**origin, "X-CSRF-Token": csrf}, json={
            "username": "owner", "password": password, "password_confirmation": password,
            "setup_code": "private setup code for test",
        })
        assert response.status_code == 201, response.text
        csrf = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
        response = client.post("/api/v1/auth/login", headers={**origin, "X-CSRF-Token": csrf},
                               json={"username": "OWNER", "password": password})
        assert response.status_code == 200, response.text
        assert client.get("/api/v1/auth/me").status_code == 200
        resident = {'name': 'Andi', 'identity_type': 'Paspor', 'identity_number': 'TEST123'}
        assert client.post('/api/v1/residents', json=resident, headers=origin).status_code == 403
        from uuid import uuid4
        headers = {**origin, 'X-CSRF-Token': response.json()['data']['csrf_token'], 'Idempotency-Key': str(uuid4())}
        created = client.post('/api/v1/residents', json=resident, headers=headers)
        assert created.status_code == 201, created.text
        resident_id = created.json()['data']['id']
        assert client.get(f'/api/v1/residents/{resident_id}').json()['data']['name'] == 'Andi'
        listing = client.get('/api/v1/residents?q=Andi&limit=1').json()['data']
        assert listing['pagination']['total'] == 1
        assert listing['items'][0]['id'] == resident_id
        assert client.post('/api/v1/residents', json=resident, headers={**headers, 'Idempotency-Key': str(uuid4())}).status_code == 409
        updated = client.patch(f'/api/v1/residents/{resident_id}', json={**resident, 'name': 'Andi Baru'}, headers=headers)
        assert updated.status_code == 200, updated.text
        assert updated.json()['data']['name'] == 'Andi Baru'
        assert client.post("/api/v1/auth/logout", headers=origin).status_code == 403
        login_csrf = response.json()["data"]["csrf_token"]
        fresh_csrf = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
        assert fresh_csrf == login_csrf
        assert client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"] == login_csrf
        assert client.post("/api/v1/auth/logout", headers={**origin, "X-CSRF-Token": fresh_csrf}).status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 401
        client.cookies.set('kamartha_session', 'expired-or-forged', domain='testserver.local', path='/')
        recovery = client.get('/api/v1/auth/csrf')
        assert recovery.status_code == 200
        assert recovery.json()['data']['setup_available'] is False
        csrf = recovery.json()['data']['csrf_token']
        response = client.post('/api/v1/auth/login', headers={**origin, 'X-CSRF-Token': csrf},
                               json={'username': 'owner', 'password': password})
        assert response.status_code == 200
        assert client.get('/api/v1/auth/me').json()['data']['mode'] == 'PREPARATION'
        csrf = client.get('/api/v1/auth/csrf').json()['data']['csrf_token']
        new_password = 'a different integration password phrase'
        response = client.post('/api/v1/auth/change-password', headers={**origin, 'X-CSRF-Token': csrf},
                               json={'old_password': password, 'password': new_password,
                                     'password_confirmation': new_password})
        assert response.status_code == 200
        assert client.get('/api/v1/auth/me').status_code == 401


def test_idempotency_replay_and_conflict(migrated_connection):
    from uuid import uuid4
    from app.core.idempotency import remember, replay
    from app.core.errors import AppError
    from app.db.session import lock_business

    db = Session(migrated_connection, join_transaction_mode='create_savepoint')
    with db, db.begin():
        lock_business(db)
        manager = db.execute(text('''
            INSERT INTO kamartha.managers(username, username_normalized, password_hash)
            VALUES ('owner', 'owner', 'test-only') RETURNING id
        ''')).scalar_one()
        key = uuid4()
        assert replay(db, manager, 'test', key, {'amount': 100}) is None
        remember(db, manager, 'test', key, {'amount': 100}, {'id': 'result'})
        assert replay(db, manager, 'test', key, {'amount': 100})['response_data'] == {'id': 'result'}
        with pytest.raises(AppError) as error:
            replay(db, manager, 'test', key, {'amount': 200})
        assert error.value.status == 409
