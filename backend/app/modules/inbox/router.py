import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.config import get_settings
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.inbox import service
from app.modules.inbox.models import LinkState
from app.modules.inbox.schemas import LinkDecision, MockDeliverRequest
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])


def _link_payload(link) -> dict:
    return {
        "id": str(link.id),
        "invoice_id": str(link.invoice_id),
        "link_state": link.link_state.value,
        "evidence": link.evidence,
        "confirmed_by": str(link.confirmed_by) if link.confirmed_by else None,
    }


def _message_payload(db: Session, user: User, message) -> dict:
    return {
        "id": str(message.id),
        "mailbox_id": str(message.mailbox_id),
        "folder": message.folder,
        "uidvalidity": message.uidvalidity,
        "uid": message.uid,
        "rfc_message_id": message.rfc_message_id,
        "sender": message.sender,
        "recipient": message.recipient,
        "subject": message.subject,
        "received_at": message.received_at.isoformat(),
        "body_text": message.sanitized_body,
        "content_type": message.content_type,
        "ingestion_state": message.ingestion_state.value,
        "links": [_link_payload(link) for link in service.links_for(db, user.tenant_id, message.id)],
    }


@router.get("/mailbox/status", response_model=ApiResponse[dict])
def mailbox_status(user: User = Depends(get_current_user)) -> ApiResponse[dict]:
    settings = get_settings()
    return success(
        {
            "provider": "mock",
            "live_imap": "NOT_IMPLEMENTED",
            "imap_enabled": False,
            "imap_enabled_setting": settings.imap_enabled,
            "sends_mail": False,
            "tenant_id": str(user.tenant_id),
        }
    )


@router.post("/mailbox/mock-deliver", response_model=ApiResponse[dict])
def mock_deliver(
    payload: MockDeliverRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    settings = get_settings()
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    results = service.ingest_mock(db, user, payload.messages, str(uuid.uuid4()))
    db.commit()
    return success({"results": results, "sends_mail": False})


@router.get("/messages", response_model=ApiResponse[dict])
def list_messages(
    link_state: LinkState | None = None,
    unlinked: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    state = "UNLINKED" if unlinked else (link_state.value if link_state else None)
    rows, total = service.list_messages(db, user, state, page, page_size)
    return success(
        {
            "items": [_message_payload(db, user, row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@router.get("/messages/{message_id}", response_model=ApiResponse[dict])
def get_message(
    message_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    message = service.message_for_tenant(db, user.tenant_id, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return success(_message_payload(db, user, message))


@router.post("/messages/{message_id}/links", response_model=ApiResponse[dict])
def post_link(
    message_id: UUID,
    payload: LinkDecision,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    link = service.decide_link(db, user, message_id, payload, str(uuid.uuid4()))
    db.commit()
    db.refresh(link)
    return success(_link_payload(link))
