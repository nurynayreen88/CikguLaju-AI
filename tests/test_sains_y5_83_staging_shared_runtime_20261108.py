"""Staging-only authenticated Web/Telegram shared 83 Year5 Science source tests."""
from __future__ import annotations
import io
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask
from docx import Document
from pypdf import PdfReader

from web.sains_y5_83_staging_shared_runtime_20261108 import (
    _roster,_resolve_lesson,preview_rows,install,STAGING_FLAG,STAGING_CONTEXT,
)
from web.telegram_verified_sequence_rph_bridge import (
    _build_state,_source_text,create_native_sequence_rph_blueprint,
    _unit_catalog,
)
from tools.render_sains_y5_83_rph_draf_20261107 import word_doc,pdf_doc


def make_runtime():
    def _commit(state,mapped):
        if not mapped:
            raise ValueError("empty grouped SP")
        state["sk_code"]=mapped[0]["sk_code"]
        state["sp_code"]=mapped[0]["sp_code"]
        state["grouped_sp_codes"]=[x["sp_code"] for x in mapped]

    def unique_units(rows):
        seen=set()
        result=[]
        for row in rows:
            key=(row["unit_code"],row["unit_title"])
            if key not in seen:
                seen.add(key)
                result.append(key)
        return result

    def output_file(state,text,unique,kind):
        entry=_resolve_lesson(state)
        if not entry or entry["sp_full_text"] not in text:
            raise ValueError("Web native selection/content mismatch")
        path=Path(tempfile.gettempdir())/(unique+"_Sains_T5."+(
            "docx" if kind=="word" else "pdf"))
        if kind=="word":
            # Simulate native Telegram's strict three-table Word contract.
            # The standalone Year5 renderer intentionally uses two tables,
            # so passing it directly would be correctly rejected by Web's
            # compact_web_word_notes verification.
            document=Document()
            heading=document.add_table(rows=2,cols=2)
            heading.cell(0,0).text="RPH SAINS TAHUN 5"
            heading.cell(0,1).text=entry["tajuk"]
            heading.cell(1,0).text=entry["sk"]+" — "+entry["sk_title"]
            heading.cell(1,1).text=entry["sp"]+" — "+entry["sp_full_text"]
            activity=document.add_table(rows=3,cols=3)
            for idx,(label,body) in enumerate((
                ("Aktiviti 1",entry["teacher1"]+". "+entry["pupil1"]),
                ("Aktiviti 2",entry["teacher2"]+". "+entry["pupil2"]),
                ("PBD",entry["pbd"]))):
                activity.cell(idx,0).text=label
                activity.cell(idx,1).text=body
                activity.cell(idx,2).text="Catatan guru"
            footer=document.add_table(rows=1,cols=2)
            footer.cell(0,0).text="BBM: "+entry["materials"]
            footer.cell(0,1).text="DRAF/HOLD"
            document.save(path)
        else:
            pdf_doc(path,entry)
        return str(path)

    return SimpleNamespace(
        CIKGULAJU_DB_V2600_ACTIVE=True,
        _sm2542_rows=lambda y,s: [{"origin":"original","year":y,"subject":s}],
        _sm2542_unique_units=unique_units,
        _commit_multi_sp=_commit,
        _local_rph_text=lambda state: "original native fallback for other subjects",
        _rph_rows=lambda state,*a,**kw: {
            "KELAS":state.get("rph_class") or "5 Bestari",
            "TARIKH":state.get("rph_date") or "08/11/2026",
            "MASA":state.get("rph_time") or "07:30–08:30",
        },
        create_word_file=lambda state,text,unique:output_file(state,text,unique,"word"),
        create_pdf_file=lambda state,text,unique:output_file(state,text,unique,"pdf"),
    )


