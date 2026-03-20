import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


# ─── Request body ─────────────────────────────────────────────────────────────

class ComplaintRequest(BaseModel):
    """What the caller sends to POST /complaint"""

    request_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Idempotency key — send the same UUID to avoid duplicates"
    )
    user_id: uuid.UUID = Field(
        description="Must exist in the users table"
    )
    channel: Literal["email", "whatsapp", "twitter", "phone", "web", "branch", "api"] = Field(
        description="Source channel of the complaint"
    )
    message: str = Field(
        min_length=5,
        max_length=5000,
        description="The complaint text"
    )

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message cannot be blank or whitespace only")
        return v.strip()


# ─── Response bodies ──────────────────────────────────────────────────────────

class ComplaintResponse(BaseModel):
    """What we return after successfully ingesting a complaint"""

    complaint_id: uuid.UUID
    request_id:   uuid.UUID
    status:       str
    message:      str        # human-readable confirmation
    created_at:   datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status:   str
    postgres: str
    redis:    str
