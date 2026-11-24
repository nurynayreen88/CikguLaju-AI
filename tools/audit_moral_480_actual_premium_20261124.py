"""Actual installed native Moral RPH generator, exact RPT session sources.
No network, user account, quota, payment or production database writes.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import shutil
import subprocess
import uuid
import fitz
from docx import Document
from docx.oxml.ns import qn

from tools.bm_native_v26_navigation_audit import database
from web.moral_rpt_rph_source import load_plan, VARIANT
from web.rph_shared_source_identity import source_fingerprint
from web.native_rph_telegram_api import build_native_input
from web.rph_reference_style_20261121 import color_for_state


def native_input(year, number):
    plan=load_plan(year,number)
    assert plan, (year,number)
    fields=plan["fields"]
    def get(key):
        return fields.get(key,"")
    labels=("STANDARD KANDUNGAN","STANDARD PEMBELAJARAN",
            "OBJEKTIF PEMBELAJARAN","KRITERIA KEJAYAAN",
            "BAHAN BANTU MENGAJAR","EMK / NILAI","PENTAKSIRAN")
    header=[{"label":label,"value":value} for label,value in (
        ("Mata Pelajaran","Pendidikan Moral"),("Tahun/Tingkatan",f"Tahun {year}"),
        ("Tarikh",""),("Hari",""),("Masa",""),("Kelas",""),("Bilangan Murid",""),
        ("Tajuk",plan["title"]),("PENGETAHUAN SEDIA ADA",""),("KBAT / PAK21",""))]
    header += [{"label":key,"value":get(key)} for key in labels]
    phases=[{"label":label,"activity":get(key),"notes":""} for label,key in (
        ("Set Induksi","SET INDUKSI"),("Aktiviti Utama","AKTIVITI UTAMA"),("Penutup","PENUTUP"))]
    return build_native_input({
        "subject":"MORAL","component":None,"year":year,"lesson":number,
        "unit":plan["unit"],"source_variant":VARIANT,
        "source_digest":source_fingerprint(year,"MORAL",number,variant=VARIANT),
        "teacher":{"class":"","date":"","time":"","students":"","reflection":""},
        "layout":{"style":"telegram-native-rph-v1","header":header,
        "activity_header":["Fasa","Aktiviti Pengajaran & Pembelajaran","Catatan"],
        "phases":phases,"footer":[{"label":"Pemulihan / Pengayaan","value":""},
        {"label":"Refleksi","value":"____ / ____ murid mencapai objektif."}]},
        "format":"word"})


def main():
    from tools import run_telegram_with_curriculum_api as live
    runtime=live.telegram_runtime
    tmp, db=database()
    out=Path("qa/moral-actual-native").resolve()
    out.mkdir(parents=True,exist_ok=True)
    reports=[]
    failures=[]
    try:
        runtime.DB_PATH=str(db)
        runtime.CIKGULAJU_DB_V2600_ACTIVE=True
        assert live.RPH_REFERENCE_WORD_STYLE_ACTIVE
        assert live.RPH_REFERENCE_PDF_STYLE_ACTIVE
        assert runtime.CIKGULAJU_MORAL_80_ACTIVE
        for year in range(2,7):
            for number in range(1,97):
                state, native, _=native_input(year,number)
                assert color_for_state(state)=="F8EAF2"
                rows=runtime._rph_rows(state,native)
                plan=load_plan(year,number)
                assert rows["TAJUK"] and not rows["TAJUK"].startswith("PdP ")
                assert rows["AKTIVITI UTAMA"]
                assert rows["REFLEKSI"]
                # Actual documents from every representative route, including
                # beginning/middle/end and core/reinforcement selection.
                if number not in (1,4,8,48,96):
                    continue
                word=pdf=None
                try:
                    uid="moralqa"+uuid.uuid4().hex[:14]
                    word=Path(runtime.create_word_file(state,native,uid))
                    pdf=Path(runtime.create_pdf_file(state,native,uid+"p"))
                    doc=Document(word)
                    assert len(doc.tables)==4, (year,number,"old layout",len(doc.tables))
                    assert len(doc.tables[0].columns)==2
                    assert "Pendidikan Moral" in doc.tables[0].cell(0,0).text
                    assert "Kelas" in doc.tables[0].cell(0,1).text
                    assert any(p.text.strip()=="RANCANGAN PENGAJARAN HARIAN" and p.alignment==1 for p in doc.paragraphs)
                    widths=[sum(c.width.twips for c in t.columns) for t in doc.tables]
                    assert max(widths)-min(widths)<30,widths
                    assert "F8EAF2" in doc.tables[0]._tbl.xml
                    display="\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
                    assert rows["REFLEKSI"] in display
                    sp_cells = [r.cells[1].text for r in doc.tables[1].rows if r.cells[0].text.strip().casefold() == "standard pembelajaran"]
                    assert len(sp_cells) == 1
                    codes = [re.match(r"^\d+\.\d+", line)[0] for line in rows["STANDARD PEMBELAJARAN"].splitlines()]
                    assert [re.match(r"^\d+\.\d+", line)[0] for line in sp_cells[0].splitlines()] == codes, (year,number,sp_cells)
                    name=f"Moral_T{year}_Sesi{number:03d}"
                    shutil.copy2(word,out/(name+".docx"))
                    shutil.copy2(pdf,out/(name+".pdf"))
                    with fitz.open(pdf) as book:
                        assert len(book)==1, (year,number,"native PDF pages",len(book))
                        page=book[0]
                        assert 594<page.rect.width<597 and 840<page.rect.height<844
                        content=page.get_text()
                        assert "Pendidikan Moral" in content
                        assert "Refleksi" in content
                        # Match actual rendered text lines, not merely code presence.
                        assert all(re.search(r"(?m)^\s*" + re.escape(code) + r"(?![\d.])", content) for code in codes), (year,number,codes,"SP line breaks missing in PDF")
                        # Native PDF subject palette must be rendered, not merely
                        # a DOCX wrapper. Test colored vector rectangles.
                        color=(248/255,234/255,242/255)
                        assert any(d.get("fill") and all(abs(a-b)<.035 for a,b in zip(d["fill"],color)) for d in page.get_drawings()),"native PDF pastel missing"
                    reports.append({"year":year,"session":number,"word_tables":4,"pdf_pages":1,"widths":widths})
                except Exception as exc:
                    failures.append([year,number,type(exc).__name__,str(exc)[:250]])
                finally:
                    if word: word.unlink(missing_ok=True)
                    if pdf: pdf.unlink(missing_ok=True)
        converted=out/"word-to-pdf"
        converted.mkdir(exist_ok=True)
        with TemporaryDirectory() as temp:
            files=sorted(out.glob("*.docx"))
            if files:
                subprocess.run(["libreoffice","-env:UserInstallation="+(Path(temp)/"profile").as_uri(),"--headless","--convert-to","pdf","--outdir",str(converted),*map(str,files)],check=True,timeout=300)
            for doc in files:
                with fitz.open(converted/(doc.stem+".pdf")) as book:
                    if len(book)!=1:
                        failures.append([doc.name,"converted Word pages",len(book)])
        (out/"report.json").write_text(json.dumps({"source_rows":480,"samples":reports,"failures":failures},ensure_ascii=False,indent=2))
        print("MORAL NATIVE",len(reports),"/25", "failures",failures,flush=True)
        assert len(reports)==25 and not failures
    finally:
        tmp.cleanup()

if __name__=="__main__":
    main()
