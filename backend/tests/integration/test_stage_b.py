from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError

from app.core.clock import BusinessClock
from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.modules.auth import router as auth_router, service as auth_service
from app.modules.rooms import router as rooms_router
from app.modules.residents import router as residents_router
from app.modules.initialization import router as init_router

pytestmark = pytest.mark.integration


@pytest.fixture
def api(migrated_connection, monkeypatch):
    def session(request):
        return Session(migrated_connection, join_transaction_mode='create_savepoint')
    for module in [auth_router, auth_service, rooms_router, residents_router, init_router]:
        monkeypatch.setattr(module, 'open_session', session)
    migrated_connection.execute(text('''INSERT INTO kamartha.managers(username,username_normalized,password_hash,password_changed_at)
        VALUES ('admin','admin',:hash,'2026-01-01T00:00:00Z')'''), {'hash': hash_password('DemoPass2026!')})
    settings = Settings(environment='test', database_url=None, _env_file=None,
                        ip_hash_secret='test-only-secret-at-least-32-characters')
    clock = BusinessClock(lambda: datetime(2026, 3, 1, tzinfo=timezone.utc))
    app = create_app(settings, clock=clock)
    async def database_failure(request, error):
        from fastapi.responses import JSONResponse
        return JSONResponse({'test_database_error': str(error.orig)}, status_code=500)
    app.add_exception_handler(DBAPIError, database_failure)
    with TestClient(app) as client:
        token = client.get('/api/v1/auth/csrf').json()['data']['csrf_token']
        login = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'DemoPass2026!'},
                            headers={'Origin': settings.app_origin, 'X-CSRF-Token': token})
        assert login.status_code == 200
        client.headers.update({'Origin': settings.app_origin, 'X-CSRF-Token': login.json()['data']['csrf_token'], 'Idempotency-Key': str(uuid4())})
        yield client


def build_draft(api):
    room = api.post('/api/v1/rooms', json={'number': 'A1', 'room_type': 'Standar', 'supported_occupants': 2, 'reference_price': 500000})
    assert room.status_code == 201, room.text
    resident = api.post('/api/v1/residents', json={'name': 'Andi', 'identity_type': 'Paspor', 'identity_number': 'TEST01'})
    assert resident.status_code == 201
    settings = api.get('/api/v1/initialization/settings').json()['data']
    saved = api.put('/api/v1/initialization/settings', json={'cutover_date': '2026-03-01', 'expected_version': settings['version']})
    assert saved.status_code == 200
    package = next(p for p in settings['packages'] if p['occupant_type'] == 1 and p['period_months'] == 1)
    resident_id = resident.json()['data']['id']
    data = {'room_id': room.json()['data']['id'], 'package_id': package['id'], 'starts_on': '2026-01-31',
            'ends_on': '2026-03-31', 'price': 500000, 'responsible_resident_id': resident_id,
            'occupancies': [{'resident_id': resident_id, 'entered_on': '2026-01-31', 'state': 'STAYING'}],
            'invoices': [{'period_start': '2026-02-28', 'due_on': '2026-02-28', 'amount': 500000, 'opening_paid': 500000}]}
    return data


@pytest.mark.parametrize('state,end,expected', [
    ('EXITED', '2026-03-31', 'EMPTY'),
    ('STAYING', '2026-03-31', 'OCCUPIED'),
    ('STAYING', '2026-03-01', 'NEEDS_CONFIRMATION'),
    ('EXITED', '2026-03-01', 'EMPTY'),
])
def test_room_status_uses_actual_occupancy(api, migrated_connection, state, end, expected):
    data = build_draft(api)
    db = migrated_connection
    manager = db.scalar(text('SELECT id FROM kamartha.managers'))
    lease = db.scalar(text('''INSERT INTO kamartha.leases(room_id,package_id,starts_on,
        agreed_ends_on,effective_ends_on,period_anchor,occupant_type_snapshot,
        period_months_snapshot,period_price_snapshot,source,created_by)
        VALUES (:room,:package,'2026-01-31',CAST(:end AS DATE),CAST(:end AS DATE),
        '2026-01-31',1,1,500000,'OPERATIONAL',:manager) RETURNING id'''),
        {'room': data['room_id'], 'package': data['package_id'], 'end': end, 'manager': manager})
    db.execute(text('''INSERT INTO kamartha.occupancies(lease_id,resident_id,entered_on,state,exited_on,recorded_by)
        VALUES (:lease,:resident,'2026-01-31',:state,CAST(:exited AS DATE),:manager)'''),
        {'lease': lease, 'resident': data['responsible_resident_id'], 'state': state,
         'exited': '2026-02-20' if state == 'EXITED' else None, 'manager': manager})
    detail = api.get('/api/v1/rooms/' + data['room_id']).json()['data']
    listing = api.get('/api/v1/rooms').json()['data']['items'][0]
    assert detail['occupancy_status'] == expected
    assert listing['occupancy_status'] == expected
    assert len(detail['leases']) == 1


