from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import text

from app.core.errors import AppError
from app.core.security import csrf_token, hash_password, new_token, token_hash, verify_password
from app.db.session import open_session
from app.modules.auth.schemas import ChangePasswordInput, LoginInput, SetupInput
from app.modules.auth.service import (
    PREAUTH_COOKIE, SESSION_COOKIE, authenticate, csrf_secret, require_manager, require_origin,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def set_cookie(response, request, name, value):
    response.set_cookie(name, value, httponly=True, secure=request.app.state.settings.environment == "production",
                        samesite="lax", path="/")


def envelope(request, data):
    return {"data": data, "request_id": request.state.request_id}


@router.get("/csrf")
def csrf(request: Request, response: Response):
    session = request.cookies.get(SESSION_COOKIE)
    if session:
        try:
            require_manager(request)
        except AppError as exc:
            if exc.status != 401:
                raise
            response.delete_cookie(SESSION_COOKIE, path="/")
        else:
            return envelope(request, {"csrf_token": csrf_token(session, csrf_secret(request))})
    raw, token = new_token(), new_token()
    with open_session(request) as db, db.begin():
        setup_available = db.execute(text("SELECT 1 FROM kamartha.managers LIMIT 1")).first() is None
        db.execute(text("""
            INSERT INTO kamartha.preauth_sessions(token_hash,csrf_token_hash,expires_at)
            VALUES (:token,:csrf,:expires)
        """), {"token": token_hash(raw), "csrf": token_hash(token),
               "expires": request.app.state.clock.now() + timedelta(minutes=15)})
    set_cookie(response, request, PREAUTH_COOKIE, raw)
    return envelope(request, {"csrf_token": token, "setup_available": setup_available})


@router.post("/setup", dependencies=[Depends(require_origin)], status_code=201)
def setup(payload: SetupInput, request: Request, response: Response):
    data, _ = authenticate(request, payload, setup=True)
    response.delete_cookie(PREAUTH_COOKIE, path="/")
    return envelope(request, data)


@router.post("/login", dependencies=[Depends(require_origin)])
def login(payload: LoginInput, request: Request, response: Response):
    data, raw = authenticate(request, payload)
    set_cookie(response, request, SESSION_COOKIE, raw)
    response.delete_cookie(PREAUTH_COOKIE, path="/")
    return envelope(request, data)


@router.get("/me")
def me(request: Request, manager=Depends(require_manager)):
    with open_session(request) as db:
        mode = db.execute(text("SELECT mode FROM kamartha.app_settings WHERE id=1")).scalar_one()
    return envelope(request, {"id": str(manager["manager_id"]), "username": manager["username"], "mode": mode})


@router.post("/logout")
def logout(request: Request, response: Response, manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        db.execute(text("UPDATE kamartha.sessions SET revoked_at=:now WHERE id=:id"),
                   {"now": request.app.state.clock.now(), "id": manager["session_id"]})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return envelope(request, {"logged_out": True})


@router.post("/change-password")
def change_password(payload: ChangePasswordInput, request: Request, response: Response,
                    manager=Depends(require_manager)):
    with open_session(request) as db, db.begin():
        row = db.execute(text("SELECT password_hash FROM kamartha.managers WHERE id=:id FOR UPDATE"),
                         {"id": manager["manager_id"]}).mappings().one()
        if not verify_password(payload.old_password, row["password_hash"]):
            raise AppError("PASSWORD_REJECTED", "Password lama salah.", 422)
        now = request.app.state.clock.now()
        db.execute(text("UPDATE kamartha.managers SET password_hash=:hash,password_changed_at=:now WHERE id=:id"),
                   {"hash": hash_password(payload.password), "now": now, "id": manager["manager_id"]})
        db.execute(text("UPDATE kamartha.sessions SET revoked_at=:now WHERE manager_id=:id AND revoked_at IS NULL"),
                   {"now": now, "id": manager["manager_id"]})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return envelope(request, {"login_required": True})
