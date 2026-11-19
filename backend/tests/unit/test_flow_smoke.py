import importlib
from pathlib import Path

import pytest


def test_smoke_settings_cannot_inherit_primary_profile(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3] / 'ops'))
    flow = importlib.import_module('full_flow_smoke')
    monkeypatch.setenv('APP_PROFILE', 'supabase')
    monkeypatch.setenv('SUPABASE_DATABASE_URL', 'postgresql+psycopg://owner:pw@remote.example/postgres')
    monkeypatch.setenv('SUPABASE_ENVIRONMENT', 'production')
    monkeypatch.setenv('LOCAL_DATABASE_URL', 'postgresql+psycopg://owner:pw@remote.example/local')
    settings, _, _, _ = flow.test_configuration()
    assert settings.app_profile == 'local'
    assert settings.environment == 'test'
    assert settings.database_url is None
    settings, _, _, _ = flow.test_configuration(
        app_profile='supabase', database_url='postgresql+psycopg://owner:pw@127.0.0.1/flow_test',
        supabase_url='https://example.supabase.co', supabase_service_key='test-key')
    assert settings.environment == 'test'
    assert '@127.0.0.1/flow_test' in settings.database_url.get_secret_value()


def test_live_flow_refuses_remote_database(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3] / 'ops'))
    flow = importlib.import_module('full_flow_smoke')
    backup = importlib.import_module('backup')
    with pytest.raises(backup.BackupError):
        flow.run_live('postgresql+psycopg://owner:pw@remote.example/flow_test')
