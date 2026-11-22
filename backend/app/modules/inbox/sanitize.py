import re

_MAX_BODY = 20_000
_BLOCK = re.compile(r"(?is)<(script|style).*?>.*?</\1>")
_TAG = re.compile(r"(?is)<[^>]+>")
_SPACE = re.compile(r"\s+")


def sanitize_body(text: str) -> str:
    """Keep readable text. Drop markup so stored mail cannot carry active content."""
    cleaned = _BLOCK.sub(" ", text or "")
    cleaned = _TAG.sub(" ", cleaned)
    cleaned = _SPACE.sub(" ", cleaned).strip()
    return cleaned[:_MAX_BODY]
