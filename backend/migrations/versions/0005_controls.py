"""Finalization, append-only audit and immutable-field guards."""
from alembic import op

revision = "0005_controls"
down_revision = "0004_files"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
CREATE TABLE kamartha.business_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id UUID NOT NULL,
    actor_id UUID REFERENCES kamartha.managers(id),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason TEXT NOT NULL, before_data JSONB, after_data JSONB, request_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kamartha.initialization_finalizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    singleton_key SMALLINT NOT NULL UNIQUE DEFAULT 1 CHECK (singleton_key = 1),
    cutover_date DATE NOT NULL,
    resident_count INTEGER NOT NULL CHECK (resident_count >= 0),
    occupied_room_count INTEGER NOT NULL CHECK (occupied_room_count >= 0),
    invoice_count INTEGER NOT NULL CHECK (invoice_count >= 0),
    total_receivable NUMERIC(30,0) NOT NULL CHECK (total_receivable >= 0),
    reconciliation_summary JSONB NOT NULL,
    confirmed_by UUID NOT NULL REFERENCES kamartha.managers(id),
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kamartha.backup_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(), completed_at TIMESTAMPTZ,
    state TEXT NOT NULL CHECK (state IN ('RUNNING','SUCCEEDED','FAILED')),
    application_version TEXT NOT NULL, migration_revision TEXT NOT NULL,
    manifest_location TEXT NOT NULL, database_checksum TEXT, error_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE FUNCTION kamartha.touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at := now(); RETURN NEW; END $$;
CREATE FUNCTION kamartha.reject_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Immutable historical record' USING ERRCODE = '23514'; END $$;
CREATE FUNCTION kamartha.guard_settings() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.mode = 'ACTIVE' AND
    (NEW.mode IS DISTINCT FROM OLD.mode OR NEW.cutover_date IS DISTINCT FROM OLD.cutover_date
     OR NEW.finalized_at IS DISTINCT FROM OLD.finalized_at OR NEW.finalized_by IS DISTINCT FROM OLD.finalized_by)
  THEN RAISE EXCEPTION 'Finalized settings are locked' USING ERRCODE = '23514'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER settings_guard BEFORE UPDATE ON kamartha.app_settings FOR EACH ROW EXECUTE FUNCTION kamartha.guard_settings();
CREATE FUNCTION kamartha.guard_invoice() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (SELECT mode FROM kamartha.app_settings WHERE id = 1) = 'ACTIVE' AND
    (NEW.amount IS DISTINCT FROM OLD.amount OR NEW.opening_paid IS DISTINCT FROM OLD.opening_paid
     OR NEW.lease_id IS DISTINCT FROM OLD.lease_id OR NEW.period_start IS DISTINCT FROM OLD.period_start
     OR NEW.period_end IS DISTINCT FROM OLD.period_end OR NEW.due_on IS DISTINCT FROM OLD.due_on
     OR NEW.source IS DISTINCT FROM OLD.source OR NEW.initialization_record_id IS DISTINCT FROM OLD.initialization_record_id)
  THEN RAISE EXCEPTION 'Invoice agreement and opening balance are locked' USING ERRCODE = '23514'; END IF;
  IF OLD.status = 'CANCELLED' AND NEW IS DISTINCT FROM OLD THEN
    RAISE EXCEPTION 'Cancelled invoice is immutable' USING ERRCODE = '23514'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER invoice_guard BEFORE UPDATE ON kamartha.invoices FOR EACH ROW EXECUTE FUNCTION kamartha.guard_invoice();
CREATE FUNCTION kamartha.guard_payment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.status = 'CANCELLED' OR NEW.lease_id IS DISTINCT FROM OLD.lease_id
     OR NEW.received_on IS DISTINCT FROM OLD.received_on OR NEW.total_amount IS DISTINCT FROM OLD.total_amount
     OR NEW.method IS DISTINCT FROM OLD.method OR NEW.reference IS DISTINCT FROM OLD.reference
     OR NEW.recorded_at IS DISTINCT FROM OLD.recorded_at OR NEW.recorded_by IS DISTINCT FROM OLD.recorded_by
  THEN RAISE EXCEPTION 'Receipt values are immutable; cancel and record again' USING ERRCODE = '23514'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER payment_guard BEFORE UPDATE ON kamartha.payments FOR EACH ROW EXECUTE FUNCTION kamartha.guard_payment();
""")
    for table in ("expense_audits", "business_events", "initialization_finalizations", "payment_allocations", "idempotency_records"):
        op.execute(f"CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON kamartha.{table} FOR EACH ROW EXECUTE FUNCTION kamartha.reject_change()")
    for table in ("managers", "app_settings", "sessions", "login_windows", "rooms", "residents", "packages", "initialization_records", "leases", "occupancies", "responsible_history", "invoices", "payments", "expenses", "attachments", "backup_runs"):
        op.execute(f"CREATE TRIGGER touch_updated_at BEFORE UPDATE ON kamartha.{table} FOR EACH ROW EXECUTE FUNCTION kamartha.touch_updated_at()")


def downgrade():
    raise RuntimeError("Rollback destruktif ditolak. Gunakan restore terverifikasi.")
