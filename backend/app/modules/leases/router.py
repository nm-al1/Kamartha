import json
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text

from app.core.errors import AppError
from app.core.idempotency import BusinessRequest
from app.core.pagination import Page, page_params
from app.db.session import lock_business, open_session
from app.deps import check_mode
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.billing.rules import period_boundary
from app.modules.leases.rules import (
    contract_end, next_invoice, replaceable, resident_conflict, room_conflict,
    status_of, validate_exit, validate_extension, validate_new_contract,
)
from app.modules.leases.schemas import (
    LeaseContinue, LeaseCreate, LeaseExtend, OccupancyExit, Replacement,
    ResponsibleChange,
)
from app.modules.leases.service import lease_detail, list_leases

router = APIRouter(prefix='/leases', tags=['leases'])


def load_room_and_package(db, room_id, package_id):
    room = db.execute(text('SELECT * FROM kamartha.rooms WHERE id=:id'), {'id': room_id}).mappings().one_or_none()
    package = db.execute(text('SELECT * FROM kamartha.packages WHERE id=:id AND is_active'),
                         {'id': package_id}).mappings().one_or_none()
    if room is None or package is None:
        raise AppError('NOT_FOUND', 'Kamar atau paket tidak ditemukan.', 404)
    return room, package


def ensure_residents(db, resident_ids):
    unique = list(dict.fromkeys(resident_ids))
    rows = db.execute(text('SELECT id FROM kamartha.residents WHERE id = ANY(:ids)'),
                      {'ids': unique}).scalars().all()
    if len(rows) != len(unique):
        raise AppError('NOT_FOUND', 'Salah satu penghuni tidak ditemukan.', 404)


def room_rows(db, room_id, exclude_lease=None):
    params = {'room': room_id}
    sql = """
        SELECT l.id,l.starts_on,l.effective_ends_on,
               EXISTS (SELECT 1 FROM kamartha.occupancies o
                       WHERE o.lease_id=l.id AND o.state='STAYING') AS staying
        FROM kamartha.leases l WHERE l.room_id=:room
    """
    if exclude_lease is not None:
        sql += ' AND l.id <> :exclude'
        params['exclude'] = exclude_lease
    return db.execute(text(sql), params).mappings().all()


def resident_rows(db, resident_id, exclude_lease=None):
    params = {'resident': resident_id}
    sql = """
        SELECT o.entered_on,o.state,o.exited_on,o.continued_on
        FROM kamartha.occupancies o WHERE o.resident_id=:resident
    """
    if exclude_lease is not None:
        sql += ' AND o.lease_id <> :exclude'
        params['exclude'] = exclude_lease
    return db.execute(text(sql), params).mappings().all()


def insert_responsible(db, lease_id, occupancy_id, manager_id, reason, valid_from=None):
    db.execute(text("""
        INSERT INTO kamartha.responsible_history(lease_id,occupancy_id,valid_from,reason,actor_id)
        VALUES (:lease,:occupancy,COALESCE(CAST(:valid_from AS TIMESTAMPTZ),clock_timestamp()),:reason,:manager)
    """), {'lease': lease_id, 'occupancy': occupancy_id, 'valid_from': valid_from,
           'reason': reason, 'manager': manager_id})


def close_responsible(db, lease_id):
    db.execute(text("""
        UPDATE kamartha.responsible_history SET valid_until=clock_timestamp()
        WHERE lease_id=:lease AND valid_until IS NULL
    """), {'lease': lease_id})


def event(db, request, manager_id, event_type, lease_id, reason, before=None, after=None):
    db.execute(text("""
        INSERT INTO kamartha.business_events(event_type,entity_type,entity_id,actor_id,
            reason,before_data,after_data,request_id)
        VALUES (:type,'LEASE',:entity,:actor,:reason,
            CAST(:before AS JSONB),CAST(:after AS JSONB),:request)
    """), {'type': event_type, 'entity': lease_id, 'actor': manager_id, 'reason': reason,
           'before': None if before is None else json.dumps(jsonable_encoder(before), allow_nan=False),
           'after': None if after is None else json.dumps(jsonable_encoder(after), allow_nan=False),
           'request': UUID(request.state.request_id)})