class ScienceY5StagingRuntimeTests(unittest.TestCase):
    def test_flag_off_leaves_runtime_completely_unchanged(self):
        runtime=make_runtime()
        old=(runtime._sm2542_rows,runtime._local_rph_text,runtime._rph_rows)
        with patch.dict(os.environ,{STAGING_FLAG:"0",STAGING_CONTEXT:"staging"}):
            self.assertFalse(install(runtime))
        self.assertEqual(old,(runtime._sm2542_rows,runtime._local_rph_text,
                              runtime._rph_rows))

    def test_never_install_on_production_render_even_when_flag_on(self):
        for environment,service in [
            ("production",""),
            ("staging","srv-dah3b8lbedkc738ugqt0"),
            ("staging","srv-dbm5go8u01pc738f40cg"),
        ]:
            runtime=make_runtime()
            with self.subTest(env=environment,service=service),patch.dict(
                os.environ,{STAGING_FLAG:"1",STAGING_CONTEXT:environment,
                            "RENDER_SERVICE_ID":service}):
                with self.assertRaises(RuntimeError):
                    install(runtime)
                self.assertFalse(getattr(runtime,
                    "CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW_ACTIVE",False))

    def test_authoritative_roster_is_83_unique_sp_83_pdp_and_no_repeated_unit(self):
        rows=preview_rows()
        self.assertEqual(len(rows),83)
        self.assertEqual(len({r["pdp_sequence_code"] for r in rows}),83)
        self.assertEqual(len({r["sp_code"] for r in rows}),83)
        self.assertEqual({r["source_sequence_no"] for r in rows},set(range(1,84)))
        self.assertEqual(len({r["unit_title"] for r in rows}),9)
        self.assertTrue(all(r["unit_code"]=="" for r in rows))
        self.assertTrue(all(r["sp_text"].endswith(".") for r in rows))
        self.assertTrue(all(r["verification_status"].startswith("STAGING_DRAF_HOLD")
                            for r in rows))
        self.assertTrue(all(not r["activitybook_ref"] for r in rows))
        self.assertEqual(rows[0]["pdp_sequence_code"],"SCI-Y5-PDP-001")
        self.assertEqual(rows[-1]["pdp_sequence_code"],"SCI-Y5-PDP-083")

    def test_wrapped_native_menu_document_content_and_other_subject_untouched(self):
        runtime=make_runtime()
        with patch.dict(os.environ,{STAGING_FLAG:"1",STAGING_CONTEXT:"staging",
                                    "RENDER_SERVICE_ID":""}):
            self.assertTrue(install(runtime))
            self.assertTrue(install(runtime))
            self.assertEqual(len(runtime._sm2542_rows("Tahun 5","Sains")),83)
            self.assertEqual(runtime._sm2542_rows("Tahun 4","Sains")[0]["origin"],"original")
            self.assertEqual(runtime._sm2542_rows("Tahun 5","Matematik")[0]["origin"],"original")
            units=_unit_catalog(runtime._sm2542_unique_units(preview_rows()))
            self.assertEqual(len(units),9)
            self.assertEqual(units[0]["label"],"Unit 2: Manusia")
            state=_build_state(runtime,5,"SCIENCE",units[0]["value"],
                               "SCI-Y5-PDP-001",
                               {"class":"5 Bestari","date":"2026-11-08",
                                "time":"08:00 - 09:00","students":"35"})
            self.assertEqual(state["selected_sp_codes"],["2.1.1"])
            text=_source_text(runtime,state)
            self.assertIn("Memerihalkan fungsi rangka utama manusia.",text)
            self.assertIn("DRAF/HOLD",text)
            rendered=runtime._rph_rows(state,text)
            self.assertIn("2.1.1 — Memerihalkan fungsi",rendered["STANDARD PEMBELAJARAN"])
            self.assertIn("Aktiviti 1",rendered["AKTIVITI UTAMA"])
            self.assertEqual(rendered["KELAS"],"5 Bestari")
            self.assertEqual(rendered["TARIKH"],"08/11/2026")
            with self.assertRaises(ValueError):
                _resolve_lesson({**state,"sp_code":"2.1.2"})

    def test_authenticated_native_http_units_lessons_and_pdf_word_download(self):
        runtime=make_runtime()
        with patch.dict(os.environ,{
            STAGING_FLAG:"1",STAGING_CONTEXT:"staging","RENDER_SERVICE_ID":"",
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"b"*48,
        }):
            self.assertTrue(install(runtime))
            app=Flask(__name__)
            app.register_blueprint(create_native_sequence_rph_blueprint(runtime))
            client=app.test_client()
            denied=client.get("/internal/rph/v1/sequence/units",
                              query_string={"year":"5","subject":"SCIENCE"})
            self.assertEqual(denied.status_code,401)
            auth={"Authorization":"Bearer "+"b"*48}
            response=client.get("/internal/rph/v1/sequence/units",
                query_string={"year":"5","subject":"SCIENCE"},headers=auth)
            self.assertEqual(response.status_code,200,response.json)
            self.assertEqual(len(response.json["items"]),9)
            unit=response.json["items"][0]["value"]
            lessons=client.get("/internal/rph/v1/sequence/lessons",
                query_string={"year":"5","subject":"SCIENCE","unit":unit},
                headers=auth)
            self.assertEqual(lessons.status_code,200,lessons.json)
            selected=lessons.json["items"][0]
            self.assertEqual(selected["value"],"SCI-Y5-PDP-001")
            self.assertIn("m/s",selected["textbook_ref"])
            avail=client.get("/internal/rph/v1/sequence/availability",
                query_string={"year":"5","subject":"SCIENCE","unit":unit,
                              "lesson":selected["value"]},headers=auth)
            self.assertEqual(avail.status_code,200)
            self.assertTrue(avail.json["available"])
            data={
                "selection":{"year":5,"subject":"SCIENCE","unit":unit,
                             "lesson":selected["value"]},
                "teacher":{"class":"5 Bestari","date":"2026-11-08",
                           "time":"08:00 - 09:00","students":"35"},
            }
            for fmt in ("word","pdf"):
                with self.subTest(fmt=fmt):
                    rsp=client.post("/internal/rph/v1/sequence/render",
                                    json={**data,"format":fmt},headers=auth)
                    self.assertEqual(rsp.status_code,200,rsp.get_json(silent=True))
                    self.assertIn("no-store",rsp.headers.get("Cache-Control",""))
                    self.assertIn("attachment",rsp.headers["Content-Disposition"])
                    if fmt=="word":
                        self.assertTrue(rsp.data.startswith(b"PK"))
                        doc=Document(io.BytesIO(rsp.data))
                        self.assertEqual(len(doc.tables),3)
                        self.assertIn("Memerihalkan fungsi",doc.tables[0].rows[1].cells[1].text)
                    else:
                        self.assertTrue(rsp.data.startswith(b"%PDF-"))
                        pdf=PdfReader(io.BytesIO(rsp.data))
                        self.assertEqual(len(pdf.pages),1)
                        self.assertIn("Memerihalkan fungsi",pdf.pages[0].extract_text())
            wrong=client.post("/internal/rph/v1/sequence/render",
                json={**data,"selection":{**data["selection"],
                      "lesson":"SCI-Y5-PDP-999"},"format":"word"},headers=auth)
            self.assertEqual(wrong.status_code,404)
            noauth=client.post("/internal/rph/v1/sequence/render",
                json={**data,"format":"word"})
            self.assertEqual(noauth.status_code,401)


if __name__=="__main__":
    unittest.main()
