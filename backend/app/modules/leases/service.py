from sqlalchemy import text

from app.modules.billing.rules import invoice_status
from app.modules.leases.rules import status_of


def like_pattern(value: str) -> str:
    return '%' + value.strip().replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%'


def list_leases(db, *, q: str, limit: int, offset: int, today):
    params = {'q': like_pattern(q), 'limit': limit, 'offset': offset, 'today': today}
    where = """
        WHERE (:q = '%%' OR r.number ILIKE :q ESCAPE '!'
          OR EXISTS (SELECT 1 FROM kamartha.occupancies so
                     JOIN kamartha.residents sr ON sr.id=so.resident_id
                     WHERE so.lease_id=l.id AND sr.name ILIKE :q ESCAPE '!'))
    """
    total = db.scalar(text("""
        SELECT count(*) FROM kamartha.leases l
        JOIN kamartha.rooms r ON r.id=l.room_id
    """ + where), params)
    rows = db.execute(text("""
        SELECT l.id,l.room_id,l.package_id,l.starts_on,l.agreed_ends_on,l.effective_ends_on,
               l.occupant_type_snapshot,l.period_months_snapshot,l.period_price_snapshot,
               l.source,l.early_end_reason,l.version,l.created_at,
               r.number AS room_number,
               (SELECT string_agg(sr.name, ', ' ORDER BY so.entered_on, sr.name)
                FROM kamartha.occupancies so JOIN kamartha.residents sr ON sr.id=so.resident_id
                WHERE so.lease_id=l.id AND so.state='STAYING') AS resident_names,
               EXISTS (SELECT 1 FROM kamartha.occupancies o2
                       WHERE o2.lease_id=l.id AND o2.state='STAYING') AS has_staying
        FROM kamartha.leases l
        JOIN kamartha.rooms r ON r.id=l.room_id
    """ + where + """
        ORDER BY l.starts_on DESC, l.id
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()
    items = []
    for row in rows:
        item = dict(row)
        item['status'] = status_of(starts_on=item['starts_on'],
                                   effective_ends_on=item['effective_ends_on'], today=today)
        item['needs_confirmation'] = bool(item.pop('has_staying')) and item['effective_ends_on'] <= today
        items.append(item)
    return items, total


def lease_detail(db, lease_id, today):
    row = db.execute(text("""
        SELECT l.*, r.number AS room_number, p.occupant_type, p.period_months
        FROM kamartha.leases l
        JOIN kamartha.rooms r ON r.id=l.room_id
        JOIN kamartha.packages p ON p.id=l.package_id
        WHERE l.id=:id
    """), {'id': lease_id}).mappings().one_or_none()
    if row is None:
        return None
    lease = dict(row)
    lease['status'] = status_of(starts_on=lease['starts_on'],
                                effective_ends_on=lease['effective_ends_on'], today=today)
    occupancies = db.execute(text("""
        SELECT o.*, r.name, r.identity_type, r.identity_number, r.whatsapp_number,
               EXISTS (SELECT 1 FROM kamartha.responsible_history h
                       WHERE h.occupancy_id=o.id AND h.valid_until IS NULL) AS responsible
        FROM kamartha.occupancies o
        JOIN kamartha.residents r ON r.id=o.resident_id
        WHERE o.lease_id=:id
        ORDER BY o.entered_on, o.created_at, o.id
    """), {'id': lease_id}).mappings().all()
    lease['occupancies'] = [dict(item) for item in occupancies]
    lease['needs_confirmation'] = (
        lease['status'] == 'ENDED'
        and any(item['state'] == 'STAYING' for item in lease['occupancies'])
    )
    invoices = db.execute(text("""
        WITH paid AS (
            SELECT a.invoice_id, SUM(a.amount) AS operational_paid
            FROM kamartha.payment_allocations a
            JOIN kamartha.payments p ON p.id=a.payment_id
            WHERE p.status='VALID'
            GROUP BY a.invoice_id
        )
        SELECT i.*, i.opening_paid + COALESCE(paid.operational_paid,0) AS paid_total,
               i.amount - i.opening_paid - COALESCE(paid.operational_paid,0) AS remaining
        FROM kamartha.invoices i
        LEFT JOIN paid ON paid.invoice_id=i.id
        WHERE i.lease_id=:id
        ORDER BY i.period_start, i.id
    """), {'id': lease_id}).mappings().all()
    result_invoices = []
    for item in invoices:
        invoice = dict(item)
        invoice['paid_total'] = int(invoice['paid_total'])
        invoice['remaining'] = int(invoice['remaining'])
        invoice['payment_status'] = invoice_status(
            cancelled=invoice['status'] == 'CANCELLED', amount=invoice['amount'],
            opening_paid=invoice['opening_paid'],
            operational_paid=invoice['paid_total'] - invoice['opening_paid'],
            due_on=invoice['due_on'], today=today,
        )
        result_invoices.append(invoice)
    lease['invoices'] = result_invoices
    return lease
