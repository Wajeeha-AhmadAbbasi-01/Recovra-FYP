import uuid
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: dict[str, Any] | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


def success(data: T) -> ApiResponse[T]:
    return ApiResponse(data=data, error=None)


def error(code: str, message: str, details: dict[str, Any] | None = None) -> ApiResponse[None]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return ApiResponse(data=None, error=payload)