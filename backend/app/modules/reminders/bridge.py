import httpx

from app.core.errors import AppError


class WhatsAppBridge:
    def __init__(self, settings):
        token = settings.whatsapp_bridge_token
        if token is None or len(token.get_secret_value()) < 32:
            raise AppError('WA_NOT_CONFIGURED', 'Token bridge WA minimal 32 karakter belum dikonfigurasi.', 503)
        self.url = settings.whatsapp_bridge_url
        self.headers = {'Authorization': 'Bearer ' + token.get_secret_value()}

    def request(self, method, path, payload=None):
        try:
            response = httpx.request(method, self.url + path, headers=self.headers,
                                     json=payload, timeout=20 if method == 'POST' else 3,
                                     follow_redirects=False, trust_env=False)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError('Invalid bridge response')
            return data
        except (httpx.HTTPError, ValueError) as exc:
            raise AppError('WA_BRIDGE_UNAVAILABLE', 'Bridge WhatsApp tidak dapat dihubungi. Periksa proses dan sesi QR.', 503) from exc

    def status(self):
        return self.request('GET', '/status')

    def send(self, key, number, message):
        return self.request('POST', '/send', {'key': str(key), 'number': number, 'message': message})

    def receipt(self, key):
        return self.request('GET', '/messages/' + str(key))
