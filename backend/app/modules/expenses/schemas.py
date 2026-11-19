from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class ExpenseCreate(Input):
    expense_on: date
    amount: int = Field(strict=True, gt=0, le=1_000_000_000_000)
    category: str = Field(pattern=r'^(ELECTRICITY|WATER|INTERNET|REPAIR|SALARY|OTHER)$')
    description: str = Field(min_length=1, max_length=1000)
    attachment_id: UUID | None = None


class ExpenseUpdate(ExpenseCreate):
    expected_version: int = Field(strict=True, ge=1)
    reason: str = Field(min_length=3, max_length=500)


class ExpenseCancel(Input):
    expected_version: int = Field(strict=True, ge=1)
    reason: str = Field(min_length=3, max_length=500)
