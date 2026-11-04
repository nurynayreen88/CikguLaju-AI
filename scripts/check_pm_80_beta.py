#!/usr/bin/env python3
"""Moral 80% beta release gate; offline source-backed RPH and paid PDF routes."""
from __future__ import annotations
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web.pendidikan_moral_80_runtime import load_candidate, adapt_rows, install as install_rows
from rpt_2027.pendidikan_moral.telegram_downloads import (
    source_rows, pdf_ready, build_pdf, install as install_download,
)

FAILS = []


def assert_true(ok, reason):
    if not ok:
        FAILS.append(reason)


def test_lessons():
    total = 0
    for year in range(2, 7):
        for number in range(1, 43):
            item = load_candidate(year, number)
            if item is None:
                FAILS.append("Moral Tahun %d PdP %03d rejected by source parser" % (year, number))
                continue
            assert_true(item["year"] == year and item["number"] == number,
                        "wrong source lesson number")
            sample = {"subject": "Pendidikan Moral", "year": "Tahun %d" % year,
                      "lesson_no": str(number), "sp_code": item["sp"][0],
                      "sk_code": item["sk"]}
            original = {"SENTINEL": "preserved", "TAJUK": "ORIGINAL"}
            result = adapt_rows(sample, original)
            assert_true(result is not original and result.get("SENTINEL") == "preserved",
                        "RPH beta row not updated or base overwritten")
            for key in ("TAJUK", "STANDARD PEMBELAJARAN", "OBJEKTIF PEMBELAJARAN",
                        "KRITERIA KEJAYAAN", "SET INDUKSI", "AKTIVITI UTAMA",
                        "PENTAKSIRAN", "PENUTUP", "BAHAN BANTU MENGAJAR"):
                assert_true(bool(str(result.get(key, "")).strip()),
                            "Year%d L%03d missing field %s" % (year, number, key))
            assert_true("CADANGAN CIKGULAJU" in result.get("TAJUK", ""),
                        "provisional label was removed")
            assert_true(adapt_rows(dict(sample, subject="English"), original) is original,
                        "English source unexpectedly modified")
            assert_true(adapt_rows(dict(sample, year="Tahun 1"), original) is original,
                        "Year1 source unexpectedly modified")
            assert_true(adapt_rows(dict(sample, sp_code="99.9"), original) is original,
                        "mismatched SP unexpectedly modified")
            total += 1
        assert_true(len(source_rows(year)) == 42,
                    "Year%d RPT source rows incomplete" % year)
        assert_true(pdf_ready(year), "Year%d RPT cannot be rendered" % year)
    assert_true(total == 210, "not all 210 RPH were accepted by adapter")
    assert_true(load_candidate(1, 1) is None and load_candidate(2, 43) is None,
                "unexpected extra Moral grade/lesson")
    print("Source-backed Moral RPH candidates:", total)


def test_runtime_install():
    calls = []
    def original(state, *a, **kw):
        calls.append(state)
        return {"ORIGINAL": True}
    runtime = SimpleNamespace(_rph_rows=original)
    assert_true(install_rows(runtime), "RPH install failed")
    assert_true(install_rows(runtime), "RPH install not idempotent")
    matched = runtime._rph_rows({"subject": "Pendidikan Moral", "year": "Tahun 2",
                                 "lesson_no": "1", "sp_code": "1.1"})
    assert_true("AKTIVITI UTAMA" in matched and matched["ORIGINAL"] is True,
                "RPH runtime did not preserve base row")
    unmodified = runtime._rph_rows({"subject": "Bahasa Melayu", "year": "Tahun 2",
                                    "lesson_no": "1"})
    assert_true(unmodified == {"ORIGINAL": True}, "other subject overwritten")
    assert_true(len(calls) == 2, "underlying generator bypassed")
    os.environ["CIKGULAJU_MORAL_80_ENABLED"] = "0"
    try:
        inactive = SimpleNamespace(_rph_rows=original)
        assert_true(install_rows(inactive) is False and inactive._rph_rows is original,
                    "emergency feature-off switch failed")
    finally:
        os.environ.pop("CIKGULAJU_MORAL_80_ENABLED", None)


def test_pdf_callback():
    try:
        from pypdf import PdfReader
    except ImportError:
        FAILS.append("pypdf required for beta PDF verification")
        return
    from rpt_2027.pendidikan_moral.telegram_downloads import PREFIX
    sent = []
    def sender(cid, *a):
        sent.append(("send", cid, a))
        return "message"
    class Delivered:
        ok = True
        @staticmethod
        def json():
            return {"ok": True}
    def document(cid, path, caption):
        p = Path(path)
        assert_true(p.exists() and p.read_bytes().startswith(b"%PDF-"),
                    "no valid PDF at send time")
        pdf = PdfReader(path)
        assert_true(len(pdf.pages) >= 5, "RPT PDF has too few pages")
        first = pdf.pages[0].extract_text()
        assert_true("PENDIDIKAN MORAL" in first and "CADANGAN" in first,
                    "missing PDF subject/draft label")
        sent.append(("document", cid, caption))
        return Delivered()
    def previous(cid, value):
        sent.append(("previous", cid, value))
        return "previous"
    ns = {"callback": previous, "send": sender, "send_document": document,
          "_is_admin": lambda cid: cid == 1,
          "_access_info": lambda cid: {"active": cid == 2},
          "_telegram_delivery_ok_v25279": lambda result: result.ok}
    assert_true(install_download(ns), "PDF callback install failed")
    assert_true(install_download(ns), "PDF callback install not idempotent")
    ns["callback"](3, PREFIX + "2")
    assert_true(sent[-1][0] == "send", "locked user was not denied")
    ns["callback"](2, PREFIX + "9")
    assert_true(sent[-1][0] == "send", "invalid year was not denied")
    ns["callback"](1, "home")
    assert_true(sent[-1][0] == "previous", "unrelated callback was intercepted")
    for year in range(2, 7):
        ns["callback"](2, PREFIX + str(year))
        assert_true(sent[-1][0] == "document" and "Tahun %d" % year in sent[-1][2],
                    "Year%d paid RPT callback failed" % year)
    print("RPT PDF callbacks delivered for five years in offline mock")


if __name__ == "__main__":
    test_lessons()
    test_runtime_install()
    test_pdf_callback()
    for issue in FAILS[:50]:
        print("FAIL:", issue)
    if len(FAILS) > 50:
        print("...%d more" % (len(FAILS) - 50))
    print("MORAL 80 BETA GATE:", "PASS" if not FAILS else "FAIL", len(FAILS), "issues")
    raise SystemExit(bool(FAILS))
