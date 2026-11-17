from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.common.permissions import require_owner
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.team import service as team_service
from app.modules.team.schemas import (
    AcceptInvitationRequest,
    CreateInvitationRequest,
    InvitationBrief,
    MemberBrief,
)
from app.modules.team.models import TeamInvitation
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/team", tags=["team"])


@router.post("/invitations", response_model=ApiResponse[InvitationBrief], status_code=status.HTTP_201_CREATED)
def create_invitation(
    payload: CreateInvitationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[InvitationBrief]:
    require_owner(user)
    invitation, _ = team_service.create_invitation(db, user, payload)
    db.commit()
    return success(
        InvitationBrief(
            id=str(invitation.id),
            invited_email=invitation.invited_email,
            role=invitation.role.value,
            status=invitation.status.value,
            expires_at=invitation.expires_at.isoformat(),
            created_at=invitation.created_at.isoformat(),
        )
    )


@router.get("/invitations", response_model=ApiResponse[list[InvitationBrief]])
def list_invitations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[list[InvitationBrief]]:
    require_owner(user)
    rows = db.scalars(
        select(TeamInvitation).where(TeamInvitation.tenant_id == user.tenant_id).order_by(TeamInvitation.created_at.desc())
    ).all()
    return success(
        [
            InvitationBrief(
                id=str(r.id),
                invited_email=r.invited_email,
                role=r.role.value,
                status=r.status.value,
                expires_at=r.expires_at.isoformat(),
                created_at=r.created_at.isoformat(),
            )
            for r in rows
        ]
    )


@router.delete("/invitations/{invitation_id}", response_model=ApiResponse[InvitationBrief])
def revoke_invitation(
    invitation_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[InvitationBrief]:
    require_owner(user)
    invitation = team_service.revoke_invitation(db, user, invitation_id)
    db.commit()
    return success(
        InvitationBrief(
            id=str(invitation.id),
            invited_email=invitation.invited_email,
            role=invitation.role.value,
            status=invitation.status.value,
            expires_at=invitation.expires_at.isoformat(),
            created_at=invitation.created_at.isoformat(),
        )
    )


@router.post("/invitations/accept", response_model=ApiResponse[dict])
def accept_invitation(payload: AcceptInvitationRequest, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    user = team_service.accept_invitation(db, payload)
    db.commit()
    return success({"message": "Invitation accepted. Please sign in.", "email": user.email})


@router.get("/members", response_model=ApiResponse[list[MemberBrief]])
def list_members(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[list[MemberBrief]]:
    require_owner(user)
    rows = db.scalars(select(User).where(User.tenant_id == user.tenant_id).order_by(User.created_at)).all()
    return success(
        [
            MemberBrief(
                id=str(r.id),
                full_name=r.full_name,
                email=r.email,
                role=r.role.value,
                is_active=r.is_active,
            )
            for r in rows
        ]
    )