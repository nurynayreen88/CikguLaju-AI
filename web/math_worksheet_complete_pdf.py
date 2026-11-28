"""Original reviewed Mathematics PDF assets; native source matching only."""
from pathlib import Path
import json
from web.native_telegram_sequence_rph_client import _selection, _read
from web.worksheet_complete_pdf import _pdf

CATALOG = Path(__file__).resolve().parents[1] / "worksheets/staging/math_t2_verified_20261128.json"

def _norm(value):
    return " ".join(str(value or "").split()).casefold()

def resolve_math(year, unit, token):
    if type(year) is not int or year != 2:
        return None
    route, args = _selection(year, "MATH", unit, token)
    row = _read("worksheet-identity", args, route=route)
    if (not isinstance(row, dict) or row.get("available") is not True
            or row.get("year") != year or row.get("subject") != "MATH"
            or row.get("unit") != unit or row.get("token") != token):
        return None
    standards = row.get("standards")
    if not isinstance(standards, list) or not standards or not all(
            isinstance(s, dict) and isinstance(s.get("sk"), str)
            and isinstance(s.get("sp"), str) for s in standards):
        return None
    pairs = {(s["sk"], s["sp"]) for s in standards}
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if (catalog.get("scope"), catalog.get("subject"), catalog.get("year")) != ("KSSR SK", "MATH", year):
        return None
    matches = [r for r in catalog["records"]
               if r.get("runtime_unit") == unit and r.get("runtime_lesson") == token
               and _norm(r["title"]) == _norm(row.get("topic"))
               and pairs == {(r["sk"], r["sp"])}
               and r["qa"].get("storage_integrity_verified") is True
               and r["qa"].get("answer_key_match") is True]
    return matches[0] if len(matches) == 1 else None

def complete_math_pdf(year, unit, token, kind):
    if kind not in ("murid", "skema"):
        return None
    record = resolve_math(year, unit, token)
    if record is None:
        return None
    asset = record["student" if kind == "murid" else "teacher_key"]
    filename = "CIKGULAJU_LATIHAN_MATH_T2_NILAI_TEMPAT_DAN_NILAI_DIGIT_" + kind.upper() + ".pdf"
    return _pdf(asset["drive_file_id"], asset["sha256"], asset["size_bytes"]), filename
