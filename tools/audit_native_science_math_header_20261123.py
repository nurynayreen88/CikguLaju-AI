"""Read-only geometry audit of 10 genuine native SK Word/PDF RPH downloads.

Maths and Science run through Telegram's verified grouped PdP sequence, NOT
the archive and not the DLP/PPKI renderer. Never modify source DB/credits or
deploy a new generator as part of this audit.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory
import json
import sqlite3
import uuid

from tools.bm_native_v26_navigation_audit import database
from web.telegram_verified_sequence_rph_bridge import (
    _source, _unit_catalog, _available_groups, _build_state, _source_text
)


def main():
    from tools import run_telegram_with_curriculum_api as live
    import fitz
    from docx import Document
    from docx.oxml.ns import qn
    runtime = live.telegram_runtime
    temp, path = database()
    outdir = Path("qa/native-sains-math-header")
    outdir.mkdir(parents=True, exist_ok=True)
    report = []
    try:
        runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        runtime.DB_PATH = str(path)
        for code in ("SCIENCE", "MATH"):
            for year in range(2, 7):
                rowset, units = _source(runtime, year, code)
                catalog = _unit_catalog(units)
                candidates = []
                for unit in catalog:
                    groups = _available_groups(rowset, unit, year, code)
                    for lesson in groups:
                        candidates.append((unit, lesson))
                assert candidates, ("No real verified native source", code, year)
                last_error = []
                for unit, lesson in candidates[:12]:
                    try:
                        state = _build_state(runtime, year, code, unit["value"], lesson, {
                            "class":"", "date":"", "time":"", "students":"", "reflection":""
                        })
                        source = _source_text(runtime, state)
                        unique = "native_header_" + uuid.uuid4().hex[:14]
                        word = Path(runtime.create_word_file(state, source, unique))
                        pdf = Path(runtime.create_pdf_file(state, source, unique+"p"))
                        doc = Document(str(word))
                        title_candidates = [(i,p.text) for i,p in enumerate(doc.paragraphs)
                                            if "RANCANGAN PENGAJARAN HARIAN" in p.text.casefold().upper()]
                        title_outside = bool(title_candidates)
                        tables = doc.tables
                        meta = []
                        if tables:
                            celltexts = [c.text for c in tables[0].rows[0].cells]
                            meta = [{"paragraphs":len(c.paragraphs), "text_head":c.text[:130],
                                     "tabs":[[(tab.pos.twips if tab.pos else None) for tab in p.paragraph_format.tab_stops]
                                             for p in c.paragraphs[:5]]}
                                    for c in tables[0].rows[0].cells]
                        with fitz.open(str(pdf)) as pdf_doc:
                            page_count = len(pdf_doc)
                            pdf_title = bool(pdf_doc[0].search_for("RANCANGAN PENGAJARAN HARIAN"))
                            dimensions = (round(pdf_doc[0].rect.width), round(pdf_doc[0].rect.height))
                        basename = f"{code}_YEAR{year}"
                        copy2(word, outdir / f"{basename}.docx")
                        copy2(pdf, outdir / f"{basename}.pdf")
                        entry = {
                            "subject":code, "year":year, "selected_pdp":lesson,
                            "word_pages_not_assessed": True,
                            "pdf_pages":page_count, "pdf_dimensions":dimensions,
                            "word_tables":len(tables),
                            "word_title_outside":title_outside,
                            "word_title_paragraphs":title_candidates[:2],
                            "metadata_first_row":meta,
                            "pdf_has_title":pdf_title,
                            "source_chars":len(source),
                            "word_size":word.stat().st_size,
                            "pdf_size":pdf.stat().st_size,
                        }
                        report.append(entry)
                        print("NATIVE_REAL_HEADER",json.dumps({
                            k:v for k,v in entry.items()
                            if k not in ("metadata_first_row","word_title_paragraphs")},
                            ensure_ascii=False))
                        word.unlink(missing_ok=True)
                        pdf.unlink(missing_ok=True)
                        break
                    except Exception as exc:
                        last_error.append(type(exc).__name__)
                else:
                    raise AssertionError(("Cannot render native verified sample", code, year, last_error))
    finally:
        temp.cleanup()
    (outdir / "STRUCTURE_REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    assert len(report)==10
    print("NATIVE_10_REAL_YEAR_SAMPLES_AUDITED",len(report))


if __name__=="__main__":
    main()
