import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from app.core.config import Settings


@pytest.fixture(autouse=True)
def isolate_profile_environment(monkeypatch):
    monkeypatch.setenv('PYTHON_DOTENV_DISABLED', '1')
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)


@pytest.fixture
def migrated_connection(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL belum tersedia; bukan bukti integrasi lulus.")
    if os.environ.get("CONFIRM_ISOLATED_TEST_DATABASE") != "yes":
        pytest.fail("Set CONFIRM_ISOLATED_TEST_DATABASE=yes hanya untuk database uji terisolasi.")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", url)
    engine = create_engine(url, poolclass=NullPool, hide_parameters=True)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            if connection.scalar(text("SELECT to_regnamespace('kamartha')")) is not None:
                pytest.fail("Database sudah memiliki schema kamartha; tes tidak akan menimpa data.")
            config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            yield connection
        finally:
            transaction.rollback()
    engine.dispose()
