import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.collections import repository as repo
from app.modules.collections import service
from app.modules.collections.models import TaskStatus
from app.modules.collections.present import case_payload, dispute_payload, promise_payload, task_payload
from app.modules.collections.schemas import DisputeCreate, DisputePatch, PromiseCreate, PromisePatch, TaskCreate, TaskPatch
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/collections", tags=["collections"])


def _correlation() -> str:
    return str(uuid.uuid4())


@router.get("/tasks", response_model=ApiResponse[dict])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    assignee: UUID | None = None,
    customer: UUID | None = None,
    overdue: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    rows, total = service.list_tasks(
        db,
        user,
        status_filter=status_filter,
        assignee_id=assignee,
        customer_id=customer,
        overdue=overdue,
        page=page,
        page_size=page_size,
    )
    items = []
    for task in rows:
        invoice = repo.invoice_for_tenant(db, user.tenant_id, task.invoice_id)
        if invoice:
            items.append(task_payload(db, task, invoice))
    return success({"items": items, "page": page, "page_size": page_size, "total": total})


@router.post("/tasks", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def post_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    task = service.create_task(db, user, payload, _correlation())
    db.commit()
    db.refresh(task)
    invoice = repo.invoice_for_tenant(db, user.tenant_id, task.invoice_id)
    return success(task_payload(db, task, invoice))


@router.get("/tasks/{task_id}", response_model=ApiResponse[dict])
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    task = repo.task_for_tenant(db, user.tenant_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    invoice = repo.invoice_for_tenant(db, user.tenant_id, task.invoice_id)
    return success(task_payload(db, task, invoice))


@router.patch("/tasks/{task_id}", response_model=ApiResponse[dict])
def patch_task(
    task_id: UUID,
    payload: TaskPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    task = service.update_task(db, user, task_id, payload, _correlation())
    db.commit()
    db.refresh(task)
    invoice = repo.invoice_for_tenant(db, user.tenant_id, task.invoice_id)
    return success(task_payload(db, task, invoice))


@router.get("/cases", response_model=ApiResponse[dict])
def list_cases(
    status_filter: str | None = Query(default=None, alias="status"),
    customer: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    from sqlalchemy import func, select

    from app.modules.collections.models import CollectionCase

    stmt = select(CollectionCase).where(CollectionCase.tenant_id == user.tenant_id)
    if status_filter:
        stmt = stmt.where(CollectionCase.state == status_filter)
    if customer:
        from app.modules.invoices.models import Invoice

        stmt = stmt.join(Invoice, CollectionCase.invoice_id == Invoice.id).where(
            Invoice.tenant_id == user.tenant_id,
            Invoice.customer_id == customer,
        )
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.order_by(CollectionCase.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    items = []
    for case in rows:
        invoice = repo.invoice_for_tenant(db, user.tenant_id, case.invoice_id)
        if invoice:
            items.append(case_payload(case, invoice))
    return success({"items": items, "page": page, "page_size": page_size, "total": int(total)})


@router.get("/cases/{case_id}", response_model=ApiResponse[dict])
def get_case(
    case_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    case = repo.case_for_tenant(db, user.tenant_id, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    invoice = repo.invoice_for_tenant(db, user.tenant_id, case.invoice_id)
    return success(case_payload(case, invoice))


@router.get("/invoices/{invoice_id}/promises", response_model=ApiResponse[dict])
def list_promises(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    if repo.invoice_for_tenant(db, user.tenant_id, invoice_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    rows = repo.promises_for_invoice(db, user.tenant_id, invoice_id)
    return success({"items": [promise_payload(db, row) for row in rows], "total": len(rows)})


@router.post("/invoices/{invoice_id}/promises", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def post_promise(
    invoice_id: UUID,
    payload: PromiseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    promise = service.record_promise(db, user, invoice_id, payload, _correlation())
    db.commit()
    db.refresh(promise)
    return success(promise_payload(db, promise))


@router.patch("/promises/{promise_id}", response_model=ApiResponse[dict])
def patch_promise(
    promise_id: UUID,
    payload: PromisePatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    promise = service.transition_promise(db, user, promise_id, payload, _correlation())
    db.commit()
    db.refresh(promise)
    return success(promise_payload(db, promise))


@router.get("/invoices/{invoice_id}/disputes", response_model=ApiResponse[dict])
def list_disputes(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    if repo.invoice_for_tenant(db, user.tenant_id, invoice_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    rows = repo.disputes_for_invoice(db, user.tenant_id, invoice_id)
    return success({"items": [dispute_payload(db, row) for row in rows], "total": len(rows)})


@router.post("/invoices/{invoice_id}/disputes", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
def post_dispute(
    invoice_id: UUID,
    payload: DisputeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    dispute = service.record_dispute(db, user, invoice_id, payload, _correlation())
    db.commit()
    db.refresh(dispute)
    return success(dispute_payload(db, dispute))


@router.patch("/disputes/{dispute_id}", response_model=ApiResponse[dict])
def patch_dispute(
    dispute_id: UUID,
    payload: DisputePatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    dispute = service.transition_dispute(db, user, dispute_id, payload, _correlation())
    db.commit()
    db.refresh(dispute)
    return success(dispute_payload(db, dispute))


@router.get("/invoices/{invoice_id}/timeline", response_model=ApiResponse[dict])
def get_timeline(
    invoice_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    rows, total = service.timeline(db, user, invoice_id, page, page_size)
    items = [
        {
            "id": str(row.id),
            "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None,
            "origin": row.origin,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "action": row.action,
            "summary": row.summary,
            "correlation_id": row.correlation_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
    return success({"items": items, "page": page, "page_size": page_size, "total": total})


@router.get("/reminders/preview", response_model=ApiResponse[dict])
def reminder_preview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    from app.modules.collections import reminder_cycle

    items = reminder_cycle.preview_tenant_reminders(db, user.tenant_id)
    return success(
        {
            "items": items,
            "sends_customer_email": False,
            "note": "Staff-task scheduling preview only; not FBR or payment verification.",
        }
    )


@router.post("/reminders/run", response_model=ApiResponse[dict])
def run_reminders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    from app.modules.collections import reminder_cycle

    result = reminder_cycle.run_tenant_reminder_cycle(db, user.tenant_id, correlation_id=str(uuid.uuid4()))
    db.commit()
    return success(
        {
            "evaluated": result.evaluated,
            "tasks_created": result.created,
            "skipped": result.skipped,
            "expired_promises": result.expired_promises,
            "as_of": result.as_of.isoformat(),
            "policy_version": result.policy_version,
            "sends_customer_email": False,
        }
    )

