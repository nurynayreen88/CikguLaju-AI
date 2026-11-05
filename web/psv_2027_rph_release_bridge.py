"""Fail-closed source-backed PSV RPH adapter. NOT imported by production.

Staging preview is opt-in; production requires approval JSON, READY status
in both 210 RPH and RPT, and an explicit enabled switch. No DB writes.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = "Pendidikan Seni Visual"
FLAG = "CIKGULAJU_PSV_RPH_RELEASE_ENABLED"
YEAR = re.compile(r"^(?:tahun\s*)?([2-6])(?:\s*\(sk\))?$", re.I)
HEADER = re.compile(r"^# RPH Pendidikan Seni Visual Tahun ([2-6]) — PdP (\d{3})\s*$", re.M)
FIELD = re.compile(r"^\*\*([^*\n:]{1,80}):\*\*\s*(.*?)\s*$", re.M)
STEP = re.compile(
    r"^\*\*(Set induksi|Aktiviti 1|Aktiviti 2|Pengukuhan/Pentaksiran(?: PBD)?|Penutup)"
    r"[^*\n]*?:\*\*\s*(.+)$", re.M | re.I)
OBJECTIVE = re.compile(r"## Objektif dan kriteria kejayaan\s*\n(.*?)\n\s*## Langkah PdP", re.S)
EVIDENCE = re.compile(r"\b(?:Kriteria kejayaan|Bukti kejayaan|Evidens PBD|Evidens):\s*", re.I)
SP = re.compile(r"^\d+\.\d+\.\d+$")
SK = re.compile(r"^\d+\.\d+$")


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "").replace("**", "").replace(chr(96), "")).strip()


def _codes(value, pattern):
    values = [v.strip() for v in str(value or "").split(";") if v.strip()]
    return values if values and all(pattern.fullmatch(v) for v in values) else None


def _year(value):
    if type(value) is int:
        return value if 2 <= value <= 6 else None
    m = YEAR.fullmatch(str(value or "").strip())
    return int(m[1]) if m else None


def _number(value):
    raw = str(value or "").strip()
    return int(raw) if raw.isascii() and raw.isdecimal() and 1 <= int(raw) <= 42 else None


@lru_cache(maxsize=5)
def _rpt(year, root):
    try:
        path = Path(root) / "rpt_2027" / "psv" / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 42:
            return None
        for n, row in enumerate(rows, 1):
            link = row.get("Fail RPH") if year < 6 else row.get("RPH")
            expected = f"rph_standalone/psv/year{year}/lesson_{n:03d}.md"
            if (row.get("PdP") != f"{n:03d}" or row.get("Tahun") != str(year)
                or link != expected or not _codes(row.get("SK"), SK)
                or not _codes(row.get("SP"), SP)
                or row.get("Status") not in ("DRAF_SEMAK", "READY")):
                return None
        return rows
    except (OSError, csv.Error, ValueError, UnicodeError):
        return None


def _candidate_content_hash(root):
    """Lock reviewed 210 RPH and five RPT CSVs to a specific immutable revision."""
    root = Path(root)
    digest = hashlib.sha256()
    for year in range(2, 7):
        source_paths = [
            Path("rpt_2027") / "psv" / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv"
        ]
        source_paths += [
            Path("rph_standalone") / "psv" / f"year{year}" / f"lesson_{pdp:03d}.md"
            for pdp in range(1, 43)
        ]
        for relative in source_paths:
            digest.update(relative.as_posix().encode("utf-8"))
            digest.update(b"\\0")
            digest.update((root / relative).read_bytes())
            digest.update(b"\\0")
    return digest.hexdigest()


def _individual_source_audit_passed(root, expected_digest):
    """Require 210 named evidence records, not a self-declared approval JSON."""
    file = (Path(root) / "rph_standalone" / "psv" / "audits"
            / "psv_individual_210_review_20261105.csv")
    original = file.read_bytes()
    if not re.fullmatch(r"[a-f0-9]{64}", str(expected_digest or "")):
        return False
    if hashlib.sha256(original).hexdigest() != expected_digest:
        return False
    rows = list(csv.DictReader(io.StringIO(original.decode("utf-8-sig"))))
    if len(rows) != 210:
        return False
    by_id = {}
    for row in rows:
        try:
            year = int(row["Tahun"])
            pdp = int(row["PdP"])
            key = (year, pdp)
            expected_path = f"rph_standalone/psv/year{year}/lesson_{pdp:03d}.md"
            markers = set((row["Pemeriksaan_RPH_individu"] or "").split(";"))
            evidence = row["Bukti_buku"] or ""
            if (year not in range(2, 7) or pdp not in range(1, 43)
                or key in by_id or row["Fail_RPH"] != expected_path
                or row["Kelulusan_terbit"] != "PASSED"
                or not {"RPH_DIBACA", "BUKU_TEKS_VISUAL_SAH",
                        "DSKP_SEMANTIC_PASSED"}.issubset(markers)
                or not evidence.startswith("BUKU_TEKS_VISUAL_SAH:")
                or "https://" not in evidence or "ms " not in evidence.lower()
                or (row["Nota_semakan_terbuka"] or "").strip()):
                return False
            by_id[key] = True
        except (KeyError, ValueError, TypeError):
            return False
    return len(by_id) == 210


def _approved(root):
    """Fail closed unless source, audit ledger, and native runtime QA all agree."""
    try:
        root = Path(root)
        data = json.loads(
            (root / "rpt_2027" / "psv" / "psv_release_approval.json")
            .read_text(encoding="utf-8"))
        if not (data.get("approved") is True and data.get("rph_count") == 210
                and data.get("years") == [2, 3, 4, 5, 6]
                and data.get("source_review") == "INDIVIDUAL_TEXTBOOK_DSKP_PASSED"
                and data.get("runtime_staging") == "PASSED"
                and re.fullmatch(r"[a-f0-9]{40}",
                                 str(data.get("runtime_staging_commit") or ""))):
            return False
        if not _individual_source_audit_passed(root, data.get("audit_sha256")):
            return False
        if data.get("content_sha256") != _candidate_content_hash(root):
            return False
        # Every declared release lesson must be READY before installing the bridge.
        for year in range(2, 7):
            rows = _rpt(year, str(root.resolve()))
            if rows is None or any(row["Status"] != "READY" for row in rows):
                return False
            for pdp in range(1, 43):
                path = root / "rph_standalone" / "psv" / f"year{year}" / f"lesson_{pdp:03d}.md"
                if not re.search(r"(?m)^\\*\\*Status:\\*\\*\\s*READY\\s*$",
                                 path.read_text(encoding="utf-8")):
                    return False
        return True
    except (OSError, ValueError, TypeError, UnicodeError, csv.Error):
        return False


def load_candidate(year, pdp, *, preview=False, root=ROOT):
    if type(year) is not int or not 2 <= year <= 6 or type(pdp) is not int or not 1 <= pdp <= 42:
        return None
    root = str(Path(root).resolve())
    rows = _rpt(year, root)
    if rows is None:
        return None
    row = rows[pdp - 1]
    if not preview and (not _approved(root) or row["Status"] != "READY"):
        return None
    try:
        text = (Path(root) / "rph_standalone" / "psv" / f"year{year}" / f"lesson_{pdp:03d}.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    header = HEADER.search(text)
    if header is None or (int(header[1]), int(header[2])) != (year, pdp):
        return None
    meta = {k.casefold(): v.strip() for k, v in FIELD.findall(text)}
    status = meta.get("status", "")
    if "DRAF" not in status and status != "READY":
        return None
    if not preview and status != "READY":
        return None
    if _codes(meta.get("sk"), SK) != _codes(row.get("SK"), SK):
        return None
    if _codes(meta.get("sp"), SP) != _codes(row.get("SP"), SP):
        return None
    match = OBJECTIVE.search(text)
    if match is None:
        return None
    split = EVIDENCE.search(match[1])
    if split is None:
        return None
    objective = _clean(match[1][:split.start()]).rstrip(". ")
    evidence = _clean(match[1][split.end():]).rstrip(". ")
    if len(objective) < 20 or len(evidence) < 18:
        return None
    stages = {}
    for label, body in STEP.findall(text):
        key = label.casefold()
        if key.startswith("pengukuhan/"):
            key = "pbd"
        stages[key] = _clean(body)
    if any(len(stages.get(k, "")) < 20 for k in
           ("set induksi", "aktiviti 1", "aktiviti 2", "pbd", "penutup")):
        return None
    title = row.get("Tajuk karya cadangan") or row.get("Tajuk unit") or ""
    extra = row.get("Tajuk/aktiviti PdP") or ""
    if year == 6 and extra and extra != title:
        title += " — " + extra
    if len(title) < 5:
        return None
    return {
        "year": year, "pdp": pdp, "title": title, "sk": row["SK"],
        "sp": row["SP"], "objective": objective, "evidence": evidence,
        "stages": stages, "materials": _clean(meta.get("bbm")),
        "differentiation": _clean(meta.get("pembezaan")),
        "safety": _clean(meta.get("keselamatan")),
    }


def adapt_rows(state, rows, *, preview=False, root=ROOT):
    if not isinstance(state, dict) or not isinstance(rows, dict):
        return rows
    if str(state.get("subject") or "").strip().casefold() not in ("pendidikan seni visual", "psv"):
        return rows
    year = _year(state.get("year") or state.get("year_label"))
    number = _number(state.get("lesson_no") or state.get("pdp_no") or state.get("lesson"))
    if year is None or number is None:
        return rows
    plan = load_candidate(year, number, preview=preview, root=root)
    if plan is None:
        return rows
    if state.get("sp_code") and str(state["sp_code"]).strip() not in _codes(plan["sp"], SP):
        return rows
    if state.get("sk_code") and str(state["sk_code"]).strip() not in _codes(plan["sk"], SK):
        return rows
    s = plan["stages"]
    result = dict(rows)
    result.update({
        "MATA PELAJARAN": SUBJECT,
        "TAHUN/TINGKATAN": f"Tahun {year}",
        "TAJUK": plan["title"],
        "STANDARD KANDUNGAN": plan["sk"],
        "STANDARD PEMBELAJARAN": plan["sp"],
        "OBJEKTIF PEMBELAJARAN": plan["objective"],
        "KRITERIA KEJAYAAN": plan["evidence"],
        "SET INDUKSI": s["set induksi"],
        "AKTIVITI UTAMA": "Aktiviti 1 — " + s["aktiviti 1"] + "\n\nAktiviti 2 — " + s["aktiviti 2"],
        "PENTAKSIRAN": s["pbd"],
        "PENUTUP": s["penutup"],
        "BAHAN BANTU MENGAJAR": plan["materials"],
        "PEMULIHAN / PENGAYAAN": plan["differentiation"],
    })
    return result


def install(runtime, *, enabled=None, preview=False, root=ROOT):
    if enabled is None:
        enabled = os.environ.get(FLAG) == "1"
    if not enabled or (not preview and not _approved(str(Path(root).resolve()))):
        return False
    if getattr(runtime, "CIKGULAJU_PSV_RPH_BRIDGE_ACTIVE", False):
        return True
    original = getattr(runtime, "_rph_rows", None)
    if not callable(original):
        return False

    def wrapped(state, *args, **kwargs):
        old_rows = original(state, *args, **kwargs)
        try:
            return adapt_rows(state, old_rows, preview=preview, root=root)
        except Exception:
            return old_rows

    runtime._rph_rows = wrapped
    runtime.CIKGULAJU_PSV_RPH_BRIDGE_ACTIVE = True
    return True
