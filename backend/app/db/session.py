from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.errors import AppError


def make_engine(settings):
    if not settings.database_url or not settings.database_url.get_secret_value():
        return None
    url = make_url(settings.database_url.get_secret_value())
    if url.drivername != "postgresql+psycopg":
        raise ValueError("DATABASE_URL harus memakai postgresql+psycopg.")
    if settings.environment == "production":
        if url.username == "postgres" or (url.username or "").startswith("postgres."):
            raise ValueError("Runtime tidak boleh memakai akun postgres.")
        if url.query.get("sslmode") not in ("require", "verify-ca", "verify-full"):
            raise ValueError("Koneksi produksi harus memakai TLS.")
    return create_engine(
        url, pool_size=2, max_overflow=0, pool_pre_ping=True, pool_timeout=10,
        connect_args={"connect_timeout": 10}, hide_parameters=True,
    )


def open_session(request) -> Session:
    engine = request.app.state.engine
    if engine is None:
        raise AppError("SERVICE_UNAVAILABLE", "Layanan data belum tersedia.", 503)
    return Session(engine, expire_on_commit=False)


def lock_business(db: Session):
    db.execute(text("SET LOCAL lock_timeout = '5s'"))
    settings = db.execute(text(
        "SELECT * FROM kamartha.app_settings WHERE id = 1 FOR UPDATE"
    )).mappings().one_or_none()
    if settings is None:
        raise AppError("SERVICE_UNAVAILABLE", "Konfigurasi aplikasi belum tersedia.", 503)
    return settings
