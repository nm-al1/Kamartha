"""Prototype reminders: allowlisted invoices and recipients only; no blind retries."""
from datetime import timedelta
from uuid import UUID

from sqlalchemy import text

from app.core.errors import AppError
from app.db.session import lock_business
from app.modules.messaging.router import invoice_context, normalize_wa, rupiah


def stage_for(due, today):
    if due == today + timedelta(days=3):
        return 'H3'
    if due == today:
        return 'DUE'
    return None


def configuration(settings):
    if not settings.whatsapp_enabled:
        raise AppError('WA_DISABLED', 'WA otomatis uji belum diaktifkan.', 409)
    try:
        numbers = {normalize_wa(n.strip()) for n in settings.whatsapp_allowed_numbers.split(',') if n.strip()}
        invoices = {UUID(v.strip()) for v in settings.whatsapp_demo_invoice_ids.split(',') if v.strip()}
    except (ValueError, AppError) as exc:
        raise AppError('WA_NOT_CONFIGURED', 'Daftar nomor atau ID tagihan uji belum sah.', 503) from exc
    if not numbers or not invoices or len(invoices) > 100:
        raise AppError('WA_NOT_CONFIGURED', 'Isi nomor tujuan dan 1 sampai 100 ID tagihan uji yang disetujui.', 503)
    return numbers, invoices


def current_contact(db, lease_id):
    rows = db.execute(text('''SELECT r.name,r.whatsapp_number FROM kamartha.responsible_history h
        JOIN kamartha.occupancies o ON o.id=h.occupancy_id
        JOIN kamartha.residents r ON r.id=o.resident_id
        WHERE h.lease_id=:lease AND h.valid_until IS NULL'''), {'lease': lease_id}).mappings().all()
    if len(rows) != 1:
        raise AppError('WA_CONTACT_AMBIGUOUS', 'Kontak penanggung jawab aktif belum pasti.', 409)
    return rows[0]


def run_reminders(session_factory, settings, today, bridge):
    numbers, invoices = configuration(settings)
    if bridge.status().get('ready') is not True:
        raise AppError('WA_NOT_READY', 'Scan QR dan tunggu sesi WhatsApp siap.', 409)
    result = {'sent': 0, 'unknown': 0, 'skipped': 0, 'existing': 0}
    for invoice_id in sorted(invoices):
        claimed = None
        with session_factory() as db, db.begin():
            app_settings = lock_business(db)
            if app_settings['mode'] != 'ACTIVE':
                raise AppError('MODE_CONFLICT', 'Pengingat hanya tersedia setelah data awal difinalisasi.', 409)
            try:
                data = invoice_context(db, invoice_id)
            except AppError as exc:
                if exc.code != 'NOT_FOUND':
                    raise
                result['skipped'] += 1
                continue
            stage = stage_for(data['due_on'], today)
            if data['status'] != 'ACTIVE' or data['remaining'] <= 0 or stage is None:
                result['skipped'] += 1
                continue
            try:
                person = current_contact(db, data['lease_id'])
                number = normalize_wa(person['whatsapp_number'])
            except AppError:
                result['skipped'] += 1
                continue
            if number not in numbers:
                result['skipped'] += 1
                continue
            row = db.execute(text('''INSERT INTO kamartha.whatsapp_reminders
                (invoice_id,stage,status,recipient_mask,amount,reminder_date)
                VALUES (:invoice,:stage,'SENDING',:mask,:amount,:today)
                ON CONFLICT (invoice_id,stage) DO NOTHING RETURNING id'''),
                {'invoice': invoice_id, 'stage': stage, 'mask': '***' + number[-4:],
                 'amount': data['remaining'], 'today': today}).scalar_one_or_none()
            if row is None:
                result['existing'] += 1
                continue
            message = (f"[DEMO KAMARTHA] Halo {person['name']}, pengingat "
                f"{'H-3' if stage == 'H3' else 'hari jatuh tempo'} tagihan kamar {data['room_number']}. "
                f"Periode {data['period_start']} sampai {data['period_end']}, "
                f"jatuh tempo {data['due_on']}, sisa {rupiah(data['remaining'])}. "
                'Silakan konfirmasi pembayaran kepada pengelola. Pesan ini untuk pengujian yang disetujui.')
            claimed = (row, number, message)
        # Commit SENDING before crossing the external delivery boundary.
        key, number, message = claimed
        try:
            receipt = bridge.send(key, number, message)
            status = 'SENT' if receipt.get('state') == 'SENT' and receipt.get('message_id') else 'UNKNOWN'
            message_id = receipt.get('message_id') if status == 'SENT' else None
        except (AppError, TimeoutError):
            status, message_id = 'UNKNOWN', None
        with session_factory() as db, db.begin():
            saved = db.scalar(text('''UPDATE kamartha.whatsapp_reminders SET status=:status,
                provider_message_id=:message,error_code=:error,updated_at=clock_timestamp()
                WHERE id=:id AND status IN ('SENDING','UNKNOWN') RETURNING status'''),
                {'id': key, 'status': status, 'message': message_id,
                 'error': None if status == 'SENT' else 'DELIVERY_UNCERTAIN'})
            if saved is None:
                saved = db.scalar(text('SELECT status FROM kamartha.whatsapp_reminders WHERE id=:id'), {'id': key})
        result['sent' if saved == 'SENT' else 'unknown'] += 1
    return result


def reconcile_receipts(session_factory, bridge):
    with session_factory() as db, db.begin():
        db.execute(text("""UPDATE kamartha.whatsapp_reminders SET status='UNKNOWN',
            error_code='DELIVERY_UNCERTAIN',updated_at=clock_timestamp()
            WHERE status='SENDING' AND created_at < clock_timestamp() - interval '2 minutes'"""))
        keys = db.execute(text("""SELECT id FROM kamartha.whatsapp_reminders
            WHERE status IN ('SENDING','UNKNOWN') ORDER BY created_at""")).scalars().all()
    for key in keys:
        try:
            receipt = bridge.receipt(key)
        except AppError:
            break
        if receipt.get('state') == 'SENT' and receipt.get('message_id'):
            with session_factory() as db, db.begin():
                db.execute(text("""UPDATE kamartha.whatsapp_reminders SET status='SENT',
                    provider_message_id=:message,error_code=NULL,updated_at=clock_timestamp()
                    WHERE id=:id AND status IN ('SENDING','UNKNOWN')"""),
                    {'id': key, 'message': receipt['message_id']})
