"""Exact Year 2 SK DLP files shared by the RPT 2027 Web and Telegram menus."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUBJECTS = {"science_dlp": "Science", "mathematics_dlp": "Mathematics"}


def document_path(subject, year, fmt="pdf", *, root=ROOT):
    if subject not in SUBJECTS or type(year) is not int or year != 2:
        return None
    if fmt not in ("pdf", "docx"):
        return None
    name = f"CikguLaju_RPT_DLP_2027_{SUBJECTS[subject]}_Year_2.{fmt}"
    path = Path(root) / name
    try:
        if path.is_symlink() or not 8000 <= path.stat().st_size <= 2_000_000:
            return None
        with path.open("rb") as document:
            signature = b"%PDF-" if fmt == "pdf" else b"PK\x03\x04"
            return path if document.read(len(signature)) == signature else None
    except OSError:
        return None
