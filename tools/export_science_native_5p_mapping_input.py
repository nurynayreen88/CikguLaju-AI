"""Offline/staging QA: export native Science identities for manual 5P mapping.

Run only in an authorized environment with the existing server-to-server
configuration. No browser login, credit operations, deploy, DB writes or
automatic release. The catalogue is not a source RPH or academic approval.
"""
import argparse
import json
from pathlib import Path
from web import native_telegram_sequence_rph_client as native

def collect(year):
    if type(year) is not int or year not in range(2, 7):
        raise ValueError("Invalid Science year")
    units = native.list_native_units(year, "SCIENCE")
    if not units:
        raise ValueError("Empty native catalogue")
    seen_units = set()
    identities = set()
    rows = []
    for unit in units:
        token = unit["value"]
        if token in seen_units:
            raise ValueError("Duplicate unit token")
        seen_units.add(token)
        lessons = native.list_native_lessons(year, "SCIENCE", token)
        if not lessons:
            raise ValueError("Empty native unit")
        for lesson in lessons:
            lesson_id = lesson["value"]
            identity = (token, lesson_id)
            if identity in identities:
                raise ValueError("Duplicate native lesson identity")
            identities.add(identity)
            row = dict(year=year, subject="SCIENCE", curriculum="KSSR",
                       unit=token, unit_label=unit["label"], lesson_id=lesson_id,
                       lesson_label=lesson["label"], candidate_id=None,
                       ready=False)
            ref = lesson.get("textbook_ref")
            if isinstance(ref, str):
                row["textbook_ref"] = ref
            rows.append(row)
    if not rows:
        raise ValueError("Empty native lesson list")
    return dict(schema="science_native_5p_mapping_input_v1",
                source="telegram-native-pdp-sequence", year=year,
                unit_count=len(seen_units), native_selection_count=len(rows),
                unique_lesson_ids=len({r["lesson_id"] for r in rows}),
                academic_approval=False, records=rows)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", required=True, type=int, choices=range(2,7))
    parser.add_argument("--out", required=True, type=Path)
    args=parser.parse_args()
    try:
        report=collect(args.year)
        # Exclusive create: never overwrite an existing reviewed mapping.
        with args.out.open("x", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("Native selections exported:", report["native_selection_count"])
    except Exception as exc:
        # Never print an internal endpoint, exception body or credential.
        parser.exit(1, "Export failed: "+type(exc).__name__+"\n")

if __name__=="__main__":
    main()
