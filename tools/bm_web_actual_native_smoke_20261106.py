"""Offline native Word/PDF smoke for BM Web refinement with true v26.00 DB.

Rebuild only temporary verified master DB parts; no live Telegram, networking,
payment, user mutation, AI, or production database writes.
"""
import io
import os
import uuid
from pathlib import Path
from zipfile import ZipFile
from lxml import etree

from tools.bm_native_v26_navigation_audit import database
from web_v1_dropdown_catalog import _bm_verified_structured_rows, bm_sequence_token
from web.telegram_native_bm_sequence_rph_bridge import _state, _content
from web.bm_web_rph_refinement import install, _confirmed_families, _GENERIC_CUES


def main():
    os.environ["BOT_TOKEN"] = ""
    os.environ["GEMINI_API_KEY"] = ""
    tmp, db = database()
    paths = []
    try:
        os.environ["CIKGULAJU_DB_PATH"] = str(db)
        import requests

        def no_network(*_args, **_kwargs):
            raise AssertionError("Network access forbidden in offline BM smoke")

        requests.sessions.Session.request = no_network
        import app as runtime

        runtime.DB_PATH = str(db)
        runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        base_rows = runtime._rph_rows
        assert install(runtime)
        assert runtime._rph_rows is not base_rows

        cases = (
            (2, "Sahabat Karib", "Kenali Rakan"),
            (3, "Keluarga Cergas", "Suria Pagi"),
            (4, "Jiran Tetangga", "Program Kebun Komuniti"),
        )
        refined = 0
        for year, unit, topic in cases:
            candidates = [
                r for r in _bm_verified_structured_rows(db, year)
                if r["unit_title"] == unit and r["topic"] == topic
            ]
            assert candidates, ("BM PdP source missing", year, unit, topic)
            r = candidates[0]
            token = bm_sequence_token(
                year, r["theme"], r["unit_code"], r["unit_title"], r["topic"]
            )
            st = _state(runtime, year, unit, token, {
                "class": f"{year} Bestari", "date": "2026-11-06",
                "time": "08:00 - 09:00", "students": "30",
            })
            assert st["_bm_web_native_source"] == "verified_pdp_sequence"
            assert str(r["sp_code"]) in str(st["grouped_sp_codes"])
            text = _content(runtime, st)
            assert len(text.strip()) >= 500
            assert str(r["sp_code"]) in text
            import sqlite3
            with sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True) as con:
                cols = [x[1] for x in con.execute("PRAGMA table_info(curriculum_standards)")]
                print("BM curriculum_standards cols", cols, flush=True)
                for sr in st["_bm_web_verified_standards"]:
                    code = sr["sp_code"]
                    cols_needed = [c for c in ("sp_code", "sp_text", "sk_code", "year_label", "subject", "verified") if c in cols]
                    if cols_needed and "sp_code" in cols:
                        where = "sp_code=?" + (" AND year_label=?" if "year_label" in cols else "")
                        params = (code, f"Tahun {year}") if "year_label" in cols else (code,)
                        vals = con.execute("SELECT " + ",".join(cols_needed) + " FROM curriculum_standards WHERE "+where+" LIMIT 5",params).fetchall()
                        print("BM curriculum match", year, code, vals, flush=True)
            print("BM native source standards", st["_bm_web_verified_standards"], flush=True)
            old = base_rows(st, text)
            print("BM old main activity full", repr(str(old.get("AKTIVITI UTAMA") or "")[:1900]), flush=True)
            new = runtime._rph_rows(st, text)
            assert new["STANDARD PEMBELAJARAN"] == old["STANDARD PEMBELAJARAN"]
            assert new["STANDARD KANDUNGAN"] == old["STANDARD KANDUNGAN"]
            assert new.get("TAJUK") == old.get("TAJUK")
            source_generic = any(cue in str(old.get("AKTIVITI UTAMA") or "").casefold()
                                 for cue in _GENERIC_CUES)
            changed = old["AKTIVITI UTAMA"] != new["AKTIVITI UTAMA"]
            if source_generic and _confirmed_families(st):
                assert changed, ("Source-based BM activity not improved", year, topic)
                assert "Aktiviti 3" in new["AKTIVITI UTAMA"]
                assert "\n2. " in new["AKTIVITI UTAMA"]
                assert "\n3. " in new["AKTIVITI UTAMA"]
                refined += 1
            print("BM native row", year, unit, topic, "family",
                  _confirmed_families(st), "generic", source_generic,
                  "changed", changed, flush=True)

            tag = "bmsource" + uuid.uuid4().hex
            for fmt in ("word", "pdf"):
                path = Path(
                    runtime.create_word_file(st, text, tag)
                    if fmt == "word" else runtime.create_pdf_file(st, text, tag)
                )
                paths.append(path)
                assert path.is_file() and path.stat().st_size >= 1000
                b = path.read_bytes()
                if fmt == "word":
                    assert b.startswith(b"PK\x03\x04")
                    with ZipFile(io.BytesIO(b)) as archive:
                        assert archive.testzip() is None
                        root = etree.fromstring(archive.read("word/document.xml"))
                        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                        tables = list(root.iter(ns+"tbl"))
                        assert len(tables) == 3
                        if changed:
                            activity_cells = list(tables[1].iter(ns+"tc"))
                            assert any(len(list(c.iter(ns+"br"))) >= 3
                                       for c in activity_cells), "Numbered lines not physical Word breaks"
                else:
                    assert b.startswith(b"%PDF-")
                print("PASS BM genuine source RPH", year, fmt,
                      path.stat().st_size, flush=True)
        print("BM content refined in genuine source samples", refined, flush=True)
    finally:
        for p in paths:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
        tmp.cleanup()


if __name__ == "__main__":
    main()
