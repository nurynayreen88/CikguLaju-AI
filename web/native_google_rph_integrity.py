"""Production-safe file and selection integrity checks for native Google RPH.
No staging accounts, quota transport or external service dependencies.
"""
from hashlib import sha256
from io import BytesIO
import json
from zipfile import BadZipFile, ZipFile

MAX_DOCUMENT_BYTES = 12 * 1024 * 1024
MAX_WORD_XML_BYTES = 4 * 1024 * 1024

class BundleNotRendered(ValueError):
    """Invalid/incomplete documents: never charge."""

def _validated_bytes(document, kind):
    if not isinstance(document, bytes) or not 500 <= len(document) <= MAX_DOCUMENT_BYTES:
        raise BundleNotRendered("Missing, invalid or oversized " + kind)
    if kind == "pdf":
        if not document.startswith(b"%PDF-") or b"%%EOF" not in document[-2048:]:
            raise BundleNotRendered("Incomplete generated PDF")
    else:
        try:
            with ZipFile(BytesIO(document)) as archive:
                for name in ("[Content_Types].xml", "word/document.xml"):
                    info = archive.getinfo(name)
                    if info.file_size < 1 or info.file_size > MAX_WORD_XML_BYTES:
                        raise BundleNotRendered("Incomplete or oversized DOCX content")
        except (BadZipFile, KeyError, OSError):
            raise BundleNotRendered("Invalid Word document") from None
    return document


def rendered_bundle_sha256(word_bytes, pdf_bytes):
    """A deterministic digest for the SAME successful Word+PDF bundle.

    Hashes PDF and Word bytes without storing any teacher names, school
    identities, private files or raw document content in the database ledger.
    """
    word = _validated_bytes(word_bytes, "word")
    pdf = _validated_bytes(pdf_bytes, "pdf")
    return sha256(b"cikgulaju-google-rph-bundle-v1\\0" +
                  sha256(word).digest() + sha256(pdf).digest()).hexdigest()

def selection_fingerprint(selection, teacher):
    """Hash the validated exact selection; don't store teacher PII in ledger."""
    if not isinstance(selection, dict) or not isinstance(teacher, dict):
        raise ValueError("Server-validated selection required")
    canonical = json.dumps(
        {"selection": selection, "teacher": teacher},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    if not 10 <= len(canonical) <= 6000:
        raise ValueError("Oversized/invalid teacher selection")
    return sha256(b"cikgulaju-rph-job-selection-v1\0" + canonical).hexdigest()
