"""Close migration metadata access and default function execution grants."""
from alembic import op

revision = '0007_audit_permissions'
down_revision = '0006_seed_permissions'
branch_labels = depends_on = None


def upgrade():
    op.execute("""
-- Schema-scoped defaults cannot subtract PostgreSQL's global PUBLIC EXECUTE.
-- This changes future functions created by the migration owner in all schemas.
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kamartha FROM PUBLIC;
REVOKE ALL ON public.alembic_version FROM PUBLIC;
DO $$
DECLARE role_name TEXT;
BEGIN
  FOREACH role_name IN ARRAY ARRAY['anon', 'authenticated', 'service_role'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
      EXECUTE format('REVOKE ALL ON public.alembic_version FROM %I', role_name);
    END IF;
  END LOOP;
END $$;
""")


def downgrade():
    # Downgrading must not reopen anonymous migration metadata access.
    pass
