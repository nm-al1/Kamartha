"""Synthetic browser upload/review checks; intercept every API request."""
import json
from pathlib import Path
import re
import sys

from playwright.sync_api import expect, sync_playwright

from browser_figcraft_smoke import enable_semantics, fixture_handler

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / 'docs/templates/KAMARTHA-contoh-dummy-5-kamar-v2.xlsx'
sys.path.insert(0, str(ROOT / 'backend'))
from app.modules.initialization.import_excel import PRICES, read_workbook


def sample():
    tables = read_workbook(FILE.read_bytes())
    people = {r[0]: r for r in tables['Penghuni']}
    items = [{'sheet': 'Kamar', 'label': r[0], 'status': 'NEW', 'row': i}
             for i, r in enumerate(tables['Kamar'], 2)]
    items += [{'sheet': 'Penghuni', 'label': r[1], 'status': 'NEW', 'row': i}
              for i, r in enumerate(tables['Penghuni'], 2)]
    for i, contract in enumerate(tables['Kontrak'], 2):
        code, room, count, months, start, end = contract
        occupants = [{'resident_id': row[1], 'name': people[row[1]][1],
                      'entered_on': row[3], 'state': 'STAYING'}
                     for row in tables['Penempatan'] if row[0] == code]
        invoices = [{'period_start': r[1], 'due_on': r[2], 'amount': int(r[3]),
                     'opening_paid': int(r[3]) - int(r[4])}
                    for r in tables['Sisa tagihan awal'] if r[0] == code]
        items.append({'sheet': 'Kontrak', 'label': code, 'row': i, 'status': 'NEW',
            'room_number': room, 'residents': [o['name'] for o in occupants], 'occupants': occupants,
            'price': PRICES[int(count), int(months)],
            'remaining': sum(v['amount'] - v['opening_paid'] for v in invoices),
            'data': {'starts_on': start, 'ends_on': end, 'occupancies': occupants,
                     'invoices': invoices, 'responsible_resident_id': occupants[0]['resident_id']}})
    return {'tables': tables, 'preview_hash': 'a' * 64, 'can_import': True, 'errors': [],
            'items': items, 'new_rooms': 5, 'new_residents': 8, 'new_records': 5,
            'total_receivable': 1700000, 'cutover_date': '2026-11-12'}


def main():
    artifacts = ROOT / 'scratch/demo-verification-2026-11-18/opening-import'
    artifacts.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        for width, height in [(320, 568), (390, 844), (800, 360)]:
            print(f'Checking import at {width}x{height}', flush=True)
            context = browser.new_context(viewport={'width': width, 'height': height}, service_workers='block')
            state = {'signed_in': True, 'mode': 'PREPARATION'}
            counts = {'preview': 0, 'confirm': 0}
            fallback = fixture_handler(state)

            def handle(route):
                path = route.request.url.split('/api/v1', 1)[1].split('?', 1)[0]
                if path not in ('/initialization/import/preview', '/initialization/import/confirm'):
                    return fallback(route)
                headers = {'Access-Control-Allow-Origin': 'http://localhost:8081',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Allow-Headers': 'Content-Type,X-CSRF-Token,Idempotency-Key',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'}
                if route.request.method == 'OPTIONS':
                    return route.fulfill(status=204, headers=headers)
                if path.endswith('preview'):
                    counts['preview'] += 1
                    data = sample()
                else:
                    counts['confirm'] += 1
                    values = route.request.post_data_json
                    assert values == {'tables': sample()['tables'], 'preview_hash': 'a' * 64, 'confirmed': True}
                    data = {'created_rooms': 5, 'created_residents': 8, 'created_records': 5}
                route.fulfill(status=200, headers=headers, content_type='application/json',
                              body=json.dumps({'data': data, 'request_id': 'synthetic-import-qa'}))

            context.route('**/api/v1/**', handle)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto('http://localhost:8081/#/initialization', wait_until='load')
            enable_semantics(page)
            page.wait_for_timeout(3000)
            expect(page.get_by_role('heading', name=re.compile('^Data awal'))).to_be_visible(timeout=30000)
            button = page.get_by_role('button', name='Impor Excel', exact=True)
            for _ in range(30):
                box = button.bounding_box() if button.count() else None
                if box and box['y'] >= 104 and box['y'] + box['height'] <= height:
                    break
                page.mouse.move(width * .7, height / 2)
                page.mouse.wheel(0, 80)
                page.wait_for_timeout(100)
            button.click()
            with page.expect_file_chooser() as chooser:
                page.get_by_role('button', name='Pilih berkas Excel', exact=True).click()
            chooser.value.set_files({'name': 'too-large.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                     'buffer': b'x' * (2 * 1024 * 1024 + 1)})
            expect(page.get_by_text(re.compile('Berkas Excel maksimal 2 MB'))).to_be_visible(timeout=15000)
            assert counts == {'preview': 0, 'confirm': 0}
            with page.expect_file_chooser() as chooser:
                page.get_by_role('button', name='Pilih berkas Excel', exact=True).click()
            chooser.value.set_files(FILE)
            expect(page.get_by_role('group', name=re.compile('^Pratinjau data awal'))).to_be_visible(timeout=30000)
            assert counts == {'preview': 1, 'confirm': 0}
            page.screenshot(path=str(artifacts / f'preview-{width}.png'))
            confirmation = page.get_by_role('checkbox')
            for _ in range(100):
                box = confirmation.bounding_box() if confirmation.count() else None
                if box and box['y'] >= 104 and box['y'] + box['height'] <= height:
                    break
                page.mouse.move(width * .7, height / 2)
                page.mouse.wheel(0, 220)
                page.wait_for_timeout(50)
            save = page.get_by_role('button', name='Konfirmasi impor draft', exact=True)
            expect(save).to_be_disabled()
            confirmation.click()
            save.click()
            expect(page.get_by_role('heading', name=re.compile('^Data awal'))).to_be_visible(timeout=30000)
            assert counts == {'preview': 1, 'confirm': 1}
            assert not errors, errors
            context.close()
        browser.close()
    print('PASS: Excel chooser -> upload -> review -> explicit confirmation -> Data awal at 3 viewports.')
    print('Synthetic API interception only; no real backend or business writes.')


if __name__ == '__main__':
    main()
