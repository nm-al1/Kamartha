import httpx
import pytest

from app.core.errors import AppError
from app.modules.attachments.supabase_storage import SupabaseStorage


class Response:
    def __init__(self, status_code, content=b'', text=''):
        self.status_code = status_code
        self.content = content
        self.text = text


MISSING_BODY = '{"statusCode":"404","error":"not_found","message":"Object not found"}'


def test_put_normalizes_base_url_and_object_path(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        return Response(201)

    monkeypatch.setattr(httpx, 'post', fake_post)
    storage = SupabaseStorage('https://ref.supabase.co/', 'secret', 'bucket')
    storage.put('a/b.png', b'x', 'image/png')
    assert calls == ['https://ref.supabase.co/storage/v1/object/bucket/a/b.png']


def test_get_maps_missing_object_to_404(monkeypatch):
    monkeypatch.setattr(httpx, 'get', lambda *args, **kwargs: Response(404))
    with pytest.raises(AppError) as error:
        SupabaseStorage('https://ref.supabase.co', 'secret', 'bucket').get('missing')
    assert error.value.status == 404


def test_get_maps_supabase_400_not_found_to_404(monkeypatch):
    monkeypatch.setattr(
        httpx, 'get', lambda *args, **kwargs: Response(400, text=MISSING_BODY))
    with pytest.raises(AppError) as error:
        SupabaseStorage('https://ref.supabase.co', 'secret', 'bucket').get('missing')
    assert error.value.status == 404


def test_get_sends_a_fresh_cache_buster_each_time(monkeypatch):
    nonces = []

    def fake_get(url, **kwargs):
        nonces.append(kwargs['params']['v'])
        return Response(200, content=b'ok')

    monkeypatch.setattr(httpx, 'get', fake_get)
    storage = SupabaseStorage('https://ref.supabase.co', 'secret', 'bucket')
    storage.get('object')
    storage.get('object')
    assert len(nonces) == 2
    assert nonces[0] != nonces[1]


@pytest.mark.parametrize('status', [200, 204, 404])
def test_delete_accepts_idempotent_status(monkeypatch, status):
    monkeypatch.setattr(httpx, 'delete', lambda *args, **kwargs: Response(status))
    SupabaseStorage('https://ref.supabase.co', 'secret', 'bucket').delete('object')


def test_delete_accepts_supabase_400_not_found(monkeypatch):
    monkeypatch.setattr(
        httpx, 'delete', lambda *args, **kwargs: Response(400, text=MISSING_BODY))
    SupabaseStorage('https://ref.supabase.co', 'secret', 'bucket').delete('object')


def test_delete_reports_server_error(monkeypatch):
    monkeypatch.setattr(httpx, 'delete', lambda *args, **kwargs: Response(500))
    with pytest.raises(AppError) as error:
        SupabaseStorage('https://ref.supabase.co', 'secret', 'bucket').delete('object')
    assert error.value.status == 503
