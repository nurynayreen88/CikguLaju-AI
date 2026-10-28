"""Read-only validation for every Year 2 RPT 2027 staging CSV."""
import csv
import sys
from pathlib import Path
from validate_rpt_2027_source_mapping import validate

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "data/rpt_2027/year2_source_mapping_seed_20261028.csv",
    ROOT / "data/rpt_2027/year2_pj_source_mapping_batch2_20261028.csv",
)

def main():
    errors = []
    all_rows = []
    for path in FILES:
        if not path.is_file():
            errors.append(f"Missing file: {path}")
            continue
        rows, file_errors = validate(path)
        all_rows.extend(rows)
        errors.extend(f"{path.name}: {err}" for err in file_errors)
        print(f"{path.name}: {len(rows)} source rows, {len(file_errors)} errors")
    ids = [r["record_id"] for r in all_rows]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate record_id across staging files")
    print(f"Total source rows: {len(all_rows)}")
    print(f"Total errors: {len(errors)}")
    for err in errors:
        print("ERROR:", err)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
