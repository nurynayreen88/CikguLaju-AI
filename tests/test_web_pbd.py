import io
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile

from flask import Flask, jsonify

from web import pbd_routes as pbd
from web import pbd_store


class PbdTests(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(pbd.bp)
        self.client = self.app.test_client()
        self.url = "/api/web/pbd/"
        self.query = "?class=3+Amanah&year=2026"
        self.origin = {"Origin": "https://localhost"}
        self.uid = 101
        self.students = [{"id": str(uuid4()), "name": "Murid Contoh", "code": "M01"}]
        conf = {"supabase_url": "https://test.invalid", "supabase_key": "synthetic"}
        self.auth = self.enterContext(patch.object(pbd, "_auth", return_value=(conf, self.uid, None)))
        self.enterContext(patch.object(pbd, "get_profile", return_value={"class_names": ["3 Amanah"]}))

    def test_unauthenticated_and_foreign_class(self):
        with self.app.app_context():
            rejected = (jsonify({"error":"Sila log masuk"}), 401)
        with patch.object(pbd, "_auth", return_value=(None, None, rejected)):
            self.assertEqual(self.client.get(self.url + "classes").status_code, 401)
            self.assertEqual(self.client.get(self.url + "roster-count" + self.query).status_code, 401)
        with patch.object(pbd, "one") as lookup:
            self.assertEqual(self.client.get(self.url + "roster?class=3+Bestari&year=2026").status_code, 400)
            lookup.assert_not_called()

    def test_roster_count_only_returns_count_for_the_saved_class_and_year(self):
        with patch.object(pbd_store, "request_rows", return_value=[{"students":self.students}]) as rows:
            result = self.client.get(self.url + "roster-count" + self.query)
            self.assertEqual(result.get_json(), {"count":1})
            self.assertIn("no-store", result.headers["Cache-Control"])
            self.assertEqual(rows.call_args.args[1:], (self.uid, pbd.ROSTERS, "GET", {
                "class_name":"eq.3 Amanah", "school_year":"eq.2026", "select":"students", "limit":1,
            }))
            rows.reset_mock()
            self.assertEqual(self.client.get(
                self.url + "roster-count?class=3+Bestari&year=2026").status_code, 400)
            rows.assert_not_called()
            rows.return_value = []
            self.assertEqual(self.client.get(self.url + "roster-count" + self.query).get_json(), {"count":0})

    def test_import_preview_keeps_only_name_and_class_code(self):
        data = io.BytesIO()
        main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        doc = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        package = "http://schemas.openxmlformats.org/package/2006/relationships"
        with ZipFile(data, "w") as z:
            z.writestr("xl/workbook.xml", f'<workbook xmlns="{main}" xmlns:r="{doc}"><sheets><sheet name="Senarai Murid" r:id="rId1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels", f'<Relationships xmlns="{package}"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{main}"><si><t>Nama Murid</t></si><si><t>Murid Contoh</t></si></sst>')
            z.writestr("xl/worksheets/sheet1.xml", f'''
                <worksheet xmlns="{main}"><sheetData>
                <row r="1"><c r="A1" t="s"><v>0</v></c>
                <c r="B1" t="inlineStr"><is><t>No. Kad Pengenalan</t></is></c>
                <c r="C1" t="inlineStr"><is><t>Kod Murid (Pilihan)</t></is></c>
                <c r="D1" t="inlineStr"><is><t>Penjaga</t></is></c></row>
                <row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>000000000000</v></c>
                <c r="C2" t="inlineStr"><is><t>M01</t></is></c>
                <c r="D2" t="inlineStr"><is><t>Penjaga Contoh</t></is></c></row>
                </sheetData></worksheet>
            ''')
        data.seek(0)
        with patch.object(pbd, "write") as save:
            result = self.client.post(self.url + "import", data={"file": (data, "kelas.xlsx")}, headers=self.origin)
            self.assertEqual(result.status_code, 200, result.json)
            self.assertEqual(result.json, {"students":[{"name":"Murid Contoh","code":"M01"}]})
            save.assert_not_called()

    def test_import_rejects_non_workbook_and_cross_origin(self):
        self.assertEqual(self.client.post(self.url + "import", data={"file":(io.BytesIO(b"bad"),"a.xlsx")},
                                          headers=self.origin).status_code,400)
        self.assertEqual(self.client.post(self.url + "import", data={"file":(io.BytesIO(b"Nama Murid\nMurid"),"a.csv")},
                                          headers={"Origin":"https://other.invalid"}).status_code,400)

    def test_roster_save_retains_existing_id_and_rejects_stale_write(self):
        version = str(uuid4())
        with patch.object(pbd, "one", return_value={"students": self.students, "version": version}), \
             patch.object(pbd, "write", side_effect=lambda c,u,t,f,v,old: v) as save:
            stale = self.client.put(self.url + "roster" + self.query,
                                    json={"students":self.students,"version":""},headers=self.origin)
            self.assertEqual(stale.status_code,409)
            save.assert_not_called()
            valid = self.client.put(self.url + "roster" + self.query,
                                    json={"students":self.students,"version":version},headers=self.origin)
            self.assertEqual(valid.status_code,200)
            self.assertEqual(valid.json["students"][0]["id"],self.students[0]["id"])
            self.assertEqual(save.call_args.args[1],self.uid)

    def record_data(self, kind="assessment"):
        return {"id":str(uuid4()),"version":"","kind":kind,"date":"2026-11-13","subject":"English",
                "lesson":"Lesson 39","sk":"2.1","sp":"2.1.5","criteria1":"Describe one picture",
                "criteria2":"","period":"Akhir sesi","entries":[{"id":self.students[0]["id"],
                "status1":"","status2":"","method":"Lisan","note":"","followup":"","tp":"TP4"}]}

    def test_assessment_and_report_store_distinct_values(self):
        data = self.record_data()
        def lookup(conf,uid,table,filters):
            return {"students":self.students,"version":str(uuid4())} if table==pbd.ROSTERS else None
        with patch.object(pbd,"one",side_effect=lookup), \
             patch.object(pbd,"write",side_effect=lambda c,u,t,f,v,old: v) as save:
            result=self.client.post(self.url+"records"+self.query,json=data,headers=self.origin)
            self.assertEqual(result.status_code,200,result.json)
            row=save.call_args.args[4]["details"]["entries"][0]
            self.assertEqual(row["status1"],"Belum dinilai")
            self.assertNotIn("status2",row)
            self.assertNotIn("tp",row)
            data=self.record_data("report")
            result=self.client.post(self.url+"records"+self.query,json=data,headers=self.origin)
            self.assertEqual(result.status_code,200,result.json)
            row=save.call_args.args[4]["details"]["entries"][0]
            self.assertEqual(row["tp"],"TP4")
            self.assertNotIn("status1",row)

    def test_history_scoped_and_filter_uses_student_id(self):
        key=self.students[0]["id"]
        with patch.object(pbd,"request_rows",return_value=[]) as rows:
            result=self.client.get(self.url+"records"+self.query+"&student="+key)
        self.assertEqual(result.json,{"records":[],"more":False})
        args=rows.call_args.args
        self.assertEqual(args[1],self.uid)
        self.assertEqual(args[4]["class_name"],"eq.3 Amanah")
        self.assertIn(key,args[4]["details"])

    def test_csv_prefix_and_conflict(self):
        data=self.record_data("report")
        data["entries"][0]["note"]="=1+2"
        saved={**pbd.clean_record(data,self.students),"id":data["id"],"version":str(uuid4())}
        target=self.url+"records/"+saved["id"]+self.query
        with patch.object(pbd,"one",return_value=saved):
            response=self.client.get(target+"&format=csv")
        self.assertEqual(response.status_code,200)
        self.assertIn("'=1+2",response.get_data(as_text=True))
        self.assertEqual(response.headers["Cache-Control"],"private, no-store")
        with patch.object(pbd,"request_rows",return_value=[]) as rows:
            result=self.client.delete(target,json={"version":saved["version"]},headers=self.origin)
        self.assertEqual(result.status_code,409)
        self.assertEqual(rows.call_args.args[1],self.uid)

    def test_store_forces_server_owner_and_prevents_redirect(self):
        with patch.object(pbd_store,"build_opener") as open_factory:
            opener=open_factory.return_value
            opener.open.return_value.__enter__.return_value.read.return_value=b"[]"
            pbd_store.request_rows({"supabase_url":"https://test.invalid","supabase_key":"synthetic"},
                                   101,pbd.RECORDS,"POST",{"teacher_id":"eq.999"},{"teacher_id":999})
        req=opener.open.call_args.args[0]
        self.assertIn("teacher_id=eq.101",req.full_url)
        self.assertEqual(req.data,b'{"teacher_id": 101}')
        self.assertIsInstance(open_factory.call_args.args[0],pbd_store.NoRedirect)
