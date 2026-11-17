import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent


def log_event(
    db: Session,
    *,
    tenant_id: uuid.UUID | None,
    actor_user_id: uuid.UUID | None,
    entity_type: str,
    entity_id: str | None,
    action: str,
    summary: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditEvent(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            summary=summary or {},
        )
    )