import importlib
from pathlib import Path

import pytest


@pytest.fixture
def backup(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3] / 'ops'))
    return importlib.import_module('backup')


def test_backup_checksums_detect_tampering(backup, tmp_path):
    path = tmp_path / 'database.dump'
    path.write_bytes(b'original')
    expected = backup.file_digest(path)
    backup.verify_file(path, expected)
    path.write_bytes(b'changed')
    with pytest.raises(backup.BackupError, match='checksum'):
        backup.verify_file(path, expected)


def test_blob_paths_do_not_use_remote_object_keys(backup, tmp_path):
    path = backup.blob_path(tmp_path, '../../outside.pdf')
    assert path.parent == tmp_path / 'objects'
    assert len(path.name) == 64
    assert path != backup.blob_path(tmp_path, 'outside.pdf')


@pytest.mark.parametrize('url', [
    'postgresql+psycopg://owner:pw@remote.example/restore_test',
    'postgresql+psycopg://owner:pw@127.0.0.1/kamartha_dev',
    'postgresql+psycopg://owner:pw@localhost/postgres',
])
def test_restore_refuses_nonisolated_targets(backup, url):
    with pytest.raises(backup.BackupError):
        backup.validate_restore_target(url)


def test_restore_accepts_loopback_test_database(backup):
    backup.validate_restore_target('postgresql+psycopg://owner:pw@127.0.0.1/restore_test')


@pytest.mark.parametrize('base', ['http://example.supabase.co',
                                 'https://secret@example.supabase.co',
                                 'https://example.supabase.co/rest/v1'])
def test_bucket_reader_rejects_unsafe_base_urls(backup, base):
    with pytest.raises(backup.BackupError):
        backup.BucketReader(base, 'test-key', 'test-bucket')


def test_storage_listing_walks_folders_and_pages(backup, monkeypatch):
    import httpx

    client_class = httpx.Client
    calls = []

    def respond(request):
        import json
        data = json.loads(request.content)
        calls.append((data['prefix'], data['offset']))
        if data['prefix'] == 'folder/':
            rows = [{'name': 'nested.pdf', 'id': 'nested'}]
        elif data['offset'] == 0:
            rows = [{'name': 'folder', 'id': None}] + [
                {'name': f'{i:03}.png', 'id': str(i)} for i in range(99)]
        else:
            rows = [{'name': 'last.png', 'id': 'last'}]
        return httpx.Response(200, json=rows)

    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: client_class(
        **kwargs, transport=httpx.MockTransport(respond)))
    storage = backup.BucketReader('https://example.supabase.co', 'test-key', 'test-bucket')
    try:
        keys = storage.list_keys()
        assert len(keys) == 101
        assert 'folder/nested.pdf' in keys
        assert ('', 100) in calls
        assert ('folder/', 0) in calls
    finally:
        storage.close()
