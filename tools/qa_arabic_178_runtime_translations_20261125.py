"""Exercise the actual provisional Word route, not only the offline renderer."""
import re
from pathlib import Path
from docx import Document
from web.telegram_provisional_arab_music_api import _arab_index, _arab_translations, _selected, _arab_word, _lesson_rows

def main():
    out = Path("qa-arabic-runtime")
    out.mkdir(exist_ok=True)
    teacher = {"class":"", "date":"", "time":"", "students":""}
    translations = _arab_translations()
    rows = _arab_index()
    assert len(rows) == 298 and len(translations) == 178
    for (y,n), row in rows.items():
        unit = f"u{int(row['unit']):02d}"
        selected = _selected(y,"ARAB",unit,f"{n:03d}")
        if y in (2,3):
            assert selected["status"] == "READY"
            continue
        assert selected.get("status","DRAF") == "DRAF"
        assert selected["formats"] == ["word"]
        tr = translations[(y,n)]["translation"]
        dest = out / f"BA_T{y}_{n:03d}.docx"
        _arab_word(selected,teacher,dest)
        doc = Document(dest)
        visible = "\n".join(c.text for table in doc.tables for r in table.rows for c in r.cells)
        assert not re.search(r"[A-Za-z]",visible), (y,n,visible)
        assert all(v in visible for v in tr.values()), (y,n)
        assert doc.tables[1].cell(0,1).text == row["sk"]
        assert doc.tables[1].cell(1,1).text == row["sp"]
        assert all(any(run.bold for run in doc.tables[2].cell(i,1).paragraphs[0].runs) for i in (2,3))
    for y in (4,5,6):
        row=rows[(y,1)]
        selected=_selected(y,"ARAB",f"u{int(row['unit']):02d}","001")
        p=out/"manual.docx"
        _arab_word(selected,{"class":"4 Amanah","date":"2027-01-12","time":"08:00-09:00","students":"25","reflection":"Catatan guru kekal."},p)
        d=Document(p)
        assert d.tables[-1].cell(2,1).text=="Catatan guru kekal."
        assert [r.cells[2].text for r in d.tables[0].rows]==["4 Amanah","12/01/2027","08:00-09:00","25"]
        p.unlink()
    print("178/178 Arabic-only real Word route; 120 READY selections unchanged; manual reflection and metadata retained.")

if __name__=="__main__":
    main()
