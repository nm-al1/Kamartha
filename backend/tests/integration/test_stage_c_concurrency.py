"""Room and person allocation races use committed schema and independent connections."""
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
from sqlalchemy.orm import Session
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
        manager = connection.scalar(text('''
            INSERT INTO kamartha.managers(username,username_normalized,password_hash,password_changed_at)
            VALUES ('admin','admin',:hash,'2026-01-01T00:00:00Z') RETURNING id
        '''), {'hash': hash_password('DemoPass2026!')})
        connection.execute(text("""
            UPDATE kamartha.app_settings SET mode='ACTIVE',cutover_date=DATE '2026-03-01',
                finalized_at=now(),finalized_by=:manager WHERE id=1
        """), {'manager': manager})
    engine.dispose()
    settings = Settings(environment='test', database_url=live_database, _env_file=None,
                        ip_hash_secret='test-only-secret-at-least-32-characters')
    clock = BusinessClock(lambda: datetime(2026, 3, 20, tzinfo=timezone.utc))
    app = create_app(settings, clock=clock)
    with TestClient(app) as client:
        token = client.get('/api/v1/auth/csrf').json()['data']['csrf_token']
        login = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'DemoPass2026!'},
                            headers={'Origin': settings.app_origin, 'X-CSRF-Token': token})
        assert login.status_code == 200, login.text
        client.headers.update({'Origin': settings.app_origin,
                               'X-CSRF-Token': login.json()['data']['csrf_token']})
        yield client


def write(api, path, payload, key=None):
    return api.post(path, json=payload,
                    headers={'Idempotency-Key': key or str(uuid4())})


def setup(api):
    room = write(api, '/api/v1/rooms', {
        'number': 'A1', 'room_type': 'Standar', 'supported_occupants': 2,
        'reference_price': 500000,
    })
    first = write(api, '/api/v1/residents', {
        'name': 'Andi', 'identity_type': 'Paspor', 'identity_number': 'R001',
    })
    second = write(api, '/api/v1/residents', {
        'name': 'Budi', 'identity_type': 'Paspor', 'identity_number': 'R002',
    })
    packages = api.get('/api/v1/initialization/settings').json()['data']['packages']
    package_id = next(item['id'] for item in packages
                      if item['occupant_type'] == 2 and item['period_months'] == 1)
    return (room.json()['data']['id'], first.json()['data']['id'],
            second.json()['data']['id'], package_id)


def payload(room_id, package_id, residents):
    return {
        'room_id': room_id, 'package_id': package_id, 'starts_on': '2026-03-10',
        'periods': 1, 'price': 700000, 'resident_ids': residents,
        'responsible_resident_id': residents[0],
    }


def counts(api):
    with api.app.state.engine.connect() as db:
        return {name: db.scalar(text(f'SELECT count(*) FROM kamartha.{name}'))
                for name in ['leases', 'occupancies', 'invoices']}


def test_concurrent_reminder_workers_claim_only_one_delivery(api):
    from datetime import date
    from app.modules.reminders.service import run_reminders
    from test_whatsapp_reminders import Bridge

    room_id, andi, budi, package_id = setup(api)
    response = write(api, '/api/v1/leases', payload(room_id, package_id, [andi, budi]))
    assert response.status_code == 201, response.text
    engine = api.app.state.engine
    with engine.begin() as db:
        db.execute(text('UPDATE kamartha.residents SET whatsapp_number=:number WHERE id=:id'),
                   {'id': andi, 'number': '08111111111'})
    settings = Settings(_env_file=None, environment='test', whatsapp_enabled=True,
                        whatsapp_allowed_numbers='628111111111',
                        whatsapp_demo_invoice_ids=response.json()['data']['invoices'][0]['id'])
    bridge = Bridge()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run_reminders(
            lambda: Session(engine), settings, date(2026, 3, 10), bridge), range(2)))
    assert sum(result['sent'] for result in results) == 1
    assert sum(result['existing'] for result in results) == 1
    assert len(bridge.calls) == 1


def test_two_concurrent_contracts_for_one_room_create_exactly_one(api):
    room_id, andi, budi, package_id = setup(api)
    body = payload(room_id, package_id, [andi, budi])
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: write(api, '/api/v1/leases', body), range(2)))
    codes = sorted(response.status_code for response in responses)
    assert codes == [201, 409], [(r.status_code, r.text) for r in responses]
    assert counts(api) == {'leases': 1, 'occupancies': 2, 'invoices': 1}


def test_same_idempotency_key_replays_one_contract(api):
    room_id, andi, budi, package_id = setup(api)
    body = payload(room_id, package_id, [andi, budi])
    key = str(uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(
            lambda _: write(api, '/api/v1/leases', body, key=key), range(2)))
    assert [r.status_code for r in responses] == [201, 201], [r.text for r in responses]
    assert responses[0].json()['data']['id'] == responses[1].json()['data']['id']
    assert counts(api) == {'leases': 1, 'occupancies': 2, 'invoices': 1}
