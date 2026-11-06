"""STAGING ONLY: lossless punctuation adaptation for the current legacy RPH renderer.

app.py clean_doc_text strips code points outside ASCII and Latin Extended A/B.
Without adaptation, 'Buku halaman 4–5' can become 'Buku halaman 45'.
This adapter maps known punctuation to readable ASCII equivalents and FAILS
CLOSED on unexpected non-supported glyphs; never touch production app.py.
"""
import re

MAP = {
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": " - ",
    "\u2015": " - ", "\u2212": "-", "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "- ",
    "\u2192": " -> ", "\u2190": " <- ", "\u00ad": "-",
    "\u00a0": " ",
}
def _allowed_char(char):
    cp = ord(char)
    return cp in (9, 10, 13) or 32 <= cp <= 126 or 160 <= cp <= 591


def normalize_for_legacy_doc(text):
    if not isinstance(text, str):
        raise TypeError("Legacy RPH text must be a string")
    result = "".join(MAP.get(char, char) for char in text)
    if not all(_allowed_char(c) for c in result):
        unusual = sorted(set(c for c in result if not _allowed_char(c)))
        raise ValueError("Unsupported RPH text glyphs cannot be silently removed: "
                         + ", ".join(f"U+{ord(c):04X}" for c in unusual))
    return result


def normalize_check(original, rendered):
    """A pure semantic equality check after known substitutions and whitespace."""
    return " ".join(normalize_for_legacy_doc(original).split()) == " ".join(rendered.split())
