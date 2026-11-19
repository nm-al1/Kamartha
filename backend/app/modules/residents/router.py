from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text

from app.core.errors import AppError
from app.core.pagination import Page, page_params
from app.core.idempotency import BusinessRequest
from app.db.session import lock_business, open_session
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.residents.schemas import ResidentInput

router = APIRouter(prefix='/residents', tags=['residents'], dependencies=[Depends(require_manager)])


@router.get('')
def list_residents(request: Request, page: Page = Depends(page_params), q: str = Query('', max_length=150)):
    params = {'q': '%' + q.strip().replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%',
              'limit': page.limit, 'offset': page.offset}
    with open_session(request) as db, db.begin():
        total = db.scalar(text("SELECT count(*) FROM kamartha.residents WHERE name ILIKE :q ESCAPE '!'"), params)
        rows = db.execute(text("""
            SELECT * FROM kamartha.residents WHERE name ILIKE :q ESCAPE '!'
            ORDER BY lower(name), id LIMIT :limit OFFSET :offset
        """), params).mappings().all()
    return envelope(request, {'items': [dict(row) for row in rows], 'pagination': page.metadata(total)})


@router.get('/{resident_id}')
def get_resident(resident_id: UUID, request: Request):
    with open_session(request) as db:
        row = db.execute(text('SELECT * FROM kamartha.residents WHERE id=:id'), {'id': resident_id}).mappings().one_or_none()
        history = db.execute(text('''SELECT o.state,o.entered_on,o.exited_on,o.exit_date_unknown,
            l.id AS lease_id,l.starts_on,l.effective_ends_on,r.number AS room_number
            FROM kamartha.occupancies o JOIN kamartha.leases l ON l.id=o.lease_id
            JOIN kamartha.rooms r ON r.id=l.room_id WHERE o.resident_id=:id
            ORDER BY o.entered_on,o.id'''), {'id': resident_id}).mappings().all()
    if row is None:
        raise AppError('NOT_FOUND', 'Penghuni tidak ditemukan.', 404)
    return envelope(request, {**dict(row), 'history': [dict(h) for h in history]})


@router.post('', status_code=201)
def create_resident(payload: ResidentInput, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        lock_business(db)
        command = BusinessRequest(db, request, manager, 'residents.create', payload.model_dump())
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        row = db.execute(text('''
            INSERT INTO kamartha.residents(name, identity_type, identity_number, whatsapp_number, notes)
            VALUES (:name, :identity_type, :identity_number, :whatsapp_number, :notes) RETURNING *
        '''), payload.model_dump()).mappings().one()
        result = command.save(dict(row), 201)
    return envelope(request, result)


@router.patch('/{resident_id}')
def update_resident(resident_id: UUID, payload: ResidentInput, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        lock_business(db)
        command = BusinessRequest(db, request, manager, f'residents.update.{resident_id}', payload.model_dump())
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        row = db.execute(text('''
            UPDATE kamartha.residents SET name=:name, identity_type=:identity_type,
                identity_number=:identity_number, whatsapp_number=:whatsapp_number,
                notes=:notes, updated_at=now() WHERE id=:id RETURNING *
        '''), {**payload.model_dump(), 'id': resident_id}).mappings().one_or_none()
        if row is None:
            raise AppError('NOT_FOUND', 'Penghuni tidak ditemukan.', 404)
        result = command.save(dict(row))
    return envelope(request, result)
