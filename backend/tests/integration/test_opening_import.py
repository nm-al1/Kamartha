from io import BytesIO
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

import pytest
from sqlalchemy import text

from app.core.errors import AppError
from app.modules.initialization import router as init_router
from app.modules.initialization.import_excel import HEADERS, plan_import, read_workbook
from test_stage_b import api  # Reuse the isolated PostgreSQL/authenticated API fixture.


pytestmark = pytest.mark.integration
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
TEMPLATE = Path(__file__).resolve().parents[3] / 'docs/templates/KAMARTHA-template-data-lama-v2.xlsx'


def tables():
    return {
        'Kamar': [['IMPORT-01']],
        'Penghuni': [['P001', 'Penghuni uji impor', 'DUMMY', 'IMPORT-001', None, None]],
        'Kontrak': [['K001', 'IMPORT-01', '1', '1', '2026-03-01', '2026-04-01']],
        'Penempatan': [['K001', 'P001', 'Ya', '2026-03-01', 'Tinggal', None, 'Tidak']],
        'Sisa tagihan awal': [['K001', '2026-03-01', '2026-03-01', '700000', '200000']],
    }


def test_projection_direct(migrated_connection):
    settings = dict(migrated_connection.execute(text('SELECT * FROM kamartha.app_settings WHERE id=1')).mappings().one())
    settings['cutover_date'] = date(2026, 3, 1)
    result, _ = plan_import(migrated_connection, settings, date(2026, 3, 1), tables())
    assert result['can_import'], result['errors']


def test_five_room_v2_example_projects_with_paid_current_periods(migrated_connection):
    settings = dict(migrated_connection.execute(text('SELECT * FROM kamartha.app_settings WHERE id=1')).mappings().one())
    settings['cutover_date'] = date(2026, 11, 12)
    example = TEMPLATE.with_name('KAMARTHA-contoh-dummy-5-kamar-v2.xlsx')
    result, changes = plan_import(migrated_connection, settings, date(2026, 11, 12), read_workbook(example.read_bytes()))
    assert result['can_import'], result['errors']
    assert [len(rows) for rows in changes] == [5, 8, 5]
    assert result['total_receivable'] == 1700000


def workbook(data):
    output = BytesIO()
    with ZipFile(TEMPLATE) as source, ZipFile(output, 'w', ZIP_DEFLATED) as dest:
        for name in source.namelist():
            content = source.read(name)
            for index, sheet in enumerate(HEADERS, 3):
                if name != f'xl/worksheets/sheet{index}.xml':
                    continue
                root = ET.fromstring(content)
                for number, row in enumerate(data[sheet], 2):
                    for col, value in enumerate(row):
                        cell = root.find(f'.//{NS}c[@r="{chr(65 + col)}{number}"]')
                        for child in list(cell):
                            cell.remove(child)
                        if value is not None:
                            cell.set('t', 'inlineStr')
                            ET.SubElement(ET.SubElement(cell, NS + 'is'), NS + 't').text = str(value)
                content = ET.tostring(root)
            dest.writestr(name, content)
    return output.getvalue()


