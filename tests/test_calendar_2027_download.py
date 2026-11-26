"""Verify the calendar is free to logged-in users, exact-file-only, and admin upload protected."""
import hashlib,unittest
from unittest.mock import patch
from flask import Flask,Blueprint,jsonify
from web import calendar_2027_download as c

class Calendar(unittest.TestCase):
    def setUp(self):
        self.app=Flask(__name__)
        self.bp=Blueprint("calendar_test",__name__)
        self.account={"telegram_user_id":9}
        c.install_routes(self.bp,lambda:(self.account,None) if self.account else (None,(jsonify({"error":"login"}),401)))
        self.app.register_blueprint(self.bp)
        self.client=self.app.test_client()
        self.blob=b"%PDF-1.7\ncalendar fixture"
        self.data=None
        self.url="/api/rpt/2027/calendar"
        self.origin={"Origin":"https://localhost","Content-Type":"application/pdf"}
    def post(self,blob=None,headers=None):
        return self.client.post(self.url+"/upload",data=self.blob if blob is None else blob,headers=self.origin if headers is None else headers,base_url="https://localhost")
    def test_publish(self):
        def storage(config,method,blob=None):
            from io import BytesIO
            if method=="POST":self.data=blob
            return BytesIO(self.data or b"")
        with patch.object(c,"SIZE",len(self.blob)),patch.object(c,"SHA",hashlib.sha256(self.blob).hexdigest()),patch.object(c,"storage_request",side_effect=storage) as store,patch.object(c,"allowed_admin_ids",return_value={9}),patch("web_v1_telegram_auth_routes._config",return_value={}):
            self.account=None
            self.assertEqual(self.client.get(self.url+".pdf").status_code,401)
            self.account={"telegram_user_id":10}
            self.assertEqual(self.client.get(self.url+"/status").json,{"ready":False,"admin":False})
            self.assertEqual(self.client.get(self.url+".pdf").status_code,503)
            before=store.call_count
            self.assertEqual(self.post().status_code,403)
            self.assertEqual(store.call_count,before)
            self.account={"telegram_user_id":9}
            self.assertEqual(self.post(b"X"*len(self.blob)).status_code,400)
            self.assertEqual(self.post(headers={"Origin":"https://other.example","Content-Type":"application/pdf"}).status_code,400)
            self.assertEqual(store.call_count,before)
            self.assertEqual(self.post().json,{"ready":True})
            self.assertEqual(self.data,self.blob)
            self.assertEqual(self.client.get(self.url+"/status").json,{"ready":True,"admin":True})
            self.account={"telegram_user_id":10}
            response=self.client.get(self.url+".pdf")
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.data,self.blob)
            self.assertIn("attachment",response.headers["Content-Disposition"])
            self.assertEqual(response.headers["X-Calendar-SHA256"],c.SHA)
            self.assertEqual(self.client.get(self.url+"/status").json,{"ready":True,"admin":False})
    def test_pin(self):
        self.assertEqual(c.SIZE,158569)
        self.assertEqual(c.SHA,"546b580c564ef15a7d8b30bb6f27d58be964f001fcb37b24af604248b21088df")
        self.assertFalse(c.valid(b"%PDF-1.7"))
if __name__=="__main__":unittest.main()
