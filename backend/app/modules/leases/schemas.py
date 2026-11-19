from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class LeaseCreate(Input):
    room_id: UUID
    package_id: UUID
    starts_on: date
    periods: int = Field(strict=True, ge=1, le=120)
    price: int = Field(strict=True, gt=0, le=1_000_000_000_000)
    resident_ids: list[UUID] = Field(min_length=1, max_length=2)
    responsible_resident_id: UUID


class LeaseExtend(Input):
    periods: int = Field(strict=True, ge=1, le=120)
    expected_version: int = Field(strict=True, ge=1)


class OccupancyExit(Input):
    exited_on: date
    successor_resident_id: UUID | None = None
    reason: str = Field(min_length=3, max_length=500)


class ResponsibleChange(Input):
    occupancy_id: UUID
    reason: str = Field(min_length=3, max_length=500)


class Replacement(Input):
    resident_id: UUID
    entered_on: date
    predecessor_occupancy_id: UUID
    reason: str = Field(min_length=3, max_length=500)


class LeaseContinue(Input):
    package_id: UUID
    starts_on: date
    periods: int = Field(strict=True, ge=1, le=120)
    price: int = Field(strict=True, gt=0, le=1_000_000_000_000)
    resident_ids: list[UUID] = Field(min_length=1, max_length=2)
    responsible_resident_id: UUID
    reason: str = Field(min_length=3, max_length=500)
