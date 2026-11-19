from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessagePreviewInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    context_type: Literal['INVOICE', 'PAYMENT', 'LEASE']
    context_id: UUID
