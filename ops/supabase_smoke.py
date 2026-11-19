"""Verify the Supabase profile end to end without exposing secrets.

Checks app startup, PostgreSQL access through the runtime role, and a private
Storage round trip using a synthetic object that is deleted afterwards.
"""
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / 'ops'))


def main():
    import httpx
    from fastapi.testclient import TestClient

    from app.core.config import Settings
    from app.core.errors import AppError
    from app.main import create_app
    from app.modules.attachments.supabase_storage import SupabaseStorage
    import supabase_setup as setup

    values = setup.load_values()
    setup.validate(values)
    settings = Settings(_env_file=BACKEND / '.env', app_profile='supabase')
    if settings.environment != 'production':
        raise SystemExit('SUPABASE_ENVIRONMENT harus production untuk profil Supabase.')
    base = (settings.supabase_url or '').rstrip('/')
    bucket = settings.storage_bucket
    app = create_app(settings)
    if not isinstance(app.state.storage, SupabaseStorage):
        raise SystemExit('Storage bukan SupabaseStorage; periksa kredensial Storage.')

    checks = []
    key = f"smoke/{uuid4()}.png"
    payload = b'\x89PNG\r\n\x1a\nkamartha-smoke'
    with TestClient(app, base_url='https://testserver') as client:
        health = client.get('/api/v1/health')
        if health.status_code != 200:
            raise SystemExit(f"Health gagal (HTTP {health.status_code}).")
        checks.append(('health', 'lolos'))

        with app.state.engine.connect() as db:
            from sqlalchemy import text
            db.scalar(text('SELECT 1 FROM kamartha.app_settings WHERE id = 1'))
        checks.append(('database runtime', 'lolos'))

        app.state.storage.put(key, payload, 'image/png')
        stored = app.state.storage.get(key)
        if stored != payload:
            raise SystemExit('Isi objek Storage tidak sama dengan sumber.')
        checks.append(('storage tulis/baca', 'lolos'))

        anonymous = httpx.get(
            f"{base}/storage/v1/object/public/{bucket}/{key}", timeout=20)
        if anonymous.status_code == 200:
            raise SystemExit('Bucket dapat dibaca tanpa autentikasi; hentikan dan periksa.')
        checks.append(('bucket privat', 'lolos'))

        app.state.storage.delete(key)
        try:
            app.state.storage.get(key)
        except AppError as error:
            if error.status != 404:
                raise
        else:
            raise SystemExit('Objek uji masih ada setelah penghapusan.')
        checks.append(('storage hapus', 'lolos'))

    print('Smoke Supabase selesai:')
    for name, state in checks:
        print(f'  - {name}: {state}')
    print('Objek uji sudah dihapus. Tidak ada data bisnis yang diubah.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Smoke gagal ({type(error).__name__}): {error}', file=sys.stderr)
        raise SystemExit(1)
