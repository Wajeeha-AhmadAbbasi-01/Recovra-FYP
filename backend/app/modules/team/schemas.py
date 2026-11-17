from pydantic import BaseModel, Field, field_validator

from app.core.security import normalize_email


class CreateInvitationRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return normalize_email(v)
    role: str = Field(default="finance_manager")


class AcceptInvitationRequest(BaseModel):
    token: str
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class InvitationBrief(BaseModel):
    id: str
    invited_email: str
    role: str
    status: str
    expires_at: str
    created_at: str


class MemberBrief(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    is_active: bool