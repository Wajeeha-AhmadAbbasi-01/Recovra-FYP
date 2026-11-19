"""PDF extraction entry point (V2 pipeline)."""

from app.modules.imports.extraction.pipeline import extract_invoice_from_pdf

__all__ = ["extract_invoice_from_pdf"]