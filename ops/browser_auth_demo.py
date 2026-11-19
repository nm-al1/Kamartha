"""Mutating browser QA only for the isolated local demo verification database."""
import os
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def enable_semantics(page, timeout=90000):
    placeholder = page.locator('flt-semantics-placeholder')
    try:
        placeholder.wait_for(state='attached', timeout=timeout)
    except PlaywrightTimeoutError:
        return
    placeholder.evaluate('(element) => element.click()')


def type_into(locator, value):
    locator.click()
    locator.press('Control+A')
    locator.press('Backspace')
    locator.press_sequentially(value, delay=10)
    assert locator.input_value() == value


def main():
    database = os.environ['DEMO_QA_DATABASE']
    allowed_test = (
        database == 'kamartha_test'
        and os.environ.get('DEMO_QA_ALLOW_TEST_DATABASE') == 'yes'
    )
    if not allowed_test and (
        not database.startswith('kamartha_demo_') or not database.endswith('_verify')
    ):
        raise SystemExit('Browser QA requires an explicitly named demo verification database.')
    values = {}
    env_file = ROOT / 'backend' / '.env'
    for line in env_file.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            name, value = line.split('=', 1)
            values[name] = value
    code = values['LOCAL_SETUP_CODE']
    username = 'pengelola'
    password = 'DemoPass2026!'
    base_url = os.environ.get('DEMO_QA_BASE_URL', 'http://localhost:8080')
    artifacts = Path(os.environ['BROWSER_ARTIFACT_DIR'])
    artifacts.mkdir(parents=True, exist_ok=True)
    errors = []
    synchronized = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True,
            args=['--disable-features=LocalNetworkAccessChecks'])
        context = browser.new_context(viewport={'width': 390, 'height': 844})
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: synchronized.append(request.url)
                if '/billing/synchronize' in request.url else None)
        page.goto(f'{base_url}/#/login')
        enable_semantics(page)
        expect(page.get_by_role('button', name='Siapkan akun pertama', exact=True)).to_be_visible(timeout=60000)
        page.screenshot(path=str(artifacts / '01-login-390.png'))
        page.get_by_role('button', name='Siapkan akun pertama', exact=True).click()
        expect(page.get_by_role('button', name='Buat akun pengelola', exact=True)).to_be_visible()
        page.screenshot(path=str(artifacts / '02-registrasi-390.png'))
        fields = page.get_by_role('textbox')
        for index, value in enumerate([code, username, password, password]):
            type_into(fields.nth(index), value)
        page.wait_for_timeout(300)
        create = page.get_by_role('button', name='Buat akun pengelola', exact=True)
        expect(create).to_be_enabled(timeout=30000)
        page.screenshot(path=str(artifacts / '02-registrasi-terisi-390.png'))
        with page.expect_response('**/api/v1/auth/setup') as setup:
            page.get_by_role('button', name='Buat akun pengelola', exact=True).click()
        assert setup.value.status == 201, setup.value.status
        page.wait_for_url('**/#/login', timeout=30000)
        login_button = page.get_by_role('button', name='Masuk', exact=True)
        expect(login_button).to_be_enabled()
        fields = page.get_by_role('textbox')
        type_into(fields.nth(0), username)
        type_into(fields.nth(1), 'WrongPassword2026!')
        page.wait_for_timeout(300)
        with page.expect_response('**/api/v1/auth/login') as wrong:
            login_button.click()
        assert wrong.value.status == 401, wrong.value.status
        expect(page.get_by_text('Username atau password salah.', exact=False)).to_be_visible()
        type_into(fields.nth(1), password)
        page.wait_for_timeout(300)
        with page.expect_response('**/api/v1/auth/login') as login:
            login_button.click()
        assert login.value.status == 200, login.value.status
        expect(page.get_by_role('button', name='Lengkapi data awal', exact=True)).to_be_visible()
        expect(page.get_by_text('Kamar dihuni: 0', exact=False)).to_be_visible()
        assert not synchronized, 'Preparation dashboard must not synchronize invoices'
        for width, height in [(320, 568), (390, 844), (430, 932), (1280, 900)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.screenshot(path=str(artifacts / f'03-dashboard-{width}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.reload()
        enable_semantics(page)
        expect(page.get_by_role('button', name='Lengkapi data awal', exact=True)).to_be_visible(timeout=60000)
        page.get_by_role('button', name='Sesi pengelola', exact=True).click()
        with page.expect_response('**/api/v1/auth/logout') as logout:
            page.get_by_role('button', name='Keluar', exact=True).click()
        assert logout.value.status == 200, logout.value.status
        expect(page.get_by_role('button', name='Masuk', exact=True)).to_be_visible()
        page.goto(f'{base_url}/#/home')
        enable_semantics(page, timeout=5000)
        expect(page.get_by_role('button', name='Masuk', exact=True)).to_be_visible(timeout=60000)
        assert '/login' in page.url
        page.get_by_role('button', name='Lihat registrasi awal', exact=True).click()
        expect(page.get_by_text('Registrasi sudah ditutup atau belum tersedia. Silakan masuk.', exact=False)).to_be_visible()
        expect(page.get_by_role('button', name='Buat akun pengelola', exact=True)).to_be_disabled()
        page.screenshot(path=str(artifacts / '04-registrasi-ditutup.png'))
        assert not errors, errors
        print('PASS registration -> login -> preparation dashboard -> reload -> logout -> protected route')
        print('PASS wrong password rejected; first-account registration closes; preparation has no billing writes')
        print('PASS screenshots at 320/390/430/1280; no document overflow or uncaught JavaScript errors')
        browser.close()


if __name__ == '__main__':
    main()
