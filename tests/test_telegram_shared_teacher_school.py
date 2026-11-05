"""Telegram native school editing; all existing callback and timetable flows preserved."""
from copy import deepcopy
from types import SimpleNamespace
from urllib.parse import parse_qs
import unittest
from flask import Flask

from web.shared_teacher_school_telegram import install

STAMP="2026-11-05T12:35:00+00:00"


class Runtime:
    def __init__(self):
        self.app=Flask("teacher-profile-test")
        self.state={}
        self.sent=[]
        self.legacy_updates=[]
        self.callback_log=[]
        self.db_writes=[]
        self.profile={
            "telegram_user_id":123,
            "display_name":"Cikgu A",
            "school_name":"SK Lama",
            "state_name":"Johor",
            "class_names":["4 Bestari"],
            "class_profiles":[{"name":"4 Bestari","students":32,"timetable":[
                {"day":"Isnin","start":"07:30","end":"08:30","subject":"Matematik"}]}],
            "updated_at":STAMP,
        }
        @self.app.post("/webhook")
        def webhook():
            self.legacy_updates.append(1)
            return {"ok":True,"legacy":True}

    def _teacher_profile(self,cid):
        return deepcopy(self.profile) if cid==123 else None

    def _sb_request(self,method,path,**kwargs):
        self.db_writes.append((method,path,deepcopy(kwargs)))
        assert method=="PATCH"
        assert path.startswith("teacher_profiles?")
        query=parse_qs(path.split("?",1)[1])
        assert query["telegram_user_id"]==["eq.123"]
        assert query["select"]==["telegram_user_id,updated_at"]
        if query["updated_at"] != ["eq."+self.profile["updated_at"]]:
            return []
        assert set(kwargs["json"])=={"school_name","updated_at"}
        self.profile.update(deepcopy(kwargs["json"]))
        return [{"telegram_user_id":123,"updated_at":self.profile["updated_at"]}]

    def _profile_edit_menu(self,cid):
        return self.send(cid,"Old profile edit")

    def _clean_profile_page_v25296(self,cid):
        return self.send(cid,"Old profile page")

    def _profile_class_records(self,cid):
        return deepcopy(self.profile["class_profiles"])

    def _profile_access_label_v25296(self,cid):
        return "Rakan Pembangun"

    def _profile_daily_readiness_v25296(self,cid):
        return "Jadual waktu tersedia"

    def callback(self,cid,data):
        self.callback_log.append((cid,data))
        return "original-callback"

    def send(self,cid,text,kb=None):
        self.sent.append((cid,text,kb))
        return {"ok":True}


