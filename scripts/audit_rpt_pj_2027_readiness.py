"""Read-only readiness audit for RPT PJ 2027 assets and calendar.

Run from repo root: python scripts/audit_rpt_pj_2027_readiness.py DATA_DIR
This command never mutates any file or database.
"""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rpt_pj_2027_delivery import STATES, YEARS, list_available
from rpt_pj_2027_calendar import read_calendar_csv, CalendarDataError


def audit(root):
    root = Path(root)
    expected = len(STATES) * len(YEARS)
    available = list_available(root)
    snapshot = Path(__file__).resolve().parents[1] / (
        "data/rpt_pj_2027/calendar_2027_16_negeri_sheet_snapshot.csv"
    )
    result = {
        "expected_documents": expected,
        "available_documents": len(available),
        "missing_documents": [],
        "calendar_records": 0,
        "calendar_valid": False,
        "ready_for_manual_telegram_test": False,
    }
    have = {(item["negeri"].replace(" ", "_"), item["tahun"]) for item in available}
    result["missing_documents"] = [
        f"{state}/Tahun_{year}" for state in STATES for year in YEARS
        if (state, year) not in have
    ]
    try:
        records = read_calendar_csv(snapshot, strict=True)
        result["calendar_records"] = len(records)
        result["calendar_valid"] = True
    except (CalendarDataError, FileNotFoundError, OSError) as exc:
        result["calendar_error"] = str(exc)
    result["ready_for_manual_telegram_test"] = (
        len(available) == expected and result["calendar_valid"]
    )
    return result


if __name__ == "__main__":
    data_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    report = audit(data_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ready_for_manual_telegram_test"] else 1)
