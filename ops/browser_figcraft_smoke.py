"""Read-only UI smoke of the release build with intercepted synthetic API data.

No requests reach the real backend. Requires Playwright and installed Chrome.
Run against the static frontend on localhost:8081; writes screenshots to scratch.
"""
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright

from browser_auth_demo import enable_semantics, type_into

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'scratch' / 'demo-verification-2026-11-18' / 'figcraft'


def fixture_handler(state):
    def handle(route):
        request = route.request
        path = request.url.split('/api/v1', 1)[1].split('?', 1)[0]
        headers = {'Access-Control-Allow-Origin': 'http://localhost:8081',
                   'Access-Control-Allow-Credentials': 'true',
                   'Access-Control-Allow-Headers': 'Content-Type,X-CSRF-Token,Idempotency-Key',
                   'Access-Control-Allow-Methods': 'GET,POST,PATCH,PUT,OPTIONS'}
        if request.method == 'OPTIONS':
            route.fulfill(status=204, headers=headers)
            return
        status = 200
        if path == '/auth/csrf':
            data = {'csrf_token': 'synthetic-qa-token', 'setup_available': False}
        elif path == '/auth/me':
            status = 200 if state['signed_in'] else 401
            data = {'id': 'qa-manager', 'username': 'pengelola_uji', 'mode': state.get('mode', 'ACTIVE')}
        elif path == '/auth/login':
            state['signed_in'] = True
            data = {'csrf_token': 'synthetic-qa-token'}
        elif path == '/auth/logout':
            state['signed_in'] = False
            data = {'logged_out': True}
        elif path == '/dashboard':
            data = {'today': '2026-11-05', 'rooms': {'total': 3, 'occupied': 2, 'empty': 1, 'needs_confirmation': 0},
                    'people_staying': 2, 'active_contracts': 2, 'receivables': 700000,
                    'overdue_receivables': 700000, 'reminders': {'invoices': [
                        {'id': 'qa-invoice', 'room_number': 'UJI-01', 'resident_names': 'Penghuni Dummy',
                         'remaining': 700000, 'due_on': '2026-11-01'}], 'leases': []}}
        elif path == '/billing/synchronize':
            data = {'created': 0}
        elif path == '/reminders/status':
            data = {'enabled': False, 'ready': False, 'allow_demo_date': False,
                    'hour_wita': 9, 'today': '2026-11-05'}
        elif path == '/reminders/history':
            data = {'items': []}
        elif path == '/initialization/settings':
            data = {'mode': state.get('mode', 'ACTIVE'), 'packages': [], 'version': 1, 'cutover_date': '2026-11-01'}
        elif path == '/initialization/records':
            data = {'items': [], 'pagination': {'has_more': False}}
        elif path in ('/residents', '/residents/qa-resident'):
            resident = {'id': 'qa-resident', 'name': 'Penghuni Dummy', 'identity_type': 'KTP',
                        'identity_number': 'SYNTHETIC-QA', 'whatsapp_number': None, 'notes': None,
                        'history': [{'lease_id': 'qa-lease', 'room_number': 'UJI-01', 'state': 'STAYING',
                                     'entered_on': '2026-11-01', 'exited_on': None,
                                     'starts_on': '2026-11-01', 'effective_ends_on': '2026-12-01'}]}
            data = {'items': [resident], 'pagination': {'has_more': False}} if path == '/residents' else resident
        elif path == '/initialization/reconciliation':
            data = {'version': 1, 'cutover_date': '2026-11-01', 'record_count': 0,
                    'resident_count': 0, 'occupied_room_count': 0, 'invoice_count': 0,
                    'total_receivable': 0, 'records': [], 'errors': [], 'can_finalize': False}
        elif path == '/rooms':
            data = {'items': [{'id': 'qa-room', 'number': 'UJI-01', 'room_type': 'Kamar dummy',
                              'supported_occupants': 1, 'reference_price': 700000, 'occupancy_status': 'OCCUPIED'}],
                    'pagination': {'has_more': False}}
        elif path == '/rooms/qa-room':
            data = {'id': 'qa-room', 'number': 'UJI-01', 'room_type': 'Kamar dummy',
                    'supported_occupants': 1, 'reference_price': 700000, 'occupancy_status': 'OCCUPIED',
                    'is_available_for_new_lease': False, 'leases': [
                        {'id': 'qa-lease', 'starts_on': '2026-11-01', 'effective_ends_on': '2026-12-01',
                         'occupant_type_snapshot': 1, 'period_months_snapshot': 1,
                         'period_price_snapshot': 700000}]}
        elif path in ('/leases', '/leases/qa-lease'):
            lease = {'id': 'qa-lease', 'room_number': 'UJI-01', 'resident_names': 'Penghuni Dummy',
                     'starts_on': '2026-11-01', 'effective_ends_on': '2026-12-01',
                     'occupant_type_snapshot': 1, 'period_months_snapshot': 1,
                     'period_price_snapshot': 700000, 'status': 'ACTIVE', 'version': 1,
                     'occupancies': [{'id': 'qa-occupancy', 'resident_id': 'qa-resident',
                                      'name': 'Penghuni Dummy', 'responsible': True,
                                      'state': 'STAYING', 'entered_on': '2026-11-01'}],
                     'invoices': []}
            data = {'items': [lease], 'pagination': {'has_more': False}} if path == '/leases' else lease
        elif path == '/invoices':
            data = {'items': [{'id': 'qa-invoice', 'room_number': 'UJI-01', 'resident_names': 'Penghuni Dummy',
                              'period_start': '2026-11-01', 'period_end': '2026-12-01', 'due_on': '2026-11-01',
                              'remaining': 700000, 'payment_status': 'OVERDUE'}],
                    'summary': {'total_remaining': 700000}, 'pagination': {'has_more': False}}
        elif path == '/invoices/qa-invoice':
            data = {'id': 'qa-invoice', 'lease_id': 'qa-lease', 'room_number': 'UJI-01',
                    'resident_names': 'Penghuni Dummy', 'period_start': '2026-11-01',
                    'period_end': '2026-12-01', 'due_on': '2026-11-01', 'payment_status': 'OVERDUE',
                    'status': 'ACTIVE', 'amount': 700000, 'paid_total': 0, 'remaining': 700000,
                    'allocations': []}
        elif path == '/expenses':
            data = {'items': [{'id': 'qa-expense', 'expense_on': '2026-11-03', 'category': 'INTERNET',
                              'description': 'Pengeluaran dummy untuk uji UI', 'amount': 100000,
                               'status': 'VALID', 'version': 1}], 'pagination': {'has_more': False}}
        elif path == '/expenses/qa-expense':
            data = {'id': 'qa-expense', 'expense_on': '2026-11-03', 'category': 'INTERNET',
                    'description': 'Pengeluaran dummy untuk uji UI', 'amount': 100000,
                    'status': 'VALID', 'version': 1, 'attachment': None, 'audits': []}
        elif path == '/reports/cash':
            query = parse_qs(urlsplit(request.url).query)
            data = {'date_from': query['date_from'][0], 'date_to': query['date_to'][0],
                    'income': 700000, 'expense': 100000, 'difference': 600000,
                    'payments': [{'room_number': 'UJI-01', 'total_amount': 700000,
                                  'received_on': '2026-11-03', 'method': 'TRANSFER', 'status': 'VALID'}],
                    'expenses': [{'category': 'INTERNET', 'amount': 100000,
                                  'expense_on': '2026-11-03', 'description': 'Pengeluaran dummy untuk uji UI', 'status': 'VALID'}]}
        else:
            raise AssertionError('Unspecified fixture request: ' + path)
        route.fulfill(status=status, content_type='application/json', headers=headers,
                      body=json.dumps({'data': data, 'request_id': 'synthetic-browser-qa'}))
    return handle


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        try:
            for width, height in [(320, 568), (360, 800), (390, 844), (430, 932), (1280, 900)]:
                print(f'Checking UI at {width}x{height}', flush=True)
                context = browser.new_context(viewport={'width': width, 'height': height}, service_workers='block')
                state = {'signed_in': False}
                context.route('**/api/v1/**', fixture_handler(state))
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto('http://localhost:8081', wait_until='load')
                enable_semantics(page)
                page.wait_for_timeout(3000)
                username = page.get_by_role('textbox', name=re.compile('^Username'))
                expect(username).to_be_visible(timeout=60000)
                page.screenshot(path=str(ARTIFACTS / f'login-{width}.png'))
                type_into(username, 'pengelola_uji')
                type_into(page.get_by_role('textbox', name=re.compile('^Password')), 'SyntheticQaOnly!')
                page.get_by_role('button', name='Masuk', exact=True).click()
                expect(page.get_by_role('group', name=re.compile('kamartha Halo, pengelola_uji'))).to_be_visible(timeout=30000)
                page.screenshot(path=str(ARTIFACTS / f'home-{width}.png'))
                for label, path in [('Kamar', '/rooms'), ('Tagihan', '/invoices'), ('Menu', '/menu')]:
                    page.get_by_role('button', name=label, exact=True).click()
                    page.wait_for_url(lambda url: path in url, timeout=15000)
                    page.wait_for_timeout(300)
                    page.screenshot(path=str(ARTIFACTS / f'{path[1:]}-{width}.png'))
                    if label == 'Kamar':
                        page.get_by_role('button', name=re.compile('Kamar UJI-01')).click()
                        expect(page.get_by_role('heading', name='Detail kamar')).to_be_visible(timeout=15000)
                        page.wait_for_timeout(300)
                        page.screenshot(path=str(ARTIFACTS / f'room-detail-{width}.png'))
                        page.get_by_role('button', name='Kembali', exact=True).click()
                        expect(page.get_by_role('heading', name='Kamar', exact=True)).to_be_visible(timeout=15000)
                    if label == 'Tagihan':
                        page.get_by_role('button', name=re.compile('Penghuni Dummy')).click()
                        expect(page.get_by_role('heading', name=re.compile('^Tagihan'))).to_be_visible(timeout=15000)
                        page.wait_for_timeout(300)
                        page.screenshot(path=str(ARTIFACTS / f'invoice-detail-{width}.png'))
                        page.get_by_role('button', name='Catat pembayaran', exact=True).click()
                        expect(page.get_by_role('heading', name=re.compile('^Catat pembayaran'))).to_be_visible(timeout=15000)
                        page.wait_for_timeout(350)
                        page.screenshot(path=str(ARTIFACTS / f'payment-form-{width}.png'))
                        amount = page.get_by_role('textbox', name=re.compile('^Nominal diterima'))
                        for _ in range(12):
                            if amount.count() and amount.is_visible():
                                break
                            page.mouse.move(width / 2, height / 2)
                            page.mouse.wheel(0, 180)
                            page.wait_for_timeout(100)
                        type_into(amount, '700000')
                        page.get_by_role('button', name='Tinjau pembayaran', exact=True).click()
                        expect(page.get_by_role('heading', name=re.compile('^Tinjau pembayaran'))).to_be_visible(timeout=15000)
                        page.wait_for_timeout(300)
                        page.screenshot(path=str(ARTIFACTS / f'payment-review-{width}.png'))
                        page.goto('http://localhost:8081/#/invoices', wait_until='load')
                        enable_semantics(page, timeout=1000)
                        expect(page.get_by_role('heading', name=re.compile('^Tagihan'))).to_be_visible(timeout=30000)
                page.get_by_role('button', name=re.compile('^Penghuni Data dan riwayat')).click()
                page.get_by_role('button', name=re.compile('Penghuni Dummy')).click()
                expect(page.get_by_role('heading', name=re.compile('^Detail penghuni'))).to_be_visible()
                page.wait_for_timeout(350)
                page.screenshot(path=str(ARTIFACTS / f'resident-detail-{width}.png'))
                contract_link = page.get_by_role('button', name='Lihat kontrak', exact=True)
                for _ in range(12):
                    if contract_link.count() and contract_link.is_visible():
                        break
                    page.mouse.move(width / 2, height / 2)
                    page.mouse.wheel(0, 150)
                    page.wait_for_timeout(100)
                contract_link.click()
                expect(page.get_by_role('heading', name=re.compile('^Detail kontrak'))).to_be_visible()
                page.get_by_role('button', name=re.compile('^Kembali(?: Kembali)?$')).click()
                page.wait_for_timeout(350)
                page.get_by_role('button', name=re.compile('^Kembali(?: Kembali)?$')).click()
                page.wait_for_timeout(350)
                page.get_by_role('button', name=re.compile('^Kembali(?: Kembali)?$')).click()
                page.wait_for_timeout(350)
                page.get_by_role('button', name=re.compile('^Masa sewa Kontrak')).click()
                expect(page.get_by_role('heading', name=re.compile('^Masa sewa'))).to_be_visible()
                page.wait_for_timeout(350)
                page.screenshot(path=str(ARTIFACTS / f'leases-{width}.png'))
                page.get_by_role('button', name='Kontrak baru', exact=True).click()
                expect(page.get_by_role('heading', name='Kontrak baru', exact=True)).to_be_visible()
                page.wait_for_timeout(350)
                page.screenshot(path=str(ARTIFACTS / f'lease-create-{width}.png'))
                page.get_by_role('button', name=re.compile('^Kembali(?: Kembali)?$')).click()
                page.wait_for_timeout(350)
                page.get_by_role('button', name=re.compile('Kamar UJI-01')).click()
                expect(page.get_by_role('heading', name=re.compile('^Detail kontrak'))).to_be_visible()
                page.wait_for_timeout(350)
                page.screenshot(path=str(ARTIFACTS / f'lease-detail-{width}.png'))
                extend = page.get_by_role('button', name='Perpanjang', exact=True)
                for _ in range(16):
                    if extend.count() and extend.is_visible():
                        break
                    page.mouse.move(width * .65, height / 2)
                    page.mouse.wheel(0, 140)
                    page.wait_for_timeout(100)
                extend.click()
                expect(page.get_by_role('alertdialog')).to_be_visible()
                page.wait_for_timeout(300)
                page.screenshot(path=str(ARTIFACTS / f'lease-extend-{width}.png'))
                periods = page.get_by_role('textbox', name=re.compile('Jumlah periode penuh'))
                type_into(periods, '2')
                periods.press('Escape')
                try:
                    expect(page.get_by_role('alertdialog')).to_have_count(0)
                except AssertionError:
                    print(f'Extension Escape failed at {width}x{height}')
                    print(page.locator('body').aria_snapshot())
                    raise
                page.get_by_role('button', name=re.compile('^Kembali(?: Kembali)?$')).click()
                page.wait_for_timeout(350)
                page.get_by_role('button', name=re.compile('^Kembali(?: Kembali)?$')).click()
                page.wait_for_timeout(350)
                page.get_by_role('button', name=re.compile('^Pengeluaran Catat biaya')).click()
                action = page.get_by_role('button', name='Tindakan pengeluaran')
                expect(action).to_be_visible()
                page.wait_for_timeout(300)
                page.screenshot(path=str(ARTIFACTS / f'expenses-{width}.png'))
                action.click()
                expect(page.get_by_role('menuitem', name='Koreksi')).to_be_visible()
                expect(page.get_by_role('menuitem', name='Batalkan')).to_be_visible()
                page.mouse.click(8, 8)
                page.wait_for_timeout(200)
                page.get_by_role('button', name=re.compile('^Buka detail pengeluaran')).click()
                expect(page.get_by_role('heading', name=re.compile('^Detail pengeluaran'))).to_be_visible()
                page.screenshot(path=str(ARTIFACTS / f'expense-detail-{width}.png'))
                page.get_by_role('button', name='Koreksi', exact=True).click()
                expect(page.get_by_role('heading', name='Koreksi pengeluaran', exact=True)).to_be_visible()
                page.wait_for_timeout(350)
                page.screenshot(path=str(ARTIFACTS / f'expense-form-{width}.png'))
                page.get_by_role('button', name='Batal', exact=True).click()
                page.get_by_role('button', name='Batalkan', exact=True).click()
                expect(page.get_by_role('alertdialog')).to_be_visible()
                page.get_by_role('button', name='Batal', exact=True).click()
                page.get_by_role('button', name='Kembali', exact=True).click()
                expect(page.get_by_role('button', name='Tindakan pengeluaran')).to_be_visible()
                page.wait_for_timeout(400)
                page.get_by_role('button', name=re.compile('^Kembali(?: Kembali)?$')).click()
                page.wait_for_url(lambda url: '/menu' in url)
                report = page.get_by_role('button', name=re.compile('^Laporan kas Pemasukan'))
                for _ in range(8):
                    if report.count() and report.is_visible():
                        break
                    page.mouse.move(width / 2, height / 2)
                    page.mouse.wheel(0, 180)
                    page.wait_for_timeout(100)
                report.click()
                page.get_by_role('button', name='Tampilkan', exact=True).click()
                difference = page.get_by_text(re.compile('Rp600')).last
                for _ in range(10):
                    if difference.count() and difference.is_visible():
                        break
                    page.mouse.move(width / 2, height / 2)
                    page.mouse.wheel(0, 150)
                    page.wait_for_timeout(100)
                expect(difference).to_be_visible()
                page.wait_for_timeout(350)
                page.screenshot(path=str(ARTIFACTS / f'reports-{width}.png'))
                page.get_by_role('button', name=re.compile('^Kembali(?: Kembali)?$')).click()
                page.wait_for_timeout(350)
                state['mode'] = 'PREPARATION'
                page.goto('http://localhost:8081/#/initialization', wait_until='load')
                enable_semantics(page, timeout=1000)
                expect(page.get_by_role('heading', name=re.compile('^Data awal'))).to_be_visible(timeout=30000)
                page.wait_for_timeout(350)
                page.screenshot(path=str(ARTIFACTS / f'initialization-{width}.png'))
                add_record = page.get_by_role('button', name='Tambah berkas', exact=True)
                for _ in range(12):
                    if add_record.count() and add_record.is_visible():
                        break
                    page.mouse.move(width / 2, height / 2)
                    page.mouse.wheel(0, 150)
                    page.wait_for_timeout(100)
                add_record.click()
                expect(page.get_by_role('heading', name='Berkas data awal', exact=True)).to_be_visible()
                page.wait_for_timeout(350)
                page.screenshot(path=str(ARTIFACTS / f'opening-form-{width}.png'))
                page.get_by_role('button', name='Kembali', exact=True).click()
                page.goto('http://localhost:8081/#/reminders', wait_until='load')
                enable_semantics(page, timeout=1000)
                expect(page.get_by_text('WA otomatis nonaktif', exact=True)).to_be_visible(timeout=30000)
                refresh_wa = page.get_by_role('button', name='Perbarui status dan QR')
                refresh_wa.click()
                expect(refresh_wa).to_be_enabled()
                expect(page.get_by_text('WA otomatis nonaktif', exact=True)).to_be_visible()
                page.goto('http://localhost:8081/#/menu', wait_until='load')
                enable_semantics(page, timeout=1000)
                expect(page.get_by_role('heading', name='Menu', exact=True)).to_be_visible(timeout=30000)
                account = page.get_by_role('button', name=re.compile('^Akun dan sesi Lihat akun'))
                for _ in range(8):
                    if account.count() and account.is_visible():
                        break
                    page.mouse.move(width / 2, height / 2)
                    page.mouse.wheel(0, 450)
                    page.wait_for_timeout(150)
                account.click()
                expect(page.get_by_role('button', name='Keluar', exact=True)).to_be_visible()
                page.get_by_role('button', name='Keluar', exact=True).click()
                page.wait_for_url(lambda url: '/login' in url)
                if errors:
                    raise AssertionError('Browser page errors: ' + '; '.join(errors))
                results.append({'viewport': [width, height], 'status': 'PASS', 'page_errors': len(errors)})
                context.close()
        finally:
            browser.close()
    (ARTIFACTS / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print('UI browser smoke PASS: login, four primary tabs, expense back, WA disabled, session/logout.')
    print('Synthetic API interception only; no real backend requests or business writes.')
    print('Screenshots:', ARTIFACTS)


if __name__ == '__main__':
    main()