def test_opening_finalize_and_safe_replay(api, migrated_connection):
    data = build_draft(api)
    draft = {'client_record_key': str(uuid4()), 'draft_data': data}
    first = api.post('/api/v1/initialization/records', json=draft)
    assert first.status_code == 201, first.text
    assert api.post('/api/v1/initialization/records', json=draft).json()['data']['id'] == first.json()['data']['id']
    rekap = api.get('/api/v1/initialization/reconciliation').json()['data']
    assert rekap['can_finalize'], rekap
    assert rekap['total_receivable'] == 0
    values = {'expected_version': rekap['version'], 'reconciliation_hash': rekap['reconciliation_hash'],
              'confirmed_matches': True, 'confirmed_old_periods_settled': True}
    headers = {'Idempotency-Key': str(uuid4())}
    final = api.post('/api/v1/initialization/finalize', json=values, headers=headers)
    assert final.status_code == 200, final.text
    assert api.post('/api/v1/initialization/finalize', json=values, headers=headers).json()['data'] == final.json()['data']
    assert api.post('/api/v1/initialization/finalize', json=values, headers={'Idempotency-Key': str(uuid4())}).status_code == 409
    assert api.patch('/api/v1/initialization/records/' + first.json()['data']['id'], json={'expected_version': 1, 'draft_data': data}).status_code == 409
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.leases')) == 1
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.invoices WHERE opening_paid=amount')) == 1
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.payments')) == 0
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.responsible_history WHERE valid_until IS NULL')) == 1
    assert api.post('/api/v1/initialization/records', json=draft).json()['data'] == first.json()['data']


def test_incomplete_draft_and_stale_versions(api, migrated_connection):
    data = build_draft(api)
    response = api.post('/api/v1/initialization/records', json={'client_record_key': str(uuid4()), 'draft_data': {}})
    assert response.status_code == 201
    draft = response.json()['data']
    rekap = api.get('/api/v1/initialization/reconciliation').json()['data']
    assert not rekap['can_finalize']
    final = api.post('/api/v1/initialization/finalize', headers={'Idempotency-Key': str(uuid4())}, json={
        'expected_version': rekap['version'], 'reconciliation_hash': rekap['reconciliation_hash'],
        'confirmed_matches': True, 'confirmed_old_periods_settled': True})
    assert final.status_code == 422
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.leases')) == 0
    path = '/api/v1/initialization/records/' + draft['id']
    assert api.patch(path, json={'expected_version': 1, 'draft_data': data}).status_code == 200
    assert api.patch(path, json={'expected_version': 1, 'draft_data': data}, headers={'Idempotency-Key': str(uuid4())}).status_code == 409


def test_cross_record_conflict(api):
    data = build_draft(api)
    for _ in range(2):
        assert api.post('/api/v1/initialization/records', json={'client_record_key': str(uuid4()), 'draft_data': data}).status_code == 201
    assert not api.get('/api/v1/initialization/reconciliation').json()['data']['can_finalize']


