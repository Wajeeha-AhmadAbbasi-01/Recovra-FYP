import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.audit.service import log_event
from app.modules.customers.models import Customer
from app.modules.fbr_validation.engine import validate_extracted
from app.modules.fbr_validation.profiles.v2 import PROFILE_VERSION
from app.modules.fbr_validation.schemas import ValidationIssue, ValidationResult
from app.modules.imports.models import Upload, UploadStatus, ValidationAttempt, ValidationStatus
from app.modules.imports.pdf_extract import extract_invoice_from_pdf
from app.modules.imports.storage import resolve_path, store_bytes
from app.modules.invoices.models import Invoice, InvoiceItem, InvoiceLifecycle
from app.modules.users.models import User

settings = get_settings()


async def process_pdf_batch(db: Session, user: User, files: list[UploadFile]) -> list[dict]:
    if len(files) > settings.pdf_max_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many files in batch")

    results: list[dict] = []
    for file in files:
        results.append(await _process_one(db, user, file))
    db.commit()
    return results


async def _process_one(db: Session, user: User, file: UploadFile) -> dict:
    filename = (file.filename or "upload.pdf").replace("\\", "_").replace("/", "_")
    if not filename.lower().endswith(".pdf"):
        return _result_row(filename, None, ValidationStatus.REJECTED_UNSUPPORTED, [{"message": "Only PDF files allowed"}])

    data = await file.read()
    if len(data) > settings.pdf_max_bytes:
        return _result_row(filename, None, ValidationStatus.REJECTED_UNSUPPORTED, [{"message": "File too large"}])

    try:
        storage_key, sha256 = store_bytes(data)
    except OSError:
        return _result_row(filename, None, ValidationStatus.PROCESSING_ERROR, [{"message": "Storage failure"}])

    duplicate_upload = db.scalar(
        select(Upload).where(Upload.tenant_id == user.tenant_id, Upload.sha256 == sha256)
    )
    if duplicate_upload:
        return _result_row(filename, str(duplicate_upload.id), ValidationStatus.DUPLICATE, [{"message": "Duplicate file"}])

    upload = Upload(
        tenant_id=user.tenant_id,
        uploader_user_id=user.id,
        original_filename=filename[:512],
        storage_key=storage_key,
        sha256=sha256,
        mime_type=file.content_type or "application/pdf",
        size_bytes=len(data),
        status=UploadStatus.processing,
    )
    db.add(upload)
    db.flush()

    try:
        extracted, evidence = extract_invoice_from_pdf(data, max_pages=settings.pdf_max_pages)
    except ValueError as exc:
        code = str(exc)
        local_status = ValidationStatus.REJECTED_UNSUPPORTED
        if code == "encrypted":
            msg = "Encrypted PDF not supported"
        elif code == "too_many_pages":
            msg = "PDF exceeds page limit"
        elif code == "multiple_invoices_unsupported":
            msg = "One invoice per PDF is required"
        else:
            msg = "Unsupported or corrupted PDF"
            local_status = ValidationStatus.PROCESSING_ERROR
        return _finalize_attempt(
            db,
            user,
            upload,
            local_status,
            [],
            evidence={},
            message=msg,
        )

    validation = validate_extracted(extracted)
    attempt = ValidationAttempt(
        tenant_id=user.tenant_id,
        upload_id=upload.id,
        profile_version=PROFILE_VERSION,
        extracted_candidate=validation.normalized,
        local_status=ValidationStatus(validation.status),
        errors=[_issue_dict(issue) for issue in validation.issues],
        warnings=[_issue_dict(w) for w in validation.warnings],
        evidence=evidence,
    )
    db.add(attempt)
    upload.status = UploadStatus.completed if validation.status == ValidationStatus.ACCEPTED_LOCAL_CHECK.value else UploadStatus.failed
    db.flush()

    invoice_id: str | None = None
    if validation.status == ValidationStatus.ACCEPTED_LOCAL_CHECK.value:
        norm = validation.normalized
        seller_identity = f"{norm.get('seller_name','')}|{norm.get('seller_ntn','')}".strip("|")
        invoice_ref = norm["invoice_reference"]

        dup_invoice = db.scalar(
            select(Invoice).where(
                Invoice.tenant_id == user.tenant_id,
                Invoice.invoice_reference == invoice_ref,
                Invoice.seller_identity == seller_identity,
                Invoice.lifecycle_status == InvoiceLifecycle.active,
            )
        )
        if dup_invoice:
            attempt.local_status = ValidationStatus.DUPLICATE
            upload.status = UploadStatus.failed
            db.flush()
            return _result_enriched(
                filename,
                str(upload.id),
                None,
                ValidationResult(
                    status=ValidationStatus.DUPLICATE.value,
                    issues=[
                        ValidationIssue(
                            field="invoice",
                            code="DUPLICATE",
                            message="Duplicate invoice identity",
                            source="RECOVRA_BUSINESS",
                            rule_id="RECOVRA-DUP",
                        )
                    ],
                    warnings=validation.warnings,
                    normalized=validation.normalized,
                ),
                validation.normalized,
            )

        customer = db.scalar(
            select(Customer).where(
                Customer.tenant_id == user.tenant_id,
                Customer.business_name == norm.get("buyer_name"),
            )
        )
        if not customer:
            customer = Customer(
                tenant_id=user.tenant_id,
                business_name=norm["buyer_name"],
                buyer_ntn=norm.get("buyer_ntn"),
            )
            db.add(customer)
            db.flush()

        total = Decimal(norm["total_amount"])
        invoice = Invoice(
            tenant_id=user.tenant_id,
            customer_id=customer.id,
            upload_id=upload.id,
            validation_attempt_id=attempt.id,
            invoice_reference=invoice_ref,
            seller_identity=seller_identity,
            claimed_fbr_identifier=norm.get("fbr_invoice_number"),
            issue_date=datetime.strptime(norm["issue_date"], "%Y-%m-%d").date(),
            due_date=datetime.strptime(norm["due_date"], "%Y-%m-%d").date(),
            currency=norm.get("currency") or "PKR",
            total_amount=total,
            outstanding_amount=total,
            lifecycle_status=InvoiceLifecycle.active,
        )
        db.add(invoice)
        line_items = norm.get("line_items") or []
        if line_items:
            for li in line_items:
                db.add(
                    InvoiceItem(
                        invoice=invoice,
                        description=str(li.get("description", "Line"))[:512],
                        quantity=Decimal(str(li.get("quantity", "1"))),
                        unit_price=Decimal(str(li.get("unit_price", "0"))),
                        line_total=Decimal(str(li.get("line_total", "0"))),
                        hs_code=li.get("hs_code"),
                    )
                )
        else:
            db.add(
                InvoiceItem(
                    invoice=invoice,
                    description="Imported line",
                    quantity=Decimal("1"),
                    unit_price=total,
                    line_total=total,
                )
            )
        db.flush()
        invoice_id = str(invoice.id)
        log_event(
            db,
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            entity_type="invoice",
            entity_id=invoice_id,
            action="invoice_imported",
            summary={"upload_id": str(upload.id), "status": validation.status},
        )

    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        entity_type="upload",
        entity_id=str(upload.id),
        action="pdf_processed",
        summary={"status": validation.status},
    )

    return _result_enriched(filename, str(upload.id), invoice_id, validation, validation.normalized)


