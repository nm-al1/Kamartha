from collections.abc import Callable
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


class BusinessClock:
    def __init__(self, now: Callable[[], datetime] | None = None):
        self._now = now or (lambda: datetime.now(timezone.utc))

    def now(self) -> datetime:
        value = self._now()
        if value.tzinfo is None:
            raise ValueError("Clock harus memiliki zona waktu.")
        return value.astimezone(timezone.utc)

    def today(self) -> date:
        return self.now().astimezone(ZoneInfo("Asia/Makassar")).date()
