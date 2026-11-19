"""Private schema, singleton account, sessions and idempotency."""
from alembic import op

revision = "0001_core"
down_revision = None
branch_labels = depends_on = None


def upgrade():
    op.execute("""
CREATE SCHEMA kamartha;
REVOKE ALL ON SCHEMA kamartha FROM PUBLIC;
CREATE TABLE kamartha.managers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    singleton_key SMALLINT NOT NULL UNIQUE DEFAULT 1 CHECK (singleton_key = 1),
    username VARCHAR(32) NOT NULL CHECK (username ~ '^[A-Za-z0-9._]{4,32}$'),
    username_normalized VARCHAR(32) NOT NULL UNIQUE CHECK (username_normalized = lower(username)),
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kamartha.app_settings (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    kos_name VARCHAR(150) NOT NULL DEFAULT 'Kamartha',
    mode TEXT NOT NULL DEFAULT 'PREPARATION' CHECK (mode IN ('PREPARATION', 'ACTIVE')),
    cutover_date DATE,
    finalized_at TIMESTAMPTZ,
    finalized_by UUID REFERENCES kamartha.managers(id),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (mode <> 'ACTIVE' OR (cutover_date IS NOT NULL AND finalized_at IS NOT NULL AND finalized_by IS NOT NULL))
);
INSERT INTO kamartha.app_settings (id) VALUES (1);
CREATE TABLE kamartha.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manager_id UUID NOT NULL REFERENCES kamartha.managers(id),
    token_hash TEXT NOT NULL UNIQUE,
    csrf_token_hash TEXT NOT NULL,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX sessions_manager ON kamartha.sessions(manager_id);
CREATE INDEX sessions_activity ON kamartha.sessions(last_activity_at);
CREATE TABLE kamartha.preauth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash TEXT NOT NULL UNIQUE,
    csrf_token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE kamartha.login_windows (
    subject_kind TEXT NOT NULL CHECK (subject_kind IN ('USERNAME', 'IP', 'SETUP_IP')),
    subject_hash TEXT NOT NULL,
    window_started_at TIMESTAMPTZ NOT NULL,
    failure_count INTEGER NOT NULL DEFAULT 0 CHECK (failure_count >= 0),
    blocked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (subject_kind, subject_hash)
);
CREATE TABLE kamartha.idempotency_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manager_id UUID NOT NULL REFERENCES kamartha.managers(id),
    scope VARCHAR(150) NOT NULL,
    request_key UUID NOT NULL,
    payload_hash TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    response_code SMALLINT NOT NULL CHECK (response_code BETWEEN 200 AND 299),
    response_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (manager_id, scope, request_key)
);
""")


def downgrade():
    raise RuntimeError("Rollback destruktif ditolak. Gunakan restore terverifikasi.")
