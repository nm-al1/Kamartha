"""Run separately: python -m app.modules.reminders.worker (one worker only)."""
import logging
import time
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.clock import BusinessClock
from app.core.config import Settings
from app.db.session import lock_business, make_engine
from app.modules.billing.service import synchronize
from app.modules.reminders.bridge import WhatsAppBridge
from app.modules.reminders.service import configuration, reconcile_receipts, run_reminders


def scheduled_date(now, hour_wita):
    local = now.astimezone(ZoneInfo('Asia/Makassar'))
    return local.date() if local.hour >= hour_wita else None


def prepare_invoices(factory, today):
    with factory() as db, db.begin():
        business = lock_business(db)
        if business['mode'] != 'ACTIVE':
            return False
        synchronize(db, today=today, cutover=business['cutover_date'])
        return True


def main():
    settings = Settings()
    configuration(settings)
    engine = make_engine(settings)
    if engine is None:
        raise RuntimeError('Database worker belum dikonfigurasi.')
    bridge, clock = WhatsAppBridge(settings), BusinessClock()
    factory = lambda: Session(engine)
    prepared_on = None
    try:
        while True:
            try:
                today = scheduled_date(clock.now(), settings.whatsapp_hour_wita)
                if today is not None and today != prepared_on and prepare_invoices(factory, today):
                    prepared_on = today
                reconcile_receipts(factory, bridge)
                if today is not None and prepared_on == today:
                    run_reminders(factory, settings, today, bridge)
            except Exception as exc:
                logging.getLogger('kamartha.reminders').warning('reminder_tick_failed type=%s', type(exc).__name__)
            time.sleep(60)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
