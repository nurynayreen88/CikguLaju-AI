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
    for y,count in {2:60,3:60,4:58,5:60,6:60}.items():
        unit=_unit_rows(y,"ARAB")
        assert len(unit)==4
        lessons=sum(len(_lesson_rows(y,"ARAB",u["value"])) for u in unit)
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
            assert avail.json["status"]=="DRAF"
            formats=avail.json["formats"]
            if subject=="MUZIK":
                from web.telegram_provisional_arab_music_api import _selected,_music_state
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
                if fmt=="word":
                    with ZipFile(io.BytesIO(body)) as z:
                        assert "word/document.xml" in z.namelist()
                        assert z.testzip() is None
                        assert b"DRAF" in z.read("word/document.xml")
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
    print("DRAFT_SOURCE_CATALOG_AND_NATIVE_WORD_PDF_SMOKE_PASS",flush=True)


if __name__=="__main__":
    main()
