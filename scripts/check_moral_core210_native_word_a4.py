#!/usr/bin/env python3
"""Read-only physical A4 layout diagnostic for 210 Moral core RPH.

Uses active app.py Word table function AST-verified snapshot, plus the real
Moral source-to-row adapter. This is an offline approximation; no credentials,
credit balance or actual Telegram document delivery are used.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from docx.shared import Cm, Pt
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_english_rph_word_a4_layout import validate_word_function_snapshot
from qa.english_word_builder_snapshot import _create_rph_word
from web.pendidikan_moral_80_runtime import adapt_rows, load_candidate


def make_word(year: int, number: int, out: Path) -> None:
    candidate = load_candidate(year, number)
    assert candidate is not None, (year, number, "unavailable moral core RPH source")
    state = {"subject": "Pendidikan Moral", "year": f"Tahun {year}", "lesson_no": str(number)}
    base = {
        "MATA PELAJARAN": "Pendidikan Moral",
        "TAHUN/TINGKATAN": f"Tahun {year}",
        "TARIKH": "05/11/2026",
        "HARI": "Khamis",
        "MASA": "08:00 - 09:00",
        "KELAS": f"{year} Amanah",
        "BILANGAN MURID": "30",
        "PENGETAHUAN SEDIA ADA": "Murid mengenali amalan nilai moral dalam situasi harian.",
        "KBAT / PAK21": "Menaakul, berbincang dan memberi justifikasi.",
        "PEMULIHAN / PENGAYAAN": "Bimbingan kad kata kunci; murid maju menjelaskan sebab tambahan.",
        "REFLEKSI": "____/____ murid menguasai objektif; tindakan susulan: __________.",
    }
    rows = adapt_rows(state, base)
    assert rows is not base and rows.get("TAJUK") == candidate["title"], (year, number, "adapter failed")
    for key in ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP",
                "OBJEKTIF PEMBELAJARAN", "KRITERIA KEJAYAAN", "STANDARD PEMBELAJARAN"):
        assert rows.get(key), (year, number, key)
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(1.35); sec.bottom_margin = Cm(1.4)
    sec.left_margin = Cm(1.55); sec.right_margin = Cm(1.55)
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(10.5)
    _create_rph_word(doc, sec, state, rows, str(out))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", required=True)
    args = p.parse_args()
    out = Path(args.outdir).resolve()
    docx_dir = out / "docx"; pdf_dir = out / "pdf"
    docx_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    validate_word_function_snapshot()
    records = []
    for year in range(2, 7):
        for n in range(1, 43):
            path = docx_dir / f"Moral_Y{year}_PDP{n:03d}.docx"
            make_word(year, n, path)
            records.append((year, n, path))
    with TemporaryDirectory(prefix="moral_core_lo_") as tmp:
        profile = (Path(tmp)/"profile").resolve().as_uri()
        for start in range(0, len(records), 20):
            files = [str(r[2]) for r in records[start:start+20]]
            cmd = ["libreoffice", f"-env:UserInstallation={profile}", "--headless",
                   "--convert-to", "pdf", "--outdir", str(pdf_dir), *files]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)
            if result.returncode:
                raise RuntimeError("LibreOffice failed: " + result.stderr[-800:])
    outcomes = []
    for year, n, path in records:
        pdf = pdf_dir / (path.stem + ".pdf")
        if not pdf.exists():
            raise AssertionError(f"Unrendered {path.name}")
        pages = PdfReader(pdf).pages
        a4 = all(abs(float(page.mediabox.width)-595.28)<1 and abs(float(page.mediabox.height)-841.89)<1 for page in pages)
        text = " ".join((pages[0].extract_text() or "").split()).upper()
        required = all(k in text for k in ("PENDIDIKAN MORAL", "AKTIVITI", "PENUTUP"))
        outcomes.append({"year":year,"lesson":n,"pages":len(pages),"a4":a4,"required_text":required})
    totals = Counter(x["pages"] for x in outcomes)
    issues = [x for x in outcomes if x["pages"] != 1 or not x["a4"] or not x["required_text"]]
    report = {
        "result":"PASS" if not issues else "NOT_ONE_PAGE",
        "total":len(outcomes),"one_page":sum(x["pages"]==1 and x["a4"] and x["required_text"] for x in outcomes),
        "page_count_distribution":dict(totals),"issues":issues,
        "scope":"AST-verified active app.py Word table snapshot + actual Moral adapter; offline test; not live Telegram teacher delivery",
    }
    (out/"moral_core210_word_a4_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if issues:
        raise SystemExit(1)


if __name__=="__main__":
    main()
