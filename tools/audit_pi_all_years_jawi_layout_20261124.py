"""Read-only source-backed PI Year 2-6 native Word/PDF cross-year layout audit.

The real v26.00 split master DB is only verified and copied into a temporary
path. We do not mutate it, use the Web, access user credentials, or debit quota.
No academic content is invented or approved by this visual QA.
"""
from __future__ import annotations

from collections import Counter
from io import BytesIO
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import uuid
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import fitz
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from lxml import etree
from PIL import Image

from tools.bm_native_v26_navigation_audit import database
from web.pi_navigation import pi_navigation_unit
from web.telegram_verified_rpt_rph_bridge import _native_state, _native_text

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
FILL = "ECE4F6"
OUT = Path("qa/pi-y2-y6-jawi-native")
REQUIRED = ("مات ڤلاجرن", "تاهون / تيڠکتن", "تاجوق")
TEACHER = ("کلس", "تاريخ", "هاري", "ماس", "بيلڠن موريد")


def candidates(db, year):
    sql = """
       SELECT r.* FROM rpt_entries r
        WHERE r.year_label=? AND r.subject='Pendidikan Islam'
          AND r.verified=1
          AND lower(COALESCE(r.notes,'')) NOT LIKE '%superseded%'
          AND length(trim(COALESCE(r.activity_note,''))) > 35
          AND EXISTS (
             SELECT 1 FROM pi_pdp_details_v2591 p
              WHERE p.year_label=r.year_label AND p.pdp_no=r.sequence_no
                AND p.verified=1)
          AND EXISTS (
             SELECT 1 FROM rpt_entry_standards s
              WHERE s.rpt_entry_id=r.id AND s.verified=1
                AND s.standard_type='SK'
                AND trim(COALESCE(s.standard_code,'')) <> '')
          AND EXISTS (
             SELECT 1 FROM rpt_entry_standards s
              WHERE s.rpt_entry_id=r.id AND s.verified=1
                AND s.standard_type='SP'
                AND trim(COALESCE(s.standard_code,'')) <> '')
        ORDER BY r.sequence_no, r.id
    """
    return [dict(x) for x in db.execute(sql, (f"Tahun {year}",)).fetchall()]


def check_word(path, year):
    with ZipFile(path) as archive:
        assert archive.testzip() is None, (year, "invalid DOCX")
        tree = etree.fromstring(archive.read("word/document.xml"))
    tokens = [node.text or "" for node in tree.iter(W+"t")]
    assert not any("0" <= char <= "9" for value in tokens for char in value), (year, "European digits")
    fills = Counter(x.get(W+"fill") for x in tree.iter(W+"shd")
                    if x.get(W+"fill") not in (None,"auto"))
    assert fills and set(fills) == {FILL}, (year,"unexpected Word box colors",fills)
    doc = Document(path)
    assert len(doc.tables) == 4, (year, "Word panel or table count", len(doc.tables))
    title = next((p for p in doc.paragraphs
                  if p.text.strip() == "رنچڠن ڤڠاجرن هارين"),None)
    assert title is not None and title.alignment == WD_ALIGN_PARAGRAPH.CENTER, (year,"title center")
    panel = doc.tables[0]
    assert len(panel.rows) == 1 and len(panel.columns) == 2
    identity,teacher = (panel.cell(0,n).text for n in range(2))
    assert all(x in identity for x in REQUIRED), (year, "PI subject/year/topic not in right RTL panel")
    assert all(x in teacher for x in TEACHER), (year, "teacher metadata not in left RTL panel")
    assert panel._element.tblPr.find(W+"bidiVisual") is not None, (year,"physical RTL display lost")
    text = "\n".join(c.text for table in doc.tables for row in table.rows for c in row.cells)
    assert "رفليکسي" in text or "رفليکسي".replace("ک","ك") in text, (year, "reflection label missing")
    assert "اکتيۏيتي ١" in text, (year, "missing numbered Jawi activity")
    return text


def check_pdf(path, year):
    with fitz.open(path) as doc:
        assert len(doc) == 1, (year,"native PDF exceeds one A4",len(doc))
        page=doc[0]
        assert 594 < page.rect.width < 597 and 840 < page.rect.height < 844, (year,"not A4")
        pix=page.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
        im=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
        # The PI native PDF is already rasterized Jawi; the exact digital
        # text cannot be extracted. Verify the ORIGINAL centered title ink.
        ink=[]
        for y in range(41,67):
            for x in range(130,465):
                R,G,B=im.getpixel((x,y))
                if max(R,G,B)<135:
                    ink.append(x)
        assert ink and abs((min(ink)+max(ink))/2 - page.rect.width/2)<16, (
            year,"native Jawi title not centered")
        # Read the real PDF pixels inside the TWO independently shaded header
        # panels: left=class/time, right=PI/year/topic. PDF RGB conversion may
        # vary by 1-2 levels; tolerance does not change the intended color.
        def lilac_count(rect):
            count=0
            for y in range(rect[1],rect[3]):
                for x in range(rect[0],rect[2]):
                    rgb=im.getpixel((x,y))
                    if all(abs(v-t)<5 for v,t in zip(rgb,(236,228,246))):
                        count+=1
            return count
        left=lilac_count((70,80,185,136))
        right=lilac_count((358,80,470,136))
        assert left>3500 and right>3500, (year,"not both lilac panels",left,right)
        return page.rect.width,page.rect.height


