"""Durable, deduplicated WhatsApp prototype delivery log."""
from alembic import op

revision = '0008_whatsapp_reminders'
down_revision = '0007_audit_permissions'
branch_labels = depends_on = None


def upgrade():
    op.execute('''
CREATE TABLE kamartha.whatsapp_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES kamartha.invoices(id),
    stage TEXT NOT NULL CHECK (stage IN ('H3','DUE')),
    status TEXT NOT NULL CHECK (status IN ('SENDING','SENT','UNKNOWN','FAILED')),
    recipient_mask TEXT NOT NULL,
    amount BIGINT NOT NULL CHECK (amount > 0),
    reminder_date DATE NOT NULL,
    provider_message_id TEXT,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (invoice_id,stage)
);
REVOKE ALL ON kamartha.whatsapp_reminders FROM PUBLIC;
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
        REVOKE ALL ON kamartha.whatsapp_reminders FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
        REVOKE ALL ON kamartha.whatsapp_reminders FROM authenticated;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='kamartha_runtime') THEN
        REVOKE ALL ON kamartha.whatsapp_reminders FROM kamartha_runtime;
        GRANT SELECT, INSERT, UPDATE ON kamartha.whatsapp_reminders TO kamartha_runtime;
    END IF;
END $$;
''')


def downgrade():
    raise RuntimeError('Log pengiriman tidak boleh dihapus otomatis; gunakan restore terverifikasi.')