def get_lease_row(db, lease_id):
    row = db.execute(text('SELECT * FROM kamartha.leases WHERE id=:id FOR UPDATE'),
                     {'id': lease_id}).mappings().one_or_none()
    if row is None:
        raise AppError('NOT_FOUND', 'Kontrak tidak ditemukan.', 404)
    return row


def expected_version(row, requested):
    if row['version'] != requested:
        raise AppError('VERSION_CONFLICT', 'Data sudah berubah. Muat ulang dan tinjau kembali.', 409)


def detail_or_404(db, lease_id, today):
    data = lease_detail(db, lease_id, today)
    if data is None:
        raise AppError('NOT_FOUND', 'Kontrak tidak ditemukan.', 404)
    return data


@router.get('')
def list_contracts(request: Request, page: Page = Depends(page_params),
                   q: str = Query('', max_length=150), manager=Depends(require_manager)):
    with open_session(request) as db:
        items, total = list_leases(db, q=q, limit=page.limit, offset=page.offset,
                                   today=request.app.state.clock.today())
    return envelope(request, {'items': items, 'pagination': page.metadata(total)})


@router.get('/{lease_id}')
def get_contract(lease_id: UUID, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        data = detail_or_404(db, lease_id, request.app.state.clock.today())
    return envelope(request, data)


@router.post('', status_code=201)
def create_contract(payload: LeaseCreate, request: Request, manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, 'leases.create', payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        room, package = load_room_and_package(db, payload.room_id, payload.package_id)
        if not room['is_available_for_new_lease']:
            raise AppError('ROOM_CLOSED', 'Kamar tidak dibuka untuk kontrak baru.', 409)
        ensure_residents(db, payload.resident_ids)
        ends_on = contract_end(payload.starts_on, package['period_months'], payload.periods)
        try:
            validate_new_contract(
                starts_on=payload.starts_on, cutover=settings['cutover_date'], today=today,
                price=payload.price, occupant_type=package['occupant_type'],
                period_months=package['period_months'],
                capacity=room['supported_occupants'], resident_ids=payload.resident_ids,
                responsible_resident_id=payload.responsible_resident_id,
            )
        except ValueError as exc:
            raise AppError('CONTRACT_INVALID', str(exc), 422) from exc
        if room_conflict(room_rows(db, payload.room_id), starts_on=payload.starts_on, ends_on=ends_on):
            raise AppError('ROOM_CONFLICT', 'Kamar sudah dipakai pada rentang tersebut atau masih tertahan penghuni.', 409)
        for resident_id in payload.resident_ids:
            if resident_conflict(resident_rows(db, resident_id), starts_on=payload.starts_on, ends_on=ends_on):
                raise AppError('PERSON_CONFLICT', 'Salah satu penghuni sudah memiliki penghunian yang bertumpuk.', 409)
        lease_id = db.scalar(text("""
            INSERT INTO kamartha.leases(room_id,package_id,starts_on,agreed_ends_on,effective_ends_on,
                period_anchor,occupant_type_snapshot,period_months_snapshot,period_price_snapshot,
                source,created_by)
            VALUES (:room,:package,:start,:end,:end,:start,:occupants,:months,:price,'OPERATIONAL',:manager)
            RETURNING id
        """), {'room': payload.room_id, 'package': payload.package_id, 'start': payload.starts_on,
               'end': ends_on, 'occupants': package['occupant_type'],
               'months': package['period_months'], 'price': payload.price,
               'manager': manager['manager_id']})
        for resident_id in payload.resident_ids:
            occupancy_id = db.scalar(text("""
                INSERT INTO kamartha.occupancies(lease_id,resident_id,entered_on,state,recorded_by)
                VALUES (:lease,:resident,:entered,'STAYING',:manager) RETURNING id
            """), {'lease': lease_id, 'resident': resident_id, 'entered': payload.starts_on,
                   'manager': manager['manager_id']})
            if resident_id == payload.responsible_resident_id:
                insert_responsible(db, lease_id, occupancy_id, manager['manager_id'],
                                   'Penanggung jawab awal')
        invoice = next_invoice(payload.starts_on, package['period_months'], payload.price)
        db.execute(text("""
            INSERT INTO kamartha.invoices(lease_id,period_start,period_end,due_on,amount,source)
            VALUES (:lease,:start,:end,:due,:amount,'OPERATIONAL')
        """), {'lease': lease_id, 'start': invoice['period_start'], 'end': invoice['period_end'],
               'due': invoice['due_on'], 'amount': invoice['amount']})
        event(db, request, manager['manager_id'], 'LEASE_CREATED', lease_id, 'Kontrak baru')
        result = command.save(detail_or_404(db, lease_id, today), 201)
    return envelope(request, result)


@router.post('/{lease_id}/extend')
def extend_contract(lease_id: UUID, payload: LeaseExtend, request: Request,
                    manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, f'leases.extend.{lease_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        lease = get_lease_row(db, lease_id)
        expected_version(lease, payload.expected_version)
        try:
            validate_extension(periods=payload.periods,
                               effective_ends_on=lease['effective_ends_on'], today=today)
        except ValueError as exc:
            raise AppError('CONTRACT_INVALID', str(exc), 422) from exc
        if lease['effective_ends_on'] != lease['agreed_ends_on']:
            raise AppError('CONTRACT_ENDED', 'Kontrak yang sudah dipotong tidak dapat diperpanjang.', 409)
        index = 1
        while period_boundary(lease['starts_on'], lease['period_months_snapshot'], index) < lease['agreed_ends_on']:
            index += 1
        new_end = contract_end(lease['starts_on'], lease['period_months_snapshot'], index + payload.periods)
        if room_conflict(room_rows(db, lease['room_id'], exclude_lease=lease_id),
                         starts_on=lease['starts_on'], ends_on=new_end):
            raise AppError('ROOM_CONFLICT', 'Kamar sudah dipakai pada rentang perpanjangan.', 409)
        updated = db.execute(text("""
            UPDATE kamartha.leases SET agreed_ends_on=:end,effective_ends_on=:end,
                version=version+1 WHERE id=:id RETURNING *
        """), {'end': new_end, 'id': lease_id}).mappings().one()
        event(db, request, manager['manager_id'], 'LEASE_EXTENDED', lease_id,
              f'Perpanjangan {payload.periods} periode', dict(lease), dict(updated))
        result = command.save(detail_or_404(db, lease_id, today))
    return envelope(request, result)


@router.post('/{lease_id}/occupancies/{occupancy_id}/exit')
def exit_occupancy(lease_id: UUID, occupancy_id: UUID, payload: OccupancyExit,
                   request: Request, manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager,
                                  f'leases.exit.{lease_id}.{occupancy_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        get_lease_row(db, lease_id)
        occupancy = db.execute(text("""
            SELECT * FROM kamartha.occupancies WHERE id=:id AND lease_id=:lease FOR UPDATE
        """), {'id': occupancy_id, 'lease': lease_id}).mappings().one_or_none()
        if occupancy is None:
            raise AppError('NOT_FOUND', 'Penghunian tidak ditemukan pada kontrak ini.', 404)
        if occupancy['state'] != 'STAYING':
            raise AppError('OCCUPANCY_CLOSED', 'Penghunian ini sudah tidak aktif.', 409)
        try:
            validate_exit(exited_on=payload.exited_on, entered_on=occupancy['entered_on'], today=today)
        except ValueError as exc:
            raise AppError('EXIT_INVALID', str(exc), 422) from exc
        others = db.execute(text("""
            SELECT o.*,r.name FROM kamartha.occupancies o JOIN kamartha.residents r ON r.id=o.resident_id
            WHERE o.lease_id=:lease AND o.id<>:id AND o.state='STAYING'
            ORDER BY o.entered_on,o.id
        """), {'lease': lease_id, 'id': occupancy_id}).mappings().all()
        responsible = db.execute(text("""
            SELECT * FROM kamartha.responsible_history
            WHERE lease_id=:lease AND valid_until IS NULL FOR UPDATE
        """), {'lease': lease_id}).mappings().one_or_none()
        db.execute(text("""
            UPDATE kamartha.occupancies SET state='EXITED',exited_on=:date,exit_date_unknown=false
            WHERE id=:id
        """), {'date': payload.exited_on, 'id': occupancy_id})
        if others:
            if responsible and responsible['occupancy_id'] == occupancy_id:
                successor = next((row for row in others
                                  if row['resident_id'] == payload.successor_resident_id), None)
                if successor is None:
                    raise AppError('SUCCESSOR_REQUIRED',
                                   'Pilih penanggung jawab berikutnya dari penghuni yang masih tinggal.', 422)
                close_responsible(db, lease_id)
                insert_responsible(db, lease_id, successor['id'], manager['manager_id'],
                                   payload.reason, valid_from=None)
        else:
            close_responsible(db, lease_id)
            paid_future = db.execute(text("""
                SELECT i.id,i.source FROM kamartha.invoices i
                WHERE i.lease_id=:lease AND i.status='ACTIVE' AND i.period_start>=:exit
                  AND (i.source='OPENING' OR i.opening_paid>0
                       OR EXISTS (SELECT 1 FROM kamartha.payment_allocations a
                               JOIN kamartha.payments p ON p.id=a.payment_id
                               WHERE a.invoice_id=i.id AND p.status='VALID'))
                ORDER BY (i.source='OPENING') DESC,i.period_start,i.id
                LIMIT 1
            """), {'lease': lease_id, 'exit': payload.exited_on}).mappings().first()
            if paid_future:
                if paid_future['source'] == 'OPENING':
                    raise AppError('OPENING_INVOICE_LOCKED',
                                   'Pengakhiran tidak boleh membatalkan tagihan saldo awal; '
                                   'koreksi data awal melalui pemeliharaan terverifikasi.', 409)
                raise AppError('PAID_PERIOD_CONFLICT',
                               'Tagihan periode mendatang sudah menerima pembayaran; pengakhiran yang memotong periode itu ditolak.',
                               409)
            db.execute(text("""
                UPDATE kamartha.invoices SET status='CANCELLED',cancellation_reason=:reason,
                    cancelled_at=:now,cancelled_by=:manager
                WHERE lease_id=:lease AND status='ACTIVE' AND period_start>=:exit
                  AND source='OPERATIONAL' AND opening_paid=0
            """), {'reason': payload.reason, 'now': request.app.state.clock.now(),
                   'manager': manager['manager_id'], 'lease': lease_id,
                   'exit': payload.exited_on})
            lease = db.execute(text('SELECT * FROM kamartha.leases WHERE id=:id'),
                               {'id': lease_id}).mappings().one()
            effective = min(max(payload.exited_on, lease['starts_on']), lease['agreed_ends_on'])
            reason = payload.reason if effective != lease['agreed_ends_on'] else lease['early_end_reason']
            db.execute(text("""
                UPDATE kamartha.leases SET effective_ends_on=:end,early_end_reason=:reason,
                    version=version+1 WHERE id=:id
            """), {'end': effective, 'reason': reason, 'id': lease_id})
        event(db, request, manager['manager_id'], 'OCCUPANCY_EXITED', lease_id,
              payload.reason, dict(occupancy), {'exited_on': payload.exited_on})
        result = command.save(detail_or_404(db, lease_id, today))
    return envelope(request, result)


@router.post('/{lease_id}/responsible')
def change_responsible(lease_id: UUID, payload: ResponsibleChange, request: Request,
                       manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, f'leases.responsible.{lease_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        get_lease_row(db, lease_id)
        occupancy = db.execute(text("""
            SELECT * FROM kamartha.occupancies WHERE id=:id AND lease_id=:lease AND state='STAYING'
        """), {'id': payload.occupancy_id, 'lease': lease_id}).mappings().one_or_none()
        if occupancy is None:
            raise AppError('OCCUPANCY_INVALID', 'Penanggung jawab harus penghuni yang masih tinggal.', 422)
        close_responsible(db, lease_id)
        insert_responsible(db, lease_id, occupancy['id'], manager['manager_id'], payload.reason)
        event(db, request, manager['manager_id'], 'RESPONSIBLE_CHANGED', lease_id,
              payload.reason, None, {'occupancy_id': str(occupancy['id'])})
        result = command.save(detail_or_404(db, lease_id, today))
    return envelope(request, result)


@router.post('/{lease_id}/occupancies', status_code=201)
def add_replacement(lease_id: UUID, payload: Replacement, request: Request,
                    manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, f'leases.replace.{lease_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        lease = get_lease_row(db, lease_id)
        room = db.execute(text('SELECT * FROM kamartha.rooms WHERE id=:id'),
                          {'id': lease['room_id']}).mappings().one()
        predecessor = db.execute(text("""
            SELECT * FROM kamartha.occupancies WHERE id=:id AND lease_id=:lease FOR UPDATE
        """), {'id': payload.predecessor_occupancy_id, 'lease': lease_id}).mappings().one_or_none()
        if predecessor is None:
            raise AppError('NOT_FOUND', 'Penghuni lama tidak ditemukan pada kontrak ini.', 404)
        ensure_residents(db, [payload.resident_id])
        occupied = db.scalar(text("""
            SELECT count(*) FROM kamartha.occupancies WHERE lease_id=:lease AND state='STAYING'
        """), {'lease': lease_id})
        try:
            replaceable(lease_ends_on=lease['effective_ends_on'], today=today,
                        entered_on=payload.entered_on, occupied_count=occupied,
                        capacity=min(lease['occupant_type_snapshot'], room['supported_occupants']),
                        predecessor_state=predecessor['state'],
                        predecessor_exit_unknown=predecessor['exit_date_unknown'])
        except ValueError as exc:
            raise AppError('REPLACEMENT_INVALID', str(exc), 422) from exc
        if predecessor['exited_on'] and payload.entered_on < predecessor['exited_on']:
            raise AppError('REPLACEMENT_INVALID',
                           'Tanggal masuk pengganti tidak boleh sebelum tanggal keluar penghuni lama.', 422)
        if resident_conflict(resident_rows(db, payload.resident_id),
                             starts_on=payload.entered_on,
                             ends_on=lease['effective_ends_on']):
            raise AppError('PERSON_CONFLICT', 'Penghuni baru sudah memiliki penghunian yang bertumpuk.', 409)
        occupancy_id = db.scalar(text("""
            INSERT INTO kamartha.occupancies(lease_id,resident_id,entered_on,state,
                predecessor_occupancy_id,recorded_by)
            VALUES (:lease,:resident,:entered,'STAYING',:predecessor,:manager) RETURNING id
        """), {'lease': lease_id, 'resident': payload.resident_id, 'entered': payload.entered_on,
               'predecessor': predecessor['id'], 'manager': manager['manager_id']})
        if db.scalar(text("""
            SELECT count(*) FROM kamartha.responsible_history
            WHERE lease_id=:lease AND valid_until IS NULL
        """), {'lease': lease_id}) == 0:
            insert_responsible(db, lease_id, occupancy_id, manager['manager_id'], payload.reason)
        event(db, request, manager['manager_id'], 'OCCUPANCY_REPLACED', lease_id,
              payload.reason, None, {'resident_id': str(payload.resident_id),
                                    'entered_on': payload.entered_on})
        result = command.save(detail_or_404(db, lease_id, today), 201)
    return envelope(request, result)


@router.post('/{lease_id}/continue', status_code=201)
def continue_contract(lease_id: UUID, payload: LeaseContinue, request: Request,
                      manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, f'leases.continue.{lease_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        old = get_lease_row(db, lease_id)
        room, package = load_room_and_package(db, old['room_id'], payload.package_id)
        ensure_residents(db, payload.resident_ids)
        if payload.starts_on < old['effective_ends_on']:
            raise AppError('CONTINUE_INVALID', 'Kontrak lanjutan tidak boleh dimulai sebelum kontrak lama berakhir.', 422)
        if payload.starts_on > today:
            raise AppError('CONTINUE_INVALID',
                           'Kontrak lanjutan baru dapat disimpan saat tanggal mulainya tiba; '
                           'hunian dan penanggung jawab lama tetap berlaku sampai saat itu.', 422)
        old_occupancies = db.execute(text("""
            SELECT * FROM kamartha.occupancies
            WHERE lease_id=:lease AND state='STAYING' ORDER BY entered_on,id
        """), {'lease': lease_id}).mappings().all()
        old_by_resident = {row['resident_id']: row for row in old_occupancies}
        if set(payload.resident_ids) != set(old_by_resident):
            raise AppError('CONTINUE_INVALID',
                           'Semua penghuni yang masih tinggal harus disertakan dalam kontrak lanjutan.',
                           422)
        ends_on = contract_end(payload.starts_on, package['period_months'], payload.periods)
        try:
            validate_new_contract(
                starts_on=payload.starts_on, cutover=settings['cutover_date'], today=today,
                price=payload.price, occupant_type=package['occupant_type'],
                period_months=package['period_months'],
                capacity=room['supported_occupants'], resident_ids=payload.resident_ids,
                responsible_resident_id=payload.responsible_resident_id,
            )
        except ValueError as exc:
            raise AppError('CONTRACT_INVALID', str(exc), 422) from exc
        if room_conflict(room_rows(db, old['room_id'], exclude_lease=lease_id),
                         starts_on=payload.starts_on, ends_on=ends_on):
            raise AppError('ROOM_CONFLICT', 'Kamar sudah dipakai pada rentang kontrak lanjutan.', 409)
        for resident_id in payload.resident_ids:
            if resident_conflict(resident_rows(db, resident_id, exclude_lease=lease_id),
                                 starts_on=payload.starts_on, ends_on=ends_on):
                raise AppError('PERSON_CONFLICT', 'Penghuni sudah memiliki penghunian lain yang bertumpuk.', 409)
        new_id = db.scalar(text("""
            INSERT INTO kamartha.leases(room_id,package_id,starts_on,agreed_ends_on,effective_ends_on,
                period_anchor,occupant_type_snapshot,period_months_snapshot,period_price_snapshot,
                source,created_by)
            VALUES (:room,:package,:start,:end,:end,:start,:occupants,:months,:price,'OPERATIONAL',:manager)
            RETURNING id
        """), {'room': old['room_id'], 'package': payload.package_id, 'start': payload.starts_on,
               'end': ends_on, 'occupants': package['occupant_type'],
               'months': package['period_months'], 'price': payload.price,
               'manager': manager['manager_id']})
        for resident_id in payload.resident_ids:
            old_occupancy = old_by_resident[resident_id]
            db.execute(text("""
                UPDATE kamartha.occupancies SET state='CONTINUED',continued_on=:date WHERE id=:id
            """), {'date': payload.starts_on, 'id': old_occupancy['id']})
            occupancy_id = db.scalar(text("""
                INSERT INTO kamartha.occupancies(lease_id,resident_id,entered_on,state,
                    predecessor_occupancy_id,recorded_by)
                VALUES (:lease,:resident,:entered,'STAYING',:predecessor,:manager) RETURNING id
            """), {'lease': new_id, 'resident': resident_id, 'entered': payload.starts_on,
                   'predecessor': old_occupancy['id'], 'manager': manager['manager_id']})
            if resident_id == payload.responsible_resident_id:
                insert_responsible(db, new_id, occupancy_id, manager['manager_id'],
                                   payload.reason)
        close_responsible(db, lease_id)
        invoice = next_invoice(payload.starts_on, package['period_months'], payload.price)
        db.execute(text("""
            INSERT INTO kamartha.invoices(lease_id,period_start,period_end,due_on,amount,source)
            VALUES (:lease,:start,:end,:due,:amount,'OPERATIONAL')
        """), {'lease': new_id, 'start': invoice['period_start'], 'end': invoice['period_end'],
               'due': invoice['due_on'], 'amount': invoice['amount']})
        event(db, request, manager['manager_id'], 'LEASE_CONTINUED', new_id,
              payload.reason, {'from_lease': str(lease_id)}, None)
        result = command.save(detail_or_404(db, new_id, today), 201)
    return envelope(request, result)
