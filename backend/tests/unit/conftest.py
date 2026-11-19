import pytest

from app.core.config import Settings

PROFILE_KEYS = {name.upper() for name in Settings.model_fields}
EXTRA_KEYS = {
    'APP_PROFILE', 'MIGRATION_DATABASE_URL',
    'LOCAL_SETUP_CODE', 'SUPABASE_SETUP_CODE',
}


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    """Keep backend/.env values out of unit tests via load_dotenv side effects."""
    for key in PROFILE_KEYS | EXTRA_KEYS:
        monkeypatch.delenv(key, raising=False)