def test_room_crud_search_and_idempotency(api):
    values = {'number': 'A_1', 'room_type': 'Standar', 'supported_occupants': 2, 'reference_price': 500000}
    first = api.post('/api/v1/rooms', json=values)
    assert first.status_code == 201
    assert api.post('/api/v1/rooms', json=values).json()['data'] == first.json()['data']
    assert api.post('/api/v1/rooms', json={**values, 'number': 'A2'}).status_code == 409
    assert api.post('/api/v1/rooms', json=values, headers={'Idempotency-Key': str(uuid4())}).status_code == 409
    room_id = first.json()['data']['id']
    assert api.get('/api/v1/rooms?q=_').json()['data']['pagination']['total'] == 1
    assert api.get('/api/v1/rooms?limit=101').status_code == 422
    assert api.get('/api/v1/rooms/' + room_id).json()['data']['occupancy_status'] == 'EMPTY'
    assert api.patch('/api/v1/rooms/' + room_id, json={**values, 'number': 'A2'}).status_code == 200
    assert api.get('/api/v1/rooms/' + str(uuid4())).status_code == 404
    assert api.patch('/api/v1/rooms/' + str(uuid4()), json=values).status_code == 404


def test_settings_dates_and_reconciliation_change(api):
    data = build_draft(api)
    settings = api.get('/api/v1/initialization/settings').json()['data']
    assert api.put('/api/v1/initialization/settings', json={'cutover_date': '2027-01-01', 'expected_version': settings['version']},
                   headers={'Idempotency-Key': str(uuid4())}).status_code == 422
    assert api.put('/api/v1/initialization/settings', json={'cutover_date': '2026-02-01', 'expected_version': 1},
                   headers={'Idempotency-Key': str(uuid4())}).status_code == 409
    api.post('/api/v1/initialization/records', json={'client_record_key': str(uuid4()), 'draft_data': data})
    summary = api.get('/api/v1/initialization/reconciliation').json()['data']
    changed = api.patch('/api/v1/rooms/' + data['room_id'], json={'number': 'A2', 'room_type': 'Standar',
        'supported_occupants': 2, 'reference_price': 600000})
    assert changed.status_code == 200
    final = api.post('/api/v1/initialization/finalize', json={'expected_version': summary['version'],
        'reconciliation_hash': summary['reconciliation_hash'], 'confirmed_matches': True, 'confirmed_old_periods_settled': True})
    assert final.status_code == 409
    assert final.json()['error']['code'] == 'RECONCILIATION_CHANGED'


def test_materialization_failure_rolls_back_all_rows(api, migrated_connection, monkeypatch):
    data = build_draft(api)
    api.post('/api/v1/initialization/records', json={'client_record_key': str(uuid4()), 'draft_data': data})
    summary = api.get('/api/v1/initialization/reconciliation').json()['data']
    original = init_router.materialize
    def fail_after_writes(db, valid, manager):
        original(db, valid, manager)
        raise RuntimeError('Injected failure after materialization')
    monkeypatch.setattr(init_router, 'materialize', fail_after_writes)
    response = api.post('/api/v1/initialization/finalize', json={'expected_version': summary['version'],
        'reconciliation_hash': summary['reconciliation_hash'], 'confirmed_matches': True, 'confirmed_old_periods_settled': True})
    assert response.status_code == 500
    for table in ['leases', 'occupancies', 'invoices', 'initialization_finalizations']:
        assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.' + table)) == 0
    assert migrated_connection.scalar(text('SELECT mode FROM kamartha.app_settings')) == 'PREPARATION'


def test_two_people_with_one_exited_unknown_date(api, migrated_connection):
    data = build_draft(api)
    second = api.post('/api/v1/residents', json={'name': 'Budi', 'identity_type': 'Kartu pelajar', 'identity_number': 'TEST02'},
                      headers={'Idempotency-Key': str(uuid4())}).json()['data']['id']
    packages = api.get('/api/v1/initialization/settings').json()['data']['packages']
    data['package_id'] = next(p['id'] for p in packages if p['occupant_type'] == 2 and p['period_months'] == 1)
    data['occupancies'].append({'resident_id': second, 'entered_on': '2026-01-31', 'state': 'EXITED', 'exit_date_unknown': True})
    data['invoices'][0]['opening_paid'] = 200000
    api.post('/api/v1/initialization/records', json={'client_record_key': str(uuid4()), 'draft_data': data})
    summary = api.get('/api/v1/initialization/reconciliation').json()['data']
    assert summary['can_finalize'], summary
    assert summary['resident_count'] == 2
    assert summary['total_receivable'] == 300000
    response = api.post('/api/v1/initialization/finalize', json={'expected_version': summary['version'],
        'reconciliation_hash': summary['reconciliation_hash'], 'confirmed_matches': True, 'confirmed_old_periods_settled': True})
    assert response.status_code == 200, response.text
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.invoices')) == 1
    assert len(api.get('/api/v1/residents/' + second).json()['data']['history']) == 1
    assert len(api.get('/api/v1/rooms/' + data['room_id']).json()['data']['leases']) == 1
    assert api.patch('/api/v1/rooms/' + data['room_id'], json={'number': 'A1', 'room_type': 'Standar',
        'supported_occupants': 1, 'reference_price': 500000}).status_code == 409


