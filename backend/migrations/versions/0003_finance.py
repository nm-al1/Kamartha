"""Invoices, receipts, allocations and expense audit."""
from alembic import op

revision = "0003_finance"
down_revision = "0002_occupancy"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
CREATE TABLE kamartha.invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id UUID NOT NULL REFERENCES kamartha.leases(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL CHECK (period_end > period_start),
    due_on DATE NOT NULL,
    amount BIGINT NOT NULL CHECK (amount > 0 AND amount <= 1000000000000),
    opening_paid BIGINT NOT NULL DEFAULT 0 CHECK (opening_paid >= 0 AND opening_paid <= amount),
    source TEXT NOT NULL CHECK (source IN ('OPERATIONAL','OPENING')),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','CANCELLED')),
    cancellation_reason TEXT,
    cancelled_at TIMESTAMPTZ,
    cancelled_by UUID REFERENCES kamartha.managers(id),
    initialization_record_id UUID REFERENCES kamartha.initialization_records(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (lease_id,period_start), UNIQUE (id,lease_id),
    CHECK ((source = 'OPENING') = (initialization_record_id IS NOT NULL)),
    CHECK (source <> 'OPERATIONAL' OR (opening_paid = 0 AND due_on = period_start)),
    CHECK ((status = 'ACTIVE' AND cancellation_reason IS NULL AND cancelled_at IS NULL AND cancelled_by IS NULL)
       OR (status = 'CANCELLED' AND coalesce(btrim(cancellation_reason),'') <> '' AND cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL))
);
CREATE INDEX invoices_due ON kamartha.invoices(due_on);
CREATE INDEX invoices_status ON kamartha.invoices(status);
CREATE TABLE kamartha.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id UUID NOT NULL REFERENCES kamartha.leases(id),
    received_on DATE NOT NULL,
    total_amount BIGINT NOT NULL CHECK (total_amount > 0 AND total_amount <= 1000000000000),
    method TEXT NOT NULL CHECK (method IN ('CASH','TRANSFER','QRIS')),
    reference VARCHAR(200),
    status TEXT NOT NULL DEFAULT 'VALID' CHECK (status IN ('VALID','CANCELLED')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    recorded_by UUID NOT NULL REFERENCES kamartha.managers(id),
    cancellation_reason TEXT,
    cancelled_at TIMESTAMPTZ,
    cancelled_by UUID REFERENCES kamartha.managers(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id,lease_id),
    CHECK ((status = 'VALID' AND cancellation_reason IS NULL AND cancelled_at IS NULL AND cancelled_by IS NULL)
       OR (status = 'CANCELLED' AND coalesce(btrim(cancellation_reason),'') <> '' AND cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL))
);
CREATE INDEX payments_received ON kamartha.payments(received_on);
CREATE INDEX payments_lease_received ON kamartha.payments(lease_id,received_on);
CREATE TABLE kamartha.payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL,
    invoice_id UUID NOT NULL,
    lease_id UUID NOT NULL,
    amount BIGINT NOT NULL CHECK (amount > 0 AND amount <= 1000000000000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (payment_id, lease_id) REFERENCES kamartha.payments(id,lease_id),
    FOREIGN KEY (invoice_id, lease_id) REFERENCES kamartha.invoices(id,lease_id),
    UNIQUE (payment_id,invoice_id)
);
CREATE INDEX allocations_invoice ON kamartha.payment_allocations(invoice_id);
CREATE TABLE kamartha.expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_on DATE NOT NULL,
    amount BIGINT NOT NULL CHECK (amount > 0 AND amount <= 1000000000000),
    category TEXT NOT NULL CHECK (category IN ('ELECTRICITY','WATER','INTERNET','REPAIR','SALARY','OTHER')),
    description TEXT NOT NULL CHECK (btrim(description) <> ''),
    status TEXT NOT NULL DEFAULT 'VALID' CHECK (status IN ('VALID','CANCELLED')),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    created_by UUID NOT NULL REFERENCES kamartha.managers(id),
    current_attachment_id UUID,
    cancellation_reason TEXT,
    cancelled_at TIMESTAMPTZ,
    cancelled_by UUID REFERENCES kamartha.managers(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((status = 'VALID' AND cancellation_reason IS NULL AND cancelled_at IS NULL AND cancelled_by IS NULL)
       OR (status = 'CANCELLED' AND coalesce(btrim(cancellation_reason),'') <> '' AND cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL))
);
CREATE INDEX expenses_date ON kamartha.expenses(expense_on);
CREATE INDEX expenses_category ON kamartha.expenses(category);
CREATE TABLE kamartha.expense_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_id UUID NOT NULL REFERENCES kamartha.expenses(id),
    action TEXT NOT NULL CHECK (action IN ('UPDATE','CANCEL')),
    before_data JSONB NOT NULL, after_data JSONB NOT NULL,
    reason TEXT NOT NULL CHECK (btrim(reason) <> ''),
    actor_id UUID NOT NULL REFERENCES kamartha.managers(id),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    attachment_before_id UUID, attachment_after_id UUID,
    version_before INTEGER NOT NULL CHECK (version_before > 0),
    version_after INTEGER NOT NULL CHECK (version_after = version_before + 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (expense_id,version_after)
);
""")


def downgrade():
    raise RuntimeError("Rollback destruktif ditolak. Gunakan restore terverifikasi.")
