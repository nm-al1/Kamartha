import hmac
from datetime import timedelta

from fastapi import Request
from sqlalchemy import text

from app.core.errors import AppError
from app.core.security import (
    csrf_token, hash_password, new_token, subject_hash, token_hash, verify_password,
)
from app.db.session import lock_business, open_session

SESSION_COOKIE = "kamartha_session"
PREAUTH_COOKIE = "kamartha_preauth"
_DUMMY_HASH = hash_password("dummy password for timing protection")


def require_origin(request: Request):
    if request.headers.get("origin") != request.app.state.settings.app_origin:
        raise AppError("ORIGIN_REJECTED", "Origin permintaan tidak diizinkan.", 403)


def csrf_secret(request: Request) -> str:
    secret = request.app.state.settings.ip_hash_secret
    if secret is None or len(secret.get_secret_value()) < 32:
        raise AppError("SERVICE_UNAVAILABLE", "Keamanan sesi belum dikonfigurasi.", 503)
    return secret.get_secret_value()


def require_manager(request: Request):
    raw = request.cookies.get(SESSION_COOKIE)
    if not raw or len(raw) > 128:
        raise AppError("UNAUTHORIZED", "Silakan login terlebih dahulu.", 401)
    now = request.app.state.clock.now()
    with open_session(request) as db, db.begin():
        row = db.execute(text("""
            SELECT s.id AS session_id, s.manager_id, s.csrf_token_hash, m.username
            FROM kamartha.sessions s JOIN kamartha.managers m ON m.id = s.manager_id
            WHERE s.token_hash = :hash AND s.revoked_at IS NULL AND m.is_active
              AND s.last_activity_at >= :cutoff AND s.created_at >= m.password_changed_at
            FOR UPDATE OF s
        """), {"hash": token_hash(raw), "cutoff": now - timedelta(minutes=120)}).mappings().one_or_none()
        if row is None:
            raise AppError("UNAUTHORIZED", "Sesi telah berakhir. Silakan login ulang.", 401)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            require_origin(request)
            csrf = request.headers.get("x-csrf-token", "")
            if not csrf or len(csrf) > 128 or not hmac.compare_digest(token_hash(csrf), row["csrf_token_hash"]):
                raise AppError("CSRF_REJECTED", "Token keamanan tidak sah. Muat ulang halaman.", 403)
        db.execute(text("UPDATE kamartha.sessions SET last_activity_at = :now WHERE id = :id"),
                   {"now": now, "id": row["session_id"]})
        return dict(row)


def check_preauth(db, request):
    cookie = request.cookies.get(PREAUTH_COOKIE, "")
    csrf = request.headers.get("x-csrf-token", "")
    if not cookie or not csrf or len(cookie) > 128 or len(csrf) > 128:
        raise AppError("CSRF_REJECTED", "Muat ulang halaman login.", 403)
    row = db.execute(text("""
        SELECT id, csrf_token_hash FROM kamartha.preauth_sessions
        WHERE token_hash = :hash AND expires_at > :now FOR UPDATE
    """), {"hash": token_hash(cookie), "now": request.app.state.clock.now()}).mappings().one_or_none()
    if row is None or not hmac.compare_digest(token_hash(csrf), row["csrf_token_hash"]):
        raise AppError("CSRF_REJECTED", "Token keamanan login tidak sah.", 403)
    return row["id"]


