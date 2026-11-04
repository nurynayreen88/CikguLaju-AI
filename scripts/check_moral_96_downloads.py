#!/usr/bin/env python3
"""QA for full Moral 96-session RPT and 54 supplementary RPH downloads."""
from __future__ import annotations

import sys
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pypdf import PdfReader
from docx import Document
from rpt_2027.pendidikan_moral.complete_96_downloads import (
    source_rows, pdf_ready, rph_ready, build_rpt_pdf,
    build_rph_pdf, build_rph_docx, install,
    RPT_PREFIX, RPH_PDF_PREFIX, RPH_DOCX_PREFIX,
)

FORBIDDEN = ("DRAF", "BELUM READY", "SEMAKAN GURU", "CADANGAN CIKGULAJU")


def assert_no_internal_labels(s, ctx):
    assert not any(flag in str(s).upper() for flag in FORBIDDEN), ctx


def test_all_sources():
    for year in range(2, 7):
        assert pdf_ready(year, "A") and pdf_ready(year, "B")
        assert rph_ready(year)
        for group in ("A", "B"):
            rows = source_rows(year, group)
            assert len(rows) == 96, (year, group)
            assert [x["Sesi"] for x in rows] == [f"{n:03d}" for n in range(1, 97)]
            assert sum(x["Modul"] == "TERAS" for x in rows) == 42
            assert sum(x["Modul"] == "PENGUKUHAN" for x in rows) == 54
            assert all(x["Minggu_RPT"].startswith("M") for x in rows)
    assert not pdf_ready(1, "A") and not pdf_ready(6, "C")
    assert source_rows(9, "A") == [] and not rph_ready(7)
    print("PASS Moral 96 source selection: 5 years x 2 groups")


def test_rendered_pdfs_and_word():
    for year in range(2, 7):
        with TemporaryDirectory(prefix="moral96_qa_") as d:
            root = Path(d)
            for group in ("A", "B"):
                pdf = build_rpt_pdf(year, group, root/f"RPT_{group}.pdf")
                reader = PdfReader(pdf)
                assert len(reader.pages) == 14, (year, group, len(reader.pages))
                first = reader.pages[0].extract_text()
                assert "PENDIDIKAN MORAL" in first and "96 SESI" in first
                assert "KUMPULAN " + group in first
                assert_no_internal_labels(first, (year, group, "RPT header"))
                assert "096" in reader.pages[-1].extract_text(), (year, group)
            rph_pdf = build_rph_pdf(year, root/"RPH_54.pdf")
            pages = PdfReader(rph_pdf).pages
            assert len(pages) == 54, (year, "rph pdf pages", len(pages))
            for page_no in (0, 1, 26, 53):
                text = pages[page_no].extract_text()
                assert "PENDIDIKAN MORAL" in text
                assert_no_internal_labels(text, (year, "rph pdf", page_no))
                assert all(x in text for x in ("Aktiviti 1", "Aktiviti 2", "Penutup"))
            docx_path = build_rph_docx(year, root/"RPH_54.docx")
            dfile = Document(docx_path)
            titles = [p.text for p in dfile.paragraphs if
                      "RPH PENDIDIKAN MORAL TAHUN" in p.text]
            assert len(titles) == 54, (year, "docx RPH headings", len(titles))
            assert all("SESI" in t for t in titles)
            assert_no_internal_labels(" ".join(p.text for p in dfile.paragraphs),
                                      (year, "Word labels"))
        print("PASS Moral year %s: 2 RPT PDFs, 54 RPH PDF pages, 54 editable Word RPH" % year)


def test_callback_security_and_isolation():
    captured = []
    def original(cid, data):
        captured.append(("original", cid, data))
        return "original"
    def send(cid, body, *args):
        captured.append(("send", cid, body))
        return "blocked"
    def send_document(cid, path, caption):
        file = Path(path)
        assert file.exists() and file.stat().st_size > 4000
        captured.append(("document", cid, file.suffix, caption))
        return SimpleNamespace(ok=True)
    ns = {
        "callback": original,
        "send": send,
        "send_document": send_document,
        "_access_info": lambda cid: {"active": cid == 2},
        "_is_admin": lambda cid: cid == 1,
        "_telegram_delivery_ok_v25279": lambda result: bool(result.ok),
    }
    assert install(ns) and install(ns)
    assert ns["callback"](2, "rpt2027_en_pdf_2") == "original"
    assert captured[-1][0] == "original"
    ns["callback"](3, RPT_PREFIX + "a_2")
    assert captured[-1][0] == "send", "Unpaid user not blocked"
    ns["callback"](3, RPH_PDF_PREFIX + "2")
    assert captured[-1][0] == "send", "Unpaid RPH package not blocked"
    ns["callback"](2, RPT_PREFIX + "x_2")
    assert captured[-1][0] == "send", "Invalid group allowed"
    ns["callback"](2, RPH_DOCX_PREFIX + "99")
    assert captured[-1][0] == "send", "Invalid year allowed"
    for action in (RPT_PREFIX + "a_2", RPT_PREFIX + "b_2",
                   RPH_PDF_PREFIX + "2", RPH_DOCX_PREFIX + "2"):
        ns["callback"](2, action)
        assert captured[-1][0] == "document", (action, captured[-1])
        assert_no_internal_labels(captured[-1][-1], action)
    assert captured[-1][2] == ".docx"
    print("PASS paid callbacks, malformed/stale callbacks, and other-subject forwarding")


if __name__ == "__main__":
    test_all_sources()
    test_rendered_pdfs_and_word()
    test_callback_security_and_isolation()
    print("MORAL 96 COMPLETE-DOWNLOAD QA PASS")
