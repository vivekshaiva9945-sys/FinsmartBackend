import re

# Regular expressions for Indian identity documents and sensitive financial PII
_AADHAAR_REGEX = re.compile(r"\b[2-9]{1}\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b")
_PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE)
_PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}\b")
_CARD_REGEX = re.compile(r"\b(?:\d{4}[\-\s]?){3}\d{4}\b")
_EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")


def scrub_pii(text: str, mask_email: bool = False) -> str:
    """
    Scrub sensitive Personal Identifiable Information (PII) to comply with
    India's Digital Personal Data Protection (DPDP) Act 2023.
    Applies automatic redaction for Aadhaar, PAN, phone numbers, and payment cards.
    """
    if not text:
        return ""
        
    scrubbed = text
    scrubbed = _CARD_REGEX.sub("[CARD_NUMBER_REDACTED]", scrubbed)
    scrubbed = _AADHAAR_REGEX.sub("[AADHAAR_REDACTED]", scrubbed)
    scrubbed = _PAN_REGEX.sub("[PAN_REDACTED]", scrubbed)
    scrubbed = _PHONE_REGEX.sub("[PHONE_REDACTED]", scrubbed)
    
    if mask_email:
        scrubbed = _EMAIL_REGEX.sub("[EMAIL_REDACTED]", scrubbed)
        
    return scrubbed


def contains_pii(text: str) -> bool:
    """Check if the provided text contains any unmasked PII."""
    if not text:
        return False
    return bool(
        _AADHAAR_REGEX.search(text)
        or _PAN_REGEX.search(text)
        or _PHONE_REGEX.search(text)
        or _CARD_REGEX.search(text)
    )

