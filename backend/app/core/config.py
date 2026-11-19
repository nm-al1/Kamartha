from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRET_FIELDS = {'database_url', 'setup_code_hash', 'ip_hash_secret'}


def valid_origin(value: str) -> bool:
    parsed = urlsplit(value)
    return (parsed.scheme in ('http', 'https') and bool(parsed.hostname)
            and not parsed.username and not parsed.password
            and parsed.path in ('', '/') and not parsed.query and not parsed.fragment)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # One switch selects which tag block below becomes active.
    app_profile: Literal['local', 'supabase'] = 'local'

    environment: Literal['development', 'test', 'production'] = 'development'
    app_origin: str = 'http://localhost:8080'
    database_url: SecretStr | None = None
    setup_code_hash: SecretStr | None = None
    ip_hash_secret: SecretStr | None = None
    supabase_url: str | None = None
    supabase_service_key: SecretStr | None = None
    storage_bucket: str = 'kamartha-files'
    whatsapp_enabled: bool = False
    whatsapp_bridge_url: str = 'http://127.0.0.1:3001'
    whatsapp_bridge_token: SecretStr | None = None
    whatsapp_allowed_numbers: str = ''
    whatsapp_demo_invoice_ids: str = ''
    whatsapp_allow_demo_date: bool = False
    whatsapp_hour_wita: int = Field(default=9, ge=0, le=23)

    @field_validator('whatsapp_bridge_url')
    @classmethod
    def bridge_origin(cls, value):
        if not valid_origin(value):
            raise ValueError('WHATSAPP_BRIDGE_URL harus satu origin yang sah.')
        parsed = urlsplit(value)
        if parsed.scheme != 'https' and parsed.hostname not in ('127.0.0.1', 'localhost', 'whatsapp'):
            raise ValueError('Bridge HTTP hanya boleh di loopback atau service internal whatsapp.')
        return value.rstrip('/')

    # TAG: PROFIL LOCAL
    local_environment: Literal['development', 'test', 'production'] | None = None
    local_app_origin: str | None = None
    local_database_url: SecretStr | None = None
    local_setup_code_hash: SecretStr | None = None
    local_ip_hash_secret: SecretStr | None = None

    # TAG: PROFIL SUPABASE
    supabase_environment: Literal['development', 'test', 'production'] | None = None
    supabase_app_origin: str | None = None
    supabase_database_url: SecretStr | None = None
    supabase_setup_code_hash: SecretStr | None = None
    supabase_ip_hash_secret: SecretStr | None = None

    @field_validator('app_origin')
    @classmethod
    def validate_origin(cls, value: str) -> str:
        if not valid_origin(value):
            raise ValueError('APP_ORIGIN harus satu origin HTTP/HTTPS yang sah.')
        return value.rstrip('/')

    @model_validator(mode='after')
    def resolve_profile(self):
        if self.app_profile == 'supabase':
            candidates = {
                'environment': self.supabase_environment,
                'app_origin': self.supabase_app_origin,
                'database_url': self.supabase_database_url,
                'setup_code_hash': self.supabase_setup_code_hash,
                'ip_hash_secret': self.supabase_ip_hash_secret,
            }
        else:
            candidates = {
                'environment': self.local_environment,
                'app_origin': self.local_app_origin,
                'database_url': self.local_database_url,
                'setup_code_hash': self.local_setup_code_hash,
                'ip_hash_secret': self.local_ip_hash_secret,
            }
        for field, value in candidates.items():
            if value is None or value == '':
                continue
            if field == 'app_origin':
                if not valid_origin(value):
                    raise ValueError('Origin profil harus satu origin HTTP/HTTPS yang sah.')
                value = value.rstrip('/')
            elif field in SECRET_FIELDS and isinstance(value, str):
                value = SecretStr(value)
            setattr(self, field, value)
        return self
