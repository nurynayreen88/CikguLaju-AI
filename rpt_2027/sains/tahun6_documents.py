"""Published 2027 Year 6 SK Science RPT documents."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
LABEL = "Sains SK"
YEARS = (6,)
FORMATS = {"pdf": "PDF", "docx": "Word"}


def document_path(year, fmt="pdf", *, root=ROOT):
    if type(year) is not int or year not in YEARS or fmt not in FORMATS:
        return None
    path = Path(root) / f"CikguLaju_RPT_Sains_SK_Tahun6_2027.{fmt}"
    signature = b"%PDF-" if fmt == "pdf" else b"PK\x03\x04"
    try:
        if path.is_symlink() or not 8000 <= path.stat().st_size <= 2_000_000:
            return None
        with path.open("rb") as document:
            return path if document.read(len(signature)) == signature else None
    except OSError:
        return None
