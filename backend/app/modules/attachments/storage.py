from typing import Protocol

from app.core.errors import AppError


class Storage(Protocol):
    def put(self, key: str, content: bytes, mime_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class FakeStorage:
    """Process-local test storage, not a durable or verified Supabase adapter."""

    def __init__(self):
        self._objects = {}

    def put(self, key: str, content: bytes, mime_type: str) -> None:
        if not key or key.startswith('/') or '..' in key.split('/'):
            raise ValueError('Object key tidak sah.')
        self._objects[key] = (bytes(content), mime_type)

    def get(self, key: str) -> bytes:
        if key not in self._objects:
            raise AppError('NOT_FOUND', 'Berkas tidak ditemukan.', 404)
        return self._objects[key][0]

    def delete(self, key: str) -> None:
        self._objects.pop(key, None)
