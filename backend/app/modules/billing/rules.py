from calendar import monthrange
from datetime import date, timedelta

MAX_AMOUNT = 1_000_000_000_000


def validate_amount(amount: int, *, allow_zero: bool = False) -> int:
    if type(amount) is not int:
        raise ValueError("Nominal harus berupa rupiah bulat.")
    minimum = 0 if allow_zero else 1
    if not minimum <= amount <= MAX_AMOUNT:
        raise ValueError("Nominal di luar batas yang diizinkan.")
    return amount


def period_boundary(anchor: date, period_months: int, index: int) -> date:
    if type(period_months) is not int or period_months not in (1, 6, 12):
        raise ValueError("Periode paket harus 1, 6 atau 12 bulan.")
    if type(index) is not int or index < 0:
        raise ValueError("Indeks periode harus integer tidak negatif.")
    absolute_month = anchor.year * 12 + anchor.month - 1 + period_months * index
    year, month_index = divmod(absolute_month, 12)
    if not 1 <= year <= 9999:
        raise ValueError("Tanggal periode di luar rentang kalender.")
    month = month_index + 1
    return date(year, month, min(anchor.day, monthrange(year, month)[1]))


def period_is_available(period_start: date, effective_end: date, today: date) -> bool:
    return period_start < effective_end and period_start - today <= timedelta(days=3)


def invoice_remaining(amount: int, opening_paid: int, operational_paid: int) -> int:
    validate_amount(amount)
    validate_amount(opening_paid, allow_zero=True)
    validate_amount(operational_paid, allow_zero=True)
    remaining = amount - opening_paid - operational_paid
    if remaining < 0:
        raise ValueError("Total pembayaran melebihi nominal tagihan.")
    return remaining


def invoice_status(*, cancelled: bool, amount: int, opening_paid: int,
                   operational_paid: int, due_on: date, today: date) -> str:
    remaining = invoice_remaining(amount, opening_paid, operational_paid)
    if cancelled:
        return "CANCELLED"
    if remaining == 0:
        return "PAID"
    if today > due_on:
        return "OVERDUE"
    if remaining < amount:
        return "PARTIALLY_PAID"
    return "UNPAID"
