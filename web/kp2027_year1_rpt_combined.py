"""Source-hash-checked single RPT (A/B together) for each KP2027 Year 1 subject."""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile, BadZipFile

BUNDLE=(Path(__file__).resolve().parents[1]/"rpt_2027"/"kp2027"/
        "year1_rpt_bm_math_alam_gabungan_ab_20261122.zip")
BUNDLE_SHA="6d1b2c51bc8535ae4c02f6f9de3bc744bf914cae0694b8ccd82f97814b1e4d51"
SUBJECTS={"matematik":"MATH","alam_dan_manusia":"ALAM","bahasa_melayu":"BM_SK"}
FORMATS={"docx":"WORD","pdf":"PDF"}
COUNTS={"matematik":(125,124),"alam_dan_manusia":(93,93),
        "bahasa_melayu":(178,175)}

class BundleUnavailable(ValueError):
    pass

def _member(subject,fmt):
    if subject not in SUBJECTS or fmt not in FORMATS:
        raise BundleUnavailable("Pilihan RPT KP2027 tidak sah")
    basename=(f"CIKGULAJU_RPT_KP2027_T1_{SUBJECTS[subject]}"
              f"_KUMPULAN_AB_GABUNGAN_2027.{fmt}")
    return f"{FORMATS[fmt]}/{basename}",basename

@lru_cache(maxsize=1)
def _approved():
    if BUNDLE.is_symlink() or not BUNDLE.is_file():
        raise BundleUnavailable("Arkib RPT KP2027 gabungan belum dipasang")
    data=BUNDLE.read_bytes()
    if not 300_000<=len(data)<=2_000_000 or sha256(data).hexdigest()!=BUNDLE_SHA:
        raise BundleUnavailable("SHA sumber RPT KP2027 gabungan tidak sah")
    try:
        with ZipFile(BytesIO(data),"r") as z:
            expected={_member(subject,fmt)[0]
                      for subject in SUBJECTS for fmt in FORMATS}
            members={item.filename for item in z.infolist() if not item.is_dir()}
            if members!=expected|{"BACA_DULU.txt","MANIFEST_QA.json"}:
                raise BundleUnavailable("Arkib mengandungi senarai fail tidak sah")
            manifest=json.loads(z.read("MANIFEST_QA.json"))
            if (manifest.get("version")!="2026-11-22" or
                manifest.get("edition")!="AB_GABUNGAN_FORMAT_UMUM" or
                manifest.get("total_pdp_a")!=396 or
                manifest.get("total_pdp_b")!=392):
                raise BundleUnavailable("Manifest gabungan bukan edisi diluluskan")
            entries=manifest.get("files")
            if not isinstance(entries,dict):
                raise BundleUnavailable("Manifest sumber hilang")
            out={}
            for subject in SUBJECTS:
                for fmt in FORMATS:
                    path,name=_member(subject,fmt)
                    entry=entries.get(name)
                    payload=z.read(path)
                    digest=sha256(payload).hexdigest()
                    if (not isinstance(entry,dict) or entry.get("path")!=path
                        or len(payload)!=entry.get("bytes")
                        or digest!=entry.get("sha256")
                        or (fmt=="pdf" and not payload.startswith(b"%PDF-"))
                        or (fmt=="docx" and not payload.startswith(b"PK\x03\x04"))
                        or not 20_000<len(payload)<1_500_000):
                        raise BundleUnavailable("RPT KP2027 gagal semakan SHA")
                    out[(subject,fmt)]=(payload,name,digest)
            return out
    except (BadZipFile,KeyError,TypeError,ValueError,OSError) as ex:
        raise BundleUnavailable("Arkib RPT KP2027 gabungan rosak") from ex

def ready():
    try:
        _approved()
        return True
    except (BundleUnavailable,OSError):
        return False

def document(subject,fmt):
    try:
        return _approved()[(subject,fmt)]
    except KeyError as ex:
        raise BundleUnavailable("Pilihan RPT KP2027 tidak sah") from ex
