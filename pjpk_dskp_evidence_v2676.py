"""Read-only exact-scope PJPK DSKP SP evidence lookup (v26.76).

The bundle is a compact gzip/base64 snapshot of direct DSKP transcriptions
from existing source-work artifacts. It never updates a database or promotes
a release gate. A code is usable only for the same year and subject; conflicting
source wordings fail closed.
"""
import base64
import gzip
import json
import re
from pathlib import Path

VALID_YEARS = {f"Tahun {n}" for n in range(1, 7)}
SUBJECTS = {"PJ": "Pendidikan Jasmani", "PK": "Pendidikan Kesihatan"}
CODE_RE = re.compile(r"^\\d+(?:\\.\\d+){1,2}$")


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
    if len(index) < 300:
        raise ValueError(f"PJPK DSKP evidence bundle unexpectedly small: {len(index)} exact keys")
    return index


def reconcile_sp_text(year, subject, code, rpt_text, evidence):
    """Compare one RPT SP with only its same-year, same-subject DSKP evidence."""
    key = (str(year or "").strip(), str(subject or "").strip(), str(code or "").strip())
    rows = evidence.get(key, [])
    if not rows:
        return {"status": "NO_DIRECT_DSKP_TEXT", "dskp_text": "", "source_document": ""}
    variants = {row["sp_text"].strip() for row in rows}
    if len(variants) != 1 or any(row["source_status"] != "DIRECT_DSKP_TEXT_TRANSCRIBED" for row in rows):
        return {"status": "CONFLICT_REVIEW", "dskp_text": "", "source_document": " | ".join(sorted({r["source_document"] for r in rows}))}
    dskp_text = next(iter(variants))
    normalize = lambda value: re.sub(r"[^\\w]+", " ", str(value or "").casefold(), flags=re.UNICODE).strip()
    status = "EXACT_TEXT_MATCH" if normalize(rpt_text) == normalize(dskp_text) else "TEXT_DIFF_REVIEW"
    return {"status": status, "dskp_text": dskp_text, "source_document": rows[0]["source_document"], "source_file_id": rows[0]["source_file_id"]}