def preview(api, data=None):
    settings = api.get('/api/v1/initialization/settings').json()['data']
    if settings['cutover_date'] is None:
        result = api.put('/api/v1/initialization/settings', json={
            'cutover_date': '2026-03-01', 'expected_version': settings['version']})
        assert result.status_code == 200, result.text
    result = api.post('/api/v1/initialization/import/preview',
                      files={'file': ('data.xlsx', workbook(data or tables()), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
    assert result.status_code == 200, result.text
    return result.json()['data']


def confirm(api, result):
    return api.post('/api/v1/initialization/import/confirm', json={
        'tables': result['tables'], 'preview_hash': result['preview_hash'], 'confirmed': True})


def test_preview_atomic_import_and_content_replay(api, migrated_connection):
    result = preview(api)
    assert result['can_import'], result['errors']
    assert result['new_records'] == 1 and result['total_receivable'] == 200000
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.rooms')) == 0
    saved = confirm(api, result)
    assert saved.status_code == 200, saved.text
    assert saved.json()['data'] == {'created_rooms': 1, 'created_residents': 1, 'created_records': 1}
    assert confirm(api, result).json()['data'] == saved.json()['data']
    repeated = preview(api)
    assert repeated['can_import'], repeated['errors']
    assert repeated['new_records'] == repeated['new_residents'] == repeated['new_rooms'] == 0
    assert confirm(api, repeated).status_code == 200
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.initialization_records')) == 1
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.leases')) == 0
    assert api.get('/api/v1/initialization/settings').json()['data']['mode'] == 'PREPARATION'
    summary = api.get('/api/v1/initialization/reconciliation').json()['data']
    assert summary['can_finalize'] and summary['total_receivable'] == 200000


@pytest.mark.parametrize('mutation', ['missing_current', 'duplicate_room', 'bad_price', 'bad_date', 'bad_responsible', 'duplicate_identity', 'conflict'])
def test_invalid_import_is_previewed_but_never_written(api, migrated_connection, mutation):
    data = tables()
    if mutation == 'missing_current':
        data['Sisa tagihan awal'] = []
    elif mutation == 'duplicate_room':
        data['Kamar'] *= 2
    elif mutation == 'bad_price':
        data['Sisa tagihan awal'][0][3] = '600000'
    elif mutation == 'bad_date':
        data['Kontrak'][0][4] = '2026-02-30'
    elif mutation == 'bad_responsible':
        data['Penempatan'][0][2] = 'Tidak'
    elif mutation == 'duplicate_identity':
        data['Penghuni'].append(['P002', 'Nama sama identitas', 'DUMMY', 'IMPORT-001', None, None])
    elif mutation == 'conflict':
        data['Kontrak'].append(['K002', *data['Kontrak'][0][1:]])
        data['Penempatan'].append(['K002', *data['Penempatan'][0][1:]])
        data['Sisa tagihan awal'].append(['K002', *data['Sisa tagihan awal'][0][1:]])
    result = preview(api, data)
    assert not result['can_import'] and result['errors']
    assert confirm(api, result).status_code == 422
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.rooms')) == 0


def test_stale_preview_rejected(api, migrated_connection):
    result = preview(api)
    response = api.post('/api/v1/rooms', json={'number': 'OTHER', 'room_type': 'Standar',
        'supported_occupants': 2, 'reference_price': 700000})
    assert response.status_code == 201
    assert confirm(api, result).status_code == 409
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.initialization_records')) == 0


def test_rollback_if_any_write_fails(api, migrated_connection, monkeypatch):
    result = preview(api)
    original = init_router.save_import

    def fail(db, manager_id, changes):
        original(db, manager_id, changes)
        raise AppError('TEST_FAILURE', 'Simulasi gagal sebelum commit.', 409)

    monkeypatch.setattr(init_router, 'save_import', fail)
    assert confirm(api, result).status_code == 409
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.rooms')) == 0
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.residents')) == 0
    assert migrated_connection.scalar(text('SELECT count(*) FROM kamartha.initialization_records')) == 0


def test_import_requires_auth_csrf_confirmation_and_preparation(api):
    result = preview(api)
    assert api.post('/api/v1/initialization/import/confirm', json={
        'tables': result['tables'], 'preview_hash': result['preview_hash'], 'confirmed': False}).status_code == 422
    assert api.post('/api/v1/initialization/import/confirm', json={}, headers={'X-CSRF-Token': 'bad'}).status_code == 403
    api.cookies.clear()
    assert confirm(api, result).status_code == 401


def test_active_mode_blocks_new_import(api, migrated_connection):
    result = preview(api)
    summary = api.get('/api/v1/initialization/reconciliation').json()['data']
    finalized = api.post('/api/v1/initialization/finalize', json={
        'expected_version': summary['version'], 'reconciliation_hash': summary['reconciliation_hash'],
        'confirmed_matches': True, 'confirmed_old_periods_settled': True})
    assert finalized.status_code == 200, finalized.text
    assert confirm(api, result).status_code == 409
    response = api.post('/api/v1/initialization/import/preview', files={'file': ('data.xlsx', workbook(tables()))})
    assert response.status_code == 409


def test_existing_matching_data_reused_but_mismatch_not_overwritten(api, migrated_connection):
    result = preview(api)
    assert confirm(api, result).status_code == 200
    changed = tables()
    changed['Penghuni'][0][1] = 'Nama berbeda'
    result = preview(api, changed)
    assert not result['can_import']
    assert any('tidak ditimpa' in error['message'].lower() for error in result['errors'])
    assert confirm(api, result).status_code == 422
    assert migrated_connection.scalar(text('SELECT name FROM kamartha.residents')) == 'Penghuni uji impor'
