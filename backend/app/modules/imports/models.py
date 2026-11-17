import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UploadStatus(str, enum.Enum):
    received = "received"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ValidationStatus(str, enum.Enum):
    ACCEPTED_LOCAL_CHECK = "ACCEPTED_LOCAL_CHECK"
    REJECTED_LOCAL_CHECK = "REJECTED_LOCAL_CHECK"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED"
    DUPLICATE = "DUPLICATE"
    PROCESSING_ERROR = "PROCESSING_ERROR"


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    uploader_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[UploadStatus] = mapped_column(Enum(UploadStatus, name="upload_status"), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    validation_attempts: Mapped[list["ValidationAttempt"]] = relationship(back_populates="upload")


class ValidationAttempt(Base):
    __tablename__ = "validation_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    upload_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("uploads.id"), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(64), nullable=False, default="registered_b2b_goods_v1")
    extracted_candidate: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    local_status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus, name="validation_status"), nullable=False
    )
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    upload: Mapped[Upload] = relationship(back_populates="validation_attempts")