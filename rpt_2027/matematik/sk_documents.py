"""Verified PDFs for the aligned SK Mathematics plans."""

from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIGESTS = {
    4: "57f3e88155422c3f34327145beaae8067b114fb01cf65f2b231d17f378b05de3",
    5: "c740fb70bfa711b8ebdd54dbaf6b13aeb9c66018bf9dda1b7b3d1153ddaf4909",
    6: "1eda26ae8a13fda98535ce95e62e0f94ebfe7924106127df3581c21a55720847",
}
FILE_TEMPLATE = "CikguLaju_RPT_Matematik_SK_Tahun%d_2027.pdf"
DPK_FILE_TEMPLATE = "CikguLaju_RPT_Matematik_SK_Tahun%d_DPK_Edisi3_2027.pdf"
DPK_DIGESTS = {
    2: "04f5e56caf8f942a2d9e7fc55e0b5c2fc3371702505a0c756c46d403c4bc32c9",
    3: "2727448464d17996e29d10143d585bfb36517acc3ba7d5c0bc72c8f71ddcf5c6",
}


def document_path(year, *, root=ROOT, dpk=False):
    digests = DPK_DIGESTS if dpk else DIGESTS
    template = DPK_FILE_TEMPLATE if dpk else FILE_TEMPLATE
    if type(year) is not int or year not in digests:
        return None
    path = Path(root) / (template % year)
    try:
        if path.is_symlink() or not 10000 <= path.stat().st_size <= 1000000:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if not data.startswith(b"%PDF-") or sha256(data).hexdigest() != digests[year]:
        return None
    return path