def _finalize_attempt(db, user, upload, local_status, issues, evidence, message):
    attempt = ValidationAttempt(
        tenant_id=user.tenant_id,
        upload_id=upload.id,
        profile_version=PROFILE_VERSION,
        extracted_candidate={},
        local_status=local_status,
        errors=issues,
        warnings=[],
        evidence=evidence,
    )
    db.add(attempt)
    upload.status = UploadStatus.failed
    db.flush()
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        entity_type="upload",
        entity_id=str(upload.id),
        action="pdf_processed",
        summary={"status": local_status.value, "message": message},
    )
    return _result_row(upload.original_filename, str(upload.id), local_status, [{"message": message}])


def _issue_dict(issue) -> dict:
    if isinstance(issue, ValidationIssue):
        return issue.__dict__()
    if isinstance(issue, dict):
        return issue
    return {"message": str(issue)}


def _result_enriched(
    filename: str,
    upload_id: str | None,
    invoice_id: str | None,
    validation,
    norm: dict,
) -> dict:
    line_items = norm.get("line_items") or []
    return {
        "filename": filename,
        "upload_id": upload_id,
        "invoice_id": invoice_id,
        "invoice_reference": norm.get("invoice_reference"),
        "seller_name": norm.get("seller_name"),
        "buyer_name": norm.get("buyer_name"),
        "issue_date": norm.get("issue_date"),
        "due_date": norm.get("due_date"),
        "invoice_total": norm.get("total_amount"),
        "line_item_count": len(line_items),
        "validation_profile": norm.get("profile_version", PROFILE_VERSION),
        "extraction_method": norm.get("extraction_method"),
        "local_status": validation.status,
        "local_status_label": _status_label(validation.status),
        "issues": [_issue_dict(i) for i in validation.issues],
        "warnings": [_issue_dict(w) for w in validation.warnings],
    }


def _status_label(status: str) -> str:
    return {
        ValidationStatus.ACCEPTED_LOCAL_CHECK.value: "Passed Local Validation",
        ValidationStatus.NEEDS_MANUAL_REVIEW.value: "Needs Manual Review",
        ValidationStatus.REJECTED_LOCAL_CHECK.value: "Rejected — Validation Failed",
        ValidationStatus.REJECTED_UNSUPPORTED.value: "Unsupported File",
        ValidationStatus.DUPLICATE.value: "Already Imported / Duplicate",
        ValidationStatus.PROCESSING_ERROR.value: "Processing Error",
    }.get(status, status)


def _result_row(filename, upload_id, status_enum, issues):
    status_val = status_enum.value if hasattr(status_enum, "value") else str(status_enum)
    return {
        "filename": filename,
        "upload_id": upload_id,
        "invoice_id": None,
        "local_status": status_val,
        "local_status_label": _status_label(status_val),
        "issues": issues,
        "warnings": [],
    }


def get_upload_detail(db: Session, user: User, upload_id: uuid.UUID) -> Upload:
    upload = db.get(Upload, upload_id)
    if not upload or upload.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    return upload


def get_validation_for_upload(db: Session, user: User, upload_id: uuid.UUID) -> ValidationAttempt | None:
    get_upload_detail(db, user, upload_id)
    return db.scalar(
        select(ValidationAttempt)
        .where(ValidationAttempt.upload_id == upload_id, ValidationAttempt.tenant_id == user.tenant_id)
        .order_by(ValidationAttempt.created_at.desc())
    )