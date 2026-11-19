"""Production seed contains only six packages; public access is revoked."""
from alembic import op

revision = "0006_seed_permissions"
down_revision = "0005_controls"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
INSERT INTO kamartha.packages (occupant_type, period_months)
VALUES (1,1),(1,6),(1,12),(2,1),(2,6),(2,12);
REVOKE ALL ON SCHEMA kamartha FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA kamartha FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kamartha FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA kamartha REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA kamartha REVOKE ALL ON FUNCTIONS FROM PUBLIC;
DO $$
DECLARE role_name TEXT;
BEGIN
  FOREACH role_name IN ARRAY ARRAY['anon','authenticated'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
      EXECUTE format('REVOKE ALL ON SCHEMA kamartha FROM %I', role_name);
      EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA kamartha FROM %I', role_name);
      EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kamartha FROM %I', role_name);
    END IF;
  END LOOP;
END $$;
""")


def downgrade():
    raise RuntimeError("Rollback destruktif ditolak. Gunakan restore terverifikasi.")
