from pydantic import BaseModel, Field, field_validator

from app.core.security import normalize_email


class RegisterRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=255)
    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        normalized = normalize_email(v)
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Invalid email")
        return normalized


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return normalize_email(v)


class TenantBrief(BaseModel):
    id: str
    name: str


class UserBrief(BaseModel):
    id: str
    full_name: str
    email: str
    role: str


class RegisterResponse(BaseModel):
    message: str
    tenant: TenantBrief
    user: UserBrief


class MeResponse(BaseModel):
    user: UserBrief
    tenant: TenantBrief