import httpx
from uuid import uuid4

from app.core.errors import AppError


def _is_missing(response) -> bool:
    """Supabase returns 400 with a not_found body for absent private objects."""
    if response.status_code == 404:
        return True
    if response.status_code == 400:
        body = (response.text or '').lower()
        return 'not_found' in body or 'not found' in body
    return False


class SupabaseStorage:
    """Private bucket adapter; live integration verified against Supabase."""

    def __init__(self, url: str, service_key: str, bucket: str):
        self.base = url.rstrip('/')
        self.bucket = bucket
        self.headers = {'Authorization': f'Bearer {service_key}',
                        'apikey': service_key}

    def put(self, key: str, content: bytes, mime_type: str) -> None:
        response = httpx.post(
            f'{self.base}/storage/v1/object/{self.bucket}/{key}',
            content=content,
            headers={**self.headers, 'Content-Type': mime_type, 'x-upsert': 'true'},
            timeout=20,
        )
        if response.status_code not in (200, 201):
            raise AppError('STORAGE_UNAVAILABLE', 'Berkas belum dapat disimpan.', 503)

    def get(self, key: str) -> bytes:
        # The CDN caches authenticated object reads and does not purge on delete.
        # A per-request nonce keeps reads fresh and avoids stale content.
        response = httpx.get(
            f'{self.base}/storage/v1/object/{self.bucket}/{key}',
            params={'v': uuid4().hex},
            headers=self.headers, timeout=20,
        )
        if _is_missing(response):
            raise AppError('NOT_FOUND', 'Berkas tidak ditemukan.', 404)
        if response.status_code != 200:
            raise AppError('STORAGE_UNAVAILABLE', 'Berkas belum dapat dibaca.', 503)
        return response.content

    def delete(self, key: str) -> None:
        response = httpx.delete(
            f'{self.base}/storage/v1/object/{self.bucket}/{key}',
            headers=self.headers, timeout=20,
        )
        if _is_missing(response) or response.status_code in (200, 204):
            return
        raise AppError('STORAGE_UNAVAILABLE', 'Berkas belum dapat dihapus.', 503)
