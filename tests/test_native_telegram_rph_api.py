"""Authenticated Telegram native RPH document bridge, no bot state mutations."""
from io import BytesIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from docx import Document
from flask import Flask

from web.native_rph_telegram_api import (
    build_native_input, compact_web_word_notes,
    create_native_rph_blueprint,
)
from web.rph_teacher_reflection import install


def payload(fmt="word"):
    common=[
        {"label":"Subject","value":"Bahasa Inggeris"},
        {"label":"Year / Form","value":"Year 4"},
        {"label":"Date","value":"2027-03-08"},
        {"label":"Day","value":"Monday"},
        {"label":"Time","value":"09:15"},
        {"label":"Class","value":"4 Bestari"},
        {"label":"Number of Pupils","value":"—"},
        {"label":"Topic","value":"Where are you from?"},
        {"label":"Main Content Standard","value":"1.2"},
        {"label":"Main Learning Standard","value":"1.2.2"},
        {"label":"Complementary Content Standard","value":"1.1"},
        {"label":"Complementary Learning Standard","value":"1.1.1"},
        {"label":"Learning Objectives","value":"Pupils can listen for two countries."},
        {"label":"Success Criteria","value":"Two correct answers."},
        {"label":"Prior Knowledge","value":"Country names."},
        {"label":"Teaching and Learning Materials","value":"SB p.5; TB p.18."},
        {"label":"CCE / Values","value":"Respect."},
        {"label":"HOTS / 21st Century Skills","value":"Explain a clue."},
        {"label":"Assessment","value":"Four listening answers."},
    ]
    return {
        "subject":"ENGLISH","component":None,"year":4,"lesson":1,"unit":"Where are you from?",
        "teacher":{"class":"4 Bestari","date":"2027-03-08","time":"09:15"},
        "layout":{
            "style":"telegram-native-rph-v1",
            "header":common,
            "activity_header":["Phase / Time","Teaching and Learning Activities","Notes"],
            "phases":[
                {"label":"Set Induction","activity":"Teacher greets. Pupils respond.","notes":""},
                {"label":"Main Activities","activity":"Activity 1: Listen. Pupils match the flag.","notes":""},
                {"label":"Closure","activity":"Pupils recap the country names.","notes":""},
            ],
            "footer":[{"label":"Remedial / Enrichment","value":"Visual prompts."},
                      {"label":"Reflection","value":"____ pupils met objectives."}],
        },"format":fmt,
    }


class FakeRuntime:
    def __init__(self):
        self.calls=[]
        self.last_path=None

    def _rph_rows(self,state,ai_text):
        return {"REFLEKSI":"____ pupils met objectives.",
                "AKTIVITI UTAMA":"Pupils match the flag."}

    def create_word_file(self,state,ai_text,cid):
        self.calls.append(("word",state,ai_text,cid))
        doc=Document()
        doc.add_paragraph("RANCANGAN PENGAJARAN HARIAN")
        info=doc.add_table(rows=2,cols=2)
        info.cell(0,0).text="Subject";info.cell(0,1).text="English"
        phase=doc.add_table(rows=2,cols=3)
        phase.cell(0,0).text="Phase / Time"
        phase.cell(0,1).text="Teaching and Learning Activities"
        phase.cell(0,2).text="Notes"
        phase.cell(1,0).text="Main Activities"
        phase.cell(1,1).text="Activity 1: Listen. Pupils match the flag."
        phase.cell(1,2).text=""
        footer=doc.add_table(rows=2,cols=2)
        footer.cell(0,0).text="Reflection"
        footer.cell(0,1).text=self._rph_rows(state,ai_text)["REFLEKSI"]
        self.last_path=os.path.join(tempfile.gettempdir(),cid+"_TEST.docx")
        doc.save(self.last_path)
        return self.last_path

    def create_pdf_file(self,state,ai_text,cid):
        self.calls.append(("pdf",state,ai_text,cid))
        self.last_path=os.path.join(tempfile.gettempdir(),cid+"_TEST.pdf")
        Path(self.last_path).write_bytes(b"%PDF-1.4\n"+b"0"*2000)
        return self.last_path


