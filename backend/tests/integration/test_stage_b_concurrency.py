"""Concurrency checks that need committed schema and independent connections.

The other integration tests deliberately run inside one rolled-back transaction.
That cannot exercise row-lock contention, so this module migrates a dedicated
throwaway test database, commits it, and removes every object it created.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from app.core.clock import BusinessClock
from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
def live_database(monkeypatch):
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('TEST_DATABASE_URL belum tersedia; bukan bukti integrasi lulus.')
    if os.environ.get('CONFIRM_ISOLATED_TEST_DATABASE') != 'yes':
        pytest.fail('Set CONFIRM_ISOLATED_TEST_DATABASE=yes hanya untuk database uji terisolasi.')
    database = make_url(url).database or ''
    if not database.endswith('_test'):
        pytest.fail('Tes konkurensi hanya boleh memakai database uji berakhiran _test.')
    monkeypatch.setenv('MIGRATION_DATABASE_URL', url)
    engine = create_engine(url, poolclass=NullPool, hide_parameters=True)
    with engine.connect() as connection:
        if connection.scalar(text("SELECT to_regnamespace('kamartha')")) is not None:
            pytest.fail('Database uji sudah memiliki schema kamartha; tes tidak akan menimpa data.')
        if connection.scalar(text("SELECT to_regclass('public.alembic_version')")) is not None:
            pytest.fail('Database uji masih menyimpan alembic_version; bersihkan sebelum menjalankan tes.')
        config = Config(str(Path(__file__).parents[2] / 'alembic.ini'))
        config.attributes['connection'] = connection
        command.upgrade(config, 'head')
        connection.commit()
    try:
        yield url
    finally:
        engine.dispose()
        with engine.connect() as connection:
            connection.execute(text('DROP SCHEMA IF EXISTS kamartha CASCADE'))
            connection.execute(text('DROP TABLE IF EXISTS public.alembic_version'))
            connection.commit()
        engine.dispose()


@pytest.fixture
def api(live_database):
    engine = create_engine(live_database, poolclass=NullPool, hide_parameters=True)
    with engine.begin() as connection:
        connection.execute(text('''
            INSERT INTO kamartha.managers(username,username_normalized,password_hash,password_changed_at)
            VALUES ('admin','admin',:hash,'2026-01-01T00:00:00Z')
        '''), {'hash': hash_password('DemoPass2026!')})
    engine.dispose()
    settings = Settings(environment='test', database_url=live_database, _env_file=None,
                        ip_hash_secret='test-only-secret-at-least-32-characters')
    clock = BusinessClock(lambda: datetime(2026, 3, 1, tzinfo=timezone.utc))
    app = create_app(settings, clock=clock)
    with TestClient(app) as client:
        token = client.get('/api/v1/auth/csrf').json()['data']['csrf_token']
        login = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'DemoPass2026!'},
                            headers={'Origin': settings.app_origin, 'X-CSRF-Token': token})
        assert login.status_code == 200, login.text
        client.headers.update({'Origin': settings.app_origin,
                               'X-CSRF-Token': login.json()['data']['csrf_token'],
                               'Idempotency-Key': str(uuid4())})
        yield client


def build_draft(api):
    room = api.post('/api/v1/rooms', json={'number': 'A1', 'room_type': 'Standar',
                                           'supported_occupants': 2, 'reference_price': 500000})
    assert room.status_code == 201, room.text
    resident = api.post('/api/v1/residents', json={'name': 'Andi', 'identity_type': 'Paspor',
                                                   'identity_number': 'TEST01'})
    assert resident.status_code == 201, resident.text
    settings = api.get('/api/v1/initialization/settings').json()['data']
    saved = api.put('/api/v1/initialization/settings',
                    json={'cutover_date': '2026-03-01', 'expected_version': settings['version']})
    assert saved.status_code == 200, saved.text
    package = next(p for p in settings['packages']
                   if p['occupant_type'] == 1 and p['period_months'] == 1)
    resident_id = resident.json()['data']['id']
    return {'room_id': room.json()['data']['id'], 'package_id': package['id'],
            'starts_on': '2026-01-31', 'ends_on': '2026-03-31', 'price': 500000,
            'responsible_resident_id': resident_id,
            'occupancies': [{'resident_id': resident_id, 'entered_on': '2026-01-31', 'state': 'STAYING'}],
            'invoices': [{'period_start': '2026-02-28', 'due_on': '2026-02-28',
                          'amount': 500000, 'opening_paid': 500000}]}


def prepare_finalization(api):
    data = build_draft(api)
    created = api.post('/api/v1/initialization/records',
                       json={'client_record_key': str(uuid4()), 'draft_data': data})
    assert created.status_code == 201, created.text
    summary = api.get('/api/v1/initialization/reconciliation').json()['data']
    assert summary['can_finalize'], summary['errors']
    payload = {'expected_version': summary['version'],
               'reconciliation_hash': summary['reconciliation_hash'],
               'confirmed_matches': True, 'confirmed_old_periods_settled': True}
    return payload


def finalize(api, payload, key):
    return api.post('/api/v1/initialization/finalize', json=payload,
                    headers={'Idempotency-Key': key})


def counts(api):
    with api.app.state.engine.connect() as db:
        return {name: db.scalar(text(f'SELECT count(*) FROM kamartha.{name}'))
                for name in ['initialization_finalizations', 'leases', 'occupancies',
                             'invoices', 'responsible_history', 'payments']}


def test_simultaneous_finalize_requests_materialize_once(api):
    payload = prepare_finalization(api)
    keys = [str(uuid4()), str(uuid4())]
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda key: finalize(api, payload, key), keys))
    codes = sorted(response.status_code for response in responses)
    assert codes == [200, 409], [(r.status_code, r.text) for r in responses]
    rejected = next(r for r in responses if r.status_code == 409)
    assert rejected.json()['error']['code'] == 'MODE_REJECTED'
    assert counts(api) == {'initialization_finalizations': 1, 'leases': 1, 'occupancies': 1,
                           'invoices': 1, 'responsible_history': 1, 'payments': 0}
    with api.app.state.engine.connect() as db:
        assert db.scalar(text('SELECT mode FROM kamartha.app_settings WHERE id=1')) == 'ACTIVE'


def test_simultaneous_replay_with_same_key_returns_one_result(api):
    payload = prepare_finalization(api)
    key = str(uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: finalize(api, payload, key), range(2)))
    assert [r.status_code for r in responses] == [200, 200], [r.text for r in responses]
    assert responses[0].json()['data'] == responses[1].json()['data']
    assert counts(api)['initialization_finalizations'] == 1
    assert counts(api)['leases'] == 1


def test_two_writes_with_same_session_csrf_token_both_succeed(api):
    token = api.headers['X-CSRF-Token']
    assert api.get('/api/v1/auth/csrf').json()['data']['csrf_token'] == token

    def create(index):
        return api.post('/api/v1/residents', headers={'Idempotency-Key': str(uuid4())},
                        json={'name': f'Concurrent {index}', 'identity_type': 'Paspor',
                              'identity_number': f'CONC{index}'})

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(create, range(2)))
    assert [r.status_code for r in responses] == [201, 201], [r.text for r in responses]
    assert {r.json()['data']['name'] for r in responses} == {'Concurrent 0', 'Concurrent 1'}
    assert api.get('/api/v1/auth/csrf').json()['data']['csrf_token'] == token


def test_concurrent_draft_creation_with_same_key_stores_one_record(api):
    data = build_draft(api)
    body = {'client_record_key': str(uuid4()), 'draft_data': data}
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: api.post('/api/v1/initialization/records', json=body), range(2)))
    assert [r.status_code for r in responses] == [201, 201], [r.text for r in responses]
    assert responses[0].json()['data']['id'] == responses[1].json()['data']['id']
    with api.app.state.engine.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM kamartha.initialization_records')) == 1
        assert db.scalar(text('''SELECT count(*) FROM kamartha.idempotency_records
                                 WHERE scope='initialization.create' ''')) == 1
