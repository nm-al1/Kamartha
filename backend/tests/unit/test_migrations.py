import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


def test_migrations_form_one_linear_history():
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    revisions = list(script.walk_revisions())
    assert len(revisions) == 8
    assert script.get_current_head() == "0008_whatsapp_reminders"


def test_offline_upgrade_contains_private_schema_and_integrity_controls(monkeypatch):
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql+psycopg://offline.invalid/test")
    output = io.StringIO()
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"), output_buffer=output)
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    for table in (
        "app_settings", "managers", "sessions", "preauth_sessions", "login_windows",
        "idempotency_records", "rooms", "residents", "packages", "leases",
        "occupancies", "responsible_history", "invoices", "payments",
        "payment_allocations", "expenses", "expense_audits", "attachments",
        "initialization_records", "initialization_finalizations", "business_events", "backup_runs",
        "whatsapp_reminders",
    ):
        assert f"CREATE TABLE kamartha.{table}" in sql
    assert "2097152" in sql
    assert "FOREIGN KEY (invoice_id, lease_id)" in sql
    assert "REVOKE ALL ON SCHEMA kamartha FROM PUBLIC" in sql
    assert "opening_paid" in sql and "CREATE TRIGGER" in sql
    assert "UNIQUE (invoice_id,stage)" in sql
