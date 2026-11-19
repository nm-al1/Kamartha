from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from app.db.session import open_session
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager

router = APIRouter(tags=['dashboard'])


def reminder_data(db, today):
    invoices = db.execute(text("""
        WITH paid AS (
            SELECT a.invoice_id, SUM(a.amount) AS amount
            FROM kamartha.payment_allocations a
            JOIN kamartha.payments p ON p.id=a.payment_id
            WHERE p.status='VALID' GROUP BY a.invoice_id
        )
        SELECT i.id,i.period_start,i.period_end,i.due_on,r.number AS room_number,
               (SELECT string_agg(sr.name, ', ' ORDER BY so.entered_on, sr.name)
                FROM kamartha.occupancies so JOIN kamartha.residents sr ON sr.id=so.resident_id
                WHERE so.lease_id=i.lease_id AND so.state='STAYING') AS resident_names,
               i.amount - i.opening_paid - COALESCE(paid.amount,0) AS remaining,
               l.id AS lease_id
        FROM kamartha.invoices i
        JOIN kamartha.leases l ON l.id=i.lease_id
        JOIN kamartha.rooms r ON r.id=l.room_id
        LEFT JOIN paid ON paid.invoice_id=i.id
        WHERE i.status='ACTIVE' AND i.due_on <= :soon
          AND i.amount - i.opening_paid - COALESCE(paid.amount,0) > 0
        ORDER BY i.due_on,i.period_start,i.id
        LIMIT 50
    """), {'soon': today + timedelta(days=3)}).mappings().all()
    leases = db.execute(text("""
        SELECT l.id,r.number AS room_number,l.effective_ends_on,
               EXISTS (SELECT 1 FROM kamartha.occupancies o
                       WHERE o.lease_id=l.id AND o.state='STAYING') AS staying
        FROM kamartha.leases l JOIN kamartha.rooms r ON r.id=l.room_id
        WHERE l.effective_ends_on <= :soon
          AND (l.effective_ends_on >= :today
               OR EXISTS (SELECT 1 FROM kamartha.occupancies o
                          WHERE o.lease_id=l.id AND o.state='STAYING'))
        ORDER BY l.effective_ends_on,l.id LIMIT 50
    """), {'soon': today + timedelta(days=3), 'today': today}).mappings().all()
    return {
        'invoices': [{**dict(item), 'remaining': int(item['remaining'])} for item in invoices],
        'leases': [dict(item) for item in leases],
    }


@router.get('/dashboard')
def dashboard(request: Request, manager=Depends(require_manager)):
    today = request.app.state.clock.today()
    with open_session(request) as db:
        total_rooms = db.scalar(text('SELECT count(*) FROM kamartha.rooms'))
        needs = db.scalar(text("""
            SELECT count(DISTINCT l.room_id) FROM kamartha.leases l
            JOIN kamartha.occupancies o ON o.lease_id=l.id
            WHERE o.state='STAYING' AND l.effective_ends_on <= :today
        """), {'today': today})
        occupied = db.scalar(text("""
            SELECT count(DISTINCT l.room_id) FROM kamartha.leases l
            JOIN kamartha.occupancies o ON o.lease_id=l.id
            WHERE o.state='STAYING' AND o.entered_on <= :today
              AND l.starts_on <= :today AND l.effective_ends_on > :today
        """), {'today': today})
        people = db.scalar(text("""
            SELECT count(DISTINCT o.resident_id) FROM kamartha.occupancies o
            WHERE o.state='STAYING' AND o.entered_on <= :today
        """), {'today': today})
        active = db.scalar(text("""
            SELECT count(*) FROM kamartha.leases
            WHERE starts_on <= :today AND effective_ends_on > :today
        """), {'today': today})
        receivable = db.scalar(text("""
            WITH paid AS (
                SELECT a.invoice_id, SUM(a.amount) AS amount
                FROM kamartha.payment_allocations a
                JOIN kamartha.payments p ON p.id=a.payment_id
                WHERE p.status='VALID' GROUP BY a.invoice_id
            )
            SELECT COALESCE(SUM(i.amount - i.opening_paid - COALESCE(paid.amount,0)),0)
            FROM kamartha.invoices i LEFT JOIN paid ON paid.invoice_id=i.id
            WHERE i.status='ACTIVE'
        """))
        overdue = db.scalar(text("""
            WITH paid AS (
                SELECT a.invoice_id, SUM(a.amount) AS amount
                FROM kamartha.payment_allocations a
                JOIN kamartha.payments p ON p.id=a.payment_id
                WHERE p.status='VALID' GROUP BY a.invoice_id
            )
            SELECT COALESCE(SUM(i.amount - i.opening_paid - COALESCE(paid.amount,0)),0)
            FROM kamartha.invoices i LEFT JOIN paid ON paid.invoice_id=i.id
            WHERE i.status='ACTIVE' AND i.due_on < :today
        """), {'today': today})
        reminders = reminder_data(db, today)
    return envelope(request, {
        'today': today,
        'rooms': {'total': total_rooms, 'occupied': occupied,
                  'needs_confirmation': needs,
                  'empty': total_rooms - occupied - needs},
        'people_staying': people,
        'active_contracts': active,
        'receivables': int(receivable),
        'overdue_receivables': int(overdue),
        'reminders': reminders,
    })


@router.get('/reminders')
def reminders(request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        data = reminder_data(db, request.app.state.clock.today())
    return envelope(request, data)