def test_business_endpoints_require_session_and_csrf(api):
    values = {'number': 'A1', 'room_type': 'Standar', 'supported_occupants': 1, 'reference_price': 100}
    assert api.post('/api/v1/rooms', json=values, headers={'X-CSRF-Token': 'wrong'}).status_code == 403
    api.cookies.clear()
    for path in ['/rooms', '/residents', '/initialization/settings', '/initialization/records', '/initialization/reconciliation']:
        assert api.get('/api/v1' + path).status_code == 401


def test_finalization_rejects_changed_key_payload(api):
    data = build_draft(api)
    api.post('/api/v1/initialization/records', json={'client_record_key': str(uuid4()), 'draft_data': data})
    summary = api.get('/api/v1/initialization/reconciliation').json()['data']
    payload = {'expected_version': summary['version'], 'reconciliation_hash': summary['reconciliation_hash'],
               'confirmed_matches': True, 'confirmed_old_periods_settled': True}
    assert api.post('/api/v1/initialization/finalize', json=payload).status_code == 200
    assert api.post('/api/v1/initialization/finalize', json={**payload, 'expected_version': 99}).status_code == 409


def test_original_draft_creation_replays_after_edit_without_overwriting(api, migrated_connection):
    data = build_draft(api)
    body = {'client_record_key': str(uuid4()), 'draft_data': data}
    created = api.post('/api/v1/initialization/records', json=body)
    assert created.status_code == 201
    original = created.json()['data']
    path = '/api/v1/initialization/records/' + original['id']
    changed = {**data, 'price': 600000}
    edited = api.patch(path, json={'expected_version': 1, 'draft_data': changed},
                       headers={'Idempotency-Key': str(uuid4())})
    assert edited.status_code == 200
    replay = api.post('/api/v1/initialization/records', json=body)
    assert replay.status_code == 201, replay.text
    assert replay.json()['data'] == original
    assert api.get(path).json()['data']['draft_data'] == changed
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.initialization_records')) == 1
    conflict = api.post('/api/v1/initialization/records', json={**body, 'draft_data': changed})
    assert conflict.status_code == 409


@pytest.mark.parametrize('unknown', [False, True])
def test_finalized_exited_lease_keeps_closed_contact_history(api, migrated_connection, unknown):
    data = build_draft(api)
    data['occupancies'][0].update(state='EXITED', exit_date_unknown=unknown)
    if not unknown:
        data['occupancies'][0]['exited_on'] = '2026-02-20'
    created = api.post('/api/v1/initialization/records', json={'client_record_key': str(uuid4()), 'draft_data': data})
    assert created.status_code == 201
    summary = api.get('/api/v1/initialization/reconciliation').json()['data']
    assert summary['can_finalize'], summary['errors']
    response = api.post('/api/v1/initialization/finalize', json={
        'expected_version': summary['version'], 'reconciliation_hash': summary['reconciliation_hash'],
        'confirmed_matches': True, 'confirmed_old_periods_settled': True},
        headers={'Idempotency-Key': str(uuid4())})
    assert response.status_code == 200, response.text
    history = migrated_connection.execute(text('SELECT * FROM kamartha.responsible_history')).mappings().one()
    assert history['valid_until'] is not None
    assert history['valid_until'] > history['valid_from']
    occupancy = migrated_connection.execute(text('SELECT * FROM kamartha.occupancies')).mappings().one()
    assert history['occupancy_id'] == occupancy['id']
    assert occupancy['exit_date_unknown'] is unknown
    if unknown:
        assert occupancy['exited_on'] is None
    else:
        assert str(occupancy['exited_on']) == '2026-02-20'
