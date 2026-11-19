import os

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

load_dotenv()
url = os.environ.get("MIGRATION_DATABASE_URL")
if not url:
    raise RuntimeError("MIGRATION_DATABASE_URL wajib diisi dengan koneksi owner migrasi.")
if make_url(url).drivername != "postgresql+psycopg":
    raise RuntimeError("Migrasi memerlukan PostgreSQL dengan driver psycopg.")

if context.is_offline_mode():
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
elif context.config.attributes.get("connection") is not None:
    context.configure(connection=context.config.attributes["connection"])
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool, hide_parameters=True)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
