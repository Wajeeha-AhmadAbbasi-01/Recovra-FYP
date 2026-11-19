from app.modules.fbr_validation.profiles.v2 import PROFILE_VERSION, validate_extracted_v2
from app.modules.fbr_validation.schemas import ExtractedInvoice, ValidationResult

# V2 is the active local validation profile; V1 attempts remain on historical records only.


def validate_extracted(extracted: ExtractedInvoice) -> ValidationResult:
    return validate_extracted_v2(extracted)