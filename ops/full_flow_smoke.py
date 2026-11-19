"""Exercise business APIs in disposable PostgreSQL with a temporary private Supabase bucket.

Run via ops/test_postgres.py --flow-smoke. Never points the application at the
primary Supabase database and never uses the primary manager's credentials.
"""
from datetime import timedelta
import io
import os
from pathlib import Path
import secrets
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))


class SmokeError(RuntimeError):
    pass


def test_configuration(**overrides):
    from app.core.clock import BusinessClock
    from app.core.config import Settings
    from app.core.security import hash_password

    setup_code, password = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
    values = {name: None for name in Settings.model_fields
              if name.startswith(('local_', 'supabase_'))}
    values.update(_env_file=None, app_profile='local', environment='test',
                  app_origin='http://localhost:8081', database_url=None,
                  setup_code_hash=hash_password(setup_code), ip_hash_secret=secrets.token_urlsafe(40))
    values.update(overrides)
    settings = Settings(**values)
    clock = BusinessClock()
    return settings, clock, setup_code, password


def exercise(client, origin, setup_code, password, today):
    from PIL import Image
    cutover = today.replace(day=1)
    previous_month = (cutover - timedelta(days=1)).replace(day=1)
    next_month = (cutover.replace(day=28) + timedelta(days=4)).replace(day=1)
    cutover_text, today_text = cutover.isoformat(), today.isoformat()

    def request(method, path, expected=200, **kwargs):
        headers = dict(kwargs.pop('headers', {}))
        if method not in ('GET', 'HEAD'):
            headers.setdefault('Idempotency-Key', str(uuid4()))
        response = client.request(method, '/api/v1' + path, headers=headers, **kwargs)
        if response.status_code != expected:
            raise SmokeError(f'{method} {path}: expected HTTP {expected}, got {response.status_code}.')
        return response

    def data(method, path, expected=200, **kwargs):
        return request(method, path, expected, **kwargs).json()['data']

    def check(condition, message):
        if not condition:
            raise SmokeError(message)

    def write(path, payload, expected=201, **kwargs):
        return data('POST', path, expected, json=payload, **kwargs)

    csrf = data('GET', '/auth/csrf')
    check(csrf['setup_available'], 'Isolated database must have no manager.')
    client.headers.update({'Origin': origin, 'X-CSRF-Token': csrf['csrf_token']})
    write('/auth/setup', {'username': 'flowtest', 'password': password,
                         'password_confirmation': password, 'setup_code': setup_code})
    csrf = data('GET', '/auth/csrf')
    client.headers['X-CSRF-Token'] = csrf['csrf_token']
    login = write('/auth/login', {'username': 'flowtest', 'password': password}, expected=200)
    client.headers['X-CSRF-Token'] = login['csrf_token']
    check(data('GET', '/auth/me')['mode'] == 'PREPARATION', 'Unexpected initial mode.')

    def room(number):
        return write('/rooms', {'number': number, 'room_type': 'Standar',
                                'supported_occupants': 1, 'reference_price': 700000})

    def resident(number):
        return write('/residents', {'name': 'Penghuni Dummy ' + number,
                                    'identity_type': 'Paspor', 'identity_number': 'SMOKE-' + number,
                                    'whatsapp_number': '08123456789'})

    old_room, new_room = room('UJI-01'), room('UJI-02')
    old_person, new_person = resident('01'), resident('02')
    settings = data('GET', '/initialization/settings')
    package = next(p for p in settings['packages'] if p['occupant_type'] == 1 and p['period_months'] == 1)
    data('PUT', '/initialization/settings', json={
        'cutover_date': cutover_text, 'expected_version': settings['version']})
    draft = {'client_record_key': str(uuid4()), 'draft_data': {
        'room_id': old_room['id'], 'package_id': package['id'],
        'starts_on': previous_month.isoformat(), 'ends_on': next_month.isoformat(), 'price': 500000,
        'responsible_resident_id': old_person['id'],
        'occupancies': [{'resident_id': old_person['id'], 'entered_on': previous_month.isoformat(), 'state': 'STAYING'}],
        'invoices': [{'period_start': cutover_text, 'due_on': cutover_text,
                      'amount': 500000, 'opening_paid': 200000}]}}
    write('/initialization/records', draft)
    summary = data('GET', '/initialization/reconciliation')
    check(summary['can_finalize'] and summary['total_receivable'] == 300000,
          'Opening reconciliation must preserve Rp300000 receivable.')
    final_payload = {'expected_version': summary['version'],
                     'reconciliation_hash': summary['reconciliation_hash'],
                     'confirmed_matches': True, 'confirmed_old_periods_settled': True}
    final_key = str(uuid4())
    finalized = write('/initialization/finalize', final_payload, 200,
                      headers={'Idempotency-Key': final_key})
    check(write('/initialization/finalize', final_payload, 200,
                headers={'Idempotency-Key': final_key}) == finalized, 'Finalize replay changed its result.')
    check(finalized['mode'] == 'ACTIVE', 'Finalization did not activate the isolated application.')
    request('POST', '/initialization/records', 409, json={**draft, 'client_record_key': str(uuid4())})

    lease_payload = {'room_id': new_room['id'], 'package_id': package['id'], 'starts_on': cutover_text,
                     'periods': 1, 'price': 700000, 'resident_ids': [new_person['id']],
                     'responsible_resident_id': new_person['id']}
    lease = write('/leases', lease_payload)
    request('POST', '/leases', 409, json=lease_payload)
    check(len(lease['invoices']) == 1, 'Contract did not create exactly one invoice.')
    invoice = lease['invoices'][0]
    check(write('/billing/synchronize', {}, 200)['created'] == 0, 'Synchronization duplicated invoices.')

    def upload(color):
        image = io.BytesIO()
        Image.new('RGB', (2, 2), color).save(image, format='PNG')
        content = image.getvalue()
        uploaded = data('POST', '/attachments', 201, files={'file': ('dummy.png', content, 'image/png')})
        check(request('GET', f"/attachments/{uploaded['id']}/content").content == content,
              'Staged attachment download differs.')
        return uploaded, content

    payment_attachment, payment_bytes = upload((10, 20, 30))
    expense_attachment, expense_bytes = upload((30, 20, 10))
    partial_payload = {'lease_id': lease['id'], 'received_on': today_text, 'total_amount': 400000,
                       'method': 'TRANSFER', 'allocations': [{'invoice_id': invoice['id'], 'amount': 400000}]}
    partial_key = str(uuid4())
    partial = write('/payments', partial_payload, headers={'Idempotency-Key': partial_key})
    check(write('/payments', partial_payload, headers={'Idempotency-Key': partial_key})['id'] == partial['id'],
          'Payment replay created another payment.')
    request('POST', '/payments', 409, headers={'Idempotency-Key': partial_key},
            json={**partial_payload, 'reference': 'changed'})
    check(data('GET', '/invoices/' + invoice['id'])['remaining'] == 300000, 'Partial payment balance differs.')
    write('/payments/' + partial['id'] + '/cancel', {'reason': 'Koreksi uji dummy'}, 200)
    check(data('GET', '/invoices/' + invoice['id'])['remaining'] == 700000, 'Cancelled payment did not restore balance.')
    request('POST', '/payments', 422, json={**partial_payload, 'total_amount': 800000,
            'allocations': [{'invoice_id': invoice['id'], 'amount': 800000}]})
    payment = write('/payments', {**partial_payload, 'total_amount': 700000,
                                 'allocations': [{'invoice_id': invoice['id'], 'amount': 700000}],
                                 'attachment_id': payment_attachment['id']})
    check(payment['attachment']['id'] == payment_attachment['id'], 'Receipt was not linked.')
    detail = data('GET', '/invoices/' + invoice['id'])
    check(detail['remaining'] == 0 and detail['payment_status'] == 'PAID', 'Full payment did not settle invoice.')

    expense_payload = {'expense_on': today_text, 'amount': 90000, 'category': 'INTERNET',
                       'description': 'Pengeluaran dummy, bukan data nyata'}
    request('POST', '/expenses', 409, json={**expense_payload, 'attachment_id': payment_attachment['id']})
    expense = write('/expenses', {**expense_payload, 'attachment_id': expense_attachment['id']})
    updated_payload = {**expense_payload, 'amount': 100000, 'attachment_id': expense_attachment['id'],
                       'expected_version': expense['version'], 'reason': 'Koreksi nominal uji dummy'}
    expense = data('PATCH', '/expenses/' + expense['id'], json=updated_payload)
    check(expense['version'] == 2 and len(expense['audits']) == 1, 'Expense audit/version mismatch.')
    request('PATCH', '/expenses/' + expense['id'], 409, json=updated_payload)
    for attachment, content in ((payment_attachment, payment_bytes), (expense_attachment, expense_bytes)):
        check(request('GET', '/attachments/' + attachment['id'] + '/content').content == content,
              'Linked attachment download differs.')

    cash = data('GET', '/reports/cash', params={'date_from': cutover_text, 'date_to': today_text})
    check((cash['income'], cash['expense'], cash['difference']) == (700000, 100000, 600000),
          'Cash report includes cancelled payments or opening balances, or has wrong expenses.')
    dashboard = data('GET', '/dashboard')
    check(dashboard['receivables'] == 300000, 'Dashboard did not preserve opening receivables.')
    check(dashboard['rooms']['occupied'] == 2, 'Room occupancy differs.')
    preview = write('/messages/preview', {'context_type': 'PAYMENT', 'context_id': payment['id']}, 200)
    check(preview['whatsapp_url'].startswith('https://wa.me/'), 'WhatsApp preview did not return a link.')
    write('/auth/logout', {}, 200)
    request('GET', '/auth/me', 401)
    request('GET', '/attachments/' + payment_attachment['id'] + '/content', 401)
    return {'mode': 'ACTIVE', 'income': cash['income'], 'expense': cash['expense'],
            'difference': cash['difference'], 'receivables': dashboard['receivables'], 'attachments': 2}


