from fastapi.encoders import jsonable_encoder
from sqlalchemy import text


def list_expenses(db, *, q='', category='', status='', date_from=None, date_to=None,
                  limit=20, offset=0):
    params = {'q': q, 'category': category, 'status': status,
              'from': date_from, 'to': date_to, 'limit': limit, 'offset': offset}
    where = """
        WHERE (:q = '' OR description ILIKE :q ESCAPE '!')
          AND (:category = '' OR category=:category)
          AND (:status = '' OR status=:status)
          AND (CAST(:from AS DATE) IS NULL OR expense_on >= CAST(:from AS DATE))
          AND (CAST(:to AS DATE) IS NULL OR expense_on <= CAST(:to AS DATE))
    """
    total = db.scalar(text('SELECT count(*) FROM kamartha.expenses' + where), params)
    rows = db.execute(text(
        'SELECT * FROM kamartha.expenses' + where +
        ' ORDER BY expense_on DESC,id DESC LIMIT :limit OFFSET :offset'),
        params).mappings().all()
    return [dict(row) for row in rows], total


def expense_detail(db, expense_id):
    row = db.execute(text('SELECT * FROM kamartha.expenses WHERE id=:id'),
                     {'id': expense_id}).mappings().one_or_none()
    if row is None:
        return None
    data = dict(row)
    data['audits'] = [dict(item) for item in db.execute(text("""
        SELECT * FROM kamartha.expense_audits WHERE expense_id=:id
        ORDER BY recorded_at,version_after
    """), {'id': expense_id}).mappings().all()]
    attachment = None
    if data['current_attachment_id']:
        attachment = db.execute(text("""
            SELECT id,mime_type,byte_size,sha256 FROM kamartha.attachments WHERE id=:id
        """), {'id': data['current_attachment_id']}).mappings().one_or_none()
    data['attachment'] = None if attachment is None else dict(attachment)
    return jsonable_encoder(data)
