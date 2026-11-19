from datetime import date

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from app.core.errors import AppError
from app.db.session import open_session
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager
from app.modules.reminders.bridge import WhatsAppBridge
from app.modules.reminders.service import configuration, reconcile_receipts, run_reminders

router = APIRouter(prefix='/reminders', tags=['WA prototype'])


class RunInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    demo_date: date | None = None


@router.get('/status')
def status(request: Request, manager=Depends(require_manager)):
    settings = request.app.state.settings
    data = {'enabled': settings.whatsapp_enabled, 'prototype': True,
            'allow_demo_date': settings.whatsapp_enabled and settings.whatsapp_allow_demo_date,
            'hour_wita': settings.whatsapp_hour_wita, 'ready': False, 'qr': None,
            'today': str(request.app.state.clock.today()),
            'note': 'Nomor dan tagihan uji harus disetujui. Bukan layanan operasional.'}
    if settings.whatsapp_enabled:
        try:
            numbers, invoices = configuration(settings)
            data.update(allowed_numbers=['***' + n[-4:] for n in sorted(numbers)], invoice_count=len(invoices))
            state = WhatsAppBridge(settings).status()
            ready = state.get('ready') is True
            bridge_state = state.get('state')
            data.update(ready=ready, qr=state.get('qr') if not ready and bridge_state == 'SCAN_QR' else None,
                        bridge_state=bridge_state)
        except AppError as exc:
            data['note'] = exc.message
    return envelope(request, data)


@router.get('/history')
def history(request: Request, manager=Depends(require_manager)):
    if not request.app.state.settings.whatsapp_enabled:
        return envelope(request, {'items': []})
    with open_session(request) as db:
        rows = db.execute(text('''SELECT w.*,r.number AS room_number,i.due_on
            FROM kamartha.whatsapp_reminders w JOIN kamartha.invoices i ON i.id=w.invoice_id
            JOIN kamartha.leases l ON l.id=i.lease_id JOIN kamartha.rooms r ON r.id=l.room_id
            ORDER BY w.created_at DESC,w.id LIMIT 100''')).mappings().all()
    return envelope(request, {'items': [dict(r) for r in rows]})


@router.post('/run')
def run(payload: RunInput, request: Request, manager=Depends(require_manager)):
    settings = request.app.state.settings
    if payload.demo_date is not None and not settings.whatsapp_allow_demo_date:
        raise AppError('WA_DEMO_DATE_DISABLED', 'Simulasi tanggal tidak diizinkan.', 403)
    configuration(settings)
    bridge = WhatsAppBridge(settings)
    factory = lambda: open_session(request)
    reconcile_receipts(factory, bridge)
    return envelope(request, run_reminders(factory, settings,
        payload.demo_date or request.app.state.clock.today(), bridge))
