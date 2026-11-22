from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.collections.models import (
    DisputeStatus,
    PromiseStatus,
    TaskPriority,
    TaskStatus,
    TaskType,
)


class TaskCreate(BaseModel):
    invoice_id: UUID
    task_type: TaskType
    reason: str = Field(min_length=1, max_length=2000)
    due_at: datetime | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    assignee_id: UUID | None = None

    @field_validator("due_at")
    @classmethod
    def due_at_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("due_at must include a timezone")
        return value


class TaskPatch(BaseModel):
    status: TaskStatus | None = None
    assignee_id: UUID | None = None
    clear_assignee: bool = False
    due_at: datetime | None = None
    priority: TaskPriority | None = None

    @field_validator("due_at")
    @classmethod
    def due_at_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("due_at must include a timezone")
        return value


class PromiseCreate(BaseModel):
    amount: Decimal | None = None
    promised_date: date
    follow_up_date: date | None = None
    note: str | None = Field(default=None, max_length=4000)

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("amount must be greater than zero")
        return value


class PromisePatch(BaseModel):
    status: PromiseStatus


class DisputeCreate(BaseModel):
    challenged_amount: Decimal | None = None
    reason: str = Field(min_length=1, max_length=4000)

    @field_validator("challenged_amount")
    @classmethod
    def positive_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("challenged_amount must be greater than zero")
        return value


class DisputePatch(BaseModel):
    status: DisputeStatus
    resolution_note: str | None = Field(default=None, max_length=4000)
