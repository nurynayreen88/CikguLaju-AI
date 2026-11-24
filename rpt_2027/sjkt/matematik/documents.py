"""RPT 2027 Matematik SJKT Tahun 2 downloads."""

from pathlib import Path

CODE = "matematik_sjkt"
LABEL = "Matematik SJKT"
YEARS = (2,)
FORMATS = {"pdf": "PDF", "docx": "Word"}
ROOT = Path(__file__).resolve().parent


def document_path(year, fmt="pdf", *, root=ROOT):
    if type(year) is not int or year not in YEARS or fmt not in FORMATS:
        return None
    path = Path(root) / f"RPT_2027_Matematik_SJKT_Tahun_{year}.{fmt}"
    signature = b"%PDF-" if fmt == "pdf" else b"PK\x03\x04"
    try:
        if path.is_symlink() or not 8000 <= path.stat().st_size <= 2_000_000:
            return None
        with path.open("rb") as document:
            return path if document.read(len(signature)) == signature else None
    except OSError:
        return None
