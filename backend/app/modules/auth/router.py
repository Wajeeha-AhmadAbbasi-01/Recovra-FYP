import uuid

from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.config import get_settings
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.auth import service as auth_service
from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    TenantBrief,
    UserBrief,
)
from app.modules.audit.service import log_event
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


def _set_session_cookie(response: Response, session_id: uuid.UUID) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=str(session_id),
        httponly=True,
        secure=settings.session_secure_cookie,
        samesite="lax",
        max_age=settings.session_max_age_seconds,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.session_cookie_name, path="/")


@router.post("/register", response_model=ApiResponse[RegisterResponse], status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> ApiResponse[RegisterResponse]:
    tenant, user = auth_service.register_business(db, payload)
    db.commit()
    return success(
        RegisterResponse(
            message="Business account created. Please sign in.",
            tenant=TenantBrief(id=str(tenant.id), name=tenant.name),
            user=UserBrief(
                id=str(user.id),
                full_name=user.full_name,
                email=user.email,
                role=user.role.value,
            ),
        )
    )


@router.post("/login", response_model=ApiResponse[MeResponse])
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> ApiResponse[MeResponse]:
    user = auth_service.authenticate(db, payload)
    session_id = auth_service.create_session(db, user)
    db.commit()
    _set_session_cookie(response, session_id)
    tenant = user.tenant
    return success(
        MeResponse(
            user=UserBrief(
                id=str(user.id),
                full_name=user.full_name,
                email=user.email,
                role=user.role.value,
            ),
            tenant=TenantBrief(id=str(tenant.id), name=tenant.name),
        )
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> ApiResponse[dict]:
    if session_id:
        try:
            auth_service.delete_session(db, uuid.UUID(session_id))
            db.commit()
        except ValueError:
            pass
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        entity_type="user",
        entity_id=str(user.id),
        action="logout",
        summary={},
    )
    db.commit()
    _clear_session_cookie(response)
    return success({"message": "Logged out"})


@router.get("/me", response_model=ApiResponse[MeResponse])
def me(user: User = Depends(get_current_user)) -> ApiResponse[MeResponse]:
    tenant = user.tenant
    return success(
        MeResponse(
            user=UserBrief(
                id=str(user.id),
                full_name=user.full_name,
                email=user.email,
                role=user.role.value,
            ),
            tenant=TenantBrief(id=str(tenant.id), name=tenant.name),
        )
    )