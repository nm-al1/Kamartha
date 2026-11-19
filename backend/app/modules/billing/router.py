from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text

from app.core.errors import AppError
from app.core.idempotency import BusinessRequest
from app.core.pagination import Page, page_params
from app.db.session import lock_business, open_session
from app.deps import check_mode
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.billing.schemas import InvoiceCancel
from app.modules.billing.service import invoice_detail, invoice_rows, summary_amount, synchronize

router = APIRouter(prefix='/billing', tags=['billing'])
invoice_router = APIRouter(prefix='/invoices', tags=['invoices'])


@router.post('/synchronize')
def synchronize_invoices(request: Request, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, 'billing.synchronize', {})
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        result = synchronize(db, today=request.app.state.clock.today(),
                             cutover=settings['cutover_date'])
        result = command.save(result)
    return envelope(request, result)


@invoice_router.get('')
def list_invoices(request: Request, page: Page = Depends(page_params),
                  q: str = Query('', max_length=150), status: str = Query('', max_length=20),
                  date_from: date | None = None, date_to: date | None = None,
                  manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    pattern = '%' + q.strip().replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%'
    with open_session(request) as db:
        items, total = invoice_rows(db, today=today, q=pattern, status=status,
                                    date_from=date_from, date_to=date_to,
                                    limit=page.limit, offset=page.offset)
        summary = summary_amount(db, today=today, q=pattern, status=status)
    return envelope(request, {'items': items, 'summary': {'total_remaining': summary},
                              'pagination': page.metadata(total)})


@invoice_router.get('/{invoice_id}')
def get_invoice(invoice_id: UUID, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        data = invoice_detail(db, invoice_id, request.app.state.clock.today())
    if data is None:
        raise AppError('NOT_FOUND', 'Tagihan tidak ditemukan.', 404)
    return envelope(request, data)


@invoice_router.post('/{invoice_id}/cancel')
def cancel_invoice(invoice_id: UUID, payload: InvoiceCancel, request: Request,
                   manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db, db.begin():
        settings = lock_business(db)
        check_mode(settings, 'ACTIVE')
        command = BusinessRequest(db, request, manager, f'invoices.cancel.{invoice_id}',
                                  payload.model_dump(mode='json'))
        previous = command.previous()
        if previous is not None:
            return envelope(request, previous)
        invoice = db.execute(text('SELECT * FROM kamartha.invoices WHERE id=:id FOR UPDATE'),
                             {'id': invoice_id}).mappings().one_or_none()
        if invoice is None:
            raise AppError('NOT_FOUND', 'Tagihan tidak ditemukan.', 404)
        if invoice['status'] != 'ACTIVE':
            raise AppError('INVOICE_CLOSED', 'Tagihan sudah dibatalkan.', 409)
        if invoice['source'] != 'OPERATIONAL' or invoice['period_start'] <= today:
            raise AppError('CANCEL_REJECTED',
                           'Hanya tagihan operasional periode mendatang yang dapat dibatalkan.', 422)
        paid = db.scalar(text("""
            SELECT COALESCE(SUM(a.amount),0) FROM kamartha.payment_allocations a
            JOIN kamartha.payments p ON p.id=a.payment_id
            WHERE a.invoice_id=:id AND p.status='VALID'
        """), {'id': invoice_id})
        if paid:
            raise AppError('PAID_PERIOD_CONFLICT',
                           'Tagihan sudah menerima pembayaran; batalkan pembayaran terlebih dahulu.', 409)
        db.execute(text("""
            UPDATE kamartha.invoices SET status='CANCELLED',cancellation_reason=:reason,
                cancelled_at=:now,cancelled_by=:manager WHERE id=:id
        """), {'reason': payload.reason, 'now': request.app.state.clock.now(),
               'manager': manager['manager_id'], 'id': invoice_id})
        result = command.save(invoice_detail(db, invoice_id, today))
    return envelope(request, result)
