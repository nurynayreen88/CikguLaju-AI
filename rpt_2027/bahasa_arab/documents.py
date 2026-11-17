"""Draft Arabic SK 2027 RPT PDFs, byte-identical to the Web downloads."""
from hashlib import sha256
import json
from pathlib import Path

LABEL = "Bahasa Arab"
YEARS = tuple(range(2, 7))
FORMATS = {"pdf": "PDF • DRAF"}
ROOT = Path(__file__).resolve().parent


def document_path(year, fmt="pdf", *, root=ROOT):
    if type(year) is not int or year not in YEARS or fmt not in FORMATS:
        return None
    path = root / f"RPT_Bahasa_Arab_Tahun_{year}_2027_DRAF.pdf"
    if path.is_symlink() or not path.is_file():
        return None
    try:
        expected = json.loads((root / "web_rpt_pdfs_2027.json").read_text(encoding="utf-8"))
        contents = path.read_bytes()
        if not contents.startswith(b"%PDF-") or sha256(contents).hexdigest() != expected[str(year)]:
            return None
    except (OSError, KeyError, TypeError, ValueError):
        return None
    return path
