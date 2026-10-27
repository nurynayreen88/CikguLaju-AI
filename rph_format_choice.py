"""Pilihan format muat turun RPH; modul tanpa kesan sampingan.

Integrasi handler Telegram dan eksport DOCX dibuat berasingan selepas
laluan penghantaran RPH sedia ada disahkan.
"""
from typing import Tuple

FORMAT_PDF = "pdf"
FORMAT_WORD = "word"
FORMAT_BOTH = "both"

RPH_FORMAT_OPTIONS = (
    ("📕 PDF sahaja (.pdf)", FORMAT_PDF),
    ("📘 Word sahaja (.docx)", FORMAT_WORD),
    ("📚 Kedua-duanya (PDF + Word)", FORMAT_BOTH),
)


def selected_extensions(format_choice: str) -> Tuple[str, ...]:
    """Senarai fail untuk dihantar; satu pilihan tidak bermaksud satu janaan baharu."""
    mapping = {
        FORMAT_PDF: (".pdf",),
        FORMAT_WORD: (".docx",),
        FORMAT_BOTH: (".pdf", ".docx"),
    }
    try:
        return mapping[format_choice]
    except (KeyError, TypeError):
        raise ValueError("Pilihan format RPH tidak sah") from None


def format_keyboard_rows(callback_prefix: str = "rph_format"):
    """Data neutral untuk dibina menjadi InlineKeyboardButton oleh adapter Telegram."""
    return tuple(
        ((label, f"{callback_prefix}:{value}"),)
        for label, value in RPH_FORMAT_OPTIONS
    )
