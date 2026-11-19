-- Run manually as migration owner after Alembic. Provision the login password
-- through a secure administrative channel; never write it in this script.
-- Supabase: the runtime login uses "kamartha_runtime.<PROJECT-REF>" through the
-- session pooler, while the database role itself stays "kamartha_runtime".
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kamartha_runtime') THEN
        CREATE ROLE kamartha_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kamartha_runtime'
               AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls)) THEN
        RAISE EXCEPTION 'Runtime role has excessive privileges';
    END IF;
END $$;

-- The pooler still needs an explicit connection grant per database.
DO $$
BEGIN
    EXECUTE 'GRANT CONNECT ON DATABASE ' || quote_ident(current_database())
        || ' TO kamartha_runtime';
END $$;


GRANT USAGE ON SCHEMA kamartha TO kamartha_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA kamartha TO kamartha_runtime;
GRANT INSERT, UPDATE ON kamartha.managers, kamartha.sessions,
    kamartha.preauth_sessions, kamartha.login_windows, kamartha.rooms,
    kamartha.residents, kamartha.leases, kamartha.occupancies,
    kamartha.responsible_history, kamartha.invoices, kamartha.payments,
    kamartha.expenses, kamartha.attachments, kamartha.initialization_records,
    kamartha.whatsapp_reminders
    TO kamartha_runtime;
GRANT UPDATE ON kamartha.app_settings TO kamartha_runtime;
GRANT INSERT ON kamartha.idempotency_records, kamartha.payment_allocations,
    kamartha.expense_audits, kamartha.business_events,
    kamartha.initialization_finalizations TO kamartha_runtime;
GRANT DELETE ON kamartha.preauth_sessions TO kamartha_runtime;
REVOKE DELETE ON kamartha.managers, kamartha.leases, kamartha.occupancies,
    kamartha.invoices, kamartha.payments, kamartha.payment_allocations, kamartha.whatsapp_reminders,
    kamartha.expenses, kamartha.attachments FROM kamartha_runtime;
REVOKE UPDATE, DELETE ON kamartha.expense_audits, kamartha.business_events,
    kamartha.initialization_finalizations, kamartha.idempotency_records,
    kamartha.payment_allocations FROM kamartha_runtime;
