"""Read-only exact-scope PJPK DSKP SP evidence lookup (v26.76).

The evidence bundle is a compressed, text-encoded snapshot of direct DSKP
transcriptions from the existing source-work artifacts. This module never
updates a database or promotes a release gate. A code is usable only with the
same year and subject, and conflicting source wordings fail closed.
"""
import base64
import csv
import gzip
import io
import re
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent / "curriculum_sources" / "pjpk" / "dskp_sp_evidence_v2676.csv.gz.base64"
VALID_YEARS = {f"Tahun {n}" for n in range(1, 7)}
VALID_SUBJECTS = {"Pendidikan Jasmani", "Pendidikan Kesihatan"}
CODE_RE = re.compile(r"^\\d+(?:\\.\\d+){1,2}$")


def load_evidence(root=None):
    """Return exact (year, subject, SP code) -> source rows, without DB writes."""
    path = (Path(root) if root else Path(__file__).resolve().parent) / "curriculum_sources" / "pjpk" / "dskp_sp_evidence_v2676.csv.gz.base64"
    encoded = path.read_text(encoding="ascii").strip()
    raw = gzip.decompress(base64.b64decode(encoded, validate=True)).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    required = {"year_label", "subject", "sp_code", "sp_text", "source_document", "source_file_id", "source_status", "text_variant_count"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError("PJPK DSKP evidence bundle has an invalid schema")
    index = {}
    for row in reader:
        year, subject, code = row["year_label"].strip(), row["subject"].strip(), row["sp_code"].strip()
        text = row["sp_text"].strip()
        if year not in VALID_YEARS or subject not in VALID_SUBJECTS or not CODE_RE.fullmatch(code) or not text:
            raise ValueError("Invalid PJPK DSKP evidence row: " + repr((year, subject, code)))
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
