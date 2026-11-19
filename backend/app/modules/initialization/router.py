import json
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text

from app.core.errors import AppError
from app.core.pagination import Page, page_params
from app.core.idempotency import BusinessRequest, parse_key, payload_hash, remember, replay
from app.db.session import lock_business, open_session
from app.deps import check_mode
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.initialization.schemas import DraftInput, DraftUpdate, FinalizeInput, SettingsInput
from app.modules.initialization.service import encode_draft, materialize, reconciliation
from app.modules.initialization.schemas import ExcelImportInput
from app.modules.initialization.import_excel import MAX_FILE, plan_import, read_workbook, save_import, stable_id

router = APIRouter(prefix='/initialization', tags=['initialization'])


@router.post('/import/preview')
def preview_excel(request: Request, file: UploadFile, manager=Depends(require_manager)):
    if not (file.filename or '').lower().endswith('.xlsx'):
        raise AppError('IMPORT_INVALID', 'Pilih template Excel .xlsx.', 422)
    tables = read_workbook(file.file.read(MAX_FILE + 1))
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'PREPARATION')
        result, _ = plan_import(db, settings, request.app.state.clock.today(), tables)
    return envelope(request, result)


@router.post('/import/confirm')
def confirm_excel(payload: ExcelImportInput, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        values = {'tables': payload.tables, 'cutover_date': str(settings['cutover_date'])}
        # Content-based identity survives file renames, reloads and a lost success response.
        key = stable_id('batch', payload_hash(values))
        previous = replay(db, manager['manager_id'], 'initialization.import', key, values)
        if previous is not None:
            return envelope(request, previous['response_data'])
        check_mode(settings, 'PREPARATION')
        result, changes = plan_import(db, settings, request.app.state.clock.today(), payload.tables)
        if result['preview_hash'] != payload.preview_hash:
            raise AppError('IMPORT_STALE', 'Data berubah setelah pratinjau. Unggah ulang dan tinjau kembali.', 409)
        if not result['can_import']:
            raise AppError('IMPORT_INVALID', 'Perbaiki semua kesalahan sebelum impor.', 422)
        saved = save_import(db, manager['manager_id'], changes)
        remember(db, manager['manager_id'], 'initialization.import', key, values, saved)
    return envelope(request, saved)


def settings_row(db):
    return db.execute(text('SELECT * FROM kamartha.app_settings WHERE id=1')).mappings().one()


def expect_version(actual, expected):
    if actual != expected:
        raise AppError('VERSION_CONFLICT', 'Data sudah berubah. Muat ulang dan tinjau kembali.', 409)


def bump_version(db):
    db.execute(text('UPDATE kamartha.app_settings SET version=version+1 WHERE id=1'))


@router.get('/settings')
def get_settings(request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        data = dict(settings_row(db))
        data['packages'] = [dict(row) for row in db.execute(text('SELECT * FROM kamartha.packages WHERE is_active ORDER BY occupant_type,period_months')).mappings()]
    return envelope(request, data)


@router.put('/settings')
def put_settings(payload: SettingsInput, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        command = BusinessRequest(db, request, manager, 'initialization.settings', payload.model_dump())
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        check_mode(settings, 'PREPARATION')
        expect_version(settings['version'], payload.expected_version)
        if payload.cutover_date > request.app.state.clock.today():
            raise AppError('DATE_REJECTED', 'Tanggal mulai pencatatan tidak boleh di masa depan.', 422)
        db.execute(text('UPDATE kamartha.app_settings SET cutover_date=:date,version=version+1 WHERE id=1'), {'date': payload.cutover_date})
        result = command.save(dict(settings_row(db)))
    return envelope(request, result)


@router.get('/records')
def list_records(request: Request, page: Page = Depends(page_params), manager=Depends(require_manager)):
    with open_session(request) as db:
        total = db.scalar(text('SELECT count(*) FROM kamartha.initialization_records'))
        rows = db.execute(text('SELECT * FROM kamartha.initialization_records ORDER BY created_at,id LIMIT :limit OFFSET :offset'),
                          {'limit': page.limit, 'offset': page.offset}).mappings().all()
    return envelope(request, {'items': [dict(row) for row in rows], 'pagination': page.metadata(total)})


@router.get('/records/{record_id}')
def get_record(record_id: UUID, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        row = db.execute(text('SELECT * FROM kamartha.initialization_records WHERE id=:id'), {'id': record_id}).mappings().one_or_none()
    if row is None:
        raise AppError('NOT_FOUND', 'Berkas tidak ditemukan.', 404)
    return envelope(request, dict(row))


@router.post('/records', status_code=201)
def create_record(payload: DraftInput, request: Request, manager=Depends(require_manager)):
    encoded = encode_draft(payload.draft_data)
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        values = payload.model_dump(mode='json')
        previous = replay(db, manager['manager_id'], 'initialization.create', payload.client_record_key, values)
        if previous is not None:
            return envelope(request, previous['response_data'])
        check_mode(settings, 'PREPARATION')
        if settings['cutover_date'] is None:
            raise AppError('CUTOVER_REQUIRED', 'Simpan tanggal mulai pencatatan terlebih dahulu.', 422)
        row = db.execute(text('SELECT * FROM kamartha.initialization_records WHERE client_record_key=:key'), {'key': payload.client_record_key}).mappings().one_or_none()
        if row:
            if payload_hash(row['draft_data']) != payload_hash(payload.draft_data):
                raise AppError('IDEMPOTENCY_CONFLICT', 'Kunci berkas sudah dipakai dengan isian berbeda.', 409)
        else:
            row = db.execute(text('''
                INSERT INTO kamartha.initialization_records(client_record_key,draft_data,created_by)
                VALUES (:key,CAST(:data AS JSONB),:manager) RETURNING *
            '''), {'key': payload.client_record_key, 'data': encoded, 'manager': manager['manager_id']}).mappings().one()
            bump_version(db)
        result = jsonable_encoder(dict(row))
        remember(db, manager['manager_id'], 'initialization.create', payload.client_record_key, values, result, 201)
    return envelope(request, result)


@router.patch('/records/{record_id}')
def update_record(record_id: UUID, payload: DraftUpdate, request: Request, manager=Depends(require_manager)):
    encoded = encode_draft(payload.draft_data)
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        command = BusinessRequest(db, request, manager, f'initialization.update.{record_id}', payload.model_dump())
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        check_mode(settings, 'PREPARATION')
        row = db.execute(text('SELECT * FROM kamartha.initialization_records WHERE id=:id'), {'id': record_id}).mappings().one_or_none()
        if row is None:
            raise AppError('NOT_FOUND', 'Berkas tidak ditemukan.', 404)
        expect_version(row['version'], payload.expected_version)
        row = db.execute(text('''UPDATE kamartha.initialization_records SET draft_data=CAST(:data AS JSONB),
            state='DRAFT',validation_errors=NULL,version=version+1 WHERE id=:id RETURNING *'''),
            {'id': record_id, 'data': encoded}).mappings().one()
        bump_version(db)
        result = command.save(dict(row))
    return envelope(request, result)


@router.get('/reconciliation')
def get_reconciliation(request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        settings = settings_row(db)
        if settings['mode'] == 'ACTIVE':
            stored = db.scalar(text('SELECT reconciliation_summary FROM kamartha.initialization_finalizations WHERE singleton_key=1'))
            summary = {**stored, 'can_finalize': False, 'finalized': True}
        else:
            summary, _ = reconciliation(db, settings, request.app.state.clock.today())
    return envelope(request, jsonable_encoder(summary))


@router.post('/finalize')
def finalize(payload: FinalizeInput, request: Request, manager=Depends(require_manager),
             idempotency_key: str = Header(...)):
    key = parse_key(idempotency_key)
    values = payload.model_dump(mode='json')
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        previous = replay(db, manager['manager_id'], 'initialization.finalize', key, values)
        if previous:
            return envelope(request, previous['response_data'])
        check_mode(settings, 'PREPARATION')
        expect_version(settings['version'], payload.expected_version)
        summary, valid = reconciliation(db, settings, request.app.state.clock.today())
        if not summary['can_finalize']:
            raise AppError('INITIALIZATION_INVALID', 'Data awal belum lengkap atau bertentangan.', 422, summary['errors'])
        if summary['reconciliation_hash'] != payload.reconciliation_hash:
            raise AppError('RECONCILIATION_CHANGED', 'Rekap berubah. Muat ulang dan tinjau kembali.', 409)
        materialize(db, valid, manager['manager_id'])
        finalization_id = db.scalar(text('''
            INSERT INTO kamartha.initialization_finalizations(cutover_date,resident_count,occupied_room_count,
                invoice_count,total_receivable,reconciliation_summary,confirmed_by)
            VALUES (:cutover,:residents,:rooms,:invoices,:receivable,CAST(:summary AS JSONB),:manager) RETURNING id
        '''), {'cutover': settings['cutover_date'], 'residents': summary['resident_count'],
               'rooms': summary['occupied_room_count'], 'invoices': summary['invoice_count'],
               'receivable': summary['total_receivable'], 'summary': json.dumps(jsonable_encoder(summary)),
               'manager': manager['manager_id']})
        db.execute(text('''UPDATE kamartha.app_settings SET mode='ACTIVE',finalized_at=:now,
            finalized_by=:manager,version=version+1 WHERE id=1'''),
            {'now': request.app.state.clock.now(), 'manager': manager['manager_id']})
        result = {'mode': 'ACTIVE', 'finalization_id': str(finalization_id), 'total_receivable': summary['total_receivable']}
        remember(db, manager['manager_id'], 'initialization.finalize', key, values, result)
    return envelope(request, result)
