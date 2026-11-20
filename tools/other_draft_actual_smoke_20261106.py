"""Offline genuine Telegram RPH smoke for provisional BA and Music sources.

Exercises the exact private endpoints without network, payments, identity or
database writes. Tests original staging source preservation, downloads and
document signatures; DOES NOT assert teacher approval or release status.
"""
import io
import json
from pathlib import Path
import os
import re
from unittest.mock import patch
from zipfile import ZipFile

from flask import Flask

from staging.pendidikan_muzik.rpt_rph_2027.legacy_doc_text_safe_staging import (
    normalize_for_legacy_doc,
)
from staging.pendidikan_muzik.rpt_rph_2027.music_native_route_candidate import (
    ROOT as MUSIC_ROOT,
    load as load_music,
)
from staging.pendidikan_muzik.rpt_rph_2027.native_layout_preview_staging import (
    STANDARD_DESCRIPTIONS,
)
from web.telegram_provisional_arab_music_api import (
    _arab_index,_music_index,_unit_rows,_lesson_rows,_music_state,_selected,
    create_provisional_subjects_blueprint,
)


def _assert_music_standards(runtime):
    bank = json.loads((MUSIC_ROOT / STANDARD_DESCRIPTIONS).read_text(encoding="utf-8"))
    assert bank["2"]["sp"]["1.1.1"]["sk"] == "1.1"
    assert bank["4"]["sp"]["3.2.2"]["sk"] == "3.1"
    assert bank["4"]["sp"]["4.2.1"]["sk"] == "4.1"
    teacher = dict.fromkeys(("class", "date", "time", "students"), "")
    for year in range(2, 7):
        standard = bank[str(year)]
        lesson_codes = set()
        for pdp in range(1, 36):
            music = load_music(year, pdp)
            assert music is not None
            lesson_codes.update(music["sp"])
            entries = [standard["sp"][code] for code in music["sp"]]
            assert music["sk"] == list(dict.fromkeys(entry["sk"] for entry in entries))
            selection = {"year": year, "lesson": pdp, "music": music, "title": music["title"]}
            state, text = _music_state(selection, teacher)
            rendered = runtime._rph_rows(state, text)
            expected_sk = [f"{code} {standard['sk'][code]}" for code in music["sk"]]
            expected_sp = [f"{code} {entry['description']}" for code, entry in zip(music["sp"], entries, strict=True)]
            assert all(standard["sk"][code].strip() for code in music["sk"])
            assert all(entry["description"].strip() for entry in entries)
            headings = music["preview"]["layout"]["phases"][1]["activity"].splitlines()
            assert not any(re.match(r"^(Aktiviti [12]|Pengukuhan).*\d+ minit", line, re.I) for line in headings)
            assert rendered["STANDARD KANDUNGAN"] == normalize_for_legacy_doc("; ".join(expected_sk))
            assert rendered["STANDARD PEMBELAJARAN"] == normalize_for_legacy_doc("; ".join(expected_sp))
        assert lesson_codes == set(standard["sp"])
    assert load_music(2, 24)["sp"] == ["2.2.1", "2.3.2"]
    assert load_music(2, 32)["sp"] == ["3.1.2", "3.1.3"]
    assert load_music(3, 21)["sp"] == ["1.2.2", "2.4.2"]
    assert load_music(4, 5)["sp"] == ["2.2.1", "2.2.2"]
    assert load_music(5, 17)["sp"] == ["2.4.1", "2.4.2"]
    assert "A minor" in load_music(5, 19)["preview"]["phase_text"]["act2"]
    print("MUSIC_DSKP_DESCRIPTIONS_ALL_175_PASS", flush=True)


def main():
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
    assert _arab_index() and _music_index(2)
    os.environ["BOT_TOKEN"]=""
    os.environ["GEMINI_API_KEY"]=""
    os.environ["CIKGULAJU_AUTHORITATIVE_API_TOKEN"]="t"*40
    os.environ["CIKGULAJU_WEB_NATIVE_RPH_ENABLED"]="1"
    import requests
    def block_network(*a,**k):
        raise AssertionError("Network prohibited in offline QA")
    with patch.object(requests.sessions.Session,"request",new=block_network):
        import app as runtime
    _assert_music_standards(runtime)
    web=Flask("other-draft-smoke")
    web.register_blueprint(create_provisional_subjects_blueprint(runtime))
    c=web.test_client()
    auth={"Authorization":"Bearer "+"t"*40}
    unauth=c.get("/internal/rph/v1/other-drafts/units?year=2&subject=ARAB")
    assert unauth.status_code==401,unauth.json
    for subject,years in (("ARAB",(2,4,6)),("MUZIK",(2,4,6))):
        for year in years:
            first=_unit_rows(year,subject)[0]
            lesson=_lesson_rows(year,subject,first["value"])[0]["value"]
            query={"year":str(year),"subject":subject,"unit":first["value"],"lesson":lesson}
            avail=c.get("/internal/rph/v1/other-drafts/availability",
                        query_string=query,headers=auth)
            assert avail.status_code==200,(subject,year,avail.status_code,avail.json)
            reviewed = (subject, year, first["value"], lesson) == ("ARAB", 2, "u01", "001")
            assert avail.json["status"] == ("READY" if reviewed else "DRAF")
            formats=avail.json["formats"]
            if subject=="MUZIK":
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
                            from docx import Document

                            doc = Document(io.BytesIO(body))
                            assert [len(t.columns) for t in doc.tables] == [2, 3, 2]
                            assert "خطة التدريس اليومية" in doc.paragraphs[0].text
                            fields = {row.cells[0].text: row.cells[1].text for row in doc.tables[0].rows}
                            assert "1.1.1" in fields["معيار التعلّم"]
                            assert fields["الفصل"] == "2 Bestari"
                            assert fields["عدد التلاميذ"] == "30"
                            assert b'w:cs="Amiri"' in xml and b"w:bidiVisual" in xml
                            assert "CIKGULAJU_RPH_ARAB_TAHUN_2_001.docx" in result.headers["Content-Disposition"]
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
    from docx import Document

    unit_one_standards = (
        "1.1.1", "1.1.2", "1.2.1", "2.1.1", "2.2.1", "3.1.1",
        "3.2.1", "1.3.1", "1.3.2", "2.3.5", "3.4.1", "1.4.1",
    )
    assert sum(
        lesson["status"] == "READY"
        for y in range(2, 7)
        for unit in _unit_rows(y, "ARAB")
        for lesson in _lesson_rows(y, "ARAB", unit["value"])
    ) == len(unit_one_standards)
    for pdp, sp in enumerate(unit_one_standards, start=1):
        reviewed_lesson = {"year": 2, "subject": "ARAB", "unit": "u01", "lesson": f"{pdp:03d}"}
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
    print("ARABIC_UNIT_ONE_12_WORD_PASS", flush=True)
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
