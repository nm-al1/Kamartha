from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.exc import InvalidRequestError

from app.core.errors import AppError
from app.db.session import open_session
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager

router = APIRouter(prefix='/reports', tags=['reports'])


@router.get('/cash')
def cash_report(request: Request, date_from: date, date_to: date,
                manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db:
        try:
            db.connection(execution_options={'isolation_level': 'REPEATABLE READ'})
        except InvalidRequestError:
            # Tests may inject a connection whose outer transaction is already open.
            pass
        cutover = db.scalar(text('SELECT cutover_date FROM kamartha.app_settings WHERE id=1'))
        if cutover is None:
            raise AppError('REPORT_UNAVAILABLE', 'Tanggal pencatatan belum ditetapkan.', 409)
        if date_from < cutover or date_to < cutover:
            raise AppError('DATE_REJECTED', 'Rentang laporan tidak boleh sebelum batas pencatatan.', 422)
        if date_from > date_to:
            raise AppError('DATE_REJECTED', 'Tanggal awal tidak boleh sesudah tanggal akhir.', 422)
        if date_to > today:
            raise AppError('DATE_REJECTED', 'Tanggal akhir tidak boleh di masa depan.', 422)
        income = db.scalar(text("""
            SELECT COALESCE(SUM(total_amount),0) FROM kamartha.payments
            WHERE status='VALID' AND received_on BETWEEN :from AND :to
        """), {'from': date_from, 'to': date_to})
        expense = db.scalar(text("""
            SELECT COALESCE(SUM(amount),0) FROM kamartha.expenses
            WHERE status='VALID' AND expense_on BETWEEN :from AND :to
        """), {'from': date_from, 'to': date_to})
        payments = db.execute(text("""
            SELECT p.id,p.received_on,p.total_amount,p.method,p.status,p.reference,
                   r.number AS room_number
            FROM kamartha.payments p
            JOIN kamartha.leases l ON l.id=p.lease_id
            JOIN kamartha.rooms r ON r.id=l.room_id
            WHERE p.received_on BETWEEN :from AND :to
            ORDER BY p.received_on,p.id
        """), {'from': date_from, 'to': date_to}).mappings().all()
        allocations = db.execute(text("""
            SELECT a.payment_id,i.period_start,i.period_end,a.amount
            FROM kamartha.payment_allocations a
            JOIN kamartha.invoices i ON i.id=a.invoice_id
            JOIN kamartha.payments p ON p.id=a.payment_id
            WHERE p.received_on BETWEEN :from AND :to
            ORDER BY i.period_start,i.id
        """), {'from': date_from, 'to': date_to}).mappings().all()
        expenses = db.execute(text("""
            SELECT id,expense_on,amount,category,description,status
            FROM kamartha.expenses WHERE expense_on BETWEEN :from AND :to
            ORDER BY expense_on,id
        """), {'from': date_from, 'to': date_to}).mappings().all()
    by_payment = {}
    for item in allocations:
        by_payment.setdefault(item['payment_id'], []).append(dict(item))
    return envelope(request, {
        'date_from': date_from, 'date_to': date_to,
        'income': int(income), 'expense': int(expense),
        'difference': int(income) - int(expense),
        'payments': [{**dict(item), 'allocations': by_payment.get(item['id'], [])}
                     for item in payments],
        'expenses': [dict(item) for item in expenses],
    })
