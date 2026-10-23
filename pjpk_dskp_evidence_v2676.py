"""Read-only exact-scope PJPK DSKP SP evidence lookup (v26.76).

The bundle is a compact gzip/base64 snapshot of direct DSKP transcriptions
from existing source-work artifacts. It never updates a database or promotes
a release gate. A code is usable only for the same year and subject; conflicting
source wordings fail closed.
"""
import base64
import csv
import gzip
import json
import re
from pathlib import Path

VALID_YEARS = {f"Tahun {n}" for n in range(1, 7)}
SUBJECTS = {"PJ": "Pendidikan Jasmani", "PK": "Pendidikan Kesihatan"}
CODE_RE = re.compile(r"^\d+(?:\.\d+){1,2}$")


def load_evidence(root=None):
    """Return exact (year, subject, SP code) -> source rows, without DB writes."""
    path = (Path(root) if root else Path(__file__).resolve().parent) / "curriculum_sources" / "pjpk" / "dskp_sp_evidence_v2676.csv.gz.base64"
    encoded = "".join(path.read_text(encoding="ascii").split())
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    payload = json.loads(raw.decode("utf-8"))
    index = {}
    for item in payload:
        if not isinstance(item, list) or len(item) != 6:
            raise ValueError("Invalid PJPK DSKP evidence row")
        year_digit, subject_key, code, text, source_id, status = item
        year, subject = "Tahun " + str(year_digit), SUBJECTS.get(str(subject_key))
        code, text = str(code).strip(), str(text).strip()
        if year not in VALID_YEARS or not subject or not CODE_RE.fullmatch(code) or not text or status not in {"D", "C"}:
            raise ValueError("Invalid PJPK DSKP evidence row: " + repr(item[:3]))
        row = {
            "year_label": year, "subject": subject, "sp_code": code,
            "sp_text": text, "source_document": "DSKP PJPK " + year,
            "source_file_id": str(source_id or ""),
            "source_status": "DIRECT_DSKP_TEXT_TRANSCRIBED" if status == "D" else "CONFLICT_REVIEW",
        }
        index.setdefault((year, subject, code), []).append(row)
    # Supplement only with explicitly source-cited transcriptions. Existing bundle
    # rows are retained so conflicting texts still fail closed during reconciliation.
    supplement = (Path(root) if root else Path(__file__).resolve().parent) / "curriculum_sources" / "pjpk" / "dskp_sp_verified_supplement_v2679.csv"
    if supplement.is_file():
        with supplement.open("r", encoding="utf-8-sig", newline="") as stream:
            for item in csv.DictReader(stream):
                year = str(item.get("year_label", "")).strip()
                subject = str(item.get("subject", "")).strip()
                code = str(item.get("sp_code", "")).strip()
                text = str(item.get("sp_text", "")).strip()
                if (year not in VALID_YEARS or subject not in SUBJECTS.values() or not CODE_RE.fullmatch(code) 
                        or not text or not str(item.get("source_document", "")).strip() 
                        or not str(item.get("source_file_id", "")).strip()):
                    raise ValueError("Invalid source-cited PJPK DSKP supplement row: " + repr((year, subject, code)))
                row = {
                    "year_label": year, "subject": subject, "sp_code": code,
                    "sp_text": text,
                    "source_document": str(item.get("source_document", "")).strip(),
                    "source_file_id": str(item.get("source_file_id", "")).strip(),
                    "source_status": "DIRECT_DSKP_TEXT_TRANSCRIBED",
                }
                index.setdefault((year, subject, code), []).append(row)
    # Edition-specific direct transcriptions recovered from the user's original
    # DSKP files. Keep the previous bundle/supplement untouched: disagreement
    # between editions or source records is deliberately a conflict, not a win.
    for filename in ("dskp_sp_direct_t1_pj_2015_v2692.csv",
                     "dskp_sp_direct_t2_t6_pj_v2693.csv"):
        direct = (Path(root) if root else Path(__file__).resolve().parent) / "curriculum_sources" / "pjpk" / filename
        if not direct.is_file():
            raise FileNotFoundError("Required PJPK original DSKP evidence missing: " + str(direct))
        with direct.open("r", encoding="utf-8-sig", newline="") as stream:
            for item in csv.DictReader(stream):
                year, subject = item["year_label"].strip(), item["subject"].strip()
                code, wording = item["sp_code"].strip(), item["sp_text"].strip()
                document, source_id = item["source_document"].strip(), item["source_file_id"].strip()
                if (year not in VALID_YEARS or subject not in SUBJECTS.values()
                        or not CODE_RE.fullmatch(code) or not wording or not document or not source_id):
                    raise ValueError("Invalid original DSKP transcription: " + repr((year, subject, code)))
                index.setdefault((year, subject, code), []).append({
                    "year_label": year, "subject": subject, "sp_code": code,
                    "sp_text": wording, "source_document": document,
                    "source_file_id": source_id, "source_status": "DIRECT_DSKP_TEXT_TRANSCRIBED",
                })
    if len(index) < 300:
        raise ValueError(f"PJPK DSKP evidence bundle unexpectedly small: {len(index)} exact keys")
    return index


def reconcile_sp_text(year, subject, code, rpt_text, evidence):
    """Compare one RPT SP with only its same-year, same-subject DSKP evidence."""
    key = (str(year or "").strip(), str(subject or "").strip(), str(code or "").strip())
    rows = evidence.get(key, [])
    if not rows:
        return {"status": "NO_DIRECT_DSKP_TEXT", "dskp_text": "", "source_document": ""}
    normalize = lambda value: re.sub(r"[^\w]+", " ", str(value or "").casefold(), flags=re.UNICODE).strip()
    variants = {normalize(row["sp_text"]) for row in rows}
    if len(variants) != 1 or any(row["source_status"] != "DIRECT_DSKP_TEXT_TRANSCRIBED" for row in rows):
        return {"status": "CONFLICT_REVIEW", "dskp_text": "", "source_document": " | ".join(sorted({r["source_document"] for r in rows}))}
    dskp_text = rows[0]["sp_text"].strip()
    status = "EXACT_TEXT_MATCH" if normalize(rpt_text) == normalize(dskp_text) else "TEXT_DIFF_REVIEW"
    return {"status": status, "dskp_text": dskp_text, "source_document": rows[0]["source_document"], "source_file_id": rows[0]["source_file_id"]}
