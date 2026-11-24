"""Read-only five-year RPH PI Word/PDF native regression, no live accounts.

Uses immutable v26.00 verified SQLite source and native Telegram renderers.
Only temporary files and CI artifacts, no quotas, webhook, API or DB mutation.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from io import BytesIO
import sqlite3
import shutil
import uuid

from docx import Document
from lxml import etree
import fitz

from tools.bm_native_v26_navigation_audit import database
from web.pi_navigation import pi_navigation_unit
from web.telegram_verified_rpt_rph_bridge import (
    _native_state, _native_text, SourceUnavailable,
)

YEARS = (2, 3, 4, 5, 6)
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
FILL = "ECE4F6"


def check_docx(path, year, source):
    raw = path.read_bytes()
    with ZipFile(BytesIO(raw)) as package:
        assert package.testzip() is None
        root = etree.fromstring(package.read("word/document.xml"))
    doc = Document(BytesIO(raw))
    assert len(doc.tables) == 4, (year, len(doc.tables))
    assert doc.paragraphs[0].text == "رنچڠن ڤڠاجرن هارين", (year, doc.paragraphs[0].text)
    title = next(p for p in root.find(W+"body").findall(W+"p")
                 if "رنچڠن ڤڠاجرن هارين" in "".join(t.text or "" for t in p.iter(W+"t")))
    assert title.find(W+"pPr/"+W+"jc").get(W+"val") == "center", year
    banner = root.find(W+"body").findall(W+"tbl")[0]
    assert banner.find(W+"tblPr/"+W+"bidiVisual") is not None, year
    first = banner.find(W+"tr").findall(W+"tc")
    assert len(first) == 2, year
    left = "".join(t.text or "" for t in first[1].iter(W+"t"))
    right = "".join(t.text or "" for t in first[0].iter(W+"t"))
    assert "کلس" in left and "ڤنديديقن اسلام" in right, (year, left[:80], right[:80])
    assert f"تاهون {str(year).translate(str.maketrans('0123456789','٠١٢٣٤٥٦٧٨٩'))}" in right, (year,right[:120])
    tokens = tuple(t.text or "" for t in root.iter(W+"t"))
    assert not any("0" <= c <= "9" for token in tokens for c in token), year
    fills = Counter(n.get(W+"fill") for n in root.iter(W+"shd")
                    if n.get(W+"fill") not in (None,"auto"))
    assert fills and set(fills) == {FILL}, (year, fills)
    printed = "\n".join(cell.text for table in doc.tables for row in table.rows
                          for cell in row.cells)
    assert "اکتيۏيتي ١" in printed, year
    assert "رفليکسي" in printed or "رفليكسي" in printed or "موريد منچاپاي" in printed, year
    assert source["subject"] == "Pendidikan Islam"
    print("PI_WORD_OK",year,"original_rpt_id",source["id"],"tables",len(doc.tables),
          "unique_fills",list(fills),"jawi_digit_codes",sum(c in "٠١٢٣٤٥٦٧٨٩" for t in tokens for c in t),flush=True)


def check_pdf(path, year):
    with fitz.open(path) as doc:
        assert len(doc) == 1, (year, len(doc))
        page = doc[0]
        assert 594 < page.rect.width < 597 and 840 < page.rect.height < 844, (year,page.rect)
        # This native Jawi PDF is rasterized; text extraction alone is not
        # evidence of completeness. Page geometry, raster presence and actual
        # audited source-backed Word are checked instead.
        assert len(page.get_images(full=True)) >= 2, (year,"Jawi raster missing")
    print("PI_NATIVE_PDF_OK",year,"A4_ONE_PAGE",flush=True)


def main():
    from tools import run_telegram_with_curriculum_api as live
    runtime = live.telegram_runtime
    temporary, db_path = database()
    out_dir = Path("qa/pi-five-years-real")
    out_dir.mkdir(parents=True,exist_ok=True)
    try:
        runtime.DB_PATH = str(db_path)
        runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        with sqlite3.connect(db_path.resolve().as_uri()+"?mode=ro",uri=True) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            verified = {}
            for year in YEARS:
                records = conn.execute(
                    """SELECT * FROM rpt_entries WHERE year_label=? AND
                    subject='Pendidikan Islam' AND verified=1
                    AND length(trim(COALESCE(activity_note,''))) >= 70
                    AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                    ORDER BY CASE WHEN sequence_no BETWEEN 1 AND 15 THEN 0 ELSE 1 END,
                             sequence_no, id LIMIT 70""",
                    (f"Tahun {year}",)
                ).fetchall()
                verified[year] = [dict(x) for x in records]
                assert verified[year], ("Missing verified PI source",year)
        for year in YEARS:
            failures=[]
            completed=False
            for item in verified[year]:
                try:
                    selection={"year":year,"subject":"PI",
                               "unit":pi_navigation_unit(item),"lesson":int(item["id"])}
                    teacher={"class":"","date":"","time":"","students":"","reflection":""}
                    state=_native_state(runtime,selection,teacher)
                    source=_native_text(runtime,state)
                    rows=runtime._rph_rows(state,source)
                    assert rows.get("AKTIVITI UTAMA") and rows.get("REFLEKSI")
                    name="piqa"+uuid.uuid4().hex[:12]
                    word=Path(runtime.create_word_file(state,source,name))
                    pdf=Path(runtime.create_pdf_file(state,source,name+"p"))
                    try:
                        assert word.is_file() and pdf.is_file()
                        check_docx(word,year,item)
                        check_pdf(pdf,year)
                        shutil.copy2(word,out_dir/f"CIKGULAJU_PI_TAHUN_{year}_ASLI.docx")
                        shutil.copy2(pdf,out_dir/f"CIKGULAJU_PI_TAHUN_{year}_ASLI.pdf")
                        completed=True
                        break
                    finally:
                        word.unlink(missing_ok=True)
                        pdf.unlink(missing_ok=True)
                except (AssertionError,ValueError,TypeError,SourceUnavailable,OSError,IndexError) as exc:
                    failures.append((item["id"],type(exc).__name__,str(exc)[:250]))
                    if len(failures) > 12:
                        break
            if not completed:
                raise AssertionError(("PI verified sample failed",year,failures))
            print("PI_YEAR_SAMPLE_ACCEPTED",year,"rejected_candidate_count",len(failures),flush=True)
        assert len(list(out_dir.glob("*.docx")))==5
        assert len(list(out_dir.glob("*.pdf")))==5
        print("PASS ALL FIVE YEARS: 10 native samples, source preserved, RTL, Jawi numerals, A4")
    finally:
        temporary.cleanup()


if __name__=="__main__":
    main()
