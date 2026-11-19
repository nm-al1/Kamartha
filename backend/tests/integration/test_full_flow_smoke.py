import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration


def test_preparation_to_payment_and_expense_flow(migrated_connection, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3] / 'ops'))
    flow = importlib.import_module('full_flow_smoke')
    for name in ('auth.router', 'auth.service', 'rooms.router', 'residents.router',
                 'initialization.router', 'leases.router', 'billing.router',
                 'payments.router', 'expenses.router', 'dashboard.router',
                 'reports.router', 'messaging.router', 'attachments.router'):
        module = importlib.import_module('app.modules.' + name)
        monkeypatch.setattr(module, 'open_session', lambda request: Session(
            migrated_connection, join_transaction_mode='create_savepoint'))
    from app.main import create_app
    settings, clock, setup_code, password = flow.test_configuration()
    app = create_app(settings, clock=clock)
    with TestClient(app) as client:
        result = flow.exercise(client, settings.app_origin, setup_code, password, clock.today())
    assert result['mode'] == 'ACTIVE'
    assert result['income'] == 700000
    assert result['expense'] == 100000
    assert result['difference'] == 600000
    assert result['receivables'] == 300000
    assert result['attachments'] == 2
