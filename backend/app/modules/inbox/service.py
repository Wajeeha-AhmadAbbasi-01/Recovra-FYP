import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.service import log_event
from app.modules.collections.repository import invoice_for_tenant
from app.modules.inbox.models import InboundMessage, LinkState, Mailbox, MessageInvoiceLink
from app.modules.inbox.sanitize import sanitize_body
from app.modules.inbox.schemas import LinkDecision, MockMessageIn
from app.modules.invoices.models import Invoice
from app.modules.users.models import User


def _reject(code: int, message: str) -> None:
    raise HTTPException(status_code=code, detail=message)


def get_or_create_mock_mailbox(db: Session, tenant_id: uuid.UUID) -> Mailbox:
    row = db.scalar(select(Mailbox).where(Mailbox.tenant_id == tenant_id, Mailbox.provider == "mock"))
    if row:
        return row
    row = Mailbox(tenant_id=tenant_id, provider="mock", enabled=False, display_name="Finance inbox (mock)")
    db.add(row)
    db.flush()
    return row


def _existing_message(db: Session, mailbox: Mailbox, folder: str, uidvalidity: int, uid: int) -> InboundMessage | None:
    return db.scalar(
        select(InboundMessage).where(
            InboundMessage.tenant_id == mailbox.tenant_id,
            InboundMessage.mailbox_id == mailbox.id,
            InboundMessage.folder == folder,
            InboundMessage.uidvalidity == uidvalidity,
            InboundMessage.uid == uid,
        )
    )


def ingest_mock(db: Session, user: User, messages: list[MockMessageIn], correlation_id: str) -> list[dict]:
    """Persist mock envelopes. Never opens a network connection and never sends mail."""
    mailbox = get_or_create_mock_mailbox(db, user.tenant_id)
    results = []
    for item in messages:
        existing = _existing_message(db, mailbox, item.folder, item.uidvalidity, item.uid)
        if existing:
            results.append({"id": str(existing.id), "created": False})
            continue
        received = item.received_at or datetime.now(timezone.utc)
        message = InboundMessage(
            tenant_id=user.tenant_id,
            mailbox_id=mailbox.id,
            folder=item.folder,
            uidvalidity=item.uidvalidity,
            uid=item.uid,
            rfc_message_id=item.rfc_message_id,
            sender=item.sender.strip(),
            recipient=item.recipient.strip(),
            subject=item.subject.strip(),
            received_at=received,
            sanitized_body=sanitize_body(item.body),
            content_type="text/plain",
        )
        db.add(message)
        db.flush()
        _suggest_links(db, user, message, item.invoice_references)
        log_event(
            db,
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            entity_type="inbound_message",
            entity_id=str(message.id),
            action="message_ingested",
            origin="staff",
            correlation_id=correlation_id,
            summary={"mailbox_id": str(mailbox.id), "uid": item.uid, "uidvalidity": item.uidvalidity},
        )
        results.append({"id": str(message.id), "created": True})
    return results


def _suggest_links(db: Session, user: User, message: InboundMessage, references: list[str]) -> None:
    seen: set[uuid.UUID] = set()
    for reference in references:
        ref = reference.strip()
        if not ref:
            continue
        matches = db.scalars(
            select(Invoice).where(Invoice.tenant_id == user.tenant_id, Invoice.invoice_reference == ref)
        ).all()
        for invoice in matches:
            if invoice.id in seen:
                continue
            seen.add(invoice.id)
            db.add(
                MessageInvoiceLink(
                    tenant_id=user.tenant_id,
                    message_id=message.id,
                    invoice_id=invoice.id,
                    link_state=LinkState.SUGGESTED,
                    evidence={"match": "invoice_reference", "auto_confirmed": False},
                )
            )
    db.flush()


def list_messages(db: Session, user: User, link_state: str | None, page: int, page_size: int) -> tuple[list[InboundMessage], int]:
    rows = db.scalars(
        select(InboundMessage).where(InboundMessage.tenant_id == user.tenant_id).order_by(InboundMessage.received_at.desc())
    ).all()
    if link_state:
        kept = []
        for message in rows:
            states = {link.link_state.value for link in links_for(db, user.tenant_id, message.id)}
            if link_state == "UNLINKED" and not states:
                kept.append(message)
            elif link_state in states:
                kept.append(message)
        rows = kept
    start = (page - 1) * page_size
    return rows[start : start + page_size], len(rows)


def links_for(db: Session, tenant_id: uuid.UUID, message_id: uuid.UUID) -> list[MessageInvoiceLink]:
    return list(
        db.scalars(
            select(MessageInvoiceLink).where(
                MessageInvoiceLink.tenant_id == tenant_id,
                MessageInvoiceLink.message_id == message_id,
            )
        ).all()
    )


def message_for_tenant(db: Session, tenant_id: uuid.UUID, message_id: uuid.UUID) -> InboundMessage | None:
    row = db.get(InboundMessage, message_id)
    if row is None or row.tenant_id != tenant_id:
        return None
    return row


def decide_link(db: Session, user: User, message_id: uuid.UUID, payload: LinkDecision, correlation_id: str) -> MessageInvoiceLink:
    message = message_for_tenant(db, user.tenant_id, message_id)
    if message is None:
        _reject(status.HTTP_404_NOT_FOUND, "Message not found")
    invoice = invoice_for_tenant(db, user.tenant_id, payload.invoice_id)
    if invoice is None:
        _reject(status.HTTP_404_NOT_FOUND, "Invoice not found")
    target = LinkState.CONFIRMED if payload.action == "confirm" else LinkState.REJECTED
    link = db.scalar(
        select(MessageInvoiceLink).where(
            MessageInvoiceLink.tenant_id == user.tenant_id,
            MessageInvoiceLink.message_id == message.id,
            MessageInvoiceLink.invoice_id == invoice.id,
        )
    )
    if link and link.link_state == target:
        return link
    before = link.link_state.value if link else None
    if link is None:
        link = MessageInvoiceLink(
            tenant_id=user.tenant_id,
            message_id=message.id,
            invoice_id=invoice.id,
            link_state=target,
            evidence={"match": "staff", "auto_confirmed": False},
        )
        db.add(link)
    else:
        link.link_state = target
    if target == LinkState.CONFIRMED:
        link.confirmed_by = user.id
    db.flush()
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        entity_type="message_invoice_link",
        entity_id=str(link.id),
        action="message_link_confirmed" if target == LinkState.CONFIRMED else "message_link_rejected",
        origin="staff",
        correlation_id=correlation_id,
        summary={"invoice_id": str(invoice.id), "message_id": str(message.id), "before": before, "after": target.value},
    )
    return link
