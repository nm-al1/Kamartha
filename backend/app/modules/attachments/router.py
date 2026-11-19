import hashlib
import io
from datetime import timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Header, Request, Response, UploadFile
from PIL import Image
from pypdf import PdfReader
from sqlalchemy import text

from app.core.errors import AppError
from app.core.idempotency import parse_key, payload_hash, remember, replay
from app.db.session import open_session
from app.modules.auth.router import envelope
from app.modules.auth.service import require_manager

router = APIRouter(prefix='/attachments', tags=['attachments'])
ALLOWED = {'image/jpeg', 'image/png', 'application/pdf'}
MAX_BYTES = 2 * 1024 * 1024


def validate_file(content, mime):
    if mime not in ALLOWED:
        raise AppError('ATTACHMENT_TYPE', 'Gunakan JPG, PNG atau PDF.', 422)
    if mime == 'application/pdf':
        if not content.startswith(b'%PDF-'):
            raise AppError('ATTACHMENT_CORRUPT', 'Berkas PDF tidak sah.', 422)
        try:
            if len(PdfReader(io.BytesIO(content)).pages) == 0:
                raise ValueError
        except Exception as exc:
            raise AppError('ATTACHMENT_CORRUPT', 'Berkas PDF tidak sah.', 422) from exc
    else:
        expected = b'\xff\xd8\xff' if mime == 'image/jpeg' else b'\x89PNG\r\n\x1a\n'
        if not content.startswith(expected):
            raise AppError('ATTACHMENT_CORRUPT', 'Isi berkas tidak sesuai tipe gambar.', 422)
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()
        except Exception as exc:
            raise AppError('ATTACHMENT_CORRUPT', 'Berkas gambar rusak.', 422) from exc


@router.post('', status_code=201)
async def upload(request: Request, file: UploadFile = File(...),
                 idempotency_key: str = Header(...), manager=Depends(require_manager)):
    content = await file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise AppError('ATTACHMENT_TOO_LARGE', 'Ukuran berkas maksimal 2 MB.', 413)
    mime = file.content_type or ''
    validate_file(content, mime)
    digest = hashlib.sha256(content).hexdigest()
    key = parse_key(idempotency_key)
    payload = {'sha256': digest, 'mime_type': mime, 'byte_size': len(content)}
    now = request.app.state.clock.now()
    object_key = str(uuid4())
    with open_session(request) as db, db.begin():
        previous = replay(db, manager['manager_id'], 'attachments.create', key, payload)
        if previous is not None:
            return envelope(request, previous['response_data'])
        request.app.state.storage.put(object_key, content, mime)
        try:
            attachment_id = db.scalar(text("""
                INSERT INTO kamartha.attachments(uploaded_by,object_key,mime_type,byte_size,
                    sha256,state,staged_expires_at)
                VALUES (:manager,:key,:mime,:size,:sha,'STAGED',:expires) RETURNING id
            """), {'manager': manager['manager_id'], 'key': object_key, 'mime': mime,
                   'size': len(content), 'sha': digest,
                   'expires': now + timedelta(hours=24)})
            result = {'id': str(attachment_id), 'mime_type': mime,
                      'byte_size': len(content), 'sha256': digest, 'state': 'STAGED'}
            remember(db, manager['manager_id'], 'attachments.create', key, payload, result, 201)
        except Exception:
            request.app.state.storage.delete(object_key)
            raise
    return envelope(request, result)


@router.get('/{attachment_id}/content')
def content(attachment_id: UUID, request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        row = db.execute(text('SELECT * FROM kamartha.attachments WHERE id=:id'),
                         {'id': attachment_id}).mappings().one_or_none()
    if row is None or row['state'] == 'DELETED':
        raise AppError('NOT_FOUND', 'Lampiran tidak ditemukan.', 404)
    if row['state'] == 'STAGED' and row['uploaded_by'] != manager['manager_id']:
        raise AppError('FORBIDDEN', 'Lampiran belum menjadi milik catatan ini.', 403)
    body = request.app.state.storage.get(row['object_key'])
    return Response(body, media_type=row['mime_type'], headers={
        'Content-Disposition': 'inline',
        'Content-Security-Policy': "default-src 'none'; sandbox",
    })