def run_live(url):
    import httpx
    from alembic import command
    from alembic.config import Config
    from dotenv import dotenv_values
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text
    from app.main import create_app
    from backup import validate_restore_target

    url = validate_restore_target(url)
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.begin() as db:
            if db.scalar(text("SELECT to_regnamespace('kamartha') IS NOT NULL")):
                raise SmokeError('Flow smoke requires a new isolated database.')
            config = Config(str(ROOT / 'backend' / 'alembic.ini'))
            config.set_main_option('script_location', str(ROOT / 'backend' / 'migrations'))
            config.attributes['connection'] = db
            old_url = os.environ.get('MIGRATION_DATABASE_URL')
            old_disabled = os.environ.get('PYTHON_DOTENV_DISABLED')
            os.environ['MIGRATION_DATABASE_URL'] = url.render_as_string(hide_password=False)
            os.environ['PYTHON_DOTENV_DISABLED'] = '1'
            try:
                command.upgrade(config, 'head')
            finally:
                for key, old in [('MIGRATION_DATABASE_URL', old_url), ('PYTHON_DOTENV_DISABLED', old_disabled)]:
                    if old is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = old
    finally:
        engine.dispose()

    values = dotenv_values(ROOT / 'backend' / '.env', interpolate=False)
    base, service_key = values.get('SUPABASE_URL'), values.get('SUPABASE_SERVICE_KEY')
    if not base or not service_key:
        raise SmokeError('Supabase Storage configuration is missing.')
    bucket = 'kamartha-flow-test-' + uuid4().hex
    headers = {'apikey': service_key, 'Authorization': f'Bearer {service_key}'}
    from backup import BucketReader
    reader = BucketReader(base, service_key, bucket)
    created = False
    try:
        with httpx.Client(base_url=base.rstrip('/') + '/storage/v1/', headers=headers, timeout=30) as storage_api:
            response = storage_api.post('bucket', json={
                'id': bucket, 'name': bucket, 'public': False, 'file_size_limit': 2 * 1024 * 1024,
                'allowed_mime_types': ['image/jpeg', 'image/png', 'application/pdf']})
            if response.status_code not in (200, 201):
                raise SmokeError('Could not create the uniquely named test bucket.')
            created = True
            try:
                info = storage_api.get('bucket/' + bucket)
                if info.status_code != 200 or info.json().get('public') is not False:
                    raise SmokeError('Test bucket is not verified private.')
                settings, clock, setup_code, password = test_configuration(
                    app_profile='supabase', database_url=url.render_as_string(hide_password=False),
                    supabase_url=base, supabase_service_key=service_key, storage_bucket=bucket)
                with TestClient(create_app(settings, clock=clock)) as client:
                    result = exercise(client, settings.app_origin, setup_code, password, clock.today())
                keys = reader.list_keys()
                if len(keys) != result['attachments']:
                    raise SmokeError('Unexpected object count in isolated test bucket.')
                anonymous = httpx.get(base.rstrip('/') + '/storage/v1/object/public/' + bucket + '/' + keys[0], timeout=20)
                if anonymous.status_code == 200:
                    raise SmokeError('Private test object was readable without authentication.')
                print('Isolated business flow: PASS; real PostgreSQL + private Supabase Storage.')
                print('Checks: preparation/finalization, lease, invoice, payment replay/cancel, expense audit, files, cash report, logout.')
                print(f"Cash: income={result['income']}; expense={result['expense']}; net={result['difference']}; receivables={result['receivables']}.")
            finally:
                if created:
                    # Only this run's newly created UUID bucket is emptied and removed.
                    empty = storage_api.post('bucket/' + bucket + '/empty', json={})
                    if empty.status_code not in (200, 204):
                        raise SmokeError('Temporary bucket cleanup failed: ' + bucket)
                    removed = storage_api.delete('bucket/' + bucket)
                    if removed.status_code not in (200, 204):
                        raise SmokeError('Temporary bucket deletion failed: ' + bucket)
                    print('Temporary bucket emptied and deleted:', bucket)
    finally:
        reader.close()
