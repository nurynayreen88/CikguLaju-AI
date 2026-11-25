"""Exercise the actual provisional Word renderer without changing approval or format access."""
import re
from pathlib import Path
from docx import Document
from web.telegram_provisional_arab_music_api import _arab_index, _arab_translations, _selected, _arab_word, REVIEWED_ARABIC

def main():
    out = Path("qa-arabic-full-standards")
    out.mkdir(exist_ok=True)
    teacher = {"class":"", "date":"", "time":"", "students":""}
    index = _arab_index()
    translations = _arab_translations()
    assert len(index) == 298 and len(REVIEWED_ARABIC) == 120 and len(translations) == 178
    for (y,n), row in sorted(index.items()):
        selection = _selected(y,"ARAB",f"u{int(row['unit']):02d}",f"{n:03d}")
        assert selection["formats"] == ["word"]
        if y in (2,3):
            assert selection["status"] == "READY"
            continue
        assert selection.get("status","DRAF") == "DRAF"
        dest = out / f"BA_T{y}_{n:03d}.docx"
        _arab_word(selection, teacher, dest)
        doc = Document(dest)
        visible = "\n".join(c.text for table in doc.tables for r in table.rows for c in r.cells)
        assert not re.search(r"[A-Za-z]",visible), (y,n,visible)
        assert all(v in visible for v in translations[y,n]["translation"].values()), (y,n)
        assert doc.tables[1].cell(0,1).text == row["sk"]
        assert doc.tables[1].cell(1,1).text == row["sp"]
    for y in (2,3,4,5,6):
        row = index[y,1]
        sel = _selected(y,"ARAB",f"u{int(row['unit']):02d}","001")
        dest = out / "manual-test.docx"
        _arab_word(sel, {**teacher,"class":"4 Amanah","date":"2027-01-12","time":"08:00-09:00","students":"28","reflection":"Catatan guru kekal."}, dest)
        visible = "\n".join(c.text for t in Document(dest).tables for r in t.rows for c in r.cells)
        for value in ("4 Amanah","12/01/2027","08:00-09:00","28","Catatan guru kekal."):
            assert value in visible, (y,value,visible)
        dest.unlink()
    print("178/178 runtime full Arabic Word; 120 READY selections and teacher fields preserved; draft/format gates unchanged.")
if __name__ == "__main__":
    main()
