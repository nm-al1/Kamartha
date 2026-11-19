from fastapi.encoders import jsonable_encoder
from sqlalchemy import text

from app.modules.payments.rules import InvoiceBalance


def balances(db, lease_id):
    rows = db.execute(text("""
        WITH paid AS (
            SELECT a.invoice_id, SUM(a.amount) AS amount
            FROM kamartha.payment_allocations a
            JOIN kamartha.payments p ON p.id=a.payment_id
            WHERE p.status='VALID' GROUP BY a.invoice_id
        )
        SELECT i.id,i.lease_id,i.period_start,i.status,
               i.amount - i.opening_paid - COALESCE(paid.amount,0) AS remaining
        FROM kamartha.invoices i LEFT JOIN paid ON paid.invoice_id=i.id
        WHERE i.lease_id=:lease
    """), {'lease': lease_id}).mappings().all()
    return {
        row['id']: InvoiceBalance(lease_id=row['lease_id'], remaining=int(row['remaining']),
                                  period_start=row['period_start'], active=row['status'] == 'ACTIVE')
        for row in rows
    }


def payment_detail(db, payment_id):
    row = db.execute(text("""
        SELECT p.*, r.number AS room_number, l.starts_on AS lease_start,
               l.effective_ends_on AS lease_end,
               (SELECT string_agg(sr.name, ', ' ORDER BY so.entered_on, sr.name)
                FROM kamartha.occupancies so JOIN kamartha.residents sr ON sr.id=so.resident_id
                WHERE so.lease_id=p.lease_id AND so.state='STAYING') AS resident_names
        FROM kamartha.payments p
        JOIN kamartha.leases l ON l.id=p.lease_id
        JOIN kamartha.rooms r ON r.id=l.room_id
        WHERE p.id=:id
    """), {'id': payment_id}).mappings().one_or_none()
    if row is None:
        return None
    data = dict(row)
    data['allocations'] = [dict(item) for item in db.execute(text("""
        SELECT a.id,a.amount,i.id AS invoice_id,i.period_start,i.period_end,i.due_on
        FROM kamartha.payment_allocations a
        JOIN kamartha.invoices i ON i.id=a.invoice_id
        WHERE a.payment_id=:id ORDER BY i.period_start,i.id
    """), {'id': payment_id}).mappings().all()]
    attachment = db.execute(text("""
        SELECT id,mime_type,byte_size,sha256 FROM kamartha.attachments
        WHERE payment_id=:id AND state='LINKED'
    """), {'id': payment_id}).mappings().one_or_none()
    data['attachment'] = None if attachment is None else dict(attachment)
    return jsonable_encoder(data)


def list_payments(db, *, q='', status='', date_from=None, date_to=None, limit=20, offset=0):
    params = {'q': q, 'status': status, 'from': date_from, 'to': date_to,
              'limit': limit, 'offset': offset}
    where = """
        WHERE (:q = '' OR r.number ILIKE :q ESCAPE '!'
          OR EXISTS (SELECT 1 FROM kamartha.occupancies o
                     JOIN kamartha.residents res ON res.id=o.resident_id
                     WHERE o.lease_id=p.lease_id AND res.name ILIKE :q ESCAPE '!'))
          AND (:status = '' OR p.status=:status)
          AND (CAST(:from AS DATE) IS NULL OR p.received_on >= CAST(:from AS DATE))
          AND (CAST(:to AS DATE) IS NULL OR p.received_on <= CAST(:to AS DATE))
    """
    total = db.scalar(text("""
        SELECT count(*) FROM kamartha.payments p
        JOIN kamartha.leases l ON l.id=p.lease_id JOIN kamartha.rooms r ON r.id=l.room_id
    """ + where), params)
    rows = db.execute(text("""
        SELECT p.*, r.number AS room_number,
               (SELECT string_agg(sr.name, ', ' ORDER BY so.entered_on, sr.name)
                FROM kamartha.occupancies so JOIN kamartha.residents sr ON sr.id=so.resident_id
                WHERE so.lease_id=p.lease_id AND so.state='STAYING') AS resident_names
        FROM kamartha.payments p
        JOIN kamartha.leases l ON l.id=p.lease_id JOIN kamartha.rooms r ON r.id=l.room_id
    """ + where + " ORDER BY p.received_on DESC,p.id DESC LIMIT :limit OFFSET :offset"), params).mappings().all()
    return [dict(row) for row in rows], total
