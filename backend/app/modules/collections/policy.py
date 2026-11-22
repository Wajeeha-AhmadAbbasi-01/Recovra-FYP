import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.collections.models import ReminderPolicy, RiskLevel

DEFAULT_POLICY_VERSION = "m2-phase2-v1"


def ensure_reminder_policy(db: Session, tenant_id: uuid.UUID) -> ReminderPolicy:
    row = db.scalar(select(ReminderPolicy).where(ReminderPolicy.tenant_id == tenant_id))
    if row:
        return row
    row = ReminderPolicy(
        tenant_id=tenant_id,
        enabled=True,
        grace_days=0,
        timezone_name="Asia/Karachi",
        risk_level=RiskLevel.STANDARD,
        policy_version=DEFAULT_POLICY_VERSION,
    )
    db.add(row)
    db.flush()
    return row