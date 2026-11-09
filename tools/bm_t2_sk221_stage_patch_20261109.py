"""Stage-only, fail-closed copy repair for one BM Tahun 2 SK mapping.

Never edits the source SQLite file. The repaired candidate is created ONLY at
an explicitly specified new path. Nothing in this module deploys a DB or
modifies Telegram/Web production runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path


LESSON = ("Tahun 2", "Bahasa Melayu", "Hidup Berjiran",
          "Majlis Pengikat Kemesraan")
OLD = ("2.1", "2.2.1")
NEW = ("2.2", "2.2.1")


class SafetyHold(ValueError):
    """Do not proceed when source integrity or proof is uncertain."""


def _digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def _ro(path: Path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def _verify(conn):
    """Return the one rowid after verifying both source and authoritative proof."""
    if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise SafetyHold("Source SQLite integrity failed")
    rows = conn.execute(
        """SELECT rowid, sk_code, sp_code, verification_status
           FROM verified_pdp_sequence
           WHERE year_label=? AND subject=? AND unit_title=? AND pdp_title=?""",
        LESSON,
    ).fetchall()
    if len(rows) != 1 or tuple(rows[0][1:3]) != OLD:
        raise SafetyHold("BM lesson identity, count or old SK/SP changed")
    if rows[0][3] not in ("SOURCE_VERIFIED", "SOURCE_VERIFIED_SK", "VERIFIED"):
        raise SafetyHold("BM lesson is not source-verified")

    proven = conn.execute(
        """SELECT DISTINCT sk_code, sk_text, sp_text
           FROM curriculum_standards
           WHERE year_label=? AND subject=? AND sp_code=? AND verified=1""",
        (LESSON[0], LESSON[1], NEW[1]),
    ).fetchall()
    if (len(proven) != 1 or str(proven[0][0] or "").strip() != NEW[0]
            or not str(proven[0][1] or "").strip()
            or not str(proven[0][2] or "").strip()
            or "kosa kata" not in proven[0][2].casefold()
            or "idea keseluruhan" not in proven[0][2].casefold()):
        raise SafetyHold("Missing, incomplete or ambiguous verified SK/SP proof")
    return rows[0][0]


def verify_source(source: str | Path):
    path = Path(source).resolve(strict=True)
    with _ro(path) as conn:
        rowid = _verify(conn)
    return {"source": str(path), "source_sha256": _digest(path),
            "target_rowid": rowid, "before": OLD, "after": NEW}


def make_staging_copy(source: str | Path, candidate: str | Path,
                      *, expected_source_sha256: str | None = None):
    src = Path(source).resolve(strict=True)
    out = Path(candidate).resolve(strict=False)
    if src == out or out.exists():
        raise SafetyHold("Refusing overwrite of source or an existing candidate")
    if not out.parent.is_dir():
        raise SafetyHold("Candidate parent folder does not exist")
    evidence = verify_source(src)
    if (expected_source_sha256 is not None
            and evidence["source_sha256"] != expected_source_sha256):
        raise SafetyHold("Source checksum mismatch")

    # O_EXCL prevents accidental overwrite even if another task creates a
    # candidate between our initial check and open.
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    try:
        with _ro(src) as original, sqlite3.connect(out) as destination:
            original.backup(destination)
            destination.execute("PRAGMA foreign_keys=ON")
            rowid = _verify(destination)
            if rowid != evidence["target_rowid"]:
                raise SafetyHold("Row identity changed during copy")
            cur = destination.execute(
                """UPDATE verified_pdp_sequence SET sk_code=?
                   WHERE rowid=? AND year_label=? AND subject=?
                     AND unit_title=? AND pdp_title=?
                     AND sk_code=? AND sp_code=?""",
                (NEW[0], rowid, *LESSON, *OLD),
            )
            if cur.rowcount != 1:
                raise SafetyHold("Expected exactly one row to change")
            updated = destination.execute(
                "SELECT sk_code, sp_code FROM verified_pdp_sequence WHERE rowid=?",
                (rowid,),
            ).fetchone()
            if tuple(updated) != NEW:
                raise SafetyHold("Candidate does not contain corrected SK/SP")
            if destination.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise SafetyHold("Candidate SQLite integrity failed")
            destination.commit()
        if _digest(src) != evidence["source_sha256"]:
            raise SafetyHold("Source file changed during staging copy")
        return {**evidence, "candidate": str(out),
                "candidate_sha256": _digest(out), "updated_rows": 1}
    except Exception:
        out.unlink(missing_ok=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--candidate", type=Path,
                        help="NEW staging copy path; never existing/master path")
    parser.add_argument("--expected-source-sha256",
                        help="Optional pinned SHA-256 of exact source DB")
    args = parser.parse_args(argv)
    result = (make_staging_copy(
        args.source, args.candidate,
        expected_source_sha256=args.expected_source_sha256
    ) if args.candidate else verify_source(args.source))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
