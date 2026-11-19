"""Read-only business smoke test; only login/logout changes session state.

Requires Playwright, Chrome, a release web server on 127.0.0.1:8082,
and the local API on localhost:8000 configured for http://localhost:8080.
The browser intercepts static assets only, preserving the configured Origin
without stopping any developer's server on port 8080.
"""
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    username = os.environ['BROWSER_TEST_USERNAME']
    password = os.environ['BROWSER_TEST_PASSWORD']
    artifacts = Path(os.environ['BROWSER_ARTIFACT_DIR'])
    artifacts.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True,
            args=['--disable-features=LocalNetworkAccessChecks'])
        context = browser.new_context(viewport={'width': 1280, 'height': 900})
        context.route('http://localhost:8080/**', lambda route: route.fulfill(
            response=context.request.get(route.request.url.replace('localhost:8080', '127.0.0.1:8082'))))
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        with page.expect_response('**/api/v1/auth/csrf', timeout=60000):
            page.goto('http://localhost:8080')
        page.locator('flt-semantics-placeholder').wait_for(state='attached', timeout=90000)
        page.locator('flt-semantics-placeholder').evaluate('(element) => element.click()')
        page.get_by_role('textbox').first.wait_for(timeout=60000)
        expect(page.get_by_role('button', name='Masuk', exact=True)).to_be_enabled()
        page.get_by_role('textbox').nth(0).click()
        page.keyboard.type(username, delay=35)
        page.get_by_role('textbox').nth(1).click()
        page.keyboard.type(password, delay=35)
        with page.expect_response('**/api/v1/auth/login', timeout=30000) as login:
            page.get_by_role('button', name='Masuk', exact=True).click()
        assert login.value.status == 200, login.value.status
        page.wait_for_function("document.body.innerText.includes('Persiapan pencatatan')", timeout=60000)
        expect(page.get_by_role('button', name='Simpan tanggal batas', exact=True)).to_be_enabled(timeout=30000)
        print('PASS login -> initialization')
        for width in [360, 390, 430, 1280]:
            page.set_viewport_size({'width': width, 'height': 900})
            page.screenshot(path=str(artifacts / f'initialization-{width}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        print('PASS initialization screenshots at 360/390/430/1280; no document overflow')
        page.set_viewport_size({'width': 1280, 'height': 900})
        for label, expected in [('Kamar', 'Tambah kamar'), ('Penghuni', 'Tambah penghuni')]:
            page.get_by_role('button', name=label, exact=True).click()
            page.get_by_role('button', name=expected, exact=True).wait_for(timeout=30000)
            page.get_by_role('button', name=expected, exact=True).click()
            page.get_by_role('button', name='Batal', exact=True).wait_for()
            page.keyboard.press('Escape')
            page.get_by_role('button', name='Batal', exact=True).wait_for(state='detached')
            print('PASS', label, '-> form opens; Escape cancels without saving')
        page.get_by_role('button', name='Sesi pengelola', exact=True).click()
        page.get_by_role('button', name='Keluar', exact=True).click()
        page.wait_for_function("location.hash.includes('/login')", timeout=30000)
        print('PASS logout -> login')
        assert not errors, errors
        print('PASS no uncaught JavaScript errors')
        browser.close()


if __name__ == '__main__':
    main()
