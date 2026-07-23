import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ApplicationSettingUpdateRequest(BaseModel):
    value: str = Field(min_length=1)


class ApplicationSettingResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: str
    description: str | None
    created_at: datetime
    updated_at: datetime
