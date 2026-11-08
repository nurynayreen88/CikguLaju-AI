"""All 342 authored Science PdP source selection through native private Web API.

Simulation tests the actual existing Flask native sequence bridge, exact
staging source and Word/PDF contract. Render live E2E still requires a
separate review and teacher/panitia approval is NOT implied by passing CI.
"""
from __future__ import annotations

from collections import Counter
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from web.sains_342_native_staging_source_20261108 import (
    FLAG,CONTEXT,EXPECTED,_catalog,_selected,_review_text,install,preview_rows,
)
from web.telegram_verified_sequence_rph_bridge import (
    _build_state,_source_text,_unit_catalog,create_native_sequence_rph_blueprint,
)


def fake_runtime():
    def unique_units(rows):
        out=[];seen=set()
        for row in rows:
            key=row["unit_code"],row["unit_title"]
            if key not in seen:
                out.append(key);seen.add(key)
        return out

    def commit(state, mapped):
        if not mapped:
            raise ValueError("Source SP missing")
        state["sk_code"]=mapped[0]["sk_code"]
        state["sp_code"]=mapped[0]["sp_code"]
        state["grouped_sp_codes"]=[r["sp_code"] for r in mapped]

    def render(state,text,unique,kind):
        item=_selected(state)
        if item is None or item["pdp_code"] not in text:
            raise ValueError("Wrong Year/Code/SP in new Science native source")
        path=Path(tempfile.gettempdir())/(unique+"_Sains."+
             ("docx" if kind=="word" else "pdf"))
        if kind=="word":
            d=Document()
            h=d.add_table(rows=2,cols=2)
            h.cell(0,0).text="Sains "+str(item["year"])
            h.cell(0,1).text="PdP "+str(item["pdp_number"])+" DRAF/HOLD"
            h.cell(1,0).text=item["unit"]
            h.cell(1,1).text=item["sp"]+": "+item["title"]
            a=d.add_table(rows=3,cols=3)
            for i,(phase,body) in enumerate([
                ("Aktiviti 1",item["teacher1"]+" / "+item["pupil1"]),
                ("Aktiviti 2",item["teacher2"]+" / "+item["pupil2"]),
                ("PBD",item["pbd"]),
            ]):
                a.cell(i,0).text=phase
                a.cell(i,1).text=body
                a.cell(i,2).text="Bukti individu"
            foot=d.add_table(rows=1,cols=2)
            foot.cell(0,0).text="BBM "+item["materials"]
            foot.cell(0,1).text="DRAF/HOLD"
            d.save(path)
        else:
            canvas=Canvas(str(path),pagesize=A4)
            canvas.setFont("Helvetica",12)
            canvas.drawString(40,780,"SAINS DRAF/HOLD - INTERNAL REVIEW")
            canvas.drawString(40,750,item["pdp_code"])
            canvas.drawString(40,730,"SP "+item["sp"])
            canvas.drawString(40,710,"Aktiviti 1 - PBD specific review")
            canvas.drawString(40,690,"Aktiviti 2 - PBD specific review")
            canvas.save()
        return str(path)

    return SimpleNamespace(
        CIKGULAJU_DB_V2600_ACTIVE=True,
        _sm2542_rows=lambda year,sub:[{"legacy":True,"year":year,"subject":sub}],
        _sm2542_unique_units=unique_units,
        _commit_multi_sp=commit,
        _local_rph_text=lambda state:"Original English/Maths RPH remains unchanged",
        _rph_rows=lambda state,*args,**kwargs:{
            "KELAS":state.get("rph_class",""),
            "TARIKH":state.get("rph_date",""),
            "MASA":state.get("rph_time",""),
        },
        create_word_file=lambda state,text,unique:render(state,text,unique,"word"),
        create_pdf_file=lambda state,text,unique:render(state,text,unique,"pdf"),
    )


