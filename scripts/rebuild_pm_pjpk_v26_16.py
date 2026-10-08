#!/usr/bin/env python3
"""Rebuild v26.16 PM/PJPK SQLite from three versioned GitHub parts.
Never replaces an existing database; does not change runtime configuration.
Usage: python scripts/rebuild_pm_pjpk_v26_16.py
"""
from pathlib import Path
import hashlib
import os
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "CikguLaju_Curriculum_Master_v26_16_PJPK_SAFE_RELEASE.db"
PARTS = [
    ("CikguLaju_v26_16.db.part01", 12582912, "8c8304c282b783496525ad508b0bf1bf3d214b13"),
    ("CikguLaju_v26_16.db.part02", 12582912, "b45390ed74b7e4ede782f51bc783b99a47742271"),
    ("CikguLaju_v26_16.db.part03", 5267456, "59d38f0b49d6ecf3b3a071cf98c17d26e53c91fe"),
]
EXPECTED_SIZE = sum(size for _, size, _ in PARTS)

def main():
    if DEST.exists():
        raise SystemExit(f"Refusing to overwrite existing database: {DEST}")
    for name, size, git_sha in PARTS:
        path = ROOT / name
        if not path.is_file() or path.stat().st_size != size:
            raise SystemExit(f"Missing or wrong-sized part: {path}")
        raw = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        if actual != git_sha:
            raise SystemExit(f"Git blob SHA mismatch: {name}")
    fd, temp_name = tempfile.mkstemp(prefix=".v26_16_rebuild_", suffix=".db", dir=ROOT)
    try:
        with os.fdopen(fd, "wb") as out:
            for name, _, _ in PARTS:
                with (ROOT / name).open("rb") as inp:
                    while True:
                        block = inp.read(1024 * 1024)
                        if not block:
                            break
                        out.write(block)
        temp = Path(temp_name)
        if temp.stat().st_size != EXPECTED_SIZE:
            raise RuntimeError("Combined size mismatch")
        with sqlite3.connect(f"file:{temp}?mode=ro", uri=True) as db:
            result = db.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise RuntimeError(f"SQLite integrity_check failed: {result}")
        if DEST.exists():
            raise RuntimeError("Destination appeared during rebuild; refusing to overwrite")
        os.link(temp, DEST)
        print(f"Verified and created: {DEST.name} ({EXPECTED_SIZE} bytes)")
        print("No existing database replaced; runtime configuration unchanged.")
    finally:
        Path(temp_name).unlink(missing_ok=True)

if __name__ == "__main__":
    main()
