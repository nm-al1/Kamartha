from contextlib import asynccontextmanager
import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.exceptions import HTTPException

from app.core.clock import BusinessClock
from app.core.config import Settings
from app.core.errors import AppError
from app.db.session import make_engine
from app.modules.auth.router import router as auth_router
from app.modules.attachments.storage import FakeStorage
from app.modules.attachments.supabase_storage import SupabaseStorage
from app.modules.residents.router import router as residents_router
from app.modules.rooms.router import router as rooms_router
from app.modules.initialization.router import router as initialization_router
from app.modules.leases.router import router as leases_router
from app.modules.billing.router import invoice_router as invoices_router, router as billing_router
from app.modules.payments.router import router as payments_router
from app.modules.expenses.router import router as expenses_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.reports.router import router as reports_router
from app.modules.messaging.router import router as messaging_router
from app.modules.attachments.router import router as attachments_router
from app.modules.reminders.router import router as reminders_router


def create_app(settings: Settings | None = None, *, clock: BusinessClock | None = None) -> FastAPI:
    settings = settings or Settings()
    if settings.environment == 'production' and settings.app_profile != 'supabase':
        raise ValueError('ENVIRONMENT=production memerlukan APP_PROFILE=supabase.')
    if settings.app_profile == 'supabase' and not (
        settings.supabase_url and settings.supabase_service_key
    ):
        raise ValueError('SUPABASE_URL dan SUPABASE_SERVICE_KEY wajib tersedia pada profil Supabase.')
    if settings.app_profile == 'supabase' and not settings.database_url:
        raise ValueError('DATABASE_URL profil Supabase belum tersedia.')
    if settings.environment == 'production' and not settings.app_origin.startswith('https://'):
        raise ValueError('APP_ORIGIN produksi harus memakai HTTPS.')

    @asynccontextmanager
    async def lifespan(app):
        app.state.engine = make_engine(settings)
        try:
            yield
        finally:
            if app.state.engine is not None:
                app.state.engine.dispose()

    app = FastAPI(
        title="Kamartha API", version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
    )
    app.state.settings = settings
    app.state.clock = clock or BusinessClock()
    if (settings.app_profile == 'supabase'
            and settings.supabase_url and settings.supabase_service_key):
        app.state.storage = SupabaseStorage(
            settings.supabase_url,
            settings.supabase_service_key.get_secret_value(),
            settings.storage_bucket,
        )
    else:
        app.state.storage = FakeStorage()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(residents_router, prefix="/api/v1")
    app.include_router(rooms_router, prefix="/api/v1")
    app.include_router(initialization_router, prefix="/api/v1")
    app.include_router(leases_router, prefix="/api/v1")
    app.include_router(billing_router, prefix="/api/v1")
    app.include_router(invoices_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(expenses_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")
    app.include_router(reports_router, prefix="/api/v1")
    app.include_router(messaging_router, prefix="/api/v1")
    app.include_router(attachments_router, prefix="/api/v1")
    app.include_router(reminders_router, prefix="/api/v1")
    app.add_middleware(
        CORSMiddleware, allow_origins=[settings.app_origin], allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH"],
        allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = str(uuid4())
        try:
            response = await call_next(request)
        except Exception as exc:
            logging.getLogger("kamartha").error(
                "request_failed request_id=%s error_type=%s",
                request.state.request_id, type(exc).__name__,
            )
            response = error_response(request, "INTERNAL_ERROR", "Terjadi kesalahan server.", 500)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    def error_response(request, code, message, status, fields=None):
        return JSONResponse(status_code=status, content={
            "error": {"code": code, "message": message, "fields": fields},
            "request_id": request.state.request_id,
        })

    @app.exception_handler(AppError)
    async def app_error(request, exc):
        return error_response(request, exc.code, exc.message, exc.status, exc.fields)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        fields = [{"field": ".".join(map(str, item["loc"])), "code": item["type"]}
                  for item in exc.errors()]
        return error_response(request, "VALIDATION_ERROR", "Periksa isian yang diberikan.", 422, fields)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return error_response(request, code, "Permintaan tidak dapat diproses.", exc.status_code)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return error_response(request, "DATA_CONFLICT", "Data bertentangan dengan catatan yang ada.", 409)

    @app.exception_handler(DBAPIError)
    async def database_error(request, exc):
        return error_response(request, "SERVICE_UNAVAILABLE", "Layanan data belum tersedia. Coba lagi.", 503)

    @app.get("/api/v1/health")
    def health(request: Request):
        return {"data": {"status": "ok"}, "request_id": request.state.request_id}

    return app


app = create_app()
