from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


def read_pdf_text(data: bytes, *, max_pages: int) -> tuple[str, dict]:
    """Return single-page text and read evidence. Enforces Module 1 page rules."""
    evidence: dict = {"pages": [], "read_method": "pypdf"}
    try:
        reader = PdfReader(BytesIO(data))
    except PdfReadError as exc:
        raise ValueError("corrupted_or_encrypted") from exc

    if reader.is_encrypted:
        raise ValueError("encrypted")

    page_count = len(reader.pages)
    if page_count > max_pages:
        raise ValueError("too_many_pages")
    if page_count > 1:
        raise ValueError("multiple_invoices_unsupported")

    page = reader.pages[0]
    text = (page.extract_text() or "").strip()
    evidence["pages"].append({"index": 0, "chars": len(text)})
    return text, evidence