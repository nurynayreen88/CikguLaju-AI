"""Offline RPH Word/PDF smoke using shipped immutable v26.00 Telegram DB.

No live bot token, no payment/credit calls and no network allowed. Loads the
actual production Telegram RPH engine in an ephemeral GitHub CI runner.
"""
import io
import os
import tempfile
import uuid
from pathlib import Path
from zipfile import ZipFile
from lxml import etree

from tools.bm_native_v26_navigation_audit import database
from web_v1_dropdown_catalog import _bm_verified_structured_rows, bm_sequence_token
from web.telegram_native_bm_sequence_rph_bridge import _state, _content


def main():
    os.environ["BOT_TOKEN"] = ""
    os.environ["GEMINI_API_KEY"] = ""
    temporary, db = database()
    paths = []
    try:
        os.environ["CIKGULAJU_DB_PATH"] = str(db)
        # Fail rather than accidentally contact a live bot, database or AI.
        import requests
        def no_network(*args, **kwargs):
            raise AssertionError("Network use forbidden in offline native RPH test")
        requests.sessions.Session.request = no_network
        import app as runtime

        # Set the reconstructed SHA-verified v26.00 source in this isolated CI.
        runtime.DB_PATH = str(db)
        runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        candidates = [
            (2, "Sahabat Karib", "Kenali Rakan"),
            (3, "Keluarga Cergas", "Suria Pagi"),
            (4, "Jiran Tetangga", "Program Kebun Komuniti"),
        ]
        for year, unit, topic in candidates:
            rows = [r for r in _bm_verified_structured_rows(db, year)
                    if r["unit_title"] == unit and r["topic"] == topic]
            assert rows, ("BM PdP not found in v26.00", year, unit, topic)
            r = rows[0]
            token = bm_sequence_token(year, r["theme"], r["unit_code"],
                                      r["unit_title"], r["topic"])
            state = _state(runtime, year, unit, token, {
                "class": f"{year} Bestari",
                "date": "2026-11-06",
                "time": "08:00 - 09:00",
                "students": "30",
            })
            assert str(r["sp_code"]) in str(state["grouped_sp_codes"])
            text = _content(runtime, state)
            assert len(text.strip()) >= 500
            assert str(r["sp_code"]) in text
            tag = "offlinebm" + uuid.uuid4().hex
            for fmt in ("word", "pdf"):
                out = (
                    runtime.create_word_file(state, text, tag)
                    if fmt == "word" else runtime.create_pdf_file(
                        state, text, tag)
                )
                path = Path(out)
                paths.append(path)
                assert path.is_file() and path.stat().st_size > 1000
                body = path.read_bytes()
                if fmt == "word":
                    assert body.startswith(b"PK\x03\x04")
                    with ZipFile(io.BytesIO(body)) as archive:
                        assert archive.testzip() is None
                        doc = etree.fromstring(archive.read("word/document.xml"))
                        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                        tables = list(doc.iter(ns + "tbl"))
                        assert len(tables) == 3, len(tables)
                else:
                    assert body.startswith(b"%PDF-")
                print("PASS BM true v26 native",year,unit,topic,fmt,
                      "bytes",len(body),"SPs",len(state["grouped_sp_codes"]),
                      flush=True)
    finally:
        for path in paths:
            try: path.unlink(missing_ok=True)
            except OSError: pass
        temporary.cleanup()


if __name__ == "__main__":
    main()
