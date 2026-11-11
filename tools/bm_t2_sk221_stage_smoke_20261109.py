"""CI smoke: true v26.00 immutable split DB -> disposable staged candidate."""
import hashlib
import sqlite3
from pathlib import Path

from tools.bm_native_v26_navigation_audit import database
from tools.bm_t2_sk221_stage_patch_20261109 import make_staging_copy


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    tmp, source = database()
    try:
        before = sha(source)
        copy = Path(tmp.name) / "bm_t2_sk221_staging_only.db"
        report = make_staging_copy(
            source, copy, expected_source_sha256=before
        )
        assert report["updated_rows"] == 1
        assert sha(source) == before, "Original master was modified"
        assert copy.is_file() and copy != source
        sql = (
            """SELECT sk_code, sp_code FROM verified_pdp_sequence
               WHERE year_label='Tahun 2' AND subject='Bahasa Melayu'
               AND unit_title='Hidup Berjiran'
               AND pdp_title='Majlis Pengikat Kemesraan'"""
        )
        with sqlite3.connect(
            source.resolve().as_uri() + "?mode=ro", uri=True
        ) as old, sqlite3.connect(
            copy.resolve().as_uri() + "?mode=ro", uri=True
        ) as revised:
            assert old.execute(sql).fetchall() == [("2.1", "2.2.1")]
            assert revised.execute(sql).fetchall() == [("2.2", "2.2.1")]
            old_total = old.execute(
                "SELECT COUNT(*) FROM verified_pdp_sequence"
            ).fetchone()[0]
            new_total = revised.execute(
                "SELECT COUNT(*) FROM verified_pdp_sequence"
            ).fetchone()[0]
            assert old_total == new_total, "Unexpected row count change"
            assert revised.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        print("PASS BM T2 exact source repair, candidate only")
        print("source SHA256", before)
        print("candidate SHA256", report["candidate_sha256"])
        print("master row count unchanged", old_total)
    finally:
        tmp.cleanup()


if __name__ == "__main__":
    main()
