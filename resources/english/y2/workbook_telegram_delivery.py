"""Explicit Year 2 verified Workbook delivery helper for the Telegram bot.

The caller supplies the existing Telegram send_document function. This helper
never charges a trial quota and does not modify any user or curriculum state.
"""
from pathlib import Path

from .workbook_download_router import resolve_lesson


def send_verified_workbook(chat_id, lesson, send_document, root=None):
    """Send the verified PDF part; return True only after Telegram acknowledges it.

    No file is sent when the lesson is unverified or the PDF is absent.
    Exceptions from the Telegram sender are deliberately propagated.
    """
    if not callable(send_document):
        raise TypeError("send_document must be callable")
    resource = resolve_lesson(lesson, root=root)
    if resource is None:
        return False
    pdf_path = Path(resource["path"])
    caption = (
        f"English Tahun 2 • Lesson {int(lesson)} • Workbook "
        f"(halaman sumber {resource['source_page_start']}"
        f"–{resource['source_page_end']})"
    )
    with pdf_path.open("rb") as pdf:
        response = send_document(chat_id, pdf, caption)
    if response is None:
        return False
    if hasattr(response, "ok") and not response.ok:
        return False
    if hasattr(response, "json"):
        payload = response.json()
        return isinstance(payload, dict) and payload.get("ok") is True
    return False
