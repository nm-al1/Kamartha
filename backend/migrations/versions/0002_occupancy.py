"""Rooms, residents, packages, opening drafts and occupancy history."""
from alembic import op

revision = "0002_occupancy"
down_revision = "0001_core"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
CREATE TABLE kamartha.rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number VARCHAR(30) NOT NULL CHECK (number = btrim(number) AND number <> ''),
    number_normalized VARCHAR(30) NOT NULL UNIQUE CHECK (number_normalized = lower(btrim(number))),
    room_type VARCHAR(100) NOT NULL,
    supported_occupants SMALLINT NOT NULL CHECK (supported_occupants IN (1,2)),
    reference_price BIGINT NOT NULL CHECK (reference_price > 0 AND reference_price <= 1000000000000),
    is_available_for_new_lease BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kamartha.residents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL CHECK (btrim(name) <> ''),
    identity_type VARCHAR(50) NOT NULL,
    identity_number VARCHAR(100) NOT NULL,
    whatsapp_number VARCHAR(30), notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX residents_identity ON kamartha.residents(lower(btrim(identity_type)), lower(btrim(identity_number)));
CREATE TABLE kamartha.packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    occupant_type SMALLINT NOT NULL CHECK (occupant_type IN (1,2)),
    period_months SMALLINT NOT NULL CHECK (period_months IN (1,6,12)),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (occupant_type, period_months)
);
CREATE TABLE kamartha.initialization_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_record_key UUID NOT NULL UNIQUE,
    draft_data JSONB NOT NULL,
    state TEXT NOT NULL DEFAULT 'DRAFT' CHECK (state IN ('DRAFT','VALIDATED','FINALIZED')),
    validation_errors JSONB,
    created_by UUID NOT NULL REFERENCES kamartha.managers(id),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kamartha.leases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES kamartha.rooms(id),
    package_id UUID NOT NULL REFERENCES kamartha.packages(id),
    starts_on DATE NOT NULL,
    agreed_ends_on DATE NOT NULL CHECK (agreed_ends_on > starts_on),
    effective_ends_on DATE NOT NULL CHECK (effective_ends_on >= starts_on AND effective_ends_on <= agreed_ends_on),
    period_anchor DATE NOT NULL CHECK (period_anchor = starts_on),
    occupant_type_snapshot SMALLINT NOT NULL CHECK (occupant_type_snapshot IN (1,2)),
    period_months_snapshot SMALLINT NOT NULL CHECK (period_months_snapshot IN (1,6,12)),
    period_price_snapshot BIGINT NOT NULL CHECK (period_price_snapshot > 0 AND period_price_snapshot <= 1000000000000),
    source TEXT NOT NULL CHECK (source IN ('OPERATIONAL','OPENING')),
    initialization_record_id UUID REFERENCES kamartha.initialization_records(id),
    early_end_reason TEXT,
    created_by UUID NOT NULL REFERENCES kamartha.managers(id),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((source = 'OPENING') = (initialization_record_id IS NOT NULL)),
    CHECK (effective_ends_on = agreed_ends_on OR coalesce(btrim(early_end_reason),'') <> '')
);
CREATE INDEX leases_room_interval ON kamartha.leases(room_id, starts_on, effective_ends_on);
CREATE TABLE kamartha.occupancies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id UUID NOT NULL REFERENCES kamartha.leases(id),
    resident_id UUID NOT NULL REFERENCES kamartha.residents(id),
    entered_on DATE NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('STAYING','EXITED','CONTINUED')),
    exited_on DATE,
    continued_on DATE,
    exit_date_unknown BOOLEAN NOT NULL DEFAULT false,
    predecessor_occupancy_id UUID UNIQUE REFERENCES kamartha.occupancies(id),
    recorded_by UUID NOT NULL REFERENCES kamartha.managers(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, lease_id),
    CHECK (exited_on IS NULL OR exited_on >= entered_on),
    CHECK (continued_on IS NULL OR continued_on >= entered_on),
    CHECK (
      (state = 'STAYING' AND exited_on IS NULL AND continued_on IS NULL AND NOT exit_date_unknown)
      OR (state = 'EXITED' AND continued_on IS NULL AND ((exited_on IS NOT NULL AND NOT exit_date_unknown) OR (exited_on IS NULL AND exit_date_unknown)))
      OR (state = 'CONTINUED' AND continued_on IS NOT NULL AND exited_on IS NULL AND NOT exit_date_unknown)
    )
);
CREATE INDEX occupancies_lease_state ON kamartha.occupancies(lease_id,state);
CREATE INDEX occupancies_resident_interval ON kamartha.occupancies(resident_id,entered_on);
CREATE TABLE kamartha.responsible_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id UUID NOT NULL REFERENCES kamartha.leases(id),
    occupancy_id UUID NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_until TIMESTAMPTZ CHECK (valid_until > valid_from),
    reason TEXT NOT NULL CHECK (btrim(reason) <> ''),
    actor_id UUID NOT NULL REFERENCES kamartha.managers(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (occupancy_id,lease_id) REFERENCES kamartha.occupancies(id,lease_id)
);
CREATE UNIQUE INDEX responsible_current ON kamartha.responsible_history(lease_id) WHERE valid_until IS NULL;
""")


def downgrade():
    raise RuntimeError("Rollback destruktif ditolak. Gunakan restore terverifikasi.")
