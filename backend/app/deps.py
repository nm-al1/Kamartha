from fastapi import Request

from app.core.errors import AppError


def get_clock(request: Request):
    return request.app.state.clock


def get_storage(request: Request):
    return request.app.state.storage


def check_mode(locked_settings, expected: str):
    """Call after lock_business inside the same write transaction."""
    if locked_settings['mode'] != expected:
        raise AppError('MODE_REJECTED', 'Tindakan tidak tersedia pada mode aplikasi saat ini.', 409)
