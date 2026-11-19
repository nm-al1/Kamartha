import unittest
from datetime import date

from app.modules.billing.rules import (
    MAX_AMOUNT,
    invoice_remaining,
    invoice_status,
    period_boundary,
    period_is_available,
    validate_amount,
)


class CalendarTests(unittest.TestCase):
    def test_month_end_returns_to_original_anchor_day(self):
        for year, last_day in ((2027, 28), (2028, 29)):
            with self.subTest(year=year):
                anchor = date(year, 1, 31)
                self.assertEqual(period_boundary(anchor, 1, 1), date(year, 2, last_day))
                self.assertEqual(period_boundary(anchor, 1, 2), date(year, 3, 31))

    def test_six_and_twelve_month_packages(self):
        anchor = date(2026, 10, 10)
        self.assertEqual(period_boundary(anchor, 6, 1), date(2027, 4, 10))
        self.assertEqual(period_boundary(anchor, 12, 1), date(2027, 10, 10))

    def test_h_minus_three_and_exclusive_contract_end(self):
        start = date(2027, 4, 10)
        end = date(2027, 10, 10)
        self.assertFalse(period_is_available(start, end, date(2027, 4, 6)))
        self.assertTrue(period_is_available(start, end, date(2027, 4, 7)))
        self.assertTrue(period_is_available(start, end, date(2027, 5, 1)))
        self.assertFalse(period_is_available(start, start, date(2027, 4, 7)))

    def test_invalid_calendar_inputs(self):
        for months, index in ((2, 0), (True, 0), (1, -1), (1, True), (1, 0.5), (12, 10000)):
            with self.subTest(months=months, index=index), self.assertRaises(ValueError):
                period_boundary(date(2027, 1, 31), months, index)


class BalanceTests(unittest.TestCase):
    def test_opening_balance_is_separate(self):
        self.assertEqual(invoice_remaining(900000, 400000, 0), 500000)
        self.assertEqual(invoice_remaining(900000, 400000, 200000), 300000)

    def test_amount_boundaries(self):
        self.assertEqual(validate_amount(MAX_AMOUNT), MAX_AMOUNT)
        self.assertEqual(validate_amount(0, allow_zero=True), 0)
        for value in (0, -1, True, 1.5, "100", MAX_AMOUNT + 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_amount(value)

    def test_overpayment_is_not_hidden(self):
        with self.assertRaises(ValueError):
            invoice_remaining(900000, 400000, 500001)

    def test_status_priority_and_due_date_boundary(self):
        cases = (
            (True, 900000, 12, "CANCELLED"),
            (False, 900000, 12, "PAID"),
            (False, 400000, 12, "OVERDUE"),
            (False, 400000, 10, "PARTIALLY_PAID"),
            (False, 0, 10, "UNPAID"),
        )
        for cancelled, paid, day, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(invoice_status(
                    cancelled=cancelled, amount=900000, opening_paid=0,
                    operational_paid=paid, due_on=date(2026, 10, 10),
                    today=date(2026, 10, day),
                ), expected)


if __name__ == "__main__":
    unittest.main()
