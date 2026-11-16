from pathlib import Path

CODE = "bahasa_melayu_sjk"
LABEL = "Bahasa Melayu (SJK)"
YEARS = (2, 3, 4)
FORMATS = {"pdf": "PDF", "docx": "Word"}
ROOT = Path(__file__).resolve().parent


def document_path(year, fmt="pdf", *, root=ROOT):
    if type(year) is not int or year not in YEARS or fmt not in FORMATS:
        return None
    path = Path(root) / f"RPT_2027_Bahasa_Melayu_SJK_Tahun_{year}.{fmt}"
    signature = b"%PDF-" if fmt == "pdf" else b"PK\x03\x04"
    try:
        if path.is_symlink() or not 8000 <= path.stat().st_size <= 2_000_000:
            return None
        with path.open("rb") as document:
            return path if document.read(len(signature)) == signature else None
    except OSError:
        return None
