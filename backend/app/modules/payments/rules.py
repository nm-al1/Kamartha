from dataclasses import dataclass
from datetime import date, timedelta
from typing import Mapping, Sequence
from uuid import UUID

from app.modules.billing.rules import validate_amount


@dataclass(frozen=True)
class InvoiceBalance:
    lease_id: UUID
    remaining: int
    period_start: date
    active: bool


def validate_payment(
    *, lease_id: UUID, total_amount: int, method: str,
    received_on: date, today: date, cutover_date: date,
    allocations: Sequence[tuple[UUID, int]],
    balances: Mapping[UUID, InvoiceBalance],
) -> None:
    """Validate using balances read by the service under the business lock."""
    validate_amount(total_amount)
    if method not in ("CASH", "TRANSFER", "QRIS"):
        raise ValueError("Metode pembayaran harus Cash, Transfer atau QRIS.")
    if not cutover_date <= received_on <= today:
        raise ValueError("Tanggal penerimaan harus sejak batas pencatatan dan tidak di masa depan.")
    if not allocations:
        raise ValueError("Pembayaran harus memiliki alokasi tagihan.")

    seen = set()
    allocated = 0
    for invoice_id, amount in allocations:
        validate_amount(amount)
        if invoice_id in seen:
            raise ValueError("Tagihan yang sama tidak boleh dialokasikan dua kali.")
        seen.add(invoice_id)
        invoice = balances.get(invoice_id)
        if invoice is None or invoice.lease_id != lease_id:
            raise ValueError("Semua tagihan harus berasal dari masa sewa yang sama.")
        if not invoice.active or amount > invoice.remaining:
            raise ValueError("Tagihan harus aktif dan alokasi tidak boleh melebihi sisa.")
        if invoice.period_start - received_on > timedelta(days=3):
            raise ValueError("Tanggal penerimaan mendahului ketersediaan tagihan H−3.")
        allocated += amount

    if allocated != total_amount:
        raise ValueError("Total alokasi harus sama dengan total penerimaan.")
