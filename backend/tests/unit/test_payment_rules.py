import unittest
from datetime import date
from uuid import uuid4

from app.modules.payments.rules import InvoiceBalance, validate_payment


class PaymentRulesTests(unittest.TestCase):
    def setUp(self):
        self.lease_id = uuid4()
        self.first, self.second = uuid4(), uuid4()
        self.balances = {
            self.first: InvoiceBalance(self.lease_id, 500000, date(2026, 10, 1), True),
            self.second: InvoiceBalance(self.lease_id, 1000000, date(2026, 11, 1), True),
        }

    def validate(self, **changes):
        arguments = dict(
            lease_id=self.lease_id, total_amount=1500000, method="TRANSFER",
            received_on=date(2026, 10, 30), today=date(2026, 11, 2),
            cutover_date=date(2026, 10, 1),
            allocations=[(self.first, 500000), (self.second, 1000000)],
            balances=self.balances,
        )
        arguments.update(changes)
        validate_payment(**arguments)

    def test_one_receipt_can_pay_two_periods(self):
        self.validate()

    def test_supported_methods(self):
        for method in ("CASH", "TRANSFER", "QRIS"):
            with self.subTest(method=method):
                self.validate(method=method)

    def test_rejects_invalid_method_total_and_allocation(self):
        cases = [
            {"method": "cash"}, {"method": ""}, {"total_amount": True},
            {"total_amount": 1499999}, {"allocations": []},
            {"allocations": [(self.first, 0)]},
            {"allocations": [(self.first, -1)]},
            {"allocations": [(self.first, 500001)], "total_amount": 500001},
            {"allocations": [(self.first, 250000), (self.first, 250000)], "total_amount": 500000},
            {"allocations": [(uuid4(), 1500000)]},
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.validate(**changes)

    def test_rejects_cross_lease_cancelled_and_paid_invoice(self):
        for balance in (
            InvoiceBalance(uuid4(), 500000, date(2026, 10, 1), True),
            InvoiceBalance(self.lease_id, 500000, date(2026, 10, 1), False),
            InvoiceBalance(self.lease_id, 0, date(2026, 10, 1), True),
        ):
            with self.subTest(balance=balance), self.assertRaises(ValueError):
                self.validate(balances={**self.balances, self.first: balance})

    def test_received_date_bounds_and_h_minus_three(self):
        for received_on in (date(2026, 9, 30), date(2026, 11, 3), date(2026, 10, 28)):
            with self.subTest(received_on=received_on), self.assertRaises(ValueError):
                self.validate(received_on=received_on)
        self.validate(received_on=date(2026, 10, 29))
        self.validate(received_on=date(2026, 11, 2))

    def test_old_invoice_can_be_paid_since_cutover(self):
        self.validate(
            total_amount=500000, received_on=date(2026, 10, 1),
            allocations=[(self.first, 500000)],
            balances={self.first: InvoiceBalance(
                self.lease_id, 500000, date(2026, 9, 10), active=True,
            )},
        )


if __name__ == "__main__":
    unittest.main()
