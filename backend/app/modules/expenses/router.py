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
from app.modules.attachments.service import link_staged
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.expenses.schemas import ExpenseCancel, ExpenseCreate, ExpenseUpdate
from app.modules.expenses.service import expense_detail, list_expenses

router = APIRouter(prefix='/expenses', tags=['expenses'])


def validate_date(value, *, cutover, today):
    if not cutover <= value <= today:
        raise AppError('DATE_REJECTED',
                       'Tanggal pengeluaran harus sejak batas pencatatan dan tidak di masa depan.',
                       422)


def audit(db, *, expense_id, action, before, after, reason, manager_id,
          version_before, version_after, attachment_before, attachment_after):
    db.execute(text("""
        INSERT INTO kamartha.expense_audits(expense_id,action,before_data,after_data,reason,
            actor_id,attachment_before_id,attachment_after_id,version_before,version_after)
        VALUES (:expense,:action,CAST(:before AS JSONB),CAST(:after AS JSONB),:reason,
            :manager,:before_attachment,:after_attachment,:version_before,:version_after)
    """), {'expense': expense_id, 'action': action,
           'before': json.dumps(jsonable_encoder(before), allow_nan=False),
           'after': json.dumps(jsonable_encoder(after), allow_nan=False),
           'reason': reason, 'manager': manager_id,
           'before_attachment': attachment_before, 'after_attachment': attachment_after,
           'version_before': version_before, 'version_after': version_after})


@router.get('')
def get_expenses(request: Request, page: Page = Depends(page_params),
                 q: str = Query('', max_length=1000), category: str = Query('', max_length=20),
                 status: str = Query('', max_length=20), date_from: date | None = None,
                 date_to: date | None = None, manager=Depends(require_manager)):
    pattern = '%' + q.strip().replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%'
    with open_session(request) as db:
        items, total = list_expenses(db, q=pattern, category=category, status=status,
                                     date_from=date_from, date_to=date_to,
                                     limit=page.limit, offset=page.offset)
    return envelope(request, {'items': items, 'pagination': page.metadata(total)})


@router.get('/{expense_id}')
def get_expense(expense_id: UUID, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        data = expense_detail(db, expense_id)
    if data is None:
        raise AppError('NOT_FOUND', 'Pengeluaran tidak ditemukan.', 404)
    return envelope(request, data)


@router.post('', status_code=201)
def create_expense(payload: ExpenseCreate, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, 'expenses.create',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        validate_date(payload.expense_on, cutover=settings['cutover_date'],
                      today=request.app.state.clock.today())
        expense_id = db.scalar(text("""
            INSERT INTO kamartha.expenses(expense_on,amount,category,description,created_by)
            VALUES (:date,:amount,:category,:description,:manager) RETURNING id
        """), {'date': payload.expense_on, 'amount': payload.amount,
               'category': payload.category, 'description': payload.description,
               'manager': manager['manager_id']})
        if payload.attachment_id:
            link_staged(db, payload.attachment_id, manager['manager_id'],
                        expense_id=expense_id, now=request.app.state.clock.now())
            db.execute(text('UPDATE kamartha.expenses SET current_attachment_id=:attachment WHERE id=:id'),
                       {'attachment': payload.attachment_id, 'id': expense_id})
        result = command.save(expense_detail(db, expense_id), 201)
    return envelope(request, result)


@router.patch('/{expense_id}')
def update_expense(expense_id: UUID, payload: ExpenseUpdate, request: Request,
                   manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, f'expenses.update.{expense_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        validate_date(payload.expense_on, cutover=settings['cutover_date'],
                      today=request.app.state.clock.today())
        row = db.execute(text('SELECT * FROM kamartha.expenses WHERE id=:id FOR UPDATE'),
                         {'id': expense_id}).mappings().one_or_none()
        if row is None:
            raise AppError('NOT_FOUND', 'Pengeluaran tidak ditemukan.', 404)
        if row['status'] != 'VALID':
            raise AppError('EXPENSE_CLOSED', 'Pengeluaran yang dibatalkan tidak dapat diubah.', 409)
        if row['version'] != payload.expected_version:
            raise AppError('VERSION_CONFLICT', 'Data sudah berubah. Muat ulang dan tinjau kembali.', 409)
        before = dict(row)
        new_attachment = row['current_attachment_id']
        if payload.attachment_id and payload.attachment_id != row['current_attachment_id']:
            link_staged(db, payload.attachment_id, manager['manager_id'],
                        expense_id=expense_id, now=request.app.state.clock.now())
            new_attachment = payload.attachment_id
        updated = db.execute(text("""
            UPDATE kamartha.expenses SET expense_on=:date,amount=:amount,category=:category,
                description=:description,current_attachment_id=:attachment,version=version+1
            WHERE id=:id RETURNING *
        """), {'date': payload.expense_on, 'amount': payload.amount,
               'category': payload.category, 'description': payload.description,
               'attachment': new_attachment, 'id': expense_id}).mappings().one()
        audit(db, expense_id=expense_id, action='UPDATE', before=before, after=dict(updated),
              reason=payload.reason, manager_id=manager['manager_id'],
              version_before=row['version'], version_after=updated['version'],
              attachment_before=row['current_attachment_id'], attachment_after=new_attachment)
        result = command.save(expense_detail(db, expense_id))
    return envelope(request, result)


@router.post('/{expense_id}/cancel')
def cancel_expense(expense_id: UUID, payload: ExpenseCancel, request: Request,
                   manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, f'expenses.cancel.{expense_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        row = db.execute(text('SELECT * FROM kamartha.expenses WHERE id=:id FOR UPDATE'),
                         {'id': expense_id}).mappings().one_or_none()
        if row is None:
            raise AppError('NOT_FOUND', 'Pengeluaran tidak ditemukan.', 404)
        if row['status'] != 'VALID':
            raise AppError('EXPENSE_CLOSED', 'Pengeluaran sudah dibatalkan.', 409)
        if row['version'] != payload.expected_version:
            raise AppError('VERSION_CONFLICT', 'Data sudah berubah. Muat ulang dan tinjau kembali.', 409)
        before = dict(row)
        updated = db.execute(text("""
            UPDATE kamartha.expenses SET status='CANCELLED',cancellation_reason=:reason,
                cancelled_at=:now,cancelled_by=:manager,version=version+1
            WHERE id=:id RETURNING *
        """), {'reason': payload.reason, 'now': request.app.state.clock.now(),
               'manager': manager['manager_id'], 'id': expense_id}).mappings().one()
        audit(db, expense_id=expense_id, action='CANCEL', before=before, after=dict(updated),
              reason=payload.reason, manager_id=manager['manager_id'],
              version_before=row['version'], version_after=updated['version'],
              attachment_before=row['current_attachment_id'],
              attachment_after=row['current_attachment_id'])
        result = command.save(expense_detail(db, expense_id))
    return envelope(request, result)
