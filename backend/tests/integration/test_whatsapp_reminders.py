from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.modules.reminders.service import run_reminders, reconcile_receipts, stage_for
from app.modules.reminders import router
from app.modules.reminders.worker import prepare_invoices, scheduled_date
from test_stage_c import api, create, package, resident, room

pytestmark = pytest.mark.integration


class Bridge:
    def __init__(self, lose=False):
        self.calls = []
        self.lose = lose

    def status(self):
        return {'ready': True}

    def send(self, key, number, message):
        self.calls.append((key, number, message))
        if self.lose:
            raise TimeoutError('synthetic response loss')
        return {'state': 'SENT', 'message_id': 'synthetic-message'}

    def receipt(self, key):
        return {'state': 'SENT', 'message_id': 'late-confirmation'}


def setup(api, db, *, periods=1):
    person = resident(api, 'Penghuni Dummy WA', 'DUMMY-WA-01')
    db.execute(text('UPDATE kamartha.residents SET whatsapp_number=:number WHERE id=:id'),
               {'id': person, 'number': '08111111111'})
    response = create(api, room_id=room(api), package_id=package(api, 1),
                      residents=[person], responsible=person, periods=periods)
    assert response.status_code == 201, response.text
    invoice = response.json()['data']['invoices'][0]['id']
    settings = Settings(_env_file=None, environment='test', whatsapp_enabled=True,
        whatsapp_allowed_numbers='628111111111', whatsapp_demo_invoice_ids=invoice)
    factory = lambda: Session(db, join_transaction_mode='create_savepoint')
    return settings, factory, invoice


def test_h3_and_due_send_once_each_on_real_postgres(api, migrated_connection):
    settings, factory, invoice = setup(api, migrated_connection)
    bridge = Bridge()
    assert run_reminders(factory, settings, date(2026, 3, 7), bridge)['sent'] == 1
    assert run_reminders(factory, settings, date(2026, 3, 7), bridge)['existing'] == 1
    assert run_reminders(factory, settings, date(2026, 3, 8), bridge)['skipped'] == 1
    assert run_reminders(factory, settings, date(2026, 3, 10), bridge)['sent'] == 1
    assert len(bridge.calls) == 2
    assert all('[DEMO KAMARTHA]' in call[2] and 'Rp700.000' in call[2] for call in bridge.calls)
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.whatsapp_reminders')) == 2


def test_ambiguous_delivery_is_not_resent_and_can_be_reconciled(api, migrated_connection):
    settings, factory, invoice = setup(api, migrated_connection)
    bridge = Bridge(lose=True)
    assert run_reminders(factory, settings, date(2026, 3, 10), bridge)['unknown'] == 1
    assert run_reminders(factory, settings, date(2026, 3, 10), bridge)['existing'] == 1
    assert len(bridge.calls) == 1
    assert migrated_connection.scalar(text('SELECT status FROM kamartha.whatsapp_reminders')) == 'UNKNOWN'
    reconcile_receipts(factory, bridge)
    assert migrated_connection.scalar(text('SELECT status FROM kamartha.whatsapp_reminders')) == 'SENT'


def test_non_allowlisted_target_or_unconfigured_feature_never_sends(api, migrated_connection):
    settings, factory, invoice = setup(api, migrated_connection)
    bridge = Bridge()
    settings.whatsapp_allowed_numbers = '628222222222'
    assert run_reminders(factory, settings, date(2026, 3, 10), bridge)['skipped'] == 1
    settings.whatsapp_demo_invoice_ids = ''
    with pytest.raises(AppError):
        run_reminders(factory, settings, date(2026, 3, 10), bridge)
    settings.whatsapp_enabled = False
    with pytest.raises(AppError):
        run_reminders(factory, settings, date(2026, 3, 10), bridge)
    assert not bridge.calls


def test_paid_invoice_is_skipped(api, migrated_connection, monkeypatch):
    from app.modules.payments import router as payments_router
    monkeypatch.setattr(payments_router, 'open_session', lambda request: Session(migrated_connection, join_transaction_mode='create_savepoint'))
    settings, factory, invoice = setup(api, migrated_connection)
    lease = migrated_connection.scalar(text('SELECT lease_id FROM kamartha.invoices WHERE id=:id'), {'id': invoice})
    paid = api.post('/api/v1/payments', headers={'Idempotency-Key': str(uuid4())}, json={
        'lease_id': str(lease), 'received_on': '2026-03-20', 'total_amount': 700000, 'method': 'CASH',
        'allocations': [{'invoice_id': invoice, 'amount': 700000}]})
    assert paid.status_code == 201, paid.text
    bridge = Bridge()
    assert run_reminders(factory, settings, date(2026, 3, 10), bridge)['skipped'] == 1
    assert not bridge.calls


