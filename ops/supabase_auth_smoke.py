"""Create the first manager and smoke-test auth on the Supabase profile.

Run from the repository root:

    backend\\.venv\\Scripts\\python.exe ops\\supabase_auth_smoke.py

An interactive terminal prompts for the username and password. In a
non-interactive run the script generates a password and stores it in the
gitignored backend/.env.manager.local. Secrets are never printed.

Use --dry-run to check connectivity, the setup-code hash and setup availability
without writing an account.
"""
import argparse
import getpass
import os
import re
import secrets
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
sys.path.insert(0, str(BACKEND))
CREDENTIALS_FILE = BACKEND / '.env.manager.local'
USERNAME_PATTERN = re.compile(r'[A-Za-z0-9._]{4,32}')


def fail(message):
    print(f'Auth smoke dibatalkan: {message}', file=sys.stderr)
    raise SystemExit(1)


def read_env():
    from dotenv import dotenv_values

    return {
        key: (value or '').strip()
        for key, value in dotenv_values(BACKEND / '.env', interpolate=False).items()
    }


def resolve_credentials(args):
    username = args.username
    if not username and sys.stdin.isatty():
        try:
            username = input('Username pengelola [pengelola]: ').strip()
        except EOFError:
            username = ''
    username = username or 'pengelola'

    generated = args.generate_password or not sys.stdin.isatty()
    if not generated:
        try:
            password = getpass.getpass('Password pengelola: ')
            confirmation = getpass.getpass('Ulangi password: ')
        except EOFError:
            generated = True
        else:
            if password != confirmation:
                fail('konfirmasi password tidak cocok')
            return username, password, False
    return username, secrets.token_urlsafe(24), True


