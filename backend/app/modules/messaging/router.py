import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from app.core.errors import AppError
from app.db.session import open_session
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.messaging.schemas import MessagePreviewInput

router = APIRouter(prefix='/messages', tags=['messages'])


def rupiah(amount):
    return 'Rp' + f'{int(amount):,}'.replace(',', '.')


def normalize_wa(value):
    digits = re.sub(r'\D', '', value or '')
    if digits.startswith('0'):
        digits = '62' + digits[1:]
    elif digits.startswith('8'):
        digits = '62' + digits
    if not digits.startswith('62') or not 10 <= len(digits) <= 15:
        raise AppError('WA_INVALID',
                       'Nomor WhatsApp tidak valid. Perbaiki kontak penghuni terlebih dahulu.',
                       422)
    return digits


def contact(db, lease_id):
    row = db.execute(text("""
        SELECT res.name,res.whatsapp_number
        FROM kamartha.responsible_history h
        JOIN kamartha.occupancies o ON o.id=h.occupancy_id
        JOIN kamartha.residents res ON res.id=o.resident_id
        WHERE h.lease_id=:lease
        ORDER BY (h.valid_until IS NULL) DESC, h.valid_from DESC
        LIMIT 1
    """), {'lease': lease_id}).mappings().one_or_none()
    if row is None:
        raise AppError('CONTACT_MISSING', 'Kontrak belum memiliki kontak penanggung jawab.', 409)
    return row


def invoice_context(db, invoice_id):
    row = db.execute(text("""
        WITH paid AS (
            SELECT a.invoice_id, SUM(a.amount) AS amount
            FROM kamartha.payment_allocations a
            JOIN kamartha.payments p ON p.id=a.payment_id
            WHERE p.status='VALID' GROUP BY a.invoice_id
        )
        SELECT i.*,r.number AS room_number,l.id AS lease_id,
               l.occupant_type_snapshot,l.period_months_snapshot,
               i.amount - i.opening_paid - COALESCE(paid.amount,0) AS remaining
        FROM kamartha.invoices i
        JOIN kamartha.leases l ON l.id=i.lease_id
        JOIN kamartha.rooms r ON r.id=l.room_id
        LEFT JOIN paid ON paid.invoice_id=i.id
        WHERE i.id=:id
    """), {'id': invoice_id}).mappings().one_or_none()
    if row is None:
        raise AppError('NOT_FOUND', 'Tagihan tidak ditemukan.', 404)
    return row


def payment_context(db, payment_id):
    row = db.execute(text("""
        SELECT p.*,r.number AS room_number,l.id AS lease_id
        FROM kamartha.payments p
        JOIN kamartha.leases l ON l.id=p.lease_id
        JOIN kamartha.rooms r ON r.id=l.room_id
        WHERE p.id=:id
    """), {'id': payment_id}).mappings().one_or_none()
    if row is None:
        raise AppError('NOT_FOUND', 'Pembayaran tidak ditemukan.', 404)
    return row


@router.post('/preview')
def preview(payload: MessagePreviewInput, request: Request,
            manager=Depends(require_manager)):
    with open_session(request) as db:
        if payload.context_type == 'INVOICE':
            data = invoice_context(db, payload.context_id)
            person = contact(db, data['lease_id'])
            text_body = (
                f"Halo {person['name']}, tagihan kamar {data['room_number']} "
                f"periode {data['period_start']} sampai {data['period_end']} "
                f"sebesar {rupiah(data['amount'])}. "
                f"Sisa tagihan {rupiah(data['remaining'])}, jatuh tempo {data['due_on']}. "
                'Mohon konfirmasi pembayaran kepada pengelola.'
            )
        elif payload.context_type == 'PAYMENT':
            data = payment_context(db, payload.context_id)
            if data['status'] != 'VALID':
                raise AppError('PAYMENT_CANCELLED',
                               'Pembayaran Batal tidak dapat dipakai sebagai konfirmasi.', 409)
            person = contact(db, data['lease_id'])
            allocations = db.execute(text("""
                SELECT i.period_start,i.period_end,a.amount
                FROM kamartha.payment_allocations a
                JOIN kamartha.invoices i ON i.id=a.invoice_id
                WHERE a.payment_id=:id ORDER BY i.period_start
            """), {'id': payload.context_id}).mappings().all()
            detail = '; '.join(
                f"{item['period_start']} sampai {item['period_end']} {rupiah(item['amount'])}"
                for item in allocations
            )
            text_body = (
                f"Halo {person['name']}, pembayaran kamar {data['room_number']} "
                f"tanggal {data['received_on']} sebesar {rupiah(data['total_amount'])} "
                f"telah dicatat. Alokasi: {detail}. Terima kasih."
            )
        else:
            data = db.execute(text("""
                SELECT l.*,r.number AS room_number FROM kamartha.leases l
                JOIN kamartha.rooms r ON r.id=l.room_id WHERE l.id=:id
            """), {'id': payload.context_id}).mappings().one_or_none()
            if data is None:
                raise AppError('NOT_FOUND', 'Kontrak tidak ditemukan.', 404)
            person = contact(db, data['id'])
            text_body = (
                f"Halo {person['name']}, kontrak kamar {data['room_number']} "
                f"berakhir pada {data['effective_ends_on']}. "
                'Mohon konfirmasi kelanjutan atau pengakhiran sewa kepada pengelola.'
            )
        number = normalize_wa(person['whatsapp_number'])
    return envelope(request, {
        'recipient': person['name'],
        'whatsapp_number': number,
        'message': text_body,
        'whatsapp_url': f'https://wa.me/{number}?text={quote(text_body)}',
    })