def test_stage_dates_are_exact_and_default_status_is_disabled(api):
    assert stage_for(date(2026, 3, 10), date(2026, 3, 7)) == 'H3'
    assert stage_for(date(2026, 3, 10), date(2026, 3, 10)) == 'DUE'
    assert stage_for(date(2026, 3, 10), date(2026, 3, 11)) is None
    response = api.get('/api/v1/reminders/status')
    assert response.status_code == 200
    assert response.json()['data']['enabled'] is False
    assert api.post('/api/v1/reminders/run', json={}).status_code == 409


def test_worker_prepares_future_invoice_at_wita_threshold_without_allowing_it(api, migrated_connection):
    settings, factory, _ = setup(api, migrated_connection, periods=2)
    assert scheduled_date(datetime(2026, 4, 7, 0, 59, tzinfo=timezone.utc), 9) is None
    today = scheduled_date(datetime(2026, 4, 7, 1, tzinfo=timezone.utc), 9)
    assert today == date(2026, 4, 7)
    assert scheduled_date(datetime(2026, 4, 7, 12, tzinfo=timezone.utc), 9) == today
    assert scheduled_date(datetime(2026, 4, 7, 16, tzinfo=timezone.utc), 9) is None
    assert prepare_invoices(factory, today)
    assert prepare_invoices(factory, today)  # a restarted worker is safe
    invoice = migrated_connection.scalar(text("""SELECT id FROM kamartha.invoices
        WHERE due_on=DATE '2026-04-10'"""))
    assert invoice is not None
    bridge = Bridge()
    assert run_reminders(factory, settings, today, bridge)['sent'] == 0
    settings.whatsapp_demo_invoice_ids = str(invoice)
    assert run_reminders(factory, settings, today, bridge)['sent'] == 1
    assert run_reminders(factory, settings, date(2026, 4, 10), bridge)['sent'] == 1


def test_status_qr_access_and_date_permission(api, migrated_connection, monkeypatch):
    settings, factory, _ = setup(api, migrated_connection)
    app_settings = api.app.state.settings
    app_settings.whatsapp_enabled = True
    app_settings.whatsapp_allowed_numbers = settings.whatsapp_allowed_numbers
    app_settings.whatsapp_demo_invoice_ids = settings.whatsapp_demo_invoice_ids
    bridge = Bridge()
    state = {'ready': False, 'state': 'SCAN_QR', 'qr': 'synthetic-qr'}
    monkeypatch.setattr(bridge, 'status', lambda: state)
    monkeypatch.setattr(router, 'WhatsAppBridge', lambda _: bridge)
    monkeypatch.setattr(router, 'open_session', lambda _: factory())
    response = api.get('/api/v1/reminders/status')
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.json()['data']['qr'] == 'synthetic-qr'
    assert response.json()['data']['allowed_numbers'] == ['***1111']
    payload = {'demo_date': '2026-03-07'}
    assert api.post('/api/v1/reminders/run', json=payload).json()['error']['code'] == 'WA_DEMO_DATE_DISABLED'
    app_settings.whatsapp_allow_demo_date = True
    assert api.post('/api/v1/reminders/run', json=payload, headers={'X-CSRF-Token': 'invalid'}).status_code == 403
    assert api.post('/api/v1/reminders/run', json=payload, headers={'Origin': 'http://invalid.test'}).status_code == 403
    assert not bridge.calls
    state.update(ready=True, state='READY')
    assert api.get('/api/v1/reminders/status').json()['data']['qr'] is None
    assert api.post('/api/v1/reminders/run', json=payload).json()['data']['sent'] == 1
    assert api.get('/api/v1/reminders/history').json()['data']['items'][0]['stage'] == 'H3'
    api.cookies.clear()
    for endpoint in ('status', 'history'):
        assert api.get(f'/api/v1/reminders/{endpoint}').status_code == 401


def test_crash_recovery_and_late_ack_do_not_resend(api, migrated_connection):
    settings, factory, invoice = setup(api, migrated_connection)
    bridge = Bridge()

    def lose_response(key, number, message):
        migrated_connection.execute(text("""UPDATE kamartha.whatsapp_reminders
            SET created_at=clock_timestamp()-interval '3 minutes' WHERE id=:id"""), {'id': key})
        monkey_receipt = bridge.receipt
        bridge.receipt = lambda _: {'state': 'NOT_FOUND'}
        reconcile_receipts(factory, bridge)
        assert migrated_connection.scalar(text('SELECT status FROM kamartha.whatsapp_reminders')) == 'UNKNOWN'
        bridge.receipt = monkey_receipt
        reconcile_receipts(factory, bridge)
        raise TimeoutError('synthetic response loss')

    bridge.send = lose_response
    assert run_reminders(factory, settings, date(2026, 3, 10), bridge)['sent'] == 1
    assert migrated_connection.scalar(text('SELECT status FROM kamartha.whatsapp_reminders')) == 'SENT'
    assert run_reminders(factory, settings, date(2026, 3, 10), bridge)['existing'] == 1
