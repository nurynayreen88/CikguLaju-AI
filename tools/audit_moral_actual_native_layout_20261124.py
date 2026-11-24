"""Actual production-bootstrap Moral RPH design audit; no teacher login or credit debit."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess
import uuid
import fitz
from docx import Document
from docx.oxml.ns import qn
from tools.bm_native_v26_navigation_audit import database
from web.moral_rpt_rph_source import STATE_KEY, load_plan
from web.rph_reference_style_20261121 import color_for_state


def main():
    from tools import run_telegram_with_curriculum_api as live
    runtime = live.telegram_runtime
    tmp, db_path = database()
    runtime.DB_PATH = str(db_path)
    runtime.CIKGULAJU_DB_V2600_ACTIVE = True
    out = Path("qa/moral-real-native")
    out.mkdir(parents=True, exist_ok=True)
    results = []
    try:
        assert getattr(runtime, "CIKGULAJU_MORAL_80_ACTIVE", False)
        assert getattr(runtime, "_CIKGULAJU_REFERENCE_WORD_STYLE_20261121", False)
        for year in range(2, 7):
            # Both core and reinforcement routes, plus the year-end session.
            for n in (1, 4, 96):
                plan = load_plan(year,n)
                assert plan, (year,n)
                state = {"task":"rph","subject":"Pendidikan Moral","year":f"Tahun {year}",
                         "year_label":f"Tahun {year}", "lesson_no":n, "pdp_no":n, "lesson":n,
                         "topic":plan["title"],"unit":plan["unit"],"subtopic":"",
                         "rph_class":"","rph_date":"","rph_day":"","rph_time":"","rph_students":"",
                         "rph_teacher_reflection":"","rph_mode":"fast_rpt",
                         STATE_KEY:n}
                text = "\n".join(k+":\n"+str(v)+"\n" for k,v in plan["fields"].items())
                token = "moralqa"+uuid.uuid4().hex[:14]
                word = Path(runtime.create_word_file(state,text,token))
                pdf = Path(runtime.create_pdf_file(state,text,token+"p"))
                name = f"MORAL_T{year}_SESSION{n:03d}"
                shutil.copy2(word,out/(name+".docx"))
                shutil.copy2(pdf,out/(name+".pdf"))
                doc=Document(word)
                tables=doc.tables
                cells=" ".join(c.text for t in tables for r in t.rows for c in r.cells)
                title=[p for p in doc.paragraphs if p.text.strip()=="RANCANGAN PENGAJARAN HARIAN"]
                widths=[sum(col.width.mm for col in t.columns) for t in tables]
                with fitz.open(pdf) as p:
                    pages=len(p)
                    a4=all(abs(x.rect.width-595.28)<2 and abs(x.rect.height-841.89)<2 for x in p)
                    content=" ".join(x.get_text() for x in p)
                header = tables[0].cell(0,0).text if tables else ""
                xml = tables[0]._tbl.xml if tables else ""
                result={"year":year,"session":n,"tables":len(tables),"widths":widths,
                        "header":header,"centered":bool(title and title[0].alignment==1),
                        "pastel":color_for_state(state) in xml,"pdf_pages":pages,"pdf_a4":a4,
                        "has_reflection":"Refleksi".casefold() in cells.casefold(),
                        "has_activity":"Aktiviti 1" in cells and "Aktiviti 2" in cells,
                        "pdf_subject":"Pendidikan Moral".casefold() in content.casefold()}
                results.append(result)
                print("MORAL NATIVE",result,flush=True)
                word.unlink(missing_ok=True)
                pdf.unlink(missing_ok=True)
        converted=out/"word-to-pdf"
        converted.mkdir(exist_ok=True)
        with TemporaryDirectory() as temp:
            subprocess.run(["libreoffice","-env:UserInstallation="+(Path(temp)/"profile").as_uri(),
                            "--headless","--convert-to","pdf","--outdir",str(converted),
                            *map(str, sorted(out.glob("*.docx")))],check=True,timeout=240)
        for result in results:
            path=converted/f"MORAL_T{result['year']}_SESSION{result['session']:03d}.pdf"
            with fitz.open(path) as book:
                result["word_pages"]=len(book)
        (out/"report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
        errors=[r for r in results if not (r["tables"]==4 and max(r["widths"])-min(r["widths"])<1
                 and r["centered"] and r["pastel"] and r["pdf_pages"]==r["word_pages"]==1
                 and r["pdf_a4"] and r["has_reflection"] and r["has_activity"] and r["pdf_subject"])]
        print("MORAL_REAL_NATIVE_FORMAT",len(results)-len(errors),"/",len(results),errors,flush=True)
        assert not errors, errors
    finally:
        tmp.cleanup()


if __name__ == "__main__":
    main()
