"""Telegram RPT choices for Year 6 SK Science."""

from rpt_2027.sains import sk_documents


LABEL, FORMATS = sk_documents.LABEL, sk_documents.FORMATS
YEARS = (6,)


def document_path(year, fmt="pdf", *, root=sk_documents.ROOT):
    if year in YEARS:
        return sk_documents.document_path(year, fmt, root=root)
    return None
