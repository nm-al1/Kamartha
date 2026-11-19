import pytest

from app.core.config import Settings
from app.main import create_app
from app.modules.attachments.storage import FakeStorage


def settings(**overrides):
    values = dict(_env_file=None, app_profile='supabase',
                  database_url='postgresql+psycopg://runtime:pw@localhost/db',
                  supabase_url='https://example.supabase.co',
                  supabase_service_key='test-key', app_origin='https://kos.example')
    values.update(overrides)
    return Settings(**values)


@pytest.mark.parametrize('missing', ['supabase_url', 'supabase_service_key'])
def test_supabase_never_falls_back_to_memory(missing):
    with pytest.raises(ValueError, match='SUPABASE_URL'):
        create_app(settings(**{missing: None}))


def test_local_storage_remains_offline():
    app = create_app(Settings(_env_file=None, app_profile='local'))
    assert isinstance(app.state.storage, FakeStorage)


def test_production_rejects_http_origin():
    with pytest.raises(ValueError, match='HTTPS'):
        create_app(settings(environment='production', app_origin='http://kos.example'))


def test_development_supabase_allows_local_browser():
    create_app(settings(app_origin='http://localhost:8081'))
