"""Read-only release audit against shipped v26.00 Telegram master DB.

Reads original immutable .bin parts and verifies manifest SHA; writes a
temporary DB copy to the CI runner only. Never modifies the source or app DB.
"""
import hashlib
import json
import re
import sqlite3
import tempfile
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]


def database():
    manifest = json.loads((ROOT / "v26_00_manifest.json").read_text("utf-8"))
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / "master.db"
    digest = hashlib.sha256()
    with path.open("wb") as out:
        for part in manifest["parts"]:
            f = ROOT / part["file"]
            assert f.stat().st_size == part["size"]
            h = hashlib.sha256()
            with f.open("rb") as inp:
                for block in iter(lambda: inp.read(1024*1024), b""):
                    out.write(block)
                    h.update(block)
                    digest.update(block)
            assert h.hexdigest() == part["sha256"]
    assert path.stat().st_size == manifest["size"]
    assert digest.hexdigest() == manifest["sha256"]
    return tmp, path


def main():
    from web_v1_dropdown_catalog import bm_theme_options, bm_theme_identity, bm_unit_options, bm_topic_options, bm_pdp_options, _bm_verified_structured_rows
    tmp, path = database()
    try:
        with sqlite3.connect(path.resolve().as_uri()+"?mode=ro", uri=True) as con:
            assert con.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            schema = [r[1] for r in con.execute(
                "PRAGMA table_info(verified_pdp_sequence)")]
            print("BM SEQUENCE COLUMNS", schema, flush=True)
        for year in range(1, 7):
            rows = _bm_verified_structured_rows(path, year)
            choices = bm_theme_options(path, year)
            labels = [x["label"] for x in choices]
            stripped = Counter(re.sub(r"\s+", " ", t).casefold() for t in labels)
            by_text = defaultdict(list)
            for t in labels:
                clean = re.sub(r"^\s*(?:tema\s*)?\d+\s*[\.\-:)]*\s*",
                               "", t.strip(), flags=re.I)
                by_text[re.sub(r"\s+", " ", clean).casefold()].append(t)
            collisions = {k: v for k, v in by_text.items() if len(v) > 1}
            print("BM YEAR", year, "rows", len(rows), "themes", len(choices),
                  "exactdup", [k for k,v in stripped.items() if v>1],
                  "semanticdup", collisions, flush=True)
            assert len(set(bm_theme_identity(t) for t in labels)) == len(labels), (
                "Duplicate BM themes still displayed in Year " + str(year))
            # Release acceptance: real v26.00 has two spelling variants for
            # Perpaduan Year 2, two pairs of spellings Year 4, and two
            # legitimately DIFFERENT titles under Theme 1 Year 5.
            if year == 2:
                assert len(labels) == 4, labels
            elif year == 4:
                assert len(labels) == 5, labels
            elif year == 5:
                assert len(labels) == 5, labels
                assert len([t for t in labels if t.startswith("Tema 1:")]) == 2
            # Verify every listed canonical theme can navigate to a native
            # Unit, topic, and opaque grouped PdP without any writes.
            covered = 0
            for theme in labels:
                units = bm_unit_options(path, year, theme)
                assert units, ("Unit missing", year, theme)
                for item in units:
                    unit = item["value"]
                    topics = bm_topic_options(path, year, theme, unit)
                    assert topics, ("Topic missing", year, theme, unit)
                    for topic in topics:
                        pdps = bm_pdp_options(path, year, theme, unit, topic["value"])
                        assert pdps, ("PdP missing", year, theme, unit, topic["value"])
                        for pdp in pdps:
                            assert pdp["value"].startswith("b")
                            covered += 1
            print("BM NAVIGATION VERIFIED", year, "choices", covered, flush=True)
            print("BM THEMES",year,labels,flush=True)
            print("BM sample actual PdP", year,
                  [(r["theme"],r["unit_code"],r["unit_title"],r["topic"],
                    str(r.get("source_sequence_no") or ""))
                   for r in rows[:5]],flush=True)
    finally:
        tmp.cleanup()


if __name__ == "__main__":
    main()