class NativeRPHBridgeTests(unittest.TestCase):
    def setUp(self):
        self.runtime=FakeRuntime()
        app=Flask(__name__)
        app.register_blueprint(create_native_rph_blueprint(self.runtime))
        self.client=app.test_client()
        self.config=patch.dict(os.environ,{
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*48,
        })
        self.config.start();self.addCleanup(self.config.stop)

    def _post(self,p=None,token="x"*48):
        return self.client.post("/internal/rph/v1/render",json=p or payload(),
                                headers={"Authorization":"Bearer "+token})

    def test_disabled_and_invalid_bearer_fail_closed(self):
        with patch.dict(os.environ,{"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"0"}):
            self.assertEqual(self._post().status_code,503)
        self.assertEqual(self._post(token="x"*47).status_code,401)
        self.assertEqual(self.client.post("/internal/rph/v1/render",
                                         headers={"Authorization":"Bearer "+"x"*48},
                                         data="invalid").status_code,400)
        self.assertEqual(self.runtime.calls,[])

    def test_uses_existing_native_word_generator_and_shrinks_notes(self):
        response=self._post()
        self.assertEqual(response.status_code,200,response.get_json() if response.is_json else "")
        self.assertEqual(response.headers["Cache-Control"],"no-store, private")
        self.assertEqual(len(self.runtime.calls),1)
        kind,state,ai_text,cid=self.runtime.calls[0]
        self.assertEqual(kind,"word")
        self.assertEqual(state["subject"],"English")
        self.assertEqual(state["lesson_no"],1)
        self.assertEqual(state["rph_class"],"4 Bestari")
        self.assertEqual(state["rph_day"],"Monday")
        self.assertIn("AKTIVITI UTAMA",ai_text)
        self.assertIn("Pupils match the flag",ai_text)
        self.assertIn("1.2.2",ai_text)
        doc=Document(BytesIO(response.data))
        self.assertEqual(len(doc.tables),3)
        self.assertIn("flag",doc.tables[1].cell(1,1).text)
        self.assertAlmostEqual(doc.tables[1].columns[2].width.cm,1.55,places=1)
        self.assertAlmostEqual(doc.tables[1].columns[1].width.cm,14.55,places=1)
        self.assertFalse(Path(self.runtime.last_path).exists())

    def test_class_full_time_range_and_pupil_count_reach_native_generator(self):
        body=payload()
        body["teacher"]={"class":"4 Bestari","date":"2027-03-08",
                         "time":"07:30 - 08:30","students":"32"}
        response=self._post(body)
        self.assertEqual(response.status_code,200,response.get_json() if response.is_json else "")
        _,state,_,_=self.runtime.calls[0]
        self.assertEqual(state["rph_class"],"4 Bestari")
        self.assertEqual(state["rph_time"],"07:30 - 08:30")
        self.assertEqual(state["rph_students"],"32")
        self.assertEqual(state["rph_date"],"2027-03-08")

    def test_legacy_payload_without_students_still_renders(self):
        response=self._post(payload())
        self.assertEqual(response.status_code,200,response.get_json() if response.is_json else "")
        self.assertEqual(self.runtime.calls[0][1]["rph_students"],"")

    def test_custom_reflection_is_applied_after_source_rows(self):
        install(self.runtime)
        reflection="24 murid mencapai objektif.\nTindakan susulan: bimbingan & latihan."
        for fmt in ("word","pdf"):
            body=payload(fmt)
            body["teacher"]["reflection"]=reflection.replace("\n","\r\n")
            response=self._post(body)
            self.assertEqual(response.status_code,200)
            _,state,source,_=self.runtime.calls[-1]
            rows=self.runtime._rph_rows(state,source)
            self.assertEqual(rows["REFLEKSI"],reflection)
            self.assertEqual(rows["AKTIVITI UTAMA"],"Pupils match the flag.")
            if fmt=="word":
                self.assertEqual(Document(BytesIO(response.data)).tables[2].cell(0,1).text,reflection)
        self.assertIn("____ pupils",self.runtime._rph_rows({}, "")["REFLEKSI"])

    def test_invalid_reflection_does_not_render(self):
        for reflection in (False,"x"*501,"a\n"*6+"a","a\x00b","\ud800"):
            with self.subTest(reflection=reflection):
                body=payload()
                body["teacher"]["reflection"]=reflection
                self.assertEqual(self._post(body).status_code,400)
        self.assertEqual(self.runtime.calls,[])

    def test_rejects_invalid_pupil_counts_before_document_generation(self):
        for students in ("0","201","-5","2.5","1e2"," 32 ","999",
                         "0001","a"*8,32,None):
            with self.subTest(students=students):
                body=payload()
                body["teacher"]["students"]=students
                self.assertEqual(self._post(body).status_code,400)
        self.assertEqual(self.runtime.calls,[])

    def test_pdf_comes_from_telegram_native_pdf_generator(self):
        response=self._post(payload("pdf"))
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.data.startswith(b"%PDF-"))
        self.assertEqual(self.runtime.calls[0][0],"pdf")
        self.assertFalse(Path(self.runtime.last_path).exists())

    def test_rejects_tampered_layout_before_any_generation(self):
        invalid=[
            {"telegram_user_id":456},
            {"year":1},
            {"unit":"X"*400},
            {"teacher":{"class":"<script>","date":"","time":""}},
            {"layout":{"style":"web-fallback"}},
        ]
        for override in invalid:
            body=payload();body.update(override)
            with self.subTest(override=override):
                self.assertEqual(self._post(body).status_code,400)
        self.assertEqual(self.runtime.calls,[])

    def test_source_specific_activities_required(self):
        body=payload()
        body["layout"]["phases"][1]["activity"]="—"
        self.assertEqual(self._post(body).status_code,400)
        self.assertEqual(self.runtime.calls,[])

    def test_no_duplicate_ids_or_account_changes_in_source(self):
        from inspect import getsource
        from web import native_rph_telegram_api as module
        src=getsource(module)
        self.assertNotIn("supabase",src.lower())
        self.assertNotIn("set_webhook",src.lower())
        self.assertNotIn("debit_credit",src.lower())
        self.assertIn("runtime.create_word_file",src)
        self.assertIn("runtime.create_pdf_file",src)
        self.assertIn("CIKGULAJU_WEB_NATIVE_RPH_ENABLED",src)


    def test_strict_source_digest_matches_telegram_bytes(self):
        from web.rph_shared_source_identity import source_fingerprint
        digest=source_fingerprint(4,"ENGLISH",1)
        self.assertRegex(digest,r"^[a-f0-9]{64}$")
        body=payload()
        with patch.dict(os.environ,{"CIKGULAJU_WEB_RPH_SOURCE_PARITY_REQUIRED":"1"}):
            self.assertEqual(self._post(body).status_code,400)
            body["source_digest"]="0"*64
            self.assertEqual(self._post(body).status_code,400)
            body["source_digest"]=digest
            self.assertEqual(self._post(body).status_code,200)
        self.assertEqual(len(self.runtime.calls),1)

    def test_selection_state_matches_pjpk_and_psv_telegram_callbacks(self):
        from web.rph_shared_source_identity import source_fingerprint
        from web.native_rph_telegram_api import build_native_input
        pj=payload()
        pj.update(subject="PJPK",component="PK",year=3,lesson=1,
                  unit="Kemahiran Kesihatan")
        pj["layout"]["activity_header"]=[
            "Fasa / Masa","Aktiviti Pengajaran & Pembelajaran","Catatan"]
        pj["source_digest"]=source_fingerprint(3,"PJPK",1,"PK")
        state,_,_=build_native_input(pj)
        from web.pjpk_2027_preview_runtime import _selection as pj_selected
        self.assertIsNotNone(pj_selected(state))
        self.assertEqual(state["_pjpk_2027_preview_selection"],
                         {"year":3,"subject":"pk","lesson":1})
        self.assertEqual(state["sp_code"],pj_selected(state)["sp"][0])
        psv=payload()
        psv.update(subject="PSV",year=2,lesson=1,unit="Seni Visual")
        psv["layout"]["activity_header"]=[
            "Fasa / Masa","Aktiviti Pengajaran & Pembelajaran","Catatan"]
        psv["source_digest"]=source_fingerprint(2,"PSV",1)
        state,_,_=build_native_input(psv)
        from web.psv_2027_provisional_runtime import _selection as psv_selected
        self.assertIsNotNone(psv_selected(state))
        self.assertEqual(state["subject"],"Pendidikan Seni Visual")



    def test_subject_adapter_guard_uses_actual_telegram_install_state(self):
        # A Web render must use the same installed flags as the Telegram adapters.
        cases = (
            ("PJPK", "CIKGULAJU_PJPK_2027_PREVIEW_INSTALLED",
             {"component": "PJ", "year": 3, "lesson": 10,
              "unit": "Unit 4: Semangat Berjuang"}),
            ("MORAL", "CIKGULAJU_MORAL_80_ACTIVE",
             {"component": None, "year": 3, "lesson": 1,
              "unit": "Nilai Murni"}),
            ("PSV", "PSV_2027_PROVISIONAL_TELEGRAM_ACTIVE",
             {"component": None, "year": 2, "lesson": 1,
              "unit": "Seni Visual"}),
        )
        for subject, installed_flag, changes in cases:
            with self.subTest(subject=subject):
                body = payload("pdf")
                body.update(subject=subject, **changes)
                body["layout"]["activity_header"] = [
                    "Fasa / Masa", "Aktiviti Pengajaran & Pembelajaran", "Catatan"]
                setattr(self.runtime, installed_flag, False)
                denied = self._post(body)
                self.assertEqual(denied.status_code, 503, denied.get_json())
                before = len(self.runtime.calls)
                setattr(self.runtime, installed_flag, True)
                permitted = self._post(body)
                self.assertEqual(permitted.status_code, 200, permitted.get_json() if permitted.is_json else "")
                self.assertEqual(len(self.runtime.calls), before + 1)
                setattr(self.runtime, installed_flag, False)

if __name__=="__main__":
    unittest.main()
