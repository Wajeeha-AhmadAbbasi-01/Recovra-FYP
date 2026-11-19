import re
from decimal import Decimal, InvalidOperation

from app.modules.fbr_validation.schemas import ExtractedInvoice, LineItemExtracted

LINE_ITEM_PATTERN = re.compile(r"^LINE_ITEM:\s*(.+)$", re.MULTILINE)
# Visible table row fallback: description followed by numeric columns (qty + money fields).
ROW_PATTERN = re.compile(
    r"^(.{3,60}?)\s+(\d+(?:\.\d+)?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})(?:\s+([\d,]+\.\d{2}))?$"
)


def parse_line_items(text: str) -> list[LineItemExtracted]:
    items: list[LineItemExtracted] = []

    for match in LINE_ITEM_PATTERN.finditer(text):
        parts = [p.strip() for p in match.group(1).split("|")]
        if len(parts) < 4:
            continue
        try:
            items.append(
                LineItemExtracted(
                    description=parts[0],
                    quantity=Decimal(parts[1]),
                    unit_price=Decimal(parts[2].replace(",", "")),
                    line_total=Decimal(parts[3].replace(",", "")),
                    hs_code=parts[4] if len(parts) > 4 and parts[4] else None,
                    extraction_status="EXTRACTED",
                )
            )
        except (InvalidOperation, ValueError):
            continue

    if items:
        return items

    for line in text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith(("description", "subtotal", "grand", "total sales", "---")):
            continue
        m = ROW_PATTERN.match(line)
        if not m:
            continue
        desc, qty, unit, line_total = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            items.append(
                LineItemExtracted(
                    description=desc.strip(),
                    quantity=Decimal(qty),
                    unit_price=Decimal(unit.replace(",", "")),
                    line_total=Decimal(line_total.replace(",", "")),
                    extraction_status="EXTRACTED",
                )
            )
        except InvalidOperation:
            continue
    return items