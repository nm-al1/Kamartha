from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.clock import BusinessClock
from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.modules.auth import router as auth_router, service as auth_service
from app.modules.initialization import router as init_router
from app.modules.leases import router as leases_router
from app.modules.residents import router as residents_router
from app.modules.rooms import router as rooms_router

pytestmark = pytest.mark.integration


@pytest.fixture
def api(migrated_connection, monkeypatch):
    def session(request):
        return Session(migrated_connection, join_transaction_mode='create_savepoint')
    for module in [auth_router, auth_service, rooms_router, residents_router,
                   init_router, leases_router]:
        monkeypatch.setattr(module, 'open_session', session)
    migrated_connection.execute(text('''
        INSERT INTO kamartha.managers(username,username_normalized,password_hash,password_changed_at)
        VALUES ('admin','admin',:hash,'2026-01-01T00:00:00Z')
    '''), {'hash': hash_password('DemoPass2026!')})
    manager_id = migrated_connection.scalar(text('SELECT id FROM kamartha.managers'))
    migrated_connection.execute(text("""
        UPDATE kamartha.app_settings SET mode='ACTIVE', cutover_date=DATE '2026-03-01',
            finalized_at=now(), finalized_by=:manager WHERE id=1
    """), {'manager': manager_id})
    settings = Settings(environment='test', database_url=None, _env_file=None,
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


def write(api, path, **kwargs):
    headers = {'Idempotency-Key': str(uuid4())}
    headers.update(kwargs.pop('headers', {}))
    return api.post(path, headers=headers, **kwargs)


def resident(api, name, number):
    response = write(api, '/api/v1/residents', json={
        'name': name, 'identity_type': 'Paspor', 'identity_number': number,
    })
    assert response.status_code == 201, response.text
    return response.json()['data']['id']


def room(api, number='A1', capacity=2):
    response = write(api, '/api/v1/rooms', json={
        'number': number, 'room_type': 'Standar', 'supported_occupants': capacity,
        'reference_price': 500000,
    })
    assert response.status_code == 201, response.text
    return response.json()['data']['id']


def package(api, occupants, months=1):
    packages = api.get('/api/v1/initialization/settings').json()['data']['packages']
    return next(p for p in packages
                if p['occupant_type'] == occupants and p['period_months'] == months)['id']


def create(api, *, room_id, package_id, residents, responsible,
           starts_on='2026-03-10', periods=1, price=700000):
    response = write(api, '/api/v1/leases', json={
        'room_id': room_id, 'package_id': package_id, 'starts_on': starts_on,
        'periods': periods, 'price': price, 'resident_ids': residents,
        'responsible_resident_id': responsible,
    })
    return response


def test_contract_creates_one_invoice_and_rejects_room_and_person_conflicts(api):
    room_id = room(api)
    andi, budi = resident(api, 'Andi', 'C001'), resident(api, 'Budi', 'C002')
    package_id = package(api, 2)
    created = create(api, room_id=room_id, package_id=package_id,
                     residents=[andi, budi], responsible=andi)
    assert created.status_code == 201, created.text
    data = created.json()['data']
    assert data['status'] == 'ACTIVE'
    assert len(data['occupancies']) == 2
    assert sum(1 for item in data['occupancies'] if item['responsible']) == 1
    assert len(data['invoices']) == 1
    invoice = data['invoices'][0]
    assert invoice['amount'] == 700000
    assert invoice['paid_total'] == 0
    assert invoice['remaining'] == 700000
    assert str(invoice['period_start']) == '2026-03-10'
    assert str(invoice['period_end']) == '2026-04-10'
    assert str(invoice['due_on']) == '2026-03-10'

    same_room = create(api, room_id=room_id, package_id=package_id,
                       residents=[andi, budi], responsible=andi)
    assert same_room.status_code == 409
    assert same_room.json()['error']['code'] == 'ROOM_CONFLICT'

    other_room = room(api, 'A2')
    same_person = create(api, room_id=other_room, package_id=package_id,
                         residents=[andi, budi], responsible=andi)
    assert same_person.status_code == 409
    assert same_person.json()['error']['code'] == 'PERSON_CONFLICT'

    wrong_count = create(api, room_id=other_room, package_id=package_id,
                         residents=[andi], responsible=andi)
    assert wrong_count.status_code == 422


def test_exit_non_responsible_keeps_contract_and_responsible_requires_successor(api):
    room_id = room(api)
    andi, budi = resident(api, 'Andi', 'C011'), resident(api, 'Budi', 'C012')
    package_id = package(api, 2)
    created = create(api, room_id=room_id, package_id=package_id,
                     residents=[andi, budi], responsible=andi).json()['data']
    lease_id = created['id']
    budi_occupancy = next(item['id'] for item in created['occupancies']
                          if item['resident_id'] == budi)
    andi_occupancy = next(item['id'] for item in created['occupancies']
                          if item['resident_id'] == andi)

    missing = write(api, f'/api/v1/leases/{lease_id}/occupancies/{andi_occupancy}/exit',
                       json={'exited_on': '2026-03-15', 'reason': 'Pindah kerja'})
    assert missing.status_code == 422
    assert missing.json()['error']['code'] == 'SUCCESSOR_REQUIRED'

    # The failed transaction must not have stored the partial exit.
    detail = api.get(f'/api/v1/leases/{lease_id}').json()['data']
    assert sum(1 for item in detail['occupancies'] if item['state'] == 'STAYING') == 2

    exited = write(api, f'/api/v1/leases/{lease_id}/occupancies/{andi_occupancy}/exit',
                      json={'exited_on': '2026-03-15', 'successor_resident_id': budi,
                            'reason': 'Pindah kerja'})
    assert exited.status_code == 200, exited.text
    after = exited.json()['data']
    assert sum(1 for item in after['occupancies'] if item['state'] == 'STAYING') == 1
    assert next(item for item in after['occupancies']
                if item['resident_id'] == budi)['responsible']
    assert len(after['invoices']) == 1
    assert after['invoices'][0]['amount'] == 700000

    closed = write(api, f'/api/v1/leases/{lease_id}/occupancies/{budi_occupancy}/exit',
                      json={'exited_on': '2026-03-20', 'reason': 'Selesai'})
    assert closed.status_code == 200, closed.text
    assert all(item['state'] == 'EXITED' for item in closed.json()['data']['occupancies'])


def test_last_exit_keeps_started_period_and_cancels_unpaid_future_period(api, migrated_connection):
    room_id = room(api)
    andi = resident(api, 'Andi', 'C021')
    package_id = package(api, 1)
    created = create(api, room_id=room_id, package_id=package_id,
                     residents=[andi], responsible=andi, periods=2).json()['data']
    lease_id, occupancy_id = created['id'], created['occupancies'][0]['id']
    future = migrated_connection.scalar(text("""
        INSERT INTO kamartha.invoices(lease_id,period_start,period_end,due_on,amount,source)
        VALUES (:lease,DATE '2026-04-10',DATE '2026-05-10',DATE '2026-04-10',700000,'OPERATIONAL')
        RETURNING id
    """), {'lease': lease_id})
    exited = write(api, f'/api/v1/leases/{lease_id}/occupancies/{occupancy_id}/exit',
                      json={'exited_on': '2026-03-20', 'reason': 'Selesai'})
    assert exited.status_code == 200, exited.text
    detail = exited.json()['data']
    statuses = {str(item['period_start']): item['status'] for item in detail['invoices']}
    assert statuses['2026-03-10'] == 'ACTIVE'
    assert statuses['2026-04-10'] == 'CANCELLED'
    assert detail['status'] == 'ENDED'

    room_id2 = room(api, 'A2')
    citra = resident(api, 'Citra', 'C022')
    paid_contract = create(api, room_id=room_id2, package_id=package_id,
                           residents=[citra], responsible=citra,
                           starts_on='2026-03-10').json()['data']
    paid_lease, paid_occupancy = paid_contract['id'], paid_contract['occupancies'][0]['id']
    manager = migrated_connection.scalar(text('SELECT id FROM kamartha.managers'))
    paid_invoice = migrated_connection.scalar(text("""
        INSERT INTO kamartha.invoices(lease_id,period_start,period_end,due_on,amount,source)
        VALUES (:lease,DATE '2026-04-10',DATE '2026-05-10',DATE '2026-04-10',700000,'OPERATIONAL')
        RETURNING id
    """), {'lease': paid_lease})
    payment = migrated_connection.scalar(text("""
        INSERT INTO kamartha.payments(lease_id,received_on,total_amount,method,recorded_by)
        VALUES (:lease,DATE '2026-03-20',700000,'CASH',:manager) RETURNING id
    """), {'lease': paid_lease, 'manager': manager})
    migrated_connection.execute(text("""
        INSERT INTO kamartha.payment_allocations(payment_id,invoice_id,lease_id,amount)
        VALUES (:payment,:invoice,:lease,700000)
    """), {'payment': payment, 'invoice': paid_invoice, 'lease': paid_lease})
    blocked = write(api, f'/api/v1/leases/{paid_lease}/occupancies/{paid_occupancy}/exit',
                       json={'exited_on': '2026-03-20', 'reason': 'Selesai'})
    assert blocked.status_code == 409
    assert blocked.json()['error']['code'] == 'PAID_PERIOD_CONFLICT'


def test_extension_checks_version_and_room_conflict(api):
    first_room = room(api)
    andi = resident(api, 'Andi', 'C031')
    budi = resident(api, 'Budi', 'C032')
    package_id = package(api, 1)
    created = create(api, room_id=first_room, package_id=package_id,
                     residents=[andi], responsible=andi, periods=2).json()['data']
    lease_id, version = created['id'], created['version']
    extended = write(api, f'/api/v1/leases/{lease_id}/extend',
                        json={'periods': 1, 'expected_version': version})
    assert extended.status_code == 200, extended.text
    assert str(extended.json()['data']['effective_ends_on']) == '2026-06-10'
    stale = write(api, f'/api/v1/leases/{lease_id}/extend',
                     json={'periods': 1, 'expected_version': version})
    assert stale.status_code == 409

    other_room = room(api, 'A3')
    blocking = create(api, room_id=other_room, package_id=package_id,
                      residents=[budi], responsible=budi,
                      starts_on='2026-04-10', periods=1)
    assert blocking.status_code == 201


def test_replacement_and_continuation_keep_history_and_create_new_contract(api):
    room_id = room(api)
    andi, budi, citra = (resident(api, 'Andi', 'C041'), resident(api, 'Budi', 'C042'),
                         resident(api, 'Citra', 'C043'))
    package_id = package(api, 2)
    created = create(api, room_id=room_id, package_id=package_id,
                     residents=[andi, budi], responsible=budi,
                     periods=2).json()['data']
    lease_id = created['id']
    andi_occupancy = next(item['id'] for item in created['occupancies']
                          if item['resident_id'] == andi)
    exited = write(api, f'/api/v1/leases/{lease_id}/occupancies/{andi_occupancy}/exit',
                      json={'exited_on': '2026-03-15', 'reason': 'Pindah'})
    assert exited.status_code == 200, exited.text
    replaced = write(api, f'/api/v1/leases/{lease_id}/occupancies', json={
        'resident_id': citra, 'entered_on': '2026-03-16',
        'predecessor_occupancy_id': andi_occupancy, 'reason': 'Pengganti',
    })
    assert replaced.status_code == 201, replaced.text
    detail = replaced.json()['data']
    assert sum(1 for item in detail['occupancies'] if item['state'] == 'STAYING') == 2
    assert next(item for item in detail['occupancies']
                if item['resident_id'] == budi)['responsible']

    api.app.state.clock = BusinessClock(lambda: datetime(2026, 5, 10, tzinfo=timezone.utc))
    csrf = api.get('/api/v1/auth/csrf').json()['data']['csrf_token']
    login = api.post('/api/v1/auth/login',
                     json={'username': 'admin', 'password': 'DemoPass2026!'},
                     headers={'X-CSRF-Token': csrf})
    assert login.status_code == 200, login.text
    api.headers['X-CSRF-Token'] = login.json()['data']['csrf_token']
    continued = write(api, f'/api/v1/leases/{lease_id}/continue', json={
        'package_id': package_id, 'starts_on': '2026-05-10', 'periods': 1,
        'price': 800000, 'resident_ids': [budi, citra],
        'responsible_resident_id': budi, 'reason': 'Lanjut kontrak',
    })
    assert continued.status_code == 201, continued.text
    new = continued.json()['data']
    assert new['id'] != lease_id
    assert str(new['starts_on']) == '2026-05-10'
    old = api.get(f'/api/v1/leases/{lease_id}').json()['data']
    states = {item['resident_id']: item['state'] for item in old['occupancies']}
    assert states[budi] == 'CONTINUED'
    assert states[citra] == 'CONTINUED'
    assert states[andi] == 'EXITED'
    assert len(new['invoices']) == 1
    assert new['invoices'][0]['amount'] == 800000


def test_future_continuation_leaves_current_occupancy_and_contact_unchanged(api, migrated_connection):
    room_id = room(api)
    andi = resident(api, 'Andi', 'C051')
    package_id = package(api, 1)
    old = create(api, room_id=room_id, package_id=package_id,
                 residents=[andi], responsible=andi).json()['data']
    response = write(api, f"/api/v1/leases/{old['id']}/continue", json={
        'package_id': package_id, 'starts_on': '2026-04-10', 'periods': 1,
        'price': 800000, 'resident_ids': [andi],
        'responsible_resident_id': andi, 'reason': 'Lanjut kontrak',
    })
    assert response.status_code == 422, response.text
    assert response.json()['error']['code'] == 'CONTINUE_INVALID'
    after = api.get(f"/api/v1/leases/{old['id']}").json()['data']
    assert after['occupancies'] == old['occupancies']
    assert after['invoices'] == old['invoices']
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.leases')) == 1
    assert migrated_connection.scalar(text("""
        SELECT count(*) FROM kamartha.business_events WHERE event_type='LEASE_CONTINUED'
    """)) == 0


def opening_contract(api, db, opening_paid):
    room_id = room(api)
    resident_id = resident(api, 'Penghuni lama', 'C061')
    package_id = package(api, 1)
    manager_id = db.scalar(text('SELECT id FROM kamartha.managers'))
    record_id = db.scalar(text("""
        INSERT INTO kamartha.initialization_records(client_record_key,draft_data,state,created_by)
        VALUES (:key,'{}'::jsonb,'FINALIZED',:manager) RETURNING id
    """), {'key': uuid4(), 'manager': manager_id})
    lease_id = db.scalar(text("""
        INSERT INTO kamartha.leases(room_id,package_id,starts_on,agreed_ends_on,effective_ends_on,
            period_anchor,occupant_type_snapshot,period_months_snapshot,period_price_snapshot,
            source,initialization_record_id,created_by)
        VALUES (:room,:package,'2026-02-10','2026-04-10','2026-04-10',
            '2026-02-10',1,1,700000,'OPENING',:record,:manager) RETURNING id
    """), {'room': room_id, 'package': package_id, 'record': record_id, 'manager': manager_id})
    occupancy_id = db.scalar(text("""
        INSERT INTO kamartha.occupancies(lease_id,resident_id,entered_on,state,recorded_by)
        VALUES (:lease,:resident,'2026-02-10','STAYING',:manager) RETURNING id
    """), {'lease': lease_id, 'resident': resident_id, 'manager': manager_id})
    leases_router.insert_responsible(db, lease_id, occupancy_id, manager_id, 'Kontak data awal')
    invoice_id = db.scalar(text("""
        INSERT INTO kamartha.invoices(lease_id,period_start,period_end,due_on,amount,
            opening_paid,source,initialization_record_id)
        VALUES (:lease,'2026-02-10','2026-03-10','2026-02-10',700000,
            :paid,'OPENING',:record) RETURNING id
    """), {'lease': lease_id, 'paid': opening_paid, 'record': record_id})
    return lease_id, occupancy_id, invoice_id


@pytest.mark.parametrize('opening_paid', [0, 200000, 700000])
def test_last_exit_cannot_cancel_finalized_opening_invoice(api, migrated_connection, opening_paid):
    lease_id, occupancy_id, invoice_id = opening_contract(api, migrated_connection, opening_paid)
    before = api.get(f'/api/v1/leases/{lease_id}').json()['data']
    response = write(api, f'/api/v1/leases/{lease_id}/occupancies/{occupancy_id}/exit',
                     json={'exited_on': '2026-02-10', 'reason': 'Koreksi tanggal keluar lama'})
    assert response.status_code == 409, response.text
    assert response.json()['error']['code'] == 'OPENING_INVOICE_LOCKED'
    after = api.get(f'/api/v1/leases/{lease_id}').json()['data']
    assert after == before
    invoice = migrated_connection.execute(text("""
        SELECT status,opening_paid FROM kamartha.invoices WHERE id=:id
    """), {'id': invoice_id}).mappings().one()
    assert invoice['status'] == 'ACTIVE'
    assert invoice['opening_paid'] == opening_paid


def test_opening_lease_can_close_without_cancelling_started_opening_invoice(api, migrated_connection):
    lease_id, occupancy_id, invoice_id = opening_contract(api, migrated_connection, 200000)
    response = write(api, f'/api/v1/leases/{lease_id}/occupancies/{occupancy_id}/exit',
                     json={'exited_on': '2026-03-15', 'reason': 'Penghuni sudah keluar'})
    assert response.status_code == 200, response.text
    data = response.json()['data']
    assert data['occupancies'][0]['state'] == 'EXITED'
    assert data['status'] == 'ENDED'
    invoice = next(item for item in data['invoices'] if item['id'] == str(invoice_id))
    assert invoice['status'] == 'ACTIVE'
    assert invoice['paid_total'] == 200000
    assert invoice['remaining'] == 500000
