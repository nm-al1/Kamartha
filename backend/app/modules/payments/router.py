from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text

from app.core.errors import AppError
from app.core.idempotency import BusinessRequest
from app.core.pagination import Page, page_params
from app.db.session import lock_business, open_session
from app.deps import check_mode
from app.modules.attachments.service import link_staged
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.payments.rules import validate_payment
from app.modules.payments.schemas import PaymentCancel, PaymentCreate
from app.modules.payments.service import balances, list_payments, payment_detail

router = APIRouter(prefix='/payments', tags=['payments'])


def like_pattern(value):
    return '%' + value.strip().replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%'


@router.get('')
def get_payments(request: Request, page: Page = Depends(page_params),
                 q: str = Query('', max_length=150), status: str = Query('', max_length=20),
                 date_from: date | None = None, date_to: date | None = None,
                 manager=Depends(require_manager)):
    with open_session(request) as db:
        items, total = list_payments(db, q=like_pattern(q), status=status,
                                     date_from=date_from, date_to=date_to,
                                     limit=page.limit, offset=page.offset)
    return envelope(request, {'items': items, 'pagination': page.metadata(total)})


@router.get('/{payment_id}')
def get_payment(payment_id: UUID, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        data = payment_detail(db, payment_id)
    if data is None:
        raise AppError('NOT_FOUND', 'Pembayaran tidak ditemukan.', 404)
    return envelope(request, data)


@router.post('', status_code=201)
def create_payment(payload: PaymentCreate, request: Request, manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    now = request.app.state.clock.now()
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, 'payments.create',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        lease = db.execute(text('SELECT * FROM kamartha.leases WHERE id=:id FOR UPDATE'),
                           {'id': payload.lease_id}).mappings().one_or_none()
        if lease is None:
            raise AppError('NOT_FOUND', 'Kontrak tidak ditemukan.', 404)
        current = balances(db, payload.lease_id)
        try:
            validate_payment(
                lease_id=payload.lease_id, total_amount=payload.total_amount,
                method=payload.method, received_on=payload.received_on, today=today,
                cutover_date=settings['cutover_date'],
                allocations=[(item.invoice_id, item.amount) for item in payload.allocations],
                balances=current,
            )
        except ValueError as exc:
            raise AppError('PAYMENT_INVALID', str(exc), 422) from exc
        payment_id = db.scalar(text("""
            INSERT INTO kamartha.payments(lease_id,received_on,total_amount,method,reference,recorded_by)
            VALUES (:lease,:received,:amount,:method,:reference,:manager) RETURNING id
        """), {'lease': payload.lease_id, 'received': payload.received_on,
               'amount': payload.total_amount, 'method': payload.method,
               'reference': payload.reference, 'manager': manager['manager_id']})
        for allocation in payload.allocations:
            db.execute(text("""
                INSERT INTO kamartha.payment_allocations(payment_id,invoice_id,lease_id,amount)
                VALUES (:payment,:invoice,:lease,:amount)
            """), {'payment': payment_id, 'invoice': allocation.invoice_id,
                   'lease': payload.lease_id, 'amount': allocation.amount})
        link_staged(db, payload.attachment_id, manager['manager_id'],
                    payment_id=payment_id, now=now)
        result = command.save(payment_detail(db, payment_id), 201)
    return envelope(request, result)


@router.post('/{payment_id}/cancel')
def cancel_payment(payment_id: UUID, payload: PaymentCancel, request: Request,
                   manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, f'payments.cancel.{payment_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        payment = db.execute(text('SELECT * FROM kamartha.payments WHERE id=:id FOR UPDATE'),
                             {'id': payment_id}).mappings().one_or_none()
        if payment is None:
            raise AppError('NOT_FOUND', 'Pembayaran tidak ditemukan.', 404)
        if payment['status'] != 'VALID':
            raise AppError('PAYMENT_CLOSED', 'Pembayaran sudah dibatalkan.', 409)
        db.execute(text("""
            UPDATE kamartha.payments SET status='CANCELLED',cancellation_reason=:reason,
                cancelled_at=:now,cancelled_by=:manager WHERE id=:id
        """), {'reason': payload.reason, 'now': request.app.state.clock.now(),
               'manager': manager['manager_id'], 'id': payment_id})
        result = command.save(payment_detail(db, payment_id))
    return envelope(request, result)