class TestScience342StagingNoBuild(unittest.TestCase):
    def test_zero_ephemeral_build_dependencies_and_correct_342_sp_identity(self):
        _catalog.cache_clear()
        # If the source called its legacy runtime analyze() it would try to
        # read ephemeral build/ CSVs. Never do that for staging reviewer.
        import tools.audit_sains_342_pdp_release_gate_20261106 as runtime_audit
        with patch.object(runtime_audit,"analyze",side_effect=AssertionError(
                "Do NOT read ephemeral CI-generated Source DRAF indices")):
            all_rows=_catalog()
        self.assertEqual(len(all_rows),342)
        self.assertEqual(Counter(x["year"] for x in all_rows.values()),EXPECTED)
        self.assertEqual(len({x["pdp_code"] for x in all_rows.values()}),342)
        for year,count in EXPECTED.items():
            rows=preview_rows(year)
            self.assertEqual(len(rows),count)
            self.assertEqual([r["source_sequence_no"] for r in rows],
                             list(range(1,count+1)))
            self.assertTrue(all(r["verification_status"].startswith("STAGING_DRAF_HOLD")
                                for r in rows))
            self.assertTrue(all(not all_rows[r["pdp_sequence_code"]]["academic_approval"]
                                for r in rows))
            for row in rows:
                item=all_rows[row["pdp_sequence_code"]]
                self.assertEqual(row["sp_code"],item["sp"])
                self.assertEqual(row["unit_title"],item["unit"])
                self.assertEqual(row["sk_code"],item["sk"])
                self.assertEqual(len(row["activitybook_ref"]),0)
                self.assertGreater(len(_review_text(item)),500)
                if year in (4,5):
                    self.assertTrue(row["sp_text"].endswith("."))

    def test_flag_off_or_production_service_never_modifies_native_runtime(self):
        runtime=fake_runtime()
        old=(runtime._sm2542_rows,runtime._local_rph_text,runtime._rph_rows)
        with patch.dict(os.environ,{FLAG:"0",CONTEXT:"staging"}):
            self.assertFalse(install(runtime))
        self.assertEqual(old,(runtime._sm2542_rows,runtime._local_rph_text,runtime._rph_rows))
        for environment,service,prior in (
            ("production","","0"),
            ("staging","srv-dah3b8lbedkc738ugqt0","0"),
            ("staging","srv-dbm5go8u01pc738f40cg","0"),
            ("staging","","1"),
        ):
            candidate=fake_runtime()
            with self.subTest(environment=environment,service=service,prior=prior):
                with patch.dict(os.environ,{
                        FLAG:"1",CONTEXT:environment,"RENDER_SERVICE_ID":service,
                        "CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW":prior,
                }):
                    with self.assertRaises(RuntimeError):
                        install(candidate)
                    self.assertFalse(getattr(candidate,
                        "CIKGULAJU_SAINS_342_INTERNAL_REVIEW_ACTIVE",False))

    def test_staging_overrides_only_science_year2_to6_with_exact_SP_and_PBD(self):
        runtime=fake_runtime()
        with patch.dict(os.environ,{FLAG:"1",CONTEXT:"staging",
                                    "RENDER_SERVICE_ID":"",
                                    "CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW":"0"}):
            self.assertTrue(install(runtime))
            self.assertTrue(install(runtime))  # idempotent
            self.assertEqual(runtime._sm2542_rows("Tahun 1","Sains")[0]["legacy"],True)
            self.assertEqual(runtime._sm2542_rows("Tahun 5","Matematik")[0]["legacy"],True)
            for year in EXPECTED:
                rows=runtime._sm2542_rows(f"Tahun {year}","Sains")
                units=_unit_catalog(runtime._sm2542_unique_units(rows))
                self.assertGreaterEqual(len(units),7)
                first=rows[0]
                token=next(x["value"] for x in units if x["label"]==first["unit_title"])
                state=_build_state(runtime,year,"SCIENCE",token,
                                   first["pdp_sequence_code"],{
                                       "class":"5 Bestari","date":"2026-11-08",
                                       "time":"08:00 - 09:00","students":"35",
                                   })
                self.assertEqual(state["sp_code"],first["sp_code"])
                self.assertEqual(state["selected_sp_codes"],[first["sp_code"]])
                lesson=_source_text(runtime,state)
                self.assertIn(first["sp_code"],lesson)
                self.assertIn("DRAF",lesson)
                contents=runtime._rph_rows(state,lesson)
                self.assertIn(first["sp_code"],contents["STANDARD PEMBELAJARAN"])
                self.assertIn("Aktiviti 1",contents["AKTIVITI UTAMA"])
                self.assertIn("Aktiviti 2",contents["AKTIVITI UTAMA"])
                self.assertIn("Bukti individu",contents["PENTAKSIRAN"])
                self.assertEqual(contents["KELAS"],"5 Bestari")
                with self.assertRaises(ValueError):
                    _selected({**state,"sp_code":"9.9.9"})

    def test_authenticated_native_http_all_five_years_pdf_and_word(self):
        runtime=fake_runtime()
        with patch.dict(os.environ,{
            FLAG:"1",CONTEXT:"staging","RENDER_SERVICE_ID":"",
            "CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW":"0",
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"p"*48,
        }):
            self.assertTrue(install(runtime))
            app=Flask(__name__)
            app.register_blueprint(create_native_sequence_rph_blueprint(runtime))
            client=app.test_client()
            unauthorized=client.get("/internal/rph/v1/sequence/units",
                         query_string={"year":"2","subject":"SCIENCE"})
            self.assertEqual(unauthorized.status_code,401)
            headers={"Authorization":"Bearer "+"p"*48}
            for year in EXPECTED:
                with self.subTest(year=year):
                    units=client.get("/internal/rph/v1/sequence/units",
                         query_string={"year":year,"subject":"SCIENCE"},
                         headers=headers)
                    self.assertEqual(units.status_code,200,units.json)
                    unit_token=units.json["items"][0]["value"]
                    lessons=client.get("/internal/rph/v1/sequence/lessons",
                         query_string={"year":year,"subject":"SCIENCE",
                                       "unit":unit_token},headers=headers)
                    self.assertEqual(lessons.status_code,200,lessons.json)
                    first=lessons.json["items"][0]["value"]
                    self.assertEqual(first,f"SCI-Y{year}-PDP-001")
                    available=client.get("/internal/rph/v1/sequence/availability",
                          query_string={"year":year,"subject":"SCIENCE",
                                        "unit":unit_token,"lesson":first},
                          headers=headers)
                    self.assertEqual(available.status_code,200,available.json)
                    self.assertTrue(available.json["available"])
                    request={
                        "selection":{"year":year,"subject":"SCIENCE",
                                     "unit":unit_token,"lesson":first},
                        "teacher":{"class":"5 Bestari","date":"2026-11-08",
                                   "time":"08:00 - 09:00","students":"35"},
                    }
                    for fmt in ("word","pdf"):
                        response=client.post("/internal/rph/v1/sequence/render",
                             json={**request,"format":fmt},headers=headers)
                        self.assertEqual(response.status_code,200,
                                         (year,fmt,response.get_json(silent=True)))
                        self.assertIn("attachment",response.headers["Content-Disposition"])
                        if fmt=="word":
                            doc=Document(io.BytesIO(response.data))
                            self.assertEqual(len(doc.tables),3)
                            self.assertIn(first.split("-")[-1],doc.tables[0].rows[0].cells[1].text)
                        else:
                            pdf=PdfReader(io.BytesIO(response.data))
                            self.assertEqual(len(pdf.pages),1)
                            self.assertIn(first,pdf.pages[0].extract_text())
                    missing=client.get("/internal/rph/v1/sequence/availability",
                         query_string={"year":year,"subject":"SCIENCE",
                                       "unit":unit_token,"lesson":"SCI-Y9-PDP-999"},
                         headers=headers)
                    self.assertEqual(missing.status_code,404)


if __name__=="__main__":
    unittest.main()
