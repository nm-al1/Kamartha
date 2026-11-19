from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class OccupancyInput(Input):
    resident_id: UUID
    entered_on: date
    state: Literal['STAYING', 'EXITED']
    exited_on: date | None = None
    exit_date_unknown: bool = False


class OpeningInvoice(Input):
    period_start: date
    due_on: date
    amount: int = Field(strict=True, gt=0, le=1_000_000_000_000)
    opening_paid: int = Field(strict=True, ge=0, le=1_000_000_000_000)


class OpeningRecord(Input):
    room_id: UUID
    package_id: UUID
    starts_on: date
    ends_on: date
    price: int = Field(strict=True, gt=0, le=1_000_000_000_000)
    responsible_resident_id: UUID
    occupancies: list[OccupancyInput] = Field(min_length=1, max_length=200)
    invoices: list[OpeningInvoice] = Field(max_length=12000)


class DraftInput(Input):
    client_record_key: UUID
    draft_data: dict[str, Any]


class DraftUpdate(Input):
    expected_version: int = Field(ge=1)
    draft_data: dict[str, Any]


class SettingsInput(Input):
    cutover_date: date
    expected_version: int = Field(ge=1)


class FinalizeInput(Input):
    expected_version: int = Field(ge=1)
    reconciliation_hash: str = Field(min_length=64, max_length=64)
    confirmed_matches: Literal[True]
    confirmed_old_periods_settled: Literal[True]


class ExcelImportInput(Input):
    tables: dict[str, list[list[StrictStr | StrictInt | None]]]
    preview_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    confirmed: Literal[True]
