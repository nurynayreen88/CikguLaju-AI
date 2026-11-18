"""Verified PDFs for the aligned RPT and RPH Year 5 and 6 Mathematics sets."""

from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIGESTS = {
    5: "c740fb70bfa711b8ebdd54dbaf6b13aeb9c66018bf9dda1b7b3d1153ddaf4909",
    6: "1eda26ae8a13fda98535ce95e62e0f94ebfe7924106127df3581c21a55720847",
}
FILE_TEMPLATE = "CikguLaju_RPT_Matematik_SK_Tahun%d_2027.pdf"


def document_path(year, *, root=ROOT):
    if type(year) is not int or year not in DIGESTS:
        return None
    path = Path(root) / (FILE_TEMPLATE % year)
    try:
        if path.is_symlink() or not 10000 <= path.stat().st_size <= 1000000:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if not data.startswith(b"%PDF-") or sha256(data).hexdigest() != DIGESTS[year]:
        return None
    return path
