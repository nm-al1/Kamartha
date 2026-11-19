from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class InvoiceCancel(Input):
    reason: str = Field(min_length=3, max_length=500)


class CashReportQuery(BaseModel):
    date_from: date
    date_to: date
