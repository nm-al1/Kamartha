from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RoomInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    number: str = Field(min_length=1, max_length=30)
    room_type: Literal['Standar']
    supported_occupants: Literal[1, 2]
    reference_price: int = Field(strict=True, gt=0, le=1_000_000_000_000)
    is_available_for_new_lease: bool = True
