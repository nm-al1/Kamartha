import importlib
import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

pytestmark = pytest.mark.integration


def test_database_and_attachment_restore_round_trip(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3] / 'ops'))
    backup = importlib.import_module('backup')
    # Synthetic fixtures already live in pytest's disposable directory.
    monkeypatch.setattr(backup, 'protect_directory', lambda _: None)
    url = make_url(os.environ['TEST_DATABASE_URL'])
    assert url.host in ('127.0.0.1', 'localhost') and url.database.endswith('_test')
    assert os.environ.get('CONFIRM_ISOLATED_TEST_DATABASE') == 'yes'
    names = [f'backup_{uuid4().hex}_test' for _ in range(2)]
    admin = create_engine(url.set(database='postgres'), isolation_level='AUTOCOMMIT')
    engines = []
    try:
        with admin.connect() as db:
            for name in names:
                db.execute(text(f'CREATE DATABASE "{name}"'))
        source, target = [url.set(database=name) for name in names]
        engine = create_engine(source)
        engines.append(engine)
        monkeypatch.setenv('MIGRATION_DATABASE_URL', source.render_as_string(hide_password=False))
        with engine.begin() as db:
            config = Config(str(Path(__file__).parents[2] / 'alembic.ini'))
            config.attributes['connection'] = db
            command.upgrade(config, '0007_audit_permissions')
            for role in ('anon', 'authenticated', 'kamartha_runtime'):
                db.exec_driver_sql(f"""DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{role}') THEN
                        CREATE ROLE {role};
                    END IF;
                END $$""")
            db.exec_driver_sql("""ALTER DEFAULT PRIVILEGES IN SCHEMA kamartha
                GRANT ALL ON TABLES TO anon, authenticated, kamartha_runtime""")
            command.upgrade(config, 'head')
            for role in ('anon', 'authenticated', 'kamartha_runtime', 'public'):
                for privilege in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'TRIGGER', 'REFERENCES'):
                    allowed = role == 'kamartha_runtime' and privilege in ('SELECT', 'INSERT', 'UPDATE')
                    assert db.scalar(text("""SELECT has_table_privilege(:role,
                        'kamartha.whatsapp_reminders', :privilege)"""),
                        {'role': role, 'privilege': privilege}) is allowed
            # The broad defaults above were only for the ACL regression.
            db.exec_driver_sql("""ALTER DEFAULT PRIVILEGES IN SCHEMA kamartha
                REVOKE ALL ON TABLES FROM anon, authenticated, kamartha_runtime""")
            manager = db.scalar(text("""
                INSERT INTO kamartha.managers(username,username_normalized,password_hash)
                VALUES ('backup','backup','not-an-auth-test') RETURNING id
            """))
            content = b'backup attachment test bytes'
            import hashlib
            db.execute(text("""
                INSERT INTO kamartha.attachments(uploaded_by,object_key,mime_type,byte_size,
                    sha256,state,staged_expires_at)
                VALUES (:manager,'proof/test.pdf','application/pdf',:size,:sha,'STAGED',now()+interval '1 day')
            """), {'manager': manager, 'size': len(content), 'sha': hashlib.sha256(content).hexdigest()})
            reminder_id = db.scalar(text("""
                WITH room AS (
                    INSERT INTO kamartha.rooms(number,number_normalized,room_type,supported_occupants,reference_price)
                    VALUES ('B1','b1','Standar',2,700000) RETURNING id
                ), lease AS (
                    INSERT INTO kamartha.leases(room_id,package_id,starts_on,agreed_ends_on,effective_ends_on,
                        period_anchor,occupant_type_snapshot,period_months_snapshot,period_price_snapshot,source,created_by)
                    SELECT room.id,p.id,'2026-03-10','2026-04-10','2026-04-10','2026-03-10',
                        1,1,700000,'OPERATIONAL',:manager
                    FROM room CROSS JOIN kamartha.packages p WHERE p.occupant_type=1 AND p.period_months=1
                    RETURNING id
                ), invoice AS (
                    INSERT INTO kamartha.invoices(lease_id,period_start,period_end,due_on,amount,source)
                    SELECT id,'2026-03-10','2026-04-10','2026-03-10',700000,'OPERATIONAL' FROM lease RETURNING id
                )
                INSERT INTO kamartha.whatsapp_reminders(invoice_id,stage,status,recipient_mask,amount,reminder_date)
                SELECT id,'H3','UNKNOWN','***0000',700000,'2026-03-07' FROM invoice RETURNING id
            """), {'manager': manager})

        class Storage:
            def list_keys(self):
                return ['proof/test.pdf', 'unreferenced/object.png']

            def get(self, key):
                return content if key == 'proof/test.pdf' else b'orphan bytes'

        pg_bin = Path(os.environ.get('PG_BIN', r'C:\Program Files\PostgreSQL\17\bin'))
        destination = tmp_path / 'backup'
        manifest = backup.create_backup(source, Storage(), destination, pg_bin)
        assert manifest['revision'] == '0008_whatsapp_reminders'
        assert len(manifest['objects']) == 2
        backup.restore_database(target, destination, pg_bin)
        restored = create_engine(target)
        engines.append(restored)
        with restored.connect() as db:
            assert db.scalar(text('SELECT count(*) FROM kamartha.attachments')) == 1
            assert db.scalar(text('SELECT count(*) FROM kamartha.packages')) == 6
            assert db.execute(text("""SELECT stage,status,recipient_mask,amount
                FROM kamartha.whatsapp_reminders WHERE id=:id"""),
                {'id': reminder_id}).one() == ('H3', 'UNKNOWN', '***0000', 700000)
        assert backup.blob_path(destination, 'proof/test.pdf').read_bytes() == content
        class BrokenStorage(Storage):
            def get(self, key):
                return b'wrong bytes'

        incomplete = tmp_path / 'incomplete'
        with pytest.raises(backup.BackupError, match='metadata'):
            backup.create_backup(source, BrokenStorage(), incomplete, pg_bin)
        assert not (incomplete / 'manifest.json').exists()
        with pytest.raises(backup.BackupError, match='empty'):
            backup.restore_database(target, destination, pg_bin)
        backup.blob_path(destination, 'proof/test.pdf').write_bytes(b'corrupted')
        with pytest.raises(backup.BackupError, match='checksum'):
            backup.verify_backup(destination)
    finally:
        for engine in engines:
            engine.dispose()
        with admin.connect() as db:
            for name in names:
                db.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()
