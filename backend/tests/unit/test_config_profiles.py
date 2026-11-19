import pytest

from app.core.config import Settings
from app.main import create_app

LOCAL_URL = 'postgresql+psycopg://kamartha_runtime:pw@localhost:5432/kamartha_dev'
SUPABASE_URL = 'postgresql+psycopg://kamartha_runtime.ref:pw@pooler.example.test:5432/postgres?sslmode=require'
DUMMY = 'postgresql+psycopg://kamartha_runtime:pw@example.test:5432/kamartha?sslmode=require'


def test_local_profile_selects_local_block():
    settings = Settings(
        _env_file=None, app_profile='local',
        local_environment='development',
        local_app_origin='http://localhost:8080',
        local_database_url=LOCAL_URL,
        local_setup_code_hash='local-hash',
        local_ip_hash_secret='local-secret',
    )
    assert settings.environment == 'development'
    assert settings.app_origin == 'http://localhost:8080'
    assert settings.database_url.get_secret_value() == LOCAL_URL
    assert settings.setup_code_hash.get_secret_value() == 'local-hash'


def test_supabase_profile_overrides_local_block():
    settings = Settings(
        _env_file=None, app_profile='supabase',
        local_environment='development',
        local_app_origin='http://localhost:8080',
        local_database_url=LOCAL_URL,
        supabase_environment='production',
        supabase_app_origin='https://kamartha.example',
        supabase_database_url=SUPABASE_URL,
        supabase_setup_code_hash='remote-hash',
        supabase_ip_hash_secret='remote-secret',
    )
    assert settings.environment == 'production'
    assert settings.app_origin == 'https://kamartha.example'
    assert settings.database_url.get_secret_value() == SUPABASE_URL
    assert settings.setup_code_hash.get_secret_value() == 'remote-hash'


def test_supabase_profile_does_not_fall_back_to_local_values():
    settings = Settings(
        _env_file=None, app_profile='supabase',
        local_database_url=LOCAL_URL,
        local_app_origin='http://localhost:8080',
    )
    assert settings.database_url is None
    assert settings.app_origin == 'http://localhost:8080'


def test_profile_origin_must_be_a_single_origin():
    with pytest.raises(ValueError, match='Origin profil'):
        Settings(_env_file=None, app_profile='local',
                 local_app_origin='http://localhost:8080/path')


def test_production_requires_supabase_profile():
    settings = Settings(environment='production', app_profile='local',
                        database_url=DUMMY, _env_file=None)
    with pytest.raises(ValueError, match='APP_PROFILE'):
        create_app(settings)


def test_supabase_profile_requires_database_url():
    settings = Settings(environment='production', app_profile='supabase',
                        database_url=None, _env_file=None,
                        supabase_url='https://storage.example.test',
                        supabase_service_key='test-key')
    with pytest.raises(ValueError, match='DATABASE_URL'):
        create_app(settings)
