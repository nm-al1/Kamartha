import importlib.util
from pathlib import Path

import pytest

OPS_FILE = Path(__file__).resolve().parents[3] / 'ops' / 'supabase_setup.py'
spec = importlib.util.spec_from_file_location('kamartha_supabase_setup', OPS_FILE)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)

HOST = 'aws-0-ap-southeast-1.pooler.supabase.com'


def values(**overrides):
    base = {
        'ENVIRONMENT': 'production',
        'APP_ORIGIN': 'https://kamartha.example',
        'MIGRATION_DATABASE_URL': (
            f'postgresql+psycopg://postgres.abcdefghij:ownerpass@{HOST}:5432/postgres?sslmode=require'),
        'DATABASE_URL': (
            f'postgresql+psycopg://kamartha_runtime.abcdefghij:runtimepass@{HOST}:5432/postgres?sslmode=require'),
        'RUNTIME_ROLE': 'kamartha_runtime',
        'IP_HASH_SECRET': 'x' * 43,
        'SETUP_CODE_HASH': 'argon2-hash',
        'SUPABASE_URL': 'https://abcdefghij.supabase.co',
        'SUPABASE_SERVICE_KEY': 'service-key',
        'STORAGE_BUCKET': 'kamartha-files',
    }
    base.update(overrides)
    return base


def test_valid_supabase_profile_is_accepted():
    owner, runtime, role, base = setup.validate(values())
    assert owner.username == 'postgres.abcdefghij'
    assert runtime.username == 'kamartha_runtime.abcdefghij'
    assert role == 'kamartha_runtime'
    assert base == 'https://abcdefghij.supabase.co'


@pytest.mark.parametrize('key', [
    'MIGRATION_DATABASE_URL', 'DATABASE_URL', 'IP_HASH_SECRET',
    'SUPABASE_URL', 'SUPABASE_SERVICE_KEY',
])
def test_missing_value_is_rejected(key):
    data = values()
    data[key] = ''
    with pytest.raises(setup.SetupError):
        setup.validate(data)


def test_local_database_is_rejected():
    data = values(DATABASE_URL=(
        'postgresql+psycopg://kamartha_runtime:pw@localhost:5432/postgres?sslmode=require'))
    with pytest.raises(setup.SetupError, match='Supabase'):
        setup.validate(data)


def test_missing_tls_is_rejected():
    data = values(MIGRATION_DATABASE_URL=(
        f'postgresql+psycopg://postgres.abcdefghij:pw@{HOST}:5432/postgres'))
    with pytest.raises(setup.SetupError, match='sslmode'):
        setup.validate(data)


def test_rest_suffix_is_rejected():
    data = values(SUPABASE_URL='https://abcdefghij.supabase.co/rest/v1/')
    with pytest.raises(setup.SetupError, match='SUPABASE_URL'):
        setup.validate(data)


def test_owner_role_cannot_be_used_at_runtime():
    data = values(DATABASE_URL=(
        f'postgresql+psycopg://postgres.abcdefghij:pw@{HOST}:5432/postgres?sslmode=require'))
    with pytest.raises(setup.SetupError, match='runtime'):
        setup.validate(data)
