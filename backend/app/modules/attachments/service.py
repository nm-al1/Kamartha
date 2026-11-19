from sqlalchemy import text

from app.core.errors import AppError


def link_staged(db, attachment_id, manager_id, *, payment_id=None, expense_id=None, now):
    if attachment_id is None:
        return None
    row = db.execute(text("""
        SELECT * FROM kamartha.attachments WHERE id=:id FOR UPDATE
    """), {'id': attachment_id}).mappings().one_or_none()
    if row is None:
        raise AppError('ATTACHMENT_NOT_FOUND', 'Lampiran tidak ditemukan.', 404)
    if row['uploaded_by'] != manager_id:
        raise AppError('ATTACHMENT_NOT_OWNED', 'Lampiran bukan milik sesi ini.', 403)
    if row['state'] != 'STAGED' or row['staged_expires_at'] <= now:
        raise AppError('ATTACHMENT_UNAVAILABLE', 'Lampiran sudah dipakai atau kedaluwarsa.', 409)
    if (payment_id is None) == (expense_id is None):
        raise ValueError('Lampiran harus terhubung ke satu pemilik.')
    db.execute(text("""
        UPDATE kamartha.attachments SET state='LINKED',payment_id=:payment,
            expense_id=:expense,linked_at=:now WHERE id=:id
    """), {'payment': payment_id, 'expense': expense_id, 'now': now, 'id': attachment_id})
    return attachment_id