class SchoolBridgeTests(unittest.TestCase):
    def setUp(self):
        self.rt=Runtime()
        self.assertTrue(install(self.rt))
        self.client=self.rt.app.test_client()

    def test_menus_show_web_school_and_keep_other_actions(self):
        self.rt._clean_profile_page_v25296(123)
        self.assertIn("Sekolah: <b>SK Lama</b>",self.rt.sent[-1][1])
        self.assertIn("📅 LIHAT / URUS JADUAL",str(self.rt.sent[-1][2]))
        self.rt._profile_edit_menu(123)
        buttons=str(self.rt.sent[-1][2])
        self.assertIn("profedit_school",buttons)
        self.assertIn("profedit_name",buttons)
        self.assertIn("profclass_manage",buttons)

    def test_telegram_school_edit_updates_exact_shared_profile_row_only(self):
        self.rt.callback(123,"profedit_school")
        self.assertEqual(self.rt.state[123]["waiting"],"profile_school_shared")
        response=self.client.post("/webhook",json={
            "update_id":400,"message":{"chat":{"id":123,"type":"private"},
            "from":{"id":123},"text":"SK Baharu"}
        })
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.rt.profile["school_name"],"SK Baharu")
        self.assertEqual(len(self.rt.db_writes),1)
        self.assertEqual(self.rt.db_writes[0][0],"PATCH")
        self.assertEqual(self.rt.db_writes[0][2]["json"]["school_name"],"SK Baharu")
        self.assertEqual(self.rt.profile["class_profiles"][0]["students"],32)
        self.assertEqual(self.rt.profile["class_profiles"][0]["timetable"][0]["subject"],"Matematik")
        self.assertEqual(self.rt.legacy_updates,[])
        self.assertNotIn("waiting",self.rt.state[123])
        self.assertIn("Sekolah: <b>SK Baharu</b>",self.rt.sent[-1][1])

    def test_webhook_replay_does_not_rewrite_or_call_legacy(self):
        self.rt.callback(123,"profedit_school")
        payload={"update_id":401,"message":{"chat":{"id":123,"type":"private"},
            "from":{"id":123},"text":"SK Baharu"}}
        self.client.post("/webhook",json=payload)
        second=self.client.post("/webhook",json=payload)
        self.assertEqual(second.status_code,200)
        self.assertEqual(second.get_json().get("duplicate"),True)
        self.assertEqual(len(self.rt.db_writes),1)
        self.assertEqual(self.rt.legacy_updates,[])

    def test_other_sender_cannot_edit_pending_profile(self):
        self.rt.callback(123,"profedit_school")
        response=self.client.post("/webhook",json={"update_id":402,"message":{
            "chat":{"id":123,"type":"private"},"from":{"id":999},"text":"SK Palsu"}})
        self.assertEqual(response.get_json()["legacy"],True)
        self.assertEqual(self.rt.profile["school_name"],"SK Lama")
        self.assertEqual(self.rt.db_writes,[])

    def test_school_callback_navigation_cancels_edit_state(self):
        self.rt.callback(123,"profedit_school")
        self.rt.callback(123,"home")
        self.assertEqual(self.rt.callback_log[-1],(123,"home"))
        self.assertNotIn("waiting",self.rt.state[123])
        response=self.client.post("/webhook",json={"update_id":403,"message":{
            "chat":{"id":123,"type":"private"},"from":{"id":123},"text":"SK Jangan Simpan"}})
        self.assertEqual(response.get_json()["legacy"],True)
        self.assertEqual(self.rt.db_writes,[])

    def test_cancel_and_validation_no_data_changed(self):
        self.rt.callback(123,"profedit_school")
        response=self.client.post("/webhook",json={"update_id":404,"message":{
            "chat":{"id":123,"type":"private"},"from":{"id":123},"text":"x"*161}})
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.rt.db_writes,[])
        cancel=self.client.post("/webhook",json={"update_id":405,"message":{
            "chat":{"id":123,"type":"private"},"from":{"id":123},"text":"/cancel"}})
        self.assertEqual(cancel.status_code,200)
        self.assertEqual(self.rt.db_writes,[])
        self.assertNotIn("waiting",self.rt.state[123])

    def test_stale_telegram_edit_does_not_overwrite_web_school(self):
        self.rt.callback(123,"profedit_school")
        self.rt.profile["updated_at"]="2026-11-05T13:00:00+00:00"
        response=self.client.post("/webhook",json={"update_id":406,"message":{
            "chat":{"id":123,"type":"private"},"from":{"id":123},"text":"SK Cuba"}})
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.rt.profile["school_name"],"SK Lama")
        self.assertIn("berubah",self.rt.sent[-1][1])
        self.assertNotIn("waiting",self.rt.state[123])

    def test_existing_callback_and_webhook_untouched_by_default(self):
        self.assertEqual(self.rt.callback(123,"timetable"),"original-callback")
        self.assertEqual(self.rt.callback_log[-1],(123,"timetable"))
        result=self.client.post("/webhook",json={"update_id":407,"message":{
            "chat":{"id":123,"type":"private"},"from":{"id":123},"text":"Selamat pagi"}})
        self.assertEqual(result.get_json().get("legacy"),True)
        self.assertEqual(self.rt.db_writes,[])

    def test_installer_is_idempotent(self):
        self.assertTrue(install(self.rt))
        self.rt.callback(123,"profedit_school")
        payload={"update_id":408,"message":{"chat":{"id":123,"type":"private"},
                 "from":{"id":123},"text":"SK Baru Lagi"}}
        self.client.post("/webhook",json=payload)
        self.assertEqual(len(self.rt.db_writes),1)


if __name__ == "__main__":
    unittest.main()
