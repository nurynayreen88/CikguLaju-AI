"""Verify actual generated DOCX ZIP structure before quota debit."""
from io import BytesIO
from zipfile import BadZipFile, ZipFile


def validate_word_document(document):
    if not isinstance(document, bytes) or not document.startswith(bytes((80, 75, 3, 4))):
        raise ValueError("Invalid Word document signature")
    try:
        with ZipFile(BytesIO(document)) as archive:
            if archive.testzip() is not None:
                raise ValueError("Corrupt Word document archive")
            names = set(archive.namelist())
            if not {"[Content_Types].xml", "word/document.xml"}.issubset(names):
                raise ValueError("Missing Word document content")
    except (BadZipFile, OSError):
        raise ValueError("Invalid Word document archive") from None
