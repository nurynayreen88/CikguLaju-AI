"""Verify actual bundled approved bytes and direct download without admin upload."""
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask,Blueprint,jsonify
from web import calendar_2027_download as c

class Calendar(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        bp=Blueprint("calendar_test",__name__)
        self.account={"telegram_user_id":9}
        c.install_routes(bp,lambda:(self.account,None) if self.account else (None,(jsonify({"error":"login"}),401)))
        app.register_blueprint(bp)
        self.client=app.test_client()
        self.url="/api/rpt/2027/calendar"
    def test_exact_original_and_free_download(self):
        blob=c.PATH.read_bytes()
        self.assertEqual(len(blob),158569)
        self.assertEqual(hashlib.sha256(blob).hexdigest(),"546b580c564ef15a7d8b30bb6f27d58be964f001fcb37b24af604248b21088df")
        self.assertTrue(c.valid(blob))
        self.account=None
        self.assertEqual(self.client.get(self.url+".pdf").status_code,401)
        self.account={"telegram_user_id":10}
        self.assertEqual(self.client.get(self.url+"/status").json,{"ready":True})
        response=self.client.get(self.url+".pdf")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data,blob)
        self.assertEqual(response.headers["X-Calendar-SHA256"],c.SHA)
        self.assertIn("attachment",response.headers["Content-Disposition"])
        self.assertIn(c.NAME,response.headers["Content-Disposition"])
        self.assertEqual(self.client.post(self.url+"/upload",data=blob).status_code,404)
    def test_missing_and_tampered(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"bad.pdf"
            with patch.object(c,"PATH",path):
                for data in (None,b"%PDF-1.7",b"X"*c.SIZE):
                    if data is not None:path.write_bytes(data)
                    self.assertEqual(self.client.get(self.url+"/status").json,{"ready":False})
                    self.assertEqual(self.client.get(self.url+".pdf").status_code,503)
    def test_ui_no_chooser(self):
        html=(Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"index.html").read_text("utf-8")
        self.assertIn('href="/api/rpt/2027/calendar.pdf"',html)
        self.assertIn('download="'+c.NAME+'"',html)
        for token in ("calendar2027-file","calendar2027-admin","calendar2027-upload","/api/rpt/2027/calendar/upload"):
            self.assertNotIn(token,html)

if __name__=="__main__":unittest.main()