def lock_login_windows(db, request, username=None):
    secret = request.app.state.settings.ip_hash_secret
    if secret is None or len(secret.get_secret_value()) < 32:
        raise AppError("SERVICE_UNAVAILABLE", "Keamanan login belum dikonfigurasi.", 503)
    ip = request.client.host if request.client else "unknown"
    subjects = [("IP" if username is not None else "SETUP_IP", ip)]
    if username is not None:
        subjects.append(("USERNAME", username.lower()))
    now = request.app.state.clock.now()
    keys = []
    for kind, value in sorted(subjects):
        hashed = subject_hash(value, secret.get_secret_value())
        db.execute(text("""
            INSERT INTO kamartha.login_windows(subject_kind,subject_hash,window_started_at)
            VALUES (:kind,:hash,:now) ON CONFLICT DO NOTHING
        """), {"kind": kind, "hash": hashed, "now": now})
        row = db.execute(text("""
            SELECT * FROM kamartha.login_windows
            WHERE subject_kind = :kind AND subject_hash = :hash FOR UPDATE
        """), {"kind": kind, "hash": hashed}).mappings().one()
        if row["blocked_until"] and row["blocked_until"] > now:
            raise AppError("LOGIN_THROTTLED", "Terlalu banyak percobaan. Coba lagi nanti.", 429)
        if now >= row["window_started_at"] + timedelta(minutes=15):
            db.execute(text("""
                UPDATE kamartha.login_windows SET failure_count=0, blocked_until=NULL, window_started_at=:now
                WHERE subject_kind=:kind AND subject_hash=:hash
            """), {"kind": kind, "hash": hashed, "now": now})
        keys.append((kind, hashed))
    return keys


def record_failure(db, request, keys):
    for kind, hashed in keys:
        db.execute(text("""
            UPDATE kamartha.login_windows SET failure_count = failure_count + 1,
              blocked_until = CASE WHEN failure_count + 1 >= 5 THEN :until ELSE blocked_until END
            WHERE subject_kind=:kind AND subject_hash=:hash
        """), {"kind": kind, "hash": hashed, "until": request.app.state.clock.now() + timedelta(minutes=15)})


def authenticate(request, payload, *, setup=False):
    error = None
    result = None
    raw_session = new_token()
    csrf = csrf_token(raw_session, csrf_secret(request))
    with open_session(request) as db, db.begin():
        preauth_id = check_preauth(db, request)
        keys = lock_login_windows(db, request, None if setup else payload.username)
        if setup:
            lock_business(db)
            if db.execute(text("SELECT 1 FROM kamartha.managers")).first():
                raise AppError("SETUP_CLOSED", "Akun pengelola sudah tersedia.", 409)
            expected = request.app.state.settings.setup_code_hash
            if expected is None or not expected.get_secret_value():
                raise AppError("SETUP_DISABLED", "Penyiapan akun belum diaktifkan.", 503)
            if not verify_password(payload.setup_code, expected.get_secret_value()):
                record_failure(db, request, keys)
                error = AppError("SETUP_REJECTED", "Kode penyiapan tidak sah.", 403)
            else:
                row = db.execute(text("""
                    INSERT INTO kamartha.managers(username,username_normalized,password_hash)
                    VALUES (:username,:normalized,:hashed) RETURNING id,username
                """), {"username": payload.username, "normalized": payload.username.lower(),
                       "hashed": hash_password(payload.password)}).mappings().one()
                result = {"id": str(row["id"]), "username": row["username"]}
        else:
            row = db.execute(text("SELECT * FROM kamartha.managers WHERE username_normalized=:username FOR UPDATE"),
                             {"username": payload.username.lower()}).mappings().one_or_none()
            valid = verify_password(payload.password, row["password_hash"] if row else _DUMMY_HASH)
            if row is None or not valid or not row["is_active"]:
                record_failure(db, request, keys)
                error = AppError("LOGIN_REJECTED", "Username atau password salah.", 401)
            else:
                previous = request.cookies.get(SESSION_COOKIE)
                if previous:
                    db.execute(text("UPDATE kamartha.sessions SET revoked_at=:now WHERE token_hash=:hash AND revoked_at IS NULL"),
                               {"now": request.app.state.clock.now(), "hash": token_hash(previous)})
                db.execute(text("""
                    INSERT INTO kamartha.sessions(manager_id,token_hash,csrf_token_hash,created_at,last_activity_at)
                    VALUES (:manager,:token,:csrf,:now,:now)
                """), {"manager": row["id"], "token": token_hash(raw_session), "csrf": token_hash(csrf),
                       "now": request.app.state.clock.now()})
                result = {"id": str(row["id"]), "username": row["username"], "csrf_token": csrf}
        if error is None:
            db.execute(text("DELETE FROM kamartha.preauth_sessions WHERE id=:id"), {"id": preauth_id})
    # Persist failed-attempt counters before returning an authentication error.
    if error:
        raise error
    return result, raw_session
