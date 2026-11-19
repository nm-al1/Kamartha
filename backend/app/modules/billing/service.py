from datetime import timedelta

from fastapi.encoders import jsonable_encoder
from sqlalchemy import text

from app.modules.billing.rules import invoice_status, period_boundary


def synchronize(db, *, today, cutover):
    created = []
    leases = db.execute(text("""
        SELECT l.id,l.starts_on,l.effective_ends_on,l.period_months_snapshot,l.period_price_snapshot
        FROM kamartha.leases l ORDER BY l.id
    """)).mappings().all()
    for lease in leases:
        existing = set(db.execute(text("""
            SELECT period_start FROM kamartha.invoices WHERE lease_id=:id
        """), {'id': lease['id']}).scalars().all())
        index = 0
        while True:
            start = period_boundary(lease['starts_on'], lease['period_months_snapshot'], index)
            if start >= lease['effective_ends_on']:
                break
            index += 1
            if start < cutover or start > today + timedelta(days=3) or start in existing:
                continue
            end = period_boundary(lease['starts_on'], lease['period_months_snapshot'], index)
            invoice_id = db.scalar(text("""
                INSERT INTO kamartha.invoices(lease_id,period_start,period_end,due_on,amount,source)
                VALUES (:lease,:start,:end,:start,:amount,'OPERATIONAL') RETURNING id
            """), {'lease': lease['id'], 'start': start, 'end': end,
                   'amount': lease['period_price_snapshot']})
            created.append(str(invoice_id))
    return {'created': len(created), 'invoice_ids': created}


def invoice_rows(db, *, today, q='', status='', date_from=None, date_to=None,
                 limit=None, offset=0, invoice_id=None):
    params = {
        'today': today, 'q': q, 'status': status,
        'from': date_from, 'to': date_to, 'limit': limit, 'offset': offset,
    }
    params['invoice_id'] = invoice_id
    base = """
        WITH paid AS (
            SELECT a.invoice_id, SUM(a.amount) AS operational_paid
            FROM kamartha.payment_allocations a
            JOIN kamartha.payments p ON p.id=a.payment_id
            WHERE p.status='VALID'
              AND (CAST(:invoice_id AS UUID) IS NULL OR a.invoice_id=:invoice_id)
            GROUP BY a.invoice_id
        ), base AS (
            SELECT i.*, i.opening_paid + COALESCE(paid.operational_paid,0) AS paid_total,
                   i.amount - i.opening_paid - COALESCE(paid.operational_paid,0) AS remaining,
                   l.room_id, r.number AS room_number, l.starts_on AS lease_start,
                   l.effective_ends_on AS lease_end, p.occupant_type, p.period_months,
                   (SELECT string_agg(sr.name, ', ' ORDER BY so.entered_on, sr.name)
                    FROM kamartha.occupancies so
                    JOIN kamartha.residents sr ON sr.id=so.resident_id
                    WHERE so.lease_id=i.lease_id AND so.state='STAYING') AS resident_names,
                   CASE
                     WHEN i.status='CANCELLED' THEN 'CANCELLED'
                     WHEN i.amount - i.opening_paid - COALESCE(paid.operational_paid,0)=0 THEN 'PAID'
                     WHEN :today > i.due_on THEN 'OVERDUE'
                     WHEN i.amount - i.opening_paid - COALESCE(paid.operational_paid,0) < i.amount
                       THEN 'PARTIALLY_PAID'
                     ELSE 'UNPAID'
                   END AS payment_status
            FROM kamartha.invoices i
            JOIN kamartha.leases l ON l.id=i.lease_id
            JOIN kamartha.rooms r ON r.id=l.room_id
            JOIN kamartha.packages p ON p.id=l.package_id
            LEFT JOIN paid ON paid.invoice_id=i.id
            WHERE (CAST(:invoice_id AS UUID) IS NULL OR i.id=:invoice_id)
        )
        SELECT * FROM base
        WHERE (:q = '' OR room_number ILIKE :q ESCAPE '!'
               OR EXISTS (SELECT 1 FROM kamartha.occupancies o
                          JOIN kamartha.residents res ON res.id=o.resident_id
                          WHERE o.lease_id=base.lease_id AND res.name ILIKE :q ESCAPE '!'))
          AND (:status = '' OR payment_status=:status)
          AND (CAST(:from AS DATE) IS NULL OR period_start >= CAST(:from AS DATE))
          AND (CAST(:to AS DATE) IS NULL OR period_start <= CAST(:to AS DATE))
    """
    count = db.scalar(text("SELECT count(*) FROM (" + base + ") counts"), params)
    query = base + " ORDER BY due_on, period_start, id"
    if limit is not None:
        query += " LIMIT :limit OFFSET :offset"
    rows = db.execute(text(query), params).mappings().all()
    items = []
    for row in rows:
        item = dict(row)
        item['paid_total'] = int(item['paid_total'])
        item['remaining'] = int(item['remaining'])
        items.append(item)
    return items, count


