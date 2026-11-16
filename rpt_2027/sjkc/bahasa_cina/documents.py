"""Bahasa Cina SJKC RPT 2027 for W.P. Kuala Lumpur (Kumpulan B)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUBJECT = "bahasa_cina_sjkc"
LABEL = "Bahasa Cina (SJKC)"
PUBLISHED_YEARS = (2, 3, 4, 5, 6)
CALENDAR = "W.P. Kuala Lumpur · Kumpulan B"


def document_path(year, fmt="pdf", *, root=ROOT):
    if type(year) is not int or year not in PUBLISHED_YEARS:
        return None
    if fmt not in ("pdf", "docx"):
        return None
    path = Path(root) / f"RPT_2027_Bahasa_Cina_SJKC_Tahun_{year}.{fmt}"
    signature = b"%PDF-" if fmt == "pdf" else b"PK\x03\x04"
    try:
        if path.is_symlink() or not path.is_file() or not 8000 <= path.stat().st_size <= 2_000_000:
            return None
        with path.open("rb") as stream:
            return path if stream.read(len(signature)) == signature else None
    except OSError:
        return None
