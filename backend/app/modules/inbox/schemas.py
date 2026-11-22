from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MockMessageIn(BaseModel):
    uidvalidity: int = Field(ge=1)
    uid: int = Field(ge=1)
    folder: str = Field(default="INBOX", min_length=1, max_length=128)
    rfc_message_id: str | None = Field(default=None, max_length=512)
    sender: str = Field(min_length=3, max_length=320)
    recipient: str = Field(min_length=3, max_length=320)
    subject: str = Field(default="", max_length=998)
    body: str = Field(default="", max_length=100_000)
    content_type: str = Field(default="text/plain", max_length=128)
    received_at: datetime | None = None
    invoice_references: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("received_at")
    @classmethod
    def received_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("received_at must include a timezone")
        return value


class MockDeliverRequest(BaseModel):
    messages: list[MockMessageIn] = Field(min_length=1, max_length=20)


class LinkDecision(BaseModel):
    invoice_id: UUID
    action: str = Field(pattern="^(confirm|reject)$")
