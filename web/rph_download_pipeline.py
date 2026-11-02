"""Isolated Web RPH delivery pipeline; no Flask or Telegram bot import.

The caller must supply a trusted account fetched from the shared backend and
an RPH obtained from an approved server-side source. This module does not
enable public download endpoints or assert production layout parity.
"""
from web.rph_document_renderer import render_approved_rph
from web.rph_delivery_quota import authorize_rendered_document


def prepare_approved_download(rph, fmt, account, telegram_user_id,
                              supabase_url, secret_key, *, debit=None,
                              renderer=None):
    if fmt not in ("docx", "pdf"):
        raise ValueError("Unsupported document format")
    if renderer is None:
        renderer = render_approved_rph
    document, mime = renderer(rph, fmt)
    if not isinstance(document, bytes) or not document:
        raise ValueError("Renderer returned no document")
    if not isinstance(mime, str) or not mime:
        raise ValueError("Renderer returned invalid MIME type")
    expected = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if fmt not in expected or mime != expected[fmt]:
        raise ValueError("Unexpected document format")
    if fmt == "pdf" and not document.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF signature")
    if fmt == "docx" and not document.startswith(b"PK\\x03\\x04"):
        raise ValueError("Invalid Word document signature")
    authorization = authorize_rendered_document(
        account, telegram_user_id, document, supabase_url, secret_key, debit=debit)
    if not authorization["allowed"]:
        return {"allowed": False, "remaining": authorization["remaining"],
                "document": None, "mime": None}
    return {"allowed": True, "remaining": authorization["remaining"],
            "document": document, "mime": mime}
