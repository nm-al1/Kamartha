import io
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
from app.modules.attachments import router as attachments_router
from app.modules.auth import router as auth_router, service as auth_service
from app.modules.billing import router as billing_router
from app.modules.dashboard import router as dashboard_router
from app.modules.expenses import router as expenses_router
from app.modules.initialization import router as init_router
from app.modules.leases import router as leases_router
from app.modules.messaging import router as messaging_router
from app.modules.payments import router as payments_router
from app.modules.reports import router as reports_router
from app.modules.residents import router as residents_router
from app.modules.rooms import router as rooms_router

pytestmark = pytest.mark.integration

def make_png():
    from PIL import Image

    buffer = io.BytesIO()
    Image.new('RGB', (2, 2), (255, 255, 255)).save(buffer, 'PNG')
    return buffer.getvalue()


PNG = make_png()


@pytest.fixture
def api(migrated_connection, monkeypatch):
    def session(request):
        return Session(migrated_connection, join_transaction_mode='create_savepoint')
    for module in [auth_router, auth_service, rooms_router, residents_router, init_router,
                   leases_router, billing_router, payments_router, expenses_router,
                   dashboard_router, reports_router, messaging_router, attachments_router]:
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
    clock = BusinessClock(lambda: datetime(2026, 4, 7, tzinfo=timezone.utc))
    app = create_app(settings, clock=clock)
    with TestClient(app) as client:
        token = client.get('/api/v1/auth/csrf').json()['data']['csrf_token']
        login = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'DemoPass2026!'},
                            headers={'Origin': settings.app_origin, 'X-CSRF-Token': token})
        assert login.status_code == 200, login.text
        client.headers.update({'Origin': settings.app_origin,
                               'X-CSRF-Token': login.json()['data']['csrf_token']})
        yield client


def write(api, method, path, **kwargs):
    headers = {'Idempotency-Key': str(uuid4())}
    headers.update(kwargs.pop('headers', {}))
    return api.request(method, path, headers=headers, **kwargs)


def setup_contract(api, *, wa='08123456789'):
    room = write(api, 'POST', '/api/v1/rooms', json={
        'number': 'B1', 'room_type': 'Standar', 'supported_occupants': 1,
        'reference_price': 700000,
    })
    assert room.status_code == 201, room.text
    resident = write(api, 'POST', '/api/v1/residents', json={
        'name': 'Dewi', 'identity_type': 'Paspor', 'identity_number': 'D001',
        'whatsapp_number': wa,
    })
    assert resident.status_code == 201, resident.text
    resident_id = resident.json()['data']['id']
    packages = api.get('/api/v1/initialization/settings').json()['data']['packages']
    package_id = next(p['id'] for p in packages
                      if p['occupant_type'] == 1 and p['period_months'] == 1)
    created = write(api, 'POST', '/api/v1/leases', json={
        'room_id': room.json()['data']['id'], 'package_id': package_id,
        'starts_on': '2026-03-10', 'periods': 2, 'price': 700000,
        'resident_ids': [resident_id], 'responsible_resident_id': resident_id,
    })
    assert created.status_code == 201, created.text
    return created.json()['data'], resident_id


def test_invoice_detail_filters_id_inside_database(api, migrated_connection):
    from sqlalchemy import event

    lease, _ = setup_contract(api)
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        if 'FROM kamartha.invoices i' in statement:
            statements.append(statement)

    event.listen(migrated_connection, 'before_cursor_execute', capture)
    try:
        result = api.get('/api/v1/invoices/' + lease['invoices'][0]['id'])
    finally:
        event.remove(migrated_connection, 'before_cursor_execute', capture)
    assert result.status_code == 200, result.text
    assert result.json()['data']['id'] == lease['invoices'][0]['id']
    assert statements
    assert all('i.id=' in statement for statement in statements)


