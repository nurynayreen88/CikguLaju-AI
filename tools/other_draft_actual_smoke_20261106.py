"""Offline genuine Telegram RPH smoke for provisional BA and Music sources.

Exercises the exact private endpoints without network, payments, identity or
database writes. Tests original staging source preservation, downloads and
document signatures; DOES NOT assert teacher approval or release status.
"""
import io
import os
from unittest.mock import patch
from zipfile import ZipFile

from flask import Flask

from web.telegram_provisional_arab_music_api import (
    _arab_index,_music_index,_unit_rows,_lesson_rows,_selected,
    create_provisional_subjects_blueprint,
)


def main():
    from pathlib import Path
    entry=(Path(__file__).resolve().parents[1]/
           "tools/run_telegram_with_curriculum_api.py").read_text("utf8")
    assert entry.count("create_provisional_subjects_blueprint(telegram_runtime)")==1
    assert "OTHER_SUBJECTS_DRAFT_READER_REGISTERED = False" in entry
    assert "CIKGULAJU_DB_PATH =" not in (
        entry.split("# Bahasa Arab + Pendidikan Muzik DRAF:")[1]
             .split("# Private source-matched RPT")[0])
    for y,count in {2:60,3:60,4:58,5:60,6:60}.items():
        unit=_unit_rows(y,"ARAB")
        assert len(unit)==4
        lessons=0
        for u in unit:
            options=_lesson_rows(y,"ARAB",u["value"])
            lessons+=len(options)
            for option in options:
                plan=_selected(y,"ARAB",u["value"],option["value"])
                assert plan["lesson"]==int(option["value"]), (y,u,option)
        assert lessons==count,(y,lessons)
        print("ARAB DRAF catalog",y,"unit",len(unit),"pdp",lessons,flush=True)
    for y in range(2,7):
        unit=_unit_rows(y,"MUZIK")
        lessons=sum(len(_lesson_rows(y,"MUZIK",u["value"])) for u in unit)
        assert lessons==35,(y,lessons)
        print("MUZIK DRAF catalog",y,"unit",len(unit),"pdp",lessons,flush=True)
    assert len(_arab_index()) == 298 and _music_index(2)
    os.environ["BOT_TOKEN"]=""
    os.environ["GEMINI_API_KEY"]=""
    os.environ["CIKGULAJU_AUTHORITATIVE_API_TOKEN"]="t"*40
    os.environ["CIKGULAJU_WEB_NATIVE_RPH_ENABLED"]="1"
    import requests
    def block_network(*a,**k):
        raise AssertionError("Network prohibited in offline QA")
    with patch.object(requests.sessions.Session,"request",new=block_network):
        import app as runtime
    from web.rph_teacher_reflection import install as install_teacher_reflection
    assert install_teacher_reflection(runtime)
    web=Flask("other-draft-smoke")
    web.register_blueprint(create_provisional_subjects_blueprint(runtime))
    c=web.test_client()
    auth={"Authorization":"Bearer "+"t"*40}
    unauth=c.get("/internal/rph/v1/other-drafts/units?year=2&subject=ARAB")
    assert unauth.status_code==401,unauth.json
    from docx import Document
    from pypdf import PdfReader

    reflection = "Murid mengulang corak irama dengan bimbingan guru."
    for year in range(2, 7):
        unit = _unit_rows(year, "MUZIK")[0]["value"]
        lesson = _lesson_rows(year, "MUZIK", unit)[0]["value"]
        selection = {"year": year, "subject": "MUZIK", "unit": unit, "lesson": lesson}
        for manual in (False, True):
            teacher = {"class": "Bestari", "date": "2027-02-01",
                       "time": "08:00 - 09:00", "students": "30"}
            if manual:
                teacher["reflection"] = reflection
            expected = reflection if manual else "murid mencapai objektif"
            for fmt in ("word", "pdf"):
                result = c.post("/internal/rph/v1/other-drafts/render", headers=auth,
                                json={"selection": selection, "teacher": teacher, "format": fmt})
                assert result.status_code == 200, (selection, fmt, result.json)
                if fmt == "word":
                    footer = Document(io.BytesIO(result.data)).tables[-1]
                    assert [row.cells[0].text for row in footer.rows] == ["Refleksi"]
                    content = footer.cell(0, 1).text
                else:
                    pages = PdfReader(io.BytesIO(result.data)).pages
                    assert len(pages) == 1
                    content = pages[0].extract_text().split("Refleksi", 1)[1]
                    assert "Pemulihan / Pengayaan" not in pages[0].extract_text()
                assert expected in content, (selection, fmt, content)
    for subject, formats in (("MUZIK", ("word", "pdf")), ("ARAB", ("word",))):
        unit = _unit_rows(2, subject)[0]["value"]
        lesson = _lesson_rows(2, subject, unit)[0]["value"]
        selection = {"year": 2, "subject": subject, "unit": unit, "lesson": lesson}
        teacher = dict.fromkeys(("class", "date", "time", "students"), "")
        for fmt in formats:
            result = c.post("/internal/rph/v1/other-drafts/render", headers=auth,
                            json={"selection": selection, "teacher": teacher, "format": fmt})
            assert result.status_code == 200, (selection, fmt, result.json)
            labels = (("التاريخ", "الوقت", "الفصل", "عدد التلاميذ") if subject == "ARAB" else
                      ("Tarikh", "Hari", "Masa", "Kelas", "Bilangan Murid"))
            if fmt == "word":
                table = Document(io.BytesIO(result.data)).tables[0]
                fields = {left.text: right.text for left, right in (row.cells for row in table.rows)}
                assert tuple(fields[label] for label in labels) == ("",) * len(labels), fields
            else:
                pages = PdfReader(io.BytesIO(result.data)).pages
                text = " ".join(pages[0].extract_text().split())
                assert " ".join(labels) in text, text
    print("MUSIC_REFLECTION_PASS 20", flush=True)
    for subject,years in (("ARAB",(2,3,4,6)),("MUZIK",(2,4,6))):
        for year in years:
            first=_unit_rows(year,subject)[0]
            lesson=_lesson_rows(year,subject,first["value"])[0]["value"]
            query={"year":str(year),"subject":subject,"unit":first["value"],"lesson":lesson}
            avail=c.get("/internal/rph/v1/other-drafts/availability",
                        query_string=query,headers=auth)
            assert avail.status_code==200,(subject,year,avail.status_code,avail.json)
            reviewed = subject == "ARAB" and year in (2, 3) and (first["value"], lesson) == ("u01", "001")
            assert avail.json["status"] == ("READY" if reviewed else "DRAF")
            formats=avail.json["formats"]
            if subject=="MUZIK":
                from web.telegram_provisional_arab_music_api import _music_state
                src=_selected(year,subject,first["value"],lesson)
                state,text=_music_state(src,{"class":"2 Bestari","date":"2026-11-06",
                                        "time":"08:00 - 09:00","students":"30"})
                parsed=runtime._rph_rows(state,text)
                core=src["music"]["preview"]["layout"]["phases"][1]["activity"]
                print("MUZIK NATIVE DIAG",year,"source_sp",src["music"]["sp"],
                      "render_sp",str(parsed.get("STANDARD PEMBELAJARAN",""))[:160],
                      "source_act",repr(core[:85]),
                      "render_act",repr(str(parsed.get("AKTIVITI UTAMA",""))[:160]),flush=True)
            for fmt in formats:
                result=c.post("/internal/rph/v1/other-drafts/render",
                              headers=auth,json={
                                  "selection":{"year":year,"subject":subject,
                                               "unit":first["value"],"lesson":lesson},
                                  "teacher":{"class":"2 Bestari","date":"2026-11-06",
                                             "time":"08:00 - 09:00","students":"30"},
                                  "format":fmt})
                assert result.status_code==200,(subject,year,fmt,result.status_code,result.json if result.is_json else len(result.data))
                body=result.data
                assert len(body)>1000
                assert "_DRAF" not in result.headers["Content-Disposition"]
                if fmt=="word":
                    with ZipFile(io.BytesIO(body)) as z:
                        assert "word/document.xml" in z.namelist()
                        assert z.testzip() is None
                        xml = z.read("word/document.xml")
                        assert b"DRAF" not in xml
                        if reviewed:
                            doc = Document(io.BytesIO(body))
                            assert [len(t.columns) for t in doc.tables] == [2, 3, 2]
                            assert "خطة التدريس اليومية" in doc.paragraphs[0].text
                            fields = {row.cells[0].text: row.cells[1].text for row in doc.tables[0].rows}
                            assert "1.1.1" in fields["معيار التعلّم"]
                            assert fields["الفصل"] == "2 Bestari"
                            assert fields["عدد التلاميذ"] == "30"
                            assert b'w:cs="Amiri"' in xml and b"w:bidiVisual" in xml
                            assert f"CIKGULAJU_RPH_ARAB_TAHUN_{year}_001.docx" in result.headers["Content-Disposition"]
                else:
                    assert body.startswith(b"%PDF-")
                print("PASS",subject,year,lesson,fmt,len(body),flush=True)
            if subject=="ARAB":
                # Never claim PDF is downloadable until Arabic font/RTL QA.
                bad=c.post("/internal/rph/v1/other-drafts/render",
                    headers=auth,json={"selection":{"year":year,"subject":subject,
                                       "unit":first["value"],"lesson":lesson},
                        "teacher":{"class":"","date":"","time":"","students":""},
                        "format":"pdf"})
                assert bad.status_code==503,bad.json
    unit_one_standards = (
        "1.1.1", "1.1.2", "1.2.1", "2.1.1", "2.2.1", "3.1.1",
        "3.2.1", "1.3.1", "1.3.2", "2.3.5", "3.4.1", "1.4.1",
    )
    unit_two_standards = {
        13: "1.1.1", 14: "2.2.2", 15: "1.1.1", 16: "2.2.2", 17: "3.1.1", 18: "2.2.3",
        19: "1.3.1", 20: "1.3.2", 21: "2.3.1", 22: "2.3.3",
        23: "1.4.1", 24: "1.4.5", 25: "2.3.1",
        26: "3.4.1", 27: "1.4.5", 28: "2.5.1",
    }
    reviewed = {
        ("u01", pdp): sp for pdp, sp in enumerate(unit_one_standards, start=1)
    } | {("u02", pdp): sp for pdp, sp in unit_two_standards.items()}
    reviewed.update({("u03", 29): "1.1.1", ("u03", 30): "2.2.2", ("u03", 31): "1.1.1",
                     ("u03", 32): "2.2.4", ("u03", 33): "3.1.1", ("u03", 34): "2.1.2",
                     ("u03", 35): "1.3.1", ("u03", 36): "1.3.2", ("u03", 37): "2.3.5",
                     ("u03", 38): "2.3.3", ("u03", 39): "1.4.1", ("u03", 40): "1.4.3",
                     ("u03", 41): "2.4.4", ("u03", 42): "2.4.2", ("u03", 43): "2.4.3",
                     ("u03", 44): "2.5.3",
                     ("u04", 45): "1.1.1", ("u04", 46): "2.2.2", ("u04", 47): "1.1.1",
                     ("u04", 48): "2.2.2", ("u04", 49): "1.1.1", ("u04", 50): "2.2.2",
                     ("u04", 51): "3.1.1", ("u04", 52): "2.2.1", ("u04", 53): "1.3.1",
                     ("u04", 54): "2.2.3", ("u04", 55): "2.3.2", ("u04", 56): "1.4.1",
                     ("u04", 57): "1.4.3", ("u04", 58): "1.4.2", ("u04", 59): "2.4.2",
                     ("u04", 60): "3.4.1"})
    actual = {
        (y, unit["value"], int(lesson["value"]))
        for y in range(2, 7)
        for unit in _unit_rows(y, "ARAB")
        for lesson in _lesson_rows(y, "ARAB", unit["value"])
        if lesson["status"] == "READY"
    }
    year_three = {
        1: ("1.1.1", "٢ و٦"), 2: ("1.1.2", "٢ و٦"), 3: ("1.2.1", "٢ و٦"),
        4: ("2.1.1", "٢ و٦"), 5: ("2.2.1", "٤ و٨"),
        6: ("3.1.1", "٥ و٩"), 7: ("3.2.1", "٥ و٩"),
        8: ("1.3.1", "١١–١٢"), 9: ("1.3.2", "١١–١٢"), 10: ("2.3.5", "١٣–١٤"),
        11: ("3.3.1", "٢٠ و٢٤"), 12: ("1.4.1", "١٦–١٧"),
        13: ("1.1.1", "٣٠"), 14: ("2.2.1", "٣١"), 15: ("3.1.1", "٣٢"),
        16: ("1.1.1", "٣٣"), 17: ("2.2.1", "٣٤"), 18: ("3.1.1", "٣٥"),
        19: ("1.1.1", "٣٦"), 20: ("2.2.1", "٣٧"), 21: ("3.1.1", "٣٨"),
        22: ("1.3.2", "٤١"), 23: ("2.3.1", "٤٢"), 24: ("2.3.3", "٤٣"),
        25: ("1.4.1", "٤٥"), 26: ("1.4.2", "٤٦"), 27: ("1.4.3", "٤٧"),
        28: ("1.4.1", "٥٥"),
        29: ("1.1.1", "٦٠"), 30: ("2.2.1", "٦١"), 31: ("1.1.1", "٦٣"),
        32: ("2.2.4", "٦٤"), 33: ("2.2.1", "٦٤ و٦٧"), 34: ("3.1.1", "٦٨"),
        35: ("2.1.2", "٦٩"), 36: ("1.3.2", "٧٠"), 37: ("2.3.5", "٧٢"),
        38: ("2.2.3", "٧٣"), 39: ("3.3.1", "٧٨"), 40: ("2.4.1", "٧٦"),
        41: ("1.4.5", "٧٧"), 42: ("1.3.2", "٨٢"), 43: ("2.3.1", "٨٣"),
        44: ("1.4.1", "٧٦"),
        45: ("1.1.1", "٨٨"), 46: ("2.2.1", "٨٩"), 47: ("1.1.1", "٩١"),
        48: ("2.2.4", "٩٢"), 49: ("1.1.1", "٩٤"), 50: ("2.2.3", "٩٥"),
        51: ("3.1.1", "٩٦"), 52: ("1.3.2", "٩٨"), 53: ("1.3.1", "٩٩"),
        54: ("2.3.5", "١٠٠"), 55: ("1.4.3", "١٠٣"), 56: ("1.4.1", "١٠٤"),
        57: ("2.4.4", "١٠٥"), 58: ("3.4.1", "١٠٨"), 59: ("2.4.1", "١١٣"),
        60: ("3.4.1", "١٠٩"),
    }
    year_three_units = {
        **dict.fromkeys(range(1, 13), "u01"),
        **dict.fromkeys(range(13, 29), "u02"),
        **dict.fromkeys(range(29, 45), "u03"),
        **dict.fromkeys(range(45, 61), "u04"),
    }
    assert actual == ({(2, unit, pdp) for unit, pdp in reviewed}
                      | {(3, unit, pdp) for pdp, unit in year_three_units.items()})
    for (unit, pdp), sp in reviewed.items():
        reviewed_lesson = {"year": 2, "subject": "ARAB", "unit": unit, "lesson": f"{pdp:03d}"}
        status = c.get("/internal/rph/v1/other-drafts/availability", query_string=reviewed_lesson,
                       headers=auth)
        assert status.json["status"] == "READY", status.json
        assert status.json["formats"] == ["word"]
        result = c.post("/internal/rph/v1/other-drafts/render", headers=auth, json={
            "selection": reviewed_lesson, "teacher": {"class": "2 Bestari", "date": "2027-01-20",
                                                        "time": "08:00 - 09:00", "students": "30"},
            "format": "word",
        })
        assert result.status_code == 200, result.json
        doc = Document(io.BytesIO(result.data))
        fields = {row.cells[0].text: row.cells[1].text for row in doc.tables[0].rows}
        number_ar = f"{pdp:03d}".translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))
        assert number_ar in fields["الصف والحصّة"]
        assert sp in fields["معيار التعلّم"]
        assert "DRAF" not in "".join(cell.text for table in doc.tables
                                     for row in table.rows for cell in row.cells)
        if pdp == 2:
            assert "تحديد" in fields["معيار التعلّم"]
            assert "٢ و٤" in doc.tables[2].cell(1, 1).text
        if pdp == 3:
            assert "محاكاة" in fields["معيار التعلّم"]
            assert "٣ و٥" in doc.tables[2].cell(1, 1).text
    print(f"ARABIC_REVIEWED_WORD_PASS {len(reviewed)}", flush=True)
    for pdp, (sp, pages) in year_three.items():
        selection = {"year": 3, "subject": "ARAB", "unit": year_three_units[pdp], "lesson": f"{pdp:03d}"}
        status = c.get("/internal/rph/v1/other-drafts/availability", query_string=selection, headers=auth)
        assert status.json["status"] == "READY" and status.json["formats"] == ["word"]
        result = c.post("/internal/rph/v1/other-drafts/render", headers=auth, json={
            "selection": selection,
            "teacher": {"class": "3 Bestari", "date": "2027-01-20",
                        "time": "08:00 - 09:00", "students": "30", "reflection": "Catatan guru."},
            "format": "word",
        })
        assert result.status_code == 200, result.json
        doc = Document(io.BytesIO(result.data))
        fields = {row.cells[0].text: row.cells[1].text for row in doc.tables[0].rows}
        assert sp in fields["معيار التعلّم"]
        assert fields["الفصل"] == "3 Bestari" and fields["عدد التلاميذ"] == "30"
        assert pages in doc.tables[2].cell(1, 1).text
        assert doc.tables[2].cell(2, 1).text == "Catatan guru."
        assert [len(table.columns) for table in doc.tables] == [2, 3, 2]
    print(f"ARABIC_YEAR3_REVIEWED_WORD_PASS {len(year_three)}", flush=True)
    wrong_unit = {"year": 2, "subject": "ARAB", "unit": "u01", "lesson": "018"}
    status = c.get("/internal/rph/v1/other-drafts/availability",
                   query_string=wrong_unit, headers=auth)
    assert status.status_code == 404, status.json
    year6={"year":6,"subject":"ARAB","unit":"u03","lesson":"030"}
    assert c.get("/internal/rph/v1/other-drafts/availability",query_string=year6,headers=auth).status_code==200
    result=c.post("/internal/rph/v1/other-drafts/render",headers=auth,json={
        "selection":year6,"teacher":{"class":"6 Amanah","date":"2027-06-14",
                                     "time":"08:00 - 09:00","students":"30"},
        "format":"word",
    })
    assert result.status_code==200,result.json if result.is_json else None
    with ZipFile(io.BytesIO(result.data)) as document:
        text=document.read("word/document.xml").decode()
        assert "PdP 030" in text and "1.1 / 1.1.4" in text and "h63" in text
    print("DRAFT_SOURCE_CATALOG_AND_NATIVE_WORD_PDF_SMOKE_PASS",flush=True)


if __name__=="__main__":
    main()
