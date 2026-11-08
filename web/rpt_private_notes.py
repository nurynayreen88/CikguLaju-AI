"""Remove developer-only notes from a verified RPT PDF at download time.

Source PDFs and their 56-entry SHA-256 manifest remain immutable. The catalog
remains DRAF: this is not curriculum or textbook-mapping certification.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re

import fitz


_NOTES = (
    re.compile(
        r"Pemetaan\s+buku\s+teks\s+belum\s+disahkan\s*;?\s+rujuk\s+buku\s+dan\s+DSKP\s+sebelum\s+READY\.",
        re.IGNORECASE,
    ),
    re.compile(r"tidak\s+mereka\s+halaman\s+buku\s+teks\.", re.IGNORECASE),
    re.compile(
        r"Pemetaan\s+buku\s+teks\s+untuk\s+Lesson\s+ini\s+BELUM\s+DISAHKAN\s*;?\s+rujuk\s+naskhah\s+asal\s+sebelum\s+READY\.",
        re.IGNORECASE,
    ),
)


def _page_chars(page):
    """Retain a physical-character to text-position map, even in mixed Jawi."""
    stream, mapping = [], []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                for char in span.get("chars", []):
                    stream.append(char["c"])
                    mapping.append(char)
            stream.append("\n")
            mapping.append(None)
    return "".join(stream), mapping


def _strip(source):
    pdf = fitz.open(stream=source, filetype="pdf")
    if not 2 <= len(pdf) <= 300:
        raise ValueError("Invalid RPT page count")
    total = 0
    for page_number, page in enumerate(pdf, 1):
        text, positions = _page_chars(page)
        marked = set()
        rectangles = []
        for expression in _NOTES:
            for match in expression.finditer(text):
                total += 1
                marked.update(range(match.start(), match.end()))
                physical_line = []
                for char in list(positions[match.start():match.end()]) + [None]:
                    if char is None:
                        if physical_line:
                            bbox = fitz.Rect(physical_line[0]["bbox"])
                            for each in physical_line[1:]:
                                bbox |= fitz.Rect(each["bbox"])
                            # Vertical inset prevents overlap with Jawi text on
                            # neighboring lines (the font line boxes overlap).
                            inset = min(2.35, bbox.height * 0.28)
                            rectangles.append(fitz.Rect(
                                bbox.x0 + 0.15, bbox.y0 + inset,
                                bbox.x1 - 0.15, bbox.y1 - inset,
                            ))
                            physical_line = []
                    else:
                        physical_line.append(char)
        if not rectangles:
            if "Pemetaan buku teks belum" in text or "tidak mereka halaman buku teks" in text:
                raise ValueError(f"Unrecognized internal note on page {page_number}")
            continue
        expected = Counter(ch for i, ch in enumerate(text)
                           if i not in marked and not ch.isspace())
        for rectangle in rectangles:
            if rectangle.width <= 0 or rectangle.height <= 0:
                raise ValueError("Invalid internal-note region")
            page.add_redact_annot(rectangle, fill=(1, 1, 1), cross_out=False)
        page.apply_redactions(images=0, graphics=0, text=0)
        after, _ = _page_chars(page)
        actual = Counter(ch for ch in after if not ch.isspace())
        if expected != actual:
            raise ValueError(f"Unsafe text deletion on page {page_number}")
        if any(expression.search(after) for expression in _NOTES):
            raise ValueError("Internal note remained after redaction")
    if not total:
        return None
    result = pdf.tobytes(garbage=4, deflate=True)
    if not result.startswith(b"%PDF-"):
        raise ValueError("Invalid sanitized PDF")
    return result


@lru_cache(maxsize=56)
def _cached_clean(path, size, mtime_ns):
    """Cache immutable teacher-facing bytes, keyed by source-file identity."""
    raw = Path(path).read_bytes()
    if len(raw) != size or not raw.startswith(b"%PDF-"):
        raise ValueError("RPT source changed during download")
    return _strip(raw)


def pdf_for_teacher(path):
    """Return original Path if already clean; otherwise safe PDF BytesIO."""
    path = Path(path)
    stat = path.stat()
    fixed = _cached_clean(str(path), stat.st_size, stat.st_mtime_ns)
    return BytesIO(fixed) if fixed is not None else path
