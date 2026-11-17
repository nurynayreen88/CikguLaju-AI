"""Combine Word documents already delivered to the same teacher."""

from hashlib import sha256
from io import BytesIO

from itsdangerous import URLSafeTimedSerializer


WORD_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_SLOTS = 80  # Maximum saved timetable entries.
MAX_BUNDLE_BYTES = 32 * 1024 * 1024
WORD_RECEIPT_HEADER = "X-RPH-Word-Receipt"


def word_receipt_signer(secret):
    return URLSafeTimedSerializer(secret, salt="cikgulaju-rph-timetable-word-v1")


def word_receipt_claim(uid, content):
    return [uid, sha256(content).hexdigest()]


def compose_word_bundle(parts):
    """Start each RPH on a new page and retain each source's page setup."""
    from docx import Document
    from docx.enum.section import WD_SECTION_START
    from docxcompose.composer import Composer

    payloads = iter(parts)
    master = Document(BytesIO(next(payloads)))
    composer = Composer(master, preserve_styles=True)
    for data in payloads:
        document = Document(BytesIO(data))
        master.add_section(WD_SECTION_START.NEW_PAGE)
        composer.append(document)
        section = master.sections[-1]
        source = document.sections[-1]
        for prop in ("orientation", "page_width", "page_height", "top_margin", "bottom_margin",
                     "left_margin", "right_margin", "header_distance", "footer_distance", "gutter"):
            setattr(section, prop, getattr(source, prop))
        section.start_type = WD_SECTION_START.NEW_PAGE
    output = BytesIO()
    composer.save(output)
    output.seek(0)
    return output


def pdf_receipt_signer(secret):
    return URLSafeTimedSerializer(secret, salt="cikgulaju-rph-timetable-pdf-v1")


def compose_pdf_bundle(parts):
    from pypdf import PdfReader, PdfWriter
    from pypdf.errors import PdfReadError

    output = BytesIO()
    writer = PdfWriter()
    try:
        for part in parts:
            reader = PdfReader(BytesIO(part))
            if reader.is_encrypted or not reader.pages:
                raise ValueError("Invalid RPH PDF")
            for page in reader.pages:
                writer.add_page(page)
        writer.write(output)
    except PdfReadError as exc:
        raise ValueError("Invalid RPH PDF") from exc
    output.seek(0)
    return output
