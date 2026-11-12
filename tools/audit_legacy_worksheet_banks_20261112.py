"""Read-only inventory of CikguLaju's legacy worksheet SQLite banks.

No worksheet rendering, no production DB writes, no content approvals. Only
schema names, row counts and source SHA-256 are emitted for staging triage.
Usage:
    python tools/audit_legacy_worksheet_banks_20261112.py \
      --manifest audits/legacy_worksheet_sources_staging_20261112.json \
      --root . --output /tmp/legacy-worksheet-audit.json
"""
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

MAX_SOURCE_BYTES = 80 * 1024 * 1024
TABLE_PATTERN = re.compile(r"worksheet|lembaran|bbm|resource|material|template|visual|asset|question|soalan", re.I)
ALLOWED_TABLE = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")


def inspect_db(path):
    """Inspect only existing SQLite files in query-only mode."""
    if path.is_symlink() or not path.is_file():
        return {"state": "MISSING_OR_LINK"}
    size = path.stat().st_size
    if size < 100 or size > MAX_SOURCE_BYTES:
        return {"state": "INVALID_SIZE", "bytes": size}
    with path.open("rb") as handle:
        sha = hashlib.file_digest(handle, "sha256").hexdigest()
    report = {"state": "INSPECTED_NOT_APPROVED", "bytes": size,
              "sha256": sha, "integrity": None, "tables": []}
    # immutable=1 prevents journal/WAL creation; query_only blocks writes.
    from urllib.parse import quote
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro&immutable=1"
    try:
        with sqlite3.connect(uri, uri=True, timeout=1) as con:
            con.execute("PRAGMA query_only=ON")
            report["integrity"] = con.execute("PRAGMA quick_check").fetchone()[0]
            names = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            report["table_count"] = len(names)
            for name in names:
                if not TABLE_PATTERN.search(name):
                    continue
                if not ALLOWED_TABLE.fullmatch(name):
                    report["tables"].append({"table": name, "status": "UNSAFE_NAME"})
                    continue
                count = con.execute('SELECT COUNT(*) FROM "' + name + '"').fetchone()[0]
                # Schema only: column names/types contain no pupil records.
                columns = [{"name": col[1], "type": col[2]}
                           for col in con.execute('PRAGMA table_info("' + name + '")')]
                report["tables"].append({"table": name, "rows": count,
                                         "columns": columns[:32],
                                         "column_count": len(columns),
                                         "status": "UNREVIEWED_ROWS"})
    except sqlite3.DatabaseError as exc:
        report["state"] = "DB_READ_ERROR"
        report["error_type"] = type(exc).__name__
    return report


def audit(manifest, root):
    root = root.resolve()
    records = []
    for source in manifest["sources"]:
        name = source["path"]
        if Path(name).name != name or not name.endswith(".db"):
            raise ValueError("Invalid source filename in manifest")
        target = root / name
        item = {"path": name, "role": source["role"],
                "production_status": "HIDDEN_PENDING_MANUAL_APPROVAL"}
        item.update(inspect_db(target))
        records.append(item)
    return {"schema_version": 1, "visibility": "internal_staging_only",
            "production_feature_gate": "OFF",
            "approval": "NONE",
            "counts_are_not_approved_worksheets": True,
            "sources": records}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--root", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    result = audit(manifest, Path(args.root))
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print("Inspected %d legacy source slots; approved worksheets: 0" % len(result["sources"]))


if __name__ == "__main__":
    main()