def test_synchronize_creates_one_available_period_and_can_cancel_future(api):
    lease, _ = setup_contract(api)
    first = write(api, 'POST', '/api/v1/billing/synchronize')
    assert first.status_code == 200, first.text
    assert first.json()['data']['created'] == 1
    repeat = write(api, 'POST', '/api/v1/billing/synchronize')
    assert repeat.json()['data']['created'] == 0
    listing = api.get('/api/v1/invoices').json()['data']
    assert len(listing['items']) == 2
    assert listing['summary']['total_remaining'] == 1400000
    future = next(item for item in listing['items']
                  if str(item['period_start']) == '2026-04-10')
    cancelled = write(api, 'POST', f"/api/v1/invoices/{future['id']}/cancel",
                      json={'reason': 'Salah bentuk periode'})
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()['data']['status'] == 'CANCELLED'


def test_payment_allocates_exact_amount_replays_and_cancel_restores_balance(api):
    lease, _ = setup_contract(api)
    invoice = lease['invoices'][0]
    payload = {
        'lease_id': lease['id'], 'received_on': '2026-04-01', 'total_amount': 400000,
        'method': 'TRANSFER', 'reference': 'TRX-1',
        'allocations': [{'invoice_id': invoice['id'], 'amount': 400000}],
    }
    key = str(uuid4())
    created = write(api, 'POST', '/api/v1/payments', json=payload,
                    headers={'Idempotency-Key': key})
    assert created.status_code == 201, created.text
    payment = created.json()['data']
    assert payment['status'] == 'VALID'
    assert len(payment['allocations']) == 1
    replay = write(api, 'POST', '/api/v1/payments', json=payload,
                   headers={'Idempotency-Key': key})
    assert replay.status_code == 201
    assert replay.json()['data']['id'] == payment['id']
    changed = write(api, 'POST', '/api/v1/payments', json={**payload, 'total_amount': 500000,
                                                          'allocations': [{'invoice_id': invoice['id'],
                                                                           'amount': 500000}]},
                    headers={'Idempotency-Key': key})
    assert changed.status_code == 409
    over = write(api, 'POST', '/api/v1/payments', json={
        **payload, 'total_amount': 900000,
        'allocations': [{'invoice_id': invoice['id'], 'amount': 900000}],
    })
    assert over.status_code == 422
    response = api.get(f"/api/v1/invoices/{invoice['id']}")
    assert response.status_code == 200, response.text
    detail = response.json()['data']
    assert detail['paid_total'] == 400000
    assert detail['remaining'] == 300000
    assert detail['payment_status'] == 'OVERDUE'
    cancelled = write(api, 'POST', f"/api/v1/payments/{payment['id']}/cancel",
                      json={'reason': 'Salah input nominal'})
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()['data']['status'] == 'CANCELLED'
    detail = api.get(f"/api/v1/invoices/{invoice['id']}").json()['data']
    assert detail['paid_total'] == 0
    assert detail['remaining'] == 700000
    assert detail['payment_status'] == 'OVERDUE'


def test_expense_audit_and_cash_report(api):
    lease, _ = setup_contract(api)
    invoice = lease['invoices'][0]
    payment = write(api, 'POST', '/api/v1/payments', json={
        'lease_id': lease['id'], 'received_on': '2026-04-01', 'total_amount': 400000,
        'method': 'CASH', 'allocations': [{'invoice_id': invoice['id'], 'amount': 400000}],
    })
    assert payment.status_code == 201, payment.text
    expense = write(api, 'POST', '/api/v1/expenses', json={
        'expense_on': '2026-04-02', 'amount': 200000, 'category': 'INTERNET',
        'description': 'Internet April',
    })
    assert expense.status_code == 201, expense.text
    data = expense.json()['data']
    assert data['version'] == 1
    updated = write(api, 'PATCH', f"/api/v1/expenses/{data['id']}", json={
        'expense_on': '2026-04-02', 'amount': 250000, 'category': 'INTERNET',
        'description': 'Internet April koreksi', 'expected_version': 1,
        'reason': 'Tagihan provider terkoreksi',
    })
    assert updated.status_code == 200, updated.text
    assert updated.json()['data']['version'] == 2
    assert len(updated.json()['data']['audits']) == 1
    stale = write(api, 'PATCH', f"/api/v1/expenses/{data['id']}", json={
        'expense_on': '2026-04-02', 'amount': 300000, 'category': 'INTERNET',
        'description': 'Stale', 'expected_version': 1, 'reason': 'Stale',
    })
    assert stale.status_code == 409

    report = api.get('/api/v1/reports/cash', params={
        'date_from': '2026-04-01', 'date_to': '2026-04-02',
    })
    assert report.status_code == 200, report.text
    body = report.json()['data']
    assert body['income'] == 400000
    assert body['expense'] == 250000
    assert body['difference'] == 150000
    assert len(body['payments']) == 1
    assert body['payments'][0]['allocations'][0]['amount'] == 400000
    assert api.get('/api/v1/reports/cash', params={
        'date_from': '2026-02-01', 'date_to': '2026-04-02',
    }).status_code == 422
    assert api.get('/api/v1/reports/cash', params={
        'date_from': '2026-04-03', 'date_to': '2026-04-02',
    }).status_code == 422

    cancelled = write(api, 'POST', f"/api/v1/expenses/{data['id']}/cancel", json={
        'expected_version': 2, 'reason': 'Duplikat',
    })
    assert cancelled.status_code == 200, cancelled.text
    report = api.get('/api/v1/reports/cash', params={
        'date_from': '2026-04-01', 'date_to': '2026-04-02',
    }).json()['data']
    assert report['expense'] == 0


