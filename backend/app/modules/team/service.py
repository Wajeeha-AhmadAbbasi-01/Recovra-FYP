import uuid
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_token, hash_password, hash_token, normalize_email, utcnow
from app.modules.audit.service import log_event
from app.modules.team.email import send_invitation_email
from app.modules.team.models import InvitationStatus, TeamInvitation
from app.modules.team.schemas import AcceptInvitationRequest, CreateInvitationRequest
from app.modules.users.models import User, UserRole

settings = get_settings()


def create_invitation(db: Session, owner: User, payload: CreateInvitationRequest) -> tuple[TeamInvitation, str]:
    if payload.role != UserRole.finance_manager.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only finance_manager can be invited")

    email = normalize_email(str(payload.email))
    if not settings.is_test_recipient_allowed(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid recipient for environment")

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to send invitation")

    pending = db.scalars(
        select(TeamInvitation).where(
            TeamInvitation.tenant_id == owner.tenant_id,
            TeamInvitation.invited_email == email,
            TeamInvitation.status == InvitationStatus.pending,
        )
    ).all()
    for inv in pending:
        inv.status = InvitationStatus.revoked
        inv.revoked_at = utcnow()

    raw_token = generate_token()
    invitation = TeamInvitation(
        tenant_id=owner.tenant_id,
        invited_email=email,
        role=UserRole.finance_manager,
        token_hash=hash_token(raw_token),
        expires_at=utcnow() + timedelta(hours=settings.invitation_expiry_hours),
        created_by_user_id=owner.id,
        status=InvitationStatus.pending,
    )
    db.add(invitation)
    db.flush()

    invite_url = f"{settings.app_base_url}/invite/{raw_token}"
    try:
        send_invitation_email(settings, to_email=email, invite_url=invite_url)
    except Exception as exc:  # noqa: BLE001
        invitation.status = InvitationStatus.failed_delivery
        log_event(
            db,
            tenant_id=owner.tenant_id,
            actor_user_id=owner.id,
            entity_type="team_invitation",
            entity_id=str(invitation.id),
            action="invitation_delivery_failed",
            summary={"reason": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invitation could not be delivered",
        ) from exc

    log_event(
        db,
        tenant_id=owner.tenant_id,
        actor_user_id=owner.id,
        entity_type="team_invitation",
        entity_id=str(invitation.id),
        action="invitation_created",
        summary={"invited_email": email},
    )
    return invitation, raw_token


def accept_invitation(db: Session, payload: AcceptInvitationRequest) -> User:
    token_hash = hash_token(payload.token)
    invitation = db.scalar(select(TeamInvitation).where(TeamInvitation.token_hash == token_hash))
    if not invitation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation")

    if invitation.status != InvitationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation not available")
    if invitation.expires_at < utcnow():
        invitation.status = InvitationStatus.expired
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired")
    if invitation.revoked_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation revoked")

    email = invitation.invited_email
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to complete invitation")

    user = User(
        tenant_id=invitation.tenant_id,
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.finance_manager,
        is_active=True,
        invited_at=invitation.created_at,
        invitation_accepted_at=utcnow(),
        password_changed_at=utcnow(),
    )
    db.add(user)
    invitation.status = InvitationStatus.accepted
    invitation.accepted_at = utcnow()
    db.flush()

    log_event(
        db,
        tenant_id=invitation.tenant_id,
        actor_user_id=user.id,
        entity_type="team_invitation",
        entity_id=str(invitation.id),
        action="invitation_accepted",
        summary={},
    )
    return user


def revoke_invitation(db: Session, owner: User, invitation_id: uuid.UUID) -> TeamInvitation:
    invitation = db.get(TeamInvitation, invitation_id)
    if not invitation or invitation.tenant_id != owner.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invitation.status != InvitationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation not pending")
    invitation.status = InvitationStatus.revoked
    invitation.revoked_at = utcnow()
    log_event(
        db,
        tenant_id=owner.tenant_id,
        actor_user_id=owner.id,
        entity_type="team_invitation",
        entity_id=str(invitation.id),
        action="invitation_revoked",
        summary={},
    )
    return invitation