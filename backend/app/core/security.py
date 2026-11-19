import hashlib
import hmac
import secrets

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    if not 8 <= len(password) <= 128:
        raise ValueError("Password harus terdiri dari 8–128 karakter.")
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if len(password) > 128:
        return False
    try:
        return _password_hash.verify(password, hashed)
    except (UnknownHashError, ValueError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def subject_hash(subject: str, secret: str) -> str:
    return hmac.new(secret.encode(), subject.encode(), hashlib.sha256).hexdigest()


def csrf_token(session_token: str, secret: str) -> str:
    payload = b"kamartha-csrf:" + session_token.encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
