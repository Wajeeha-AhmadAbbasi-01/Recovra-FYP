# FBR rule register (Module 1 — registered B2B goods)

Profiles: `registered_b2b_goods_v1` (historical attempts), **`registered_b2b_goods_v2`** (active).

| Rule ID | Source | Field | Severity | Status |
|---------|--------|-------|----------|--------|
| FBR-INV-REF | [FBR DI API examples](https://www.fbr.gov.pk/) | invoice_reference | error | team-reviewed draft |
| FBR-SELLER-NAME | Supplier identity on registered invoice | seller_name | error | v2 |
| FBR-SELLER-ID | [Sales tax registration / NTN](https://www.fbr.gov.pk/) | seller_ntn | error | team-reviewed draft |
| FBR-BUYER | Buyer name on tax invoice | buyer_name | error | team-reviewed draft |
| FBR-DATE | Invoice issue date | issue_date | error | team-reviewed draft |
| FBR-TOTAL | Invoice total / grand total | total_amount | error | team-reviewed draft |
| RECOVRA-DUE | Recovra aging / receivables | due_date | error | business requirement |
| RECOVRA-LINE-ITEMS | Itemized extraction for B2B goods | line_items | error | v2 structured PDFs |
| RECOVRA-LINE-MATH | qty × unit vs line total (±0.05 PKR) | line_items | error | v2 business |
| RECOVRA-GRAND-TOTAL | Sum of lines vs total (±0.05 PKR) | grand_total | error | v2 business |
| RECOVRA-EXTRACT-TEXT | Text layer required | document | error | no OCR |
| RECOVRA-DISCLAIMER | Local check disclaimer | compliance | warning | always on accept |
| RECOVRA-DUP | Duplicate seller+ref | invoice | error | business |

Official URLs: see parent plan `RECOVRA_MODULE_1_IMPLEMENTATION_PLAN_REVISION_2_1_MAILPIT.md` §0.3.

**Not in scope:** live FBR/PRAL verification, OCR, universal tax rate assumptions.