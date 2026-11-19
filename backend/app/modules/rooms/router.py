from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text

from app.core.errors import AppError
from app.core.pagination import Page, page_params
from app.core.idempotency import BusinessRequest
from app.db.session import lock_business, open_session
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.rooms.schemas import RoomInput

router = APIRouter(prefix='/rooms', tags=['rooms'], dependencies=[Depends(require_manager)])

ROOM_SELECT = '''
    SELECT r.*, CASE
      WHEN EXISTS (SELECT 1 FROM kamartha.leases l JOIN kamartha.occupancies o ON o.lease_id=l.id
                   WHERE l.room_id=r.id AND o.state='STAYING' AND l.effective_ends_on<=:today)
        THEN 'NEEDS_CONFIRMATION'
      WHEN EXISTS (SELECT 1 FROM kamartha.leases l JOIN kamartha.occupancies o ON o.lease_id=l.id
                   WHERE l.room_id=r.id AND o.state='STAYING' AND o.entered_on<=:today
                   AND l.starts_on<=:today AND l.effective_ends_on>:today) THEN 'OCCUPIED'
      ELSE 'EMPTY' END AS occupancy_status
    FROM kamartha.rooms r
'''


@router.get('')
def list_rooms(request: Request, page: Page = Depends(page_params), q: str = Query('', max_length=30)):
    params = {'q': '%' + q.strip().replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%',
              'limit': page.limit, 'offset': page.offset, 'today': request.app.state.clock.today()}
    with open_session(request) as db:
        total = db.scalar(text("SELECT count(*) FROM kamartha.rooms WHERE number ILIKE :q ESCAPE '!'"), params)
        rows = db.execute(text(ROOM_SELECT + " WHERE r.number ILIKE :q ESCAPE '!' ORDER BY lower(r.number),r.id LIMIT :limit OFFSET :offset"), params).mappings().all()
    return envelope(request, {'items': [dict(row) for row in rows], 'pagination': page.metadata(total)})


@router.get('/{room_id}')
def get_room(room_id: UUID, request: Request):
    with open_session(request) as db:
        row = db.execute(text(ROOM_SELECT + ' WHERE r.id=:id'),
                         {'id': room_id, 'today': request.app.state.clock.today()}).mappings().one_or_none()
        leases = db.execute(text('''SELECT id,starts_on,effective_ends_on,occupant_type_snapshot,
            period_months_snapshot,period_price_snapshot FROM kamartha.leases WHERE room_id=:id
            ORDER BY starts_on,id'''), {'id': room_id}).mappings().all()
    if row is None:
        raise AppError('NOT_FOUND', 'Kamar tidak ditemukan.', 404)
    return envelope(request, {**dict(row), 'leases': [dict(lease) for lease in leases]})


@router.post('', status_code=201)
def create_room(payload: RoomInput, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        lock_business(db)
        command = BusinessRequest(db, request, manager, 'rooms.create', payload.model_dump())
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        row = db.execute(text('''
            INSERT INTO kamartha.rooms(number,number_normalized,room_type,supported_occupants,
                reference_price,is_available_for_new_lease)
            VALUES (:number,lower(CAST(:number AS VARCHAR)),:room_type,:supported_occupants,:reference_price,:is_available_for_new_lease)
            RETURNING *
        '''), payload.model_dump()).mappings().one()
        result = command.save(dict(row), 201)
    return envelope(request, result)


@router.patch('/{room_id}')
def update_room(room_id: UUID, payload: RoomInput, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        lock_business(db)
        command = BusinessRequest(db, request, manager, f'rooms.update.{room_id}', payload.model_dump())
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        if db.scalar(text('''SELECT EXISTS(SELECT 1 FROM kamartha.leases
            WHERE room_id=:id AND occupant_type_snapshot>:capacity)'''),
            {'id': room_id, 'capacity': payload.supported_occupants}):
            raise AppError('CAPACITY_CONFLICT', 'Dukungan kamar tidak boleh merusak kontrak yang sudah tercatat.', 409)
        row = db.execute(text('''
            UPDATE kamartha.rooms SET number=:number,number_normalized=lower(CAST(:number AS VARCHAR)),room_type=:room_type,
                supported_occupants=:supported_occupants,reference_price=:reference_price,
                is_available_for_new_lease=:is_available_for_new_lease WHERE id=:id RETURNING *
        '''), {**payload.model_dump(), 'id': room_id}).mappings().one_or_none()
        if row is None:
            raise AppError('NOT_FOUND', 'Kamar tidak ditemukan.', 404)
        result = command.save(dict(row))
    return envelope(request, result)