def summary_amount(db, *, today, q='', status=''):
    params = {'today': today, 'q': q, 'status': status, 'from': None, 'to': None,
              'limit': None, 'offset': 0}
    base = """
        WITH paid AS (
            SELECT a.invoice_id, SUM(a.amount) AS operational_paid
            FROM kamartha.payment_allocations a
            JOIN kamartha.payments p ON p.id=a.payment_id
            WHERE p.status='VALID' GROUP BY a.invoice_id
        ), base AS (
            SELECT i.*, i.amount - i.opening_paid - COALESCE(paid.operational_paid,0) AS remaining,
                   l.room_id, r.number AS room_number, l.starts_on AS lease_start,
                   l.effective_ends_on AS lease_end, p.occupant_type, p.period_months,
                   CASE WHEN i.status='CANCELLED' THEN 'CANCELLED'
                        WHEN i.amount - i.opening_paid - COALESCE(paid.operational_paid,0)=0 THEN 'PAID'
                        WHEN :today > i.due_on THEN 'OVERDUE'
                        WHEN i.amount - i.opening_paid - COALESCE(paid.operational_paid,0) < i.amount
                          THEN 'PARTIALLY_PAID' ELSE 'UNPAID' END AS payment_status
            FROM kamartha.invoices i
            JOIN kamartha.leases l ON l.id=i.lease_id
            JOIN kamartha.rooms r ON r.id=l.room_id
            JOIN kamartha.packages p ON p.id=l.package_id
            LEFT JOIN paid ON paid.invoice_id=i.id
        )
        SELECT COALESCE(SUM(remaining),0) FROM base
        WHERE status='ACTIVE' AND (:q = '' OR room_number ILIKE :q ESCAPE '!'
          OR EXISTS (SELECT 1 FROM kamartha.occupancies o JOIN kamartha.residents res ON res.id=o.resident_id
                     WHERE o.lease_id=base.lease_id AND res.name ILIKE :q ESCAPE '!'))
          AND (:status = '' OR payment_status=:status)
    """
    return int(db.scalar(text(base), params))


def invoice_detail(db, invoice_id, today):
    rows, _ = invoice_rows(db, today=today, invoice_id=invoice_id, limit=1)
    item = next((row for row in rows if row['id'] == invoice_id), None)
    if item is None:
        return None
    item['allocations'] = [dict(row) for row in db.execute(text("""
        SELECT a.id,a.amount,p.id AS payment_id,p.received_on,p.method,p.status,
               p.recorded_at
        FROM kamartha.payment_allocations a
        JOIN kamartha.payments p ON p.id=a.payment_id
        WHERE a.invoice_id=:id ORDER BY p.received_on,p.id
    """), {'id': invoice_id}).mappings().all()]
    return jsonable_encoder(item)