def test_dashboard_reminders_and_whatsapp_preview(api):
    lease, resident_id = setup_contract(api)
    dashboard = api.get('/api/v1/dashboard')
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()['data']
    assert data['rooms']['total'] == 1
    assert data['rooms']['occupied'] == 1
    assert data['people_staying'] == 1
    assert data['receivables'] == 1400000 or data['receivables'] == 700000
    reminders = api.get('/api/v1/reminders').json()['data']
    assert any(item['room_number'] == 'B1' for item in reminders['invoices'])
    preview = api.post('/api/v1/messages/preview', json={
        'context_type': 'INVOICE', 'context_id': lease['invoices'][0]['id'],
    })
    assert preview.status_code == 200, preview.text
    body = preview.json()['data']
    assert body['recipient'] == 'Dewi'
    assert body['whatsapp_number'] == '628123456789'
    assert 'Kamar B1' in body['message'] or 'kamar B1' in body['message']
    assert body['whatsapp_url'].startswith('https://wa.me/628123456789?text=')
    updated = write(api, 'PATCH', f'/api/v1/residents/{resident_id}', json={
        'name': 'Dewi', 'identity_type': 'Paspor', 'identity_number': 'D001',
        'whatsapp_number': '123', 'notes': None,
    })
    assert updated.status_code == 200
    invalid = api.post('/api/v1/messages/preview', json={
        'context_type': 'INVOICE', 'context_id': lease['invoices'][0]['id'],
    })
    assert invalid.status_code == 422


def test_attachment_validation_and_payment_link(api):
    invalid = write(api, 'POST', '/api/v1/attachments',
                    files={'file': ('x.txt', b'not an image', 'text/plain')})
    assert invalid.status_code == 422
    big = write(api, 'POST', '/api/v1/attachments',
                files={'file': ('big.png', PNG + b'0' * (2 * 1024 * 1024), 'image/png')})
    assert big.status_code == 413
    uploaded = write(api, 'POST', '/api/v1/attachments',
                     files={'file': ('proof.png', PNG, 'image/png')})
    assert uploaded.status_code == 201, uploaded.text
    attachment = uploaded.json()['data']
    content = api.get(f"/api/v1/attachments/{attachment['id']}/content")
    assert content.status_code == 200
    assert content.content == PNG
    assert content.headers['content-type'].startswith('image/png')

    lease, _ = setup_contract(api)
    invoice = lease['invoices'][0]
    payment = write(api, 'POST', '/api/v1/payments', json={
        'lease_id': lease['id'], 'received_on': '2026-04-01', 'total_amount': 700000,
        'method': 'TRANSFER', 'allocations': [{'invoice_id': invoice['id'], 'amount': 700000}],
        'attachment_id': attachment['id'],
    })
    assert payment.status_code == 201, payment.text
    assert payment.json()['data']['attachment']['id'] == attachment['id']
    detail = api.get(f"/api/v1/invoices/{invoice['id']}").json()['data']
    assert detail['payment_status'] == 'PAID'
    assert detail['remaining'] == 0
