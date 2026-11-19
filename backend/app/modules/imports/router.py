from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.fbr_validation.sample_pdf import build_illustrative_sample_pdf
from app.modules.imports import service as import_service
from app.modules.imports.storage import resolve_path
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/imports", tags=["imports"])


@router.get("/sample-invoice.pdf")
def sample_invoice_pdf() -> Response:
    data = build_illustrative_sample_pdf()
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="recovra-illustrative-sample.pdf"'},
    )


@router.get("/recent", response_model=ApiResponse[list])
def recent_imports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 30,
) -> ApiResponse[list]:
    rows = import_service.list_recent_imports(db, user, limit=limit)
    return success(rows)


@router.post("/pdf-batch", response_model=ApiResponse[dict])
async def pdf_batch(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    results = await import_service.process_pdf_batch(db, user, files)
    return success({"results": results})


@router.get("/{upload_id}", response_model=ApiResponse[dict])
def get_upload(
    upload_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    upload = import_service.get_upload_detail(db, user, upload_id)
    return success(
        {
            "id": str(upload.id),
            "original_filename": upload.original_filename,
            "status": upload.status.value,
            "sha256": upload.sha256,
            "size_bytes": upload.size_bytes,
            "received_at": upload.received_at.isoformat(),
        }
    )


@router.get("/{upload_id}/validation", response_model=ApiResponse[dict])
def get_validation(
    upload_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    attempt = import_service.get_validation_for_upload(db, user, upload_id)
    if not attempt:
        return success({"upload_id": str(upload_id), "validation": None})
    return success(
        {
            "upload_id": str(upload_id),
            "validation": {
                "id": str(attempt.id),
                "local_status": attempt.local_status.value,
                "profile_version": attempt.profile_version,
                "errors": attempt.errors or [],
                "warnings": attempt.warnings or [],
                "extracted": attempt.extracted_candidate or {},
            },
        }
    )


@router.get("/{upload_id}/document")
def download_source_pdf(
    upload_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    upload = import_service.get_upload_detail(db, user, upload_id)
    path = resolve_path(upload.storage_key)
    data = path.read_bytes()
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{upload.original_filename}"'},
    )