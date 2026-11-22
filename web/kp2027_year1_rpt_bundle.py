"""Immutable, source-checked KP2027 Tahun 1 RPT A/B downloads.

The ZIP is the CikguLaju 22 Nov 2026 QA bundle (3 subjects x 2 groups x
Word/PDF). Files remain SEMAKAN pelaksanaan, not a claim that a school's
timetable or PdP distribution is final. No paths come from user input.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile, BadZipFile

BUNDLE = (Path(__file__).resolve().parents[1] / "rpt_2027" / "kp2027"
          / "year1_rpt_bm_math_alam_20261122.zip")
BUNDLE_SHA = "eaeba933830747ff1569f433a06e1de1705fc88a658e9bd6ef5633751361936e"
SUBJECTS = {"matematik": "MATH", "bahasa_melayu": "BM_SK", "alam_dan_manusia": "ALAM"}
GROUPS = ("A", "B")
FORMATS = {"pdf": "PDF", "docx": "WORD"}
COUNTS = {"matematik": {"A": 125, "B": 124},
          "bahasa_melayu": {"A": 178, "B": 175},
          "alam_dan_manusia": {"A": 93, "B": 93}}


class BundleUnavailable(ValueError):
    pass


def _member(subject, group, fmt):
    if subject not in SUBJECTS or group not in GROUPS or fmt not in FORMATS:
        raise BundleUnavailable("Pilihan RPT KP2027 tidak sah")
    basename = ("CIKGULAJU_RPT_KP2027_T1_" + SUBJECTS[subject]
                + "_KUMPULAN_" + group + "_PDP_LENGKAP_SEMAKAN." + fmt)
    return f"{FORMATS[fmt]}/{basename}", basename


@lru_cache(maxsize=1)
def _approved_files():
    """Verify every member *before* enabling any download in catalog."""
    if BUNDLE.is_symlink() or not BUNDLE.is_file() or not 100_000 <= BUNDLE.stat().st_size <= 3_000_000:
        raise BundleUnavailable("Arkib RPT KP2027 belum dipasang")
    raw = BUNDLE.read_bytes()
    if sha256(raw).hexdigest() != BUNDLE_SHA:
        raise BundleUnavailable("SHA arkib RPT KP2027 tidak sah")
    try:
        with ZipFile(BytesIO(raw), "r") as archive:
            members = {name for name,info in ((i.filename, i) for i in archive.infolist())
                       if not info.is_dir()}
            expected = {_member(subject, group, fmt)[0]
                        for subject in SUBJECTS for group in GROUPS for fmt in FORMATS}
            if members != expected | {"BACA_DULU.txt", "MANIFEST_QA.json"}:
                raise BundleUnavailable("Senarai fail RPT KP2027 tidak lengkap")
            manifest = json.loads(archive.read("MANIFEST_QA.json"))
            files = manifest.get("files")
            if manifest.get("version") != "2026-11-22" or not isinstance(files, dict):
                raise BundleUnavailable("Manifest RPT KP2027 tidak sah")
            verified = {}
            for subject in SUBJECTS:
                for group in GROUPS:
                    for fmt in FORMATS:
                        member,basename = _member(subject,group,fmt)
                        entry = files.get(basename)
                        payload = archive.read(member)
                        if (not isinstance(entry,dict) or len(payload) != entry.get("bytes")
                            or sha256(payload).hexdigest() != entry.get("sha256")
                            or (fmt=="pdf" and not payload.startswith(b"%PDF-"))
                            or (fmt=="docx" and not payload.startswith(b"PK\x03\x04"))
                            or not 15_000 <= len(payload) <= 10_000_000):
                            raise BundleUnavailable("Fail RPT KP2027 gagal semakan hash")
                        verified[(subject,group,fmt)] = (payload,basename,entry["sha256"])
            return verified
    except (BadZipFile, KeyError, ValueError, TypeError, OSError) as exc:
        raise BundleUnavailable("RPT KP2027 belum disahkan") from exc


def ready():
    try:
        _approved_files()
        return True
    except (BundleUnavailable, OSError):
        return False


def document(subject, group, fmt):
    try:
        return _approved_files()[(subject,group,fmt)]
    except KeyError as exc:
        raise BundleUnavailable("Pilihan RPT KP2027 tidak tersedia") from exc
