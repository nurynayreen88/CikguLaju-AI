"""Fail-closed geometry audit of 10 genuine native SK Word/PDF RPH downloads.

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
                        rows = runtime._rph_rows(state, source)
                        # Actual v26 code-only SK/SP must display verified
                        # DSKP/DPK wording in BOTH Word and PDF. This is
                        # presentation-only and cannot change source rows.
                        if code == "MATH" or year in (5, 6):
                            from web.rph_verified_standard_labels_20261124 import _VERIFIED
                            family = "Matematik" if code == "MATH" else "Sains"
                            sk, sk_label, sp, sp_label = _VERIFIED[family, year]
                            assert rows["STANDARD KANDUNGAN"] == f"{sk} {sk_label}", (
                                family, year, rows.get("STANDARD KANDUNGAN"))
                            assert f"{sp} {sp_label}" in rows["STANDARD PEMBELAJARAN"], (
                                family, year, rows.get("STANDARD PEMBELAJARAN"))
                            from web.rph_verified_standard_labels_20261124 import _EXTRA_SPS
                            for code_sp, label_sp in _EXTRA_SPS.get((family, year), {}).items():
                                assert f"{code_sp} {label_sp}" in rows["STANDARD PEMBELAJARAN"], (
                                    family, year, code_sp, rows.get("STANDARD PEMBELAJARAN"))
                        reflection = rows.get("REFLEKSI", "")
                        assert isinstance(reflection, str) and reflection.strip()
                        if code == "SCIENCE":
                            # Year2/4/5/6 use exact specific criteria;
                            # Year3 Asid/Alkali uses only verified SP 8.1.1.
                            # No objective/criterion source is rewritten.
                            if year in (2, 4, 5, 6):
                                assert "4/5 item" in reflection, (year, reflection)
                                assert "mencapai objektif" not in reflection, (year, reflection)
                                assert "____ / ____ murid" in reflection, (year, reflection)
                            else:
                                # Exact real Year 3 SP 8.1.1 Asid dan Alkali,
                                # not fabricated from generic KPS/konsep.
                                assert "menguji bahan berasid, beralkali" in reflection, (
                                    year, reflection
                                )
                                assert "kertas litmus (4/5 item)" in reflection, (
                                    year, reflection
                                )
                                assert "mencapai objektif" not in reflection, (
                                    year, reflection
                                )
                        unique = "native_header_" + uuid.uuid4().hex[:14]
                        word = Path(runtime.create_word_file(state, source, unique))
                        pdf = Path(runtime.create_pdf_file(state, source, unique+"p"))
                        doc = Document(str(word))
                        if code == "MATH" or year in (5, 6):
                            table_text = " ".join(cell.text for row in doc.tables[1].rows
                                                  for cell in row.cells)
                            assert sk_label in table_text and sp_label in table_text, (
                                family, year, "Word lost verified standard descriptions")
                        if code == "SCIENCE":
                            # Word must contain the exact same reflection
                            # returned from the active _rph_rows adapter.
                            assert doc.tables[-1].rows[-1].cells[1].text == reflection, (
                                year, "Word reflection differs from source-linked rows"
                            )
                        title_candidates = [(i,p.text) for i,p in enumerate(doc.paragraphs)
                                            if "RANCANGAN PENGAJARAN HARIAN" in p.text.casefold().upper()]
                        title_outside = bool(title_candidates)
                        tables = doc.tables
                        meta = []
                        if tables:
                            celltexts = [c.text for c in tables[0].rows[0].cells]
                            meta = [{"paragraphs":len(c.paragraphs), "text_head":c.text[:130],
                                     "tabs":[[(tab.position.twips if tab.position is not None else None) for tab in p.paragraph_format.tab_stops]
                                             for p in c.paragraphs[:5]]}
                                    for c in tables[0].rows[0].cells]
                        with fitz.open(str(pdf)) as pdf_doc:
                            page_count = len(pdf_doc)
                            pdf_title = bool(pdf_doc[0].search_for("RANCANGAN PENGAJARAN HARIAN"))
                            dimensions = (round(pdf_doc[0].rect.width), round(pdf_doc[0].rect.height))
                            if code == "MATH" or year in (5, 6):
                                pdf_text = " ".join(pdf_doc[0].get_text().split())
                                assert sk_label in pdf_text and sp_label in pdf_text, (
                                    family, year, "PDF lost verified standard descriptions")
                            if code == "SCIENCE":
                                extracted = " ".join(pdf_doc[0].get_text().split())
                                expected = " ".join(reflection.split())
                                assert expected in extracted, (
                                    year, "Native PDF reflection lacks source-specific text",
                                    expected, extracted[-240:],
                                )
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
                        last_error.append((type(exc).__name__, str(exc)[:150]))
                else:
                    if code == "MATH":
                        # Keep honest evidence of any independent Math routing
                        # or renderer failure; never substitute a fake lesson.
                        # Record the error and retain verified Science samples.
                        report.append({
                            "subject":code, "year":year, "status":"NOT_VERIFIED",
                            "reason":"native audit sample did not render",
                            "error_types":list(dict.fromkeys(t for t,_ in last_error)),
                            "error_sample":last_error[:1],
                        })
                        print("NATIVE_MATH_AUDIT_UNVERIFIED",year,last_error[:1],flush=True)
                        continue
                    raise AssertionError(("Cannot render native verified sample", code, year, last_error))
    finally:
        temp.cleanup()
    (outdir / "STRUCTURE_REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    assert len(report) == 10
    for item in report:
        # Fail closed for any real year that cannot render. Never substitute
        # a hard-coded dummy lesson to mask a curriculum routing failure.
        assert item.get("status") != "NOT_VERIFIED", item
        assert item.get("word_tables") == 4, (item["subject"], item["year"], "header")
        assert item.get("word_title_outside") is True, item
        assert item.get("pdf_pages") == 1, item
        assert item.get("pdf_has_title") is True, item
        assert list(item.get("pdf_dimensions") or []) == [595, 842], item
        panels = item.get("metadata_first_row") or []
        assert len(panels) == 2, item
        assert panels[0]["text_head"].startswith("Mata Pelajaran" + chr(9)), item
        assert panels[1]["text_head"].startswith("Kelas" + chr(9)), item
        assert panels[0]["tabs"] == [[2050], [2050], [2050]], item
        assert panels[1]["tabs"] == [[1430]] * 5, item
    print("NATIVE_SAINS_MATH_10_REAL_A4_FOUR_TABLE_HEADERS_VERIFIED")


if __name__=="__main__":
    main()
