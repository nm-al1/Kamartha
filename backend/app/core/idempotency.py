"""Helpers run inside the caller's transaction after lock_business()."""
import hashlib
import json
from uuid import UUID

from sqlalchemy import text

from app.core.errors import AppError
from fastapi.encoders import jsonable_encoder


def parse_key(value: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise AppError('IDEMPOTENCY_KEY_INVALID', 'Idempotency-Key harus UUID yang sah.', 422) from exc


def payload_hash(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def replay(db, manager_id, scope, key, payload):
    row = db.execute(text('''
        SELECT payload_hash, response_code, response_data
        FROM kamartha.idempotency_records
        WHERE manager_id=:manager AND scope=:scope AND request_key=:key
    '''), {'manager': manager_id, 'scope': scope, 'key': key}).mappings().one_or_none()
    if row is not None and row['payload_hash'] != payload_hash(payload):
        raise AppError('IDEMPOTENCY_CONFLICT', 'Kunci sudah dipakai dengan isian berbeda.', 409)
    return row


def remember(db, manager_id, scope, key, payload, response_data, response_code=200):
    if not 200 <= response_code <= 299:
        raise ValueError('Hanya hasil sukses dapat disimpan.')
    db.execute(text('''
        INSERT INTO kamartha.idempotency_records
            (manager_id, scope, request_key, payload_hash, response_code, response_data)
        VALUES (:manager, :scope, :key, :hash, :code, CAST(:data AS JSONB))
    '''), {'manager': manager_id, 'scope': scope, 'key': key, 'hash': payload_hash(payload),
           'code': response_code, 'data': json.dumps(response_data, allow_nan=False)})


class BusinessRequest:
    """Replay a business write while its caller holds the singleton row lock."""

    def __init__(self, db, request, manager, scope, payload):
        self.db = db
        self.manager_id = manager['manager_id']
        self.scope = scope
        self.key = parse_key(request.headers.get('Idempotency-Key'))
        self.payload = jsonable_encoder(payload)

    def previous(self):
        row = replay(self.db, self.manager_id, self.scope, self.key, self.payload)
        return None if row is None else row['response_data']

    def save(self, result, code=200):
        encoded = jsonable_encoder(result)
        remember(self.db, self.manager_id, self.scope, self.key, self.payload, encoded, code)
        return encoded
