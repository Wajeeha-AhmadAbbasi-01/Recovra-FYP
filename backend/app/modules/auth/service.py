import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, normalize_email, utcnow, verify_password
from app.modules.audit.service import log_event
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.tenants.models import Tenant
from app.modules.users.models import Session as UserSession
from app.modules.users.models import User, UserRole

settings = get_settings()


def register_business(db: Session, payload: RegisterRequest) -> tuple[Tenant, User]:
    email = normalize_email(str(payload.email))
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if settings.app_env == "production" and email.endswith(".test"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email for environment")

    tenant = Tenant(name=payload.business_name.strip())
    user = User(
        tenant=tenant,
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.owner,
        is_active=True,
        password_changed_at=utcnow(),
    )
    db.add(tenant)
    db.add(user)
    db.flush()
    log_event(
        db,
        tenant_id=tenant.id,
        actor_user_id=user.id,
        entity_type="tenant",
        entity_id=str(tenant.id),
        action="business_registered",
        summary={"business_name": tenant.name, "owner_email": email},
    )
    return tenant, user


def authenticate(db: Session, payload: LoginRequest) -> User:
    email = normalize_email(str(payload.email))
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")
    user.last_login_at = utcnow()
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        entity_type="user",
        entity_id=str(user.id),
        action="login",
        summary={},
    )
    return user


def create_session(db: Session, user: User) -> uuid.UUID:
    expires = datetime.now(timezone.utc) + timedelta(seconds=settings.session_max_age_seconds)
    session = UserSession(user_id=user.id, expires_at=expires)
    db.add(session)
    db.flush()
    return session.id


def delete_session(db: Session, session_id: uuid.UUID) -> None:
    session = db.get(UserSession, session_id)
    if session:
        db.delete(session)