def write_credentials(username, password):
    content = (
        '# Dibuat oleh ops/supabase_auth_smoke.py. Jangan commit atau unggah.\n'
        f'# Tanggal: {date.today().isoformat()}\n'
        f'MANAGER_USERNAME={username}\n'
        f'MANAGER_PASSWORD={password}\n'
    )
    CREDENTIALS_FILE.write_text(content, encoding='utf-8')
    try:
        os.chmod(CREDENTIALS_FILE, 0o600)
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(
        description='Buat akun pengelola pertama di profil Supabase dan uji auth.')
    parser.add_argument('--username', help='Username pengelola; default pengelola.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Hanya periksa profil, hash kode setup, dan ketersediaan setup.')
    parser.add_argument('--generate-password', action='store_true',
                        help='Selalu buat password acak, walau terminal interaktif.')
    parser.add_argument('--force', action='store_true',
                        help='Timpa backend/.env.manager.local bila sudah ada.')
    args = parser.parse_args()

    from fastapi.testclient import TestClient

    from app.core.config import Settings
    from app.core.security import verify_password
    from app.main import create_app

    settings = Settings(_env_file=BACKEND / '.env', app_profile='supabase')
    if settings.app_profile != 'supabase':
        fail('APP_PROFILE bukan supabase.')
    if settings.environment != 'production':
        fail('SUPABASE_ENVIRONMENT harus production untuk profil Supabase.')
    if not settings.database_url:
        fail('SUPABASE_DATABASE_URL kosong.')
    if not settings.supabase_url or not settings.supabase_service_key:
        fail('SUPABASE_URL atau SUPABASE_SERVICE_KEY kosong.')

    values = read_env()
    setup_code = values.get('SUPABASE_SETUP_CODE', '')

    origin = settings.app_origin
    app = create_app(settings)
    checks = []
    with TestClient(app, base_url='https://testserver') as client:
        response = client.get('/api/v1/auth/csrf')
        if response.status_code != 200:
            fail(f'csrf HTTP {response.status_code}.')
        first = response.json()['data']
        setup_available = bool(first.get('setup_available'))
        checks.append(('csrf', 'lolos'))
        checks.append(('setup tersedia', 'ya' if setup_available else 'tidak'))

        if not setup_available:
            fail('akun pengelola sudah ada; tidak ada akun baru yang dibuat.')
        if not setup_code:
            fail('SUPABASE_SETUP_CODE kosong di backend/.env.')
        expected = settings.setup_code_hash
        if expected is None or not verify_password(setup_code, expected.get_secret_value()):
            fail('SUPABASE_SETUP_CODE tidak cocok dengan SUPABASE_SETUP_CODE_HASH.')
        checks.append(('kode setup', 'cocok dengan hash'))
        if args.dry_run:
            print('Preflight auth Supabase selesai:')
            for name, state in checks:
                print(f'  - {name}: {state}')
            print('Tidak ada akun yang dibuat (--dry-run).')
            return

        username, password, generated = resolve_credentials(args)
        if not USERNAME_PATTERN.fullmatch(username):
            fail('username harus 4-32 karakter: huruf, angka, titik, atau garis bawah.')
        if not 8 <= len(password) <= 128:
            fail('password harus 8-128 karakter.')
        if generated and CREDENTIALS_FILE.exists() and not args.force:
            fail(f'{CREDENTIALS_FILE.name} sudah ada; hapus atau pakai --force.')

        headers = {'Origin': origin, 'X-CSRF-Token': first['csrf_token']}
        created = client.post('/api/v1/auth/setup', headers=headers, json={
            'username': username,
            'password': password,
            'password_confirmation': password,
            'setup_code': setup_code,
        })
        if created.status_code != 201:
            code = created.json().get('error', {}).get('code', 'UNKNOWN')
            fail(f'setup HTTP {created.status_code} ({code}).')
        checks.append(('setup akun', 'lolos (HTTP 201)'))
        manager = created.json()['data']

        if generated:
            write_credentials(username, password)
            checks.append(('password', f'disimpan di {CREDENTIALS_FILE.name}'))

        response = client.get('/api/v1/auth/csrf')
        if response.status_code != 200:
            fail(f'csrf login HTTP {response.status_code}.')
        second = response.json()['data']
        if second.get('setup_available'):
            fail('setup masih tersedia setelah akun dibuat.')

        logged_in = client.post('/api/v1/auth/login', headers={
            'Origin': origin, 'X-CSRF-Token': second['csrf_token'],
        }, json={'username': username, 'password': password})
        if logged_in.status_code != 200:
            code = logged_in.json().get('error', {}).get('code', 'UNKNOWN')
            fail(f'login HTTP {logged_in.status_code} ({code}).')
        checks.append(('login', 'lolos'))
        session_csrf = logged_in.json()['data']['csrf_token']

        me = client.get('/api/v1/auth/me')
        if me.status_code != 200:
            fail(f'/auth/me HTTP {me.status_code}.')
        profile = me.json()['data']
        if profile.get('username') != username:
            fail('/auth/me mengembalikan username yang berbeda.')
        checks.append(('/auth/me', f"lolos (mode {profile.get('mode')})"))

        logged_out = client.post('/api/v1/auth/logout', headers={
            'Origin': origin, 'X-CSRF-Token': session_csrf,
        })
        if logged_out.status_code != 200:
            fail(f'logout HTTP {logged_out.status_code}.')
        checks.append(('logout', 'lolos'))

        after = client.get('/api/v1/auth/me')
        if after.status_code != 401:
            fail(f'/auth/me setelah logout HTTP {after.status_code}, bukan 401.')
        checks.append(('sesi setelah logout', 'ditolak (HTTP 401)'))

    print('Akun pengelola Supabase:')
    print(f"  - username: {manager.get('username', username)}")
    if generated:
        print(f'  - password: tersimpan di {CREDENTIALS_FILE} (tidak dicetak)')
    print('Auth smoke:')
    for name, state in checks:
        print(f'  - {name}: {state}')
    print('Tidak ada kredensial yang dicetak. Akun tersimpan di database Supabase.')


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        print(f'Auth smoke gagal ({type(error).__name__}): {error}', file=sys.stderr)
        raise SystemExit(1)
