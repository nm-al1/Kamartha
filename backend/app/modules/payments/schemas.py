from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class AllocationInput(Input):
    invoice_id: UUID
    amount: int = Field(strict=True, gt=0, le=1_000_000_000_000)


class PaymentCreate(Input):
    lease_id: UUID
    received_on: date
    total_amount: int = Field(strict=True, gt=0, le=1_000_000_000_000)
    method: str = Field(pattern=r'^(CASH|TRANSFER|QRIS)$')
    reference: str | None = Field(default=None, max_length=200)
    allocations: list[AllocationInput] = Field(min_length=1, max_length=50)
    attachment_id: UUID | None = None


class PaymentCancel(Input):
    reason: str = Field(min_length=3, max_length=500)