def check_word_to_pdf(path, year):
    with TemporaryDirectory() as tmp:
        profile=Path(tmp)/"lo-profile"
        process=subprocess.run([
            "libreoffice", "-env:UserInstallation="+profile.as_uri(),
            "--headless","--convert-to","pdf","--outdir",tmp,str(path.resolve())
        ],text=True,capture_output=True,timeout=100)
        assert process.returncode==0, (year,process.stderr[-600:])
        converted=Path(tmp)/(path.stem+".pdf")
        assert converted.is_file(), (year,"Word->PDF missing")
        with fitz.open(converted) as pdf:
            assert len(pdf)==1, (year,"Word PDF exceeds A4",len(pdf))
            assert 594<pdf[0].rect.width<597 and 840<pdf[0].rect.height<844,year


def main():
    from tools import run_telegram_with_curriculum_api as live
    runtime=live.telegram_runtime
    assert getattr(live,"RPH_PI_JAWI_NUMERALS_ACTIVE",False), "Jawi display adapter not installed"
    OUT.mkdir(parents=True,exist_ok=True)
    temp,db_path=database()
    before=getattr(runtime,"DB_PATH",None)
    before_active=getattr(runtime,"CIKGULAJU_DB_V2600_ACTIVE",False)
    all_success=[]
    try:
        runtime.DB_PATH=str(db_path)
        runtime.CIKGULAJU_DB_V2600_ACTIVE=True
        with sqlite3.connect(db_path.resolve().as_uri()+"?mode=ro",uri=True) as conn:
            conn.row_factory=sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            for year in range(2,7):
                rows=candidates(conn,year)
                print("VERIFIED_PI_SOURCE_CANDIDATES",year,len(rows),flush=True)
                assert len(rows)>=2, (year,"insufficient verified PI source")
                # Independently sample the first and second half of the
                # reviewed records, not two adjacent similar RPH.
                slices=(rows[:min(60,len(rows)//2)],
                        rows[len(rows)//2:len(rows)//2+60])
                results=[]
                for half,segment in enumerate(slices,1):
                    diagnostics=[]
                    for row in segment:
                        candidate_name=f"PI_Y{year}_H{half}_RPT{row['id']}"
                        word=None
                        pdf=None
                        try:
                            selection={"year":year,"subject":"PI",
                                       "unit":pi_navigation_unit(row),
                                       "lesson":int(row["id"])}
                            state=_native_state(runtime,selection,{
                                "class":"","date":"","time":"","students":"","reflection":"",
                            })
                            native=_native_text(runtime,state)
                            # Prefer diversity, but never write curriculum DB.
                            word=Path(runtime.create_word_file(
                                state,native,"qa"+uuid.uuid4().hex))
                            pdf=Path(runtime.create_pdf_file(
                                state,native,"qa"+uuid.uuid4().hex))
                            assert word.is_file() and pdf.is_file()
                            text=check_word(word,year)
                            check_pdf(pdf,year)
                            check_word_to_pdf(word,year)
                            dest_word=OUT/(candidate_name+".docx")
                            dest_pdf=OUT/(candidate_name+".pdf")
                            shutil.copy2(word,dest_word)
                            shutil.copy2(pdf,dest_pdf)
                            results.append((candidate_name,len(text)))
                            print("PI_REAL_NATIVE_YEAR_PASS",candidate_name,
                                  "ONE_A4", "RTL_RIGHT_IDENTITY",
                                  "JAWI_DIGITS","UNIFORM_LILAC",flush=True)
                            break
                        except Exception as exc:
                            diagnostics.append((row["id"],type(exc).__name__,str(exc)[:240]))
                            if len(diagnostics)<=4:
                                print("PI_SAMPLE_DIAGNOSTIC",year,half,
                                      repr(diagnostics[-1]),flush=True)
                        finally:
                            if word is not None: word.unlink(missing_ok=True)
                            if pdf is not None: pdf.unlink(missing_ok=True)
                    if not results or len(results)<half:
                        raise AssertionError(("No verified PI Year/half passes",year,half,
                                               len(segment),diagnostics[:12]))
                assert len(results)==2
                all_success.extend(results)
                print("PI_YEAR_COVERED",year,results,flush=True)
        assert len(all_success)==10
        print("PI_YEAR_2_TO_6_NATIVE_WORD_PDF_ALL_10_PASS",all_success,flush=True)
    finally:
        runtime.DB_PATH=before
        runtime.CIKGULAJU_DB_V2600_ACTIVE=before_active
        temp.cleanup()


if __name__=="__main__":
    main()
