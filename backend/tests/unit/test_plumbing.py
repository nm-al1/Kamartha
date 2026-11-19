import pytest
from app.core.errors import AppError
from app.core.pagination import Page
from app.deps import check_mode
from app.modules.attachments.storage import FakeStorage
from app.core.idempotency import payload_hash, parse_key
from app.core.config import Settings
from app.main import create_app
from app.modules.attachments.supabase_storage import SupabaseStorage


@pytest.mark.parametrize('url,key', [
    (None, None), ('https://storage.example.test', None),
    (None, 'test-only-storage-key'), ('https://storage.example.test', ''),
])
def test_production_rejects_missing_durable_storage(url, key):
    settings = Settings(environment='production', app_profile='supabase',
                        database_url=None, _env_file=None,
                        supabase_url=url, supabase_service_key=key)
    with pytest.raises(ValueError, match='SUPABASE'):
        create_app(settings)


DUMMY = 'postgresql+psycopg://kamartha_runtime:pw@example.test:5432/kamartha?sslmode=require'


def test_production_uses_configured_storage_without_connecting():
    settings = Settings(environment='production', app_profile='supabase',
                        app_origin='https://kos.example',
                        database_url=DUMMY, _env_file=None,
                        supabase_url='https://storage.example.test',
                        supabase_service_key='test-only-storage-key')
    assert isinstance(create_app(settings).state.storage, SupabaseStorage)


@pytest.mark.parametrize('environment', ['development', 'test'])
def test_fake_storage_remains_available_outside_production(environment):
    settings = Settings(environment=environment, database_url=None, _env_file=None,
                        supabase_url=None, supabase_service_key=None)
    assert isinstance(create_app(settings).state.storage, FakeStorage)


def test_fake_storage_roundtrip_and_idempotent_delete():
    storage = FakeStorage()
    storage.put('test/file', b'content', 'application/pdf')
    assert storage.get('test/file') == b'content'
    storage.delete('test/file')
    storage.delete('test/file')
    with pytest.raises(AppError):
        storage.get('test/file')


def test_mode_guard_rejects_wrong_mode():
    check_mode({'mode': 'ACTIVE'}, 'ACTIVE')
    with pytest.raises(AppError) as error:
        check_mode({'mode': 'PREPARATION'}, 'ACTIVE')
    assert error.value.status == 409


def test_pagination_total_covers_all_results():
    assert Page().metadata(21)['has_more']
    assert not Page(offset=20).metadata(21)['has_more']


def test_canonical_payload_and_key_validation():
    assert payload_hash({'a': 1, 'b': 2}) == payload_hash({'b': 2, 'a': 1})
    assert payload_hash({'a': 1}) != payload_hash({'a': 2})
    with pytest.raises(AppError):
        parse_key('invalid')
