from pydantic import BaseModel, ConfigDict, Field


class ResidentInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    identity_type: str = Field(min_length=1, max_length=50)
    identity_number: str = Field(min_length=1, max_length=100)
    whatsapp_number: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=10000)
