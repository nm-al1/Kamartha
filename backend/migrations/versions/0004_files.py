"""Private attachment metadata and historical evidence references."""
from alembic import op

revision = "0004_files"
down_revision = "0003_finance"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
CREATE TABLE kamartha.attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by UUID NOT NULL REFERENCES kamartha.managers(id),
    object_key TEXT NOT NULL UNIQUE,
    mime_type TEXT NOT NULL CHECK (mime_type IN ('image/jpeg','image/png','application/pdf')),
    byte_size INTEGER NOT NULL CHECK (byte_size > 0 AND byte_size <= 2097152),
    sha256 CHAR(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    state TEXT NOT NULL CHECK (state IN ('STAGED','LINKED','DELETING','DELETED')),
    staged_expires_at TIMESTAMPTZ NOT NULL,
    payment_id UUID REFERENCES kamartha.payments(id),
    expense_id UUID REFERENCES kamartha.expenses(id),
    linked_at TIMESTAMPTZ, deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id,expense_id),
    CHECK (
      (state = 'STAGED' AND payment_id IS NULL AND expense_id IS NULL AND linked_at IS NULL AND deleted_at IS NULL)
      OR (state = 'LINKED' AND ((payment_id IS NOT NULL)::int + (expense_id IS NOT NULL)::int) = 1 AND linked_at IS NOT NULL AND deleted_at IS NULL)
      OR (state = 'DELETING' AND payment_id IS NULL AND expense_id IS NULL AND linked_at IS NULL AND deleted_at IS NULL)
      OR (state = 'DELETED' AND payment_id IS NULL AND expense_id IS NULL AND linked_at IS NULL AND deleted_at IS NOT NULL)
    )
);
CREATE UNIQUE INDEX attachment_one_receipt ON kamartha.attachments(payment_id) WHERE payment_id IS NOT NULL;
CREATE INDEX attachments_staging ON kamartha.attachments(state,staged_expires_at);
ALTER TABLE kamartha.expenses ADD CONSTRAINT expense_current_attachment
    FOREIGN KEY (current_attachment_id,id) REFERENCES kamartha.attachments(id,expense_id);
ALTER TABLE kamartha.expense_audits ADD CONSTRAINT expense_attachment_before
    FOREIGN KEY (attachment_before_id,expense_id) REFERENCES kamartha.attachments(id,expense_id);
ALTER TABLE kamartha.expense_audits ADD CONSTRAINT expense_attachment_after
    FOREIGN KEY (attachment_after_id,expense_id) REFERENCES kamartha.attachments(id,expense_id);
""")


def downgrade():
    raise RuntimeError("Rollback destruktif ditolak. Gunakan restore terverifikasi.")
