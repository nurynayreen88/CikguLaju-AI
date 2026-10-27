"""Pilihan RPH PDF/Word untuk checkbox bahan PdP sedia ada.

Modul ini tidak menukar DB, kuota atau handler Telegram secara automatik.
Adapter Telegram perlu menggabungkan dua pilihan ini dengan pilihan bahan lain.
"""
from typing import Iterable, Tuple

RPH_PDF = "rph_pdf"
RPH_WORD = "rph_word"

RPH_CHECKBOX_OPTIONS = (
    ("📕 RPH (PDF)", RPH_PDF),
    ("📘 RPH (Word)", RPH_WORD),
)

DEFAULT_SELECTED = frozenset((RPH_PDF,))


def selected_rph_extensions(selected: Iterable[str]) -> Tuple[str, ...]:
    """PDF, Word atau kedua-duanya mengikut checkbox yang ditanda."""
    values = set(selected)
    return tuple(
        extension for key, extension in (
            (RPH_PDF, ".pdf"),
            (RPH_WORD, ".docx"),
        ) if key in values
    )


def toggle_rph_format(selected: Iterable[str], choice: str) -> frozenset:
    """Toggle satu pilihan tanpa menjejaskan pilihan audio/buku teks."""
    if choice not in (RPH_PDF, RPH_WORD):
        raise ValueError("Pilihan format RPH tidak sah")
    values = set(selected)
    if choice in values:
        values.remove(choice)
    else:
        values.add(choice)
    return frozenset(values)


def requires_rph_generation(selected: Iterable[str]) -> bool:
    """Dua format tetap satu permintaan kandungan RPH."""
    values = set(selected)
    return bool(values.intersection((RPH_PDF, RPH_WORD)))
