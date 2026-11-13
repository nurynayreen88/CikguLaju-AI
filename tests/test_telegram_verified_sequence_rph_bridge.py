"""Telegram-native Math/Science PdP RPH must preserve exact grouped SK/SP."""
import os
import unittest
from unittest.mock import Mock,patch
from flask import Flask

from web.telegram_verified_sequence_rph_bridge import (
    _source, _unit_catalog, _resolve, _build_state,
    create_native_sequence_rph_blueprint, SourceUnavailable,
)


def rows():
    return [
        {"unit_code":"1.0","unit_title":"Nombor Bulat","pdp_sequence_code":"M2-PDP-007",
         "source_sequence_no":7, "pdp_title":"Tambah dengan mengumpul semula",
         "subject":"Matematik","sk_code":"2.1","sp_code":"2.1.1",
         "theme":"Nombor","textbook_ref":"BT ms. 23","skill_metadata":"operasi tambah"},
        {"unit_code":"1.0","unit_title":"Nombor Bulat","pdp_sequence_code":"M2-PDP-007",
         "source_sequence_no":7,"pdp_title":"Tambah dengan mengumpul semula",
         "subject":"Matematik","sk_code":"2.1","sp_code":"2.1.2",
         "theme":"Nombor","textbook_ref":"BT ms. 23","skill_metadata":"operasi tambah"},
        {"unit_code":"1.0","unit_title":"Nombor Bulat","pdp_sequence_code":"M2-PDP-008",
         "source_sequence_no":8,"pdp_title":"Tolak","subject":"Matematik",
         "sk_code":"2.2","sp_code":"2.2.1"},
    ]


class NativeMathScienceTests(unittest.TestCase):
    def setUp(self):
        self.runtime=Mock()
        self.runtime.CIKGULAJU_DB_V2600_ACTIVE=True
        self.runtime._sm2542_rows.return_value=rows()
        self.runtime._sm2542_unique_units.return_value=[("1.0","Nombor Bulat")]
        def commit(state,mapped):
            state["sp_code"]=mapped[0]["sp_code"]
            state["sk_code"]=mapped[0]["sk_code"]
            state["selected_sp_codes"]=[x["sp_code"] for x in mapped]
            state["grouped_sp_codes"]=[x["sp_code"] for x in mapped]
        self.runtime._commit_multi_sp.side_effect=commit
        self.runtime._local_rph_text.return_value=(
            "OBJEKTIF PEMBELAJARAN: Murid menguasai pengumpulan semula.\n"
            "AKTIVITI 1: Murid menggunakan blok asas 10.\n"
            "AKTIVITI 2: Murid menyusun puluh dan sa.\n"
            "AKTIVITI 3: Murid menulis ayat matematik dan membuat semakan.\n"*10)
        self.unit=_unit_catalog([("1.0","Nombor Bulat")])[0]["value"]

    def test_native_grouping_preserves_two_sps_for_same_pdp(self):
        teacher={"class":"2 Bestari","date":"2026-11-06",
                 "time":"07:30 - 08:30","students":"32"}
        state=_build_state(self.runtime,2,"MATH",self.unit,"M2-PDP-007",teacher)
        self.assertEqual(state["subject"],"Matematik")
        self.assertEqual(state["selected_sp_codes"],["2.1.1","2.1.2"])
        self.assertEqual(state["pdp_title"],"Tambah dengan mengumpul semula")
        self.assertEqual(state["rph_students"],"32")
        self.assertEqual(state["rph_date"],"06/11/2026")

    def test_wrong_unit_or_pdp_is_rejected(self):
        for unit, pdp in (("u"+"0"*24,"M2-PDP-007"),
                          (self.unit,"M2-PDP-999")):
            with self.subTest(unit=unit,pdp=pdp), self.assertRaises(SourceUnavailable):
                _resolve(self.runtime,2,"MATH",unit,pdp)

    def test_no_weak_sps_can_pass(self):
        self.runtime._sm2542_rows.return_value=[
            {**rows()[0],"sk_code":"","sp_code":""}]
        with self.assertRaises(SourceUnavailable):
            _resolve(self.runtime,2,"MATH",self.unit,"M2-PDP-007")

    def test_science_copy_pages_follow_sp_when_database_ids_are_reused(self):
        for year, unit_code, title, code, sk, sp, pages in (
            (2, "4.1", "Haiwan", "SCI-Y2-PDP-004", "4.1", "4.1.1", "36–37"),
            (2, "4.1", "Haiwan", "SCI-Y2-PDP-004", "4.1", "4.1.4", "41–42"),
            (3, "Manusia", "Manusia / 3.1 Gigi", "SCI-Y3-PDP-005", "3.1", "3.1.1", "30–31"),
            (3, "Manusia", "Manusia / 3.1 Gigi", "SCI-Y3-PDP-005", "3.1", "3.1.5", "38"),
        ):
            with self.subTest(year=year, code=code, sp=sp):
                row = {"unit_code": unit_code, "unit_title": title, "pdp_sequence_code": code,
                       "sk_code": sk, "sp_code": sp}
                self.runtime._sm2542_rows.return_value = [row]
                self.runtime._sm2542_unique_units.return_value = [(unit_code, title)]
                app = Flask(__name__)
                app.register_blueprint(create_native_sequence_rph_blueprint(self.runtime))
                client = app.test_client()
                args = {"year": year, "subject": "SCIENCE", "unit": _unit_catalog(
                    [(unit_code, title)])[0]["value"]}
                route = "/internal/rph/v1/sequence/lessons"
                with patch.dict(os.environ, {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                             "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 40}):
                    headers = {"Authorization": "Bearer " + "x" * 40}
                    item, = client.get(route, query_string=args, headers=headers).json["items"]
                    self.assertEqual(item["science_copy_pages"], pages)
                    self.assertEqual(item["textbook_ref"], f"Buku Teks m/s {pages}")
                    row["textbook_ref"] = "Buku Teks m/s 98"
                    item, = client.get(route, query_string=args, headers=headers).json["items"]
                    self.assertNotIn("science_copy_pages", item)
                    self.assertEqual(item["textbook_ref"], "Buku Teks m/s 98")

    def test_unit_and_pdp_routes_require_strong_server_auth(self):
        app=Flask(__name__)
        app.register_blueprint(create_native_sequence_rph_blueprint(self.runtime))
        client=app.test_client()
        with patch.dict(os.environ,{
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*40
        }):
            denied=client.get("/internal/rph/v1/sequence/units",
                              query_string={"year":"2","subject":"MATH"})
            self.assertEqual(denied.status_code,401)
            headers={"Authorization":"Bearer "+"x"*40}
            approved=client.get("/internal/rph/v1/sequence/units",
                                query_string={"year":"2","subject":"MATH"},
                                headers=headers)
            self.assertEqual(approved.status_code,200)
            self.assertEqual(approved.json["items"][0]["value"],self.unit)
            lessons=client.get("/internal/rph/v1/sequence/lessons",
                               query_string={"year":"2","subject":"MATH","unit":self.unit},
                               headers=headers)
            self.assertEqual(lessons.status_code,200)
            self.assertEqual(len(lessons.json["items"]),2)
            self.assertEqual(lessons.json["items"][0]["textbook_ref"], "BT ms. 23")
            self.assertNotIn("textbook_ref", lessons.json["items"][1])


if __name__=="__main__":
    unittest.main()
