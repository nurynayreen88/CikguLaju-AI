"""Offline regression suite for durable Supabase Telegram-user records."""
import os
import unittest
from urllib.parse import parse_qs
from unittest.mock import patch

from web import supabase_user_payment_runtime as payments
from web import supabase_user_feedback_runtime as feedback


class FakeStore:
    def __init__(self):
        self.requests = []
        self.feedback = []
        self.users = {}
        self.next_request = 1
        self.next_feedback = 1
        self.available = True
        self.reads = []
        self.writes = []

    def sb(self, method, path, **kwargs):
        if not self.available:
            raise RuntimeError("Supabase offline")
        self.reads.append((method, path))
        if method == "POST" and path == "rpc/bot_payment_status_counts":
            return {status:sum(1 for x in self.requests if x["status"]==status)
                    for status in ("pending","approved","rejected")}
        if method == "POST" and path == "rpc/bot_feedback_status_counts":
            result = {status:sum(1 for x in self.feedback if x["status"]==status)
                      for status in ("baru","dibaca","selesai")}
            result["total"] = len(self.feedback)
            return result
        name,_,raw = path.partition("?")
        args = parse_qs(raw)
        if name == "bot_payment_requests":
            records=self.requests
            if method == "POST":
                payload=dict(kwargs["json"])
                if any(x["status"] == "pending"
                       and x["chat_id"] == payload["chat_id"] for x in records):
                    raise ValueError("Unique pending constraint")
                payload.update({
                    "id":self.next_request,"status":"pending",
                    "notes":"","reviewed_by":"","reviewed_at":None,
                    "submitted_at":"2026-11-04T08:00:00Z"
                })
                self.next_request += 1
                records.append(payload)
                self.writes.append(("payments",payload["id"]))
                return [dict(payload)]
            if "id" in args:
                records=[x for x in records if x["id"]==int(args["id"][0][3:])]
            if "chat_id" in args:
                records=[x for x in records if x["chat_id"]==args["chat_id"][0][3:]]
            if "status" in args:
                records=[x for x in records if x["status"]==args["status"][0][3:]]
            if method == "PATCH":
                payload=kwargs["json"]
                for row in records:
                    row.update(payload)
                return [dict(x) for x in records]
            records=sorted(records,key=lambda x:-x["id"])
            if "offset" in args:
                records=records[int(args["offset"][0]):]
            if "limit" in args:
                records=records[:int(args["limit"][0])]
            return [dict(x) for x in records]
        if name == "bot_user_feedback":
            records=self.feedback
            if method == "POST":
                data=dict(kwargs["json"])
                data.update(id=self.next_feedback,created_at="2026-11-04T08:00:00Z",
                            status="baru")
                self.next_feedback+=1
                records.append(data)
                return [dict(data)]
            if "id" in args:
                records=[x for x in records if x["id"]==int(args["id"][0][3:])]
            if "status" in args:
                rawstatus=args["status"][0]
                if rawstatus.startswith("eq."):
                    records=[x for x in records if x["status"]==rawstatus[3:]]
                elif rawstatus.startswith("neq."):
                    records=[x for x in records if x["status"]!=rawstatus[4:]]
            if method == "PATCH":
                for row in records:
                    row.update(kwargs["json"])
                return [dict(x) for x in records]
            records=sorted(records,key=lambda x:(x["status"],-x["id"]))
            if "offset" in args:records=records[int(args["offset"][0]):]
            if "limit" in args:records=records[:int(args["limit"][0])]
            return [dict(x) for x in records]
        if name == "cikgulaju_users":
            uid=int(args["telegram_user_id"][0][3:]) if "telegram_user_id" in args else None
            if method == "GET":
                if uid is not None:
                    return [dict(self.users[uid])] if uid in self.users else []
                return [dict(x) for x in self.users.values()]
            if method == "PATCH":
                self.users[uid].update(kwargs["json"])
                return None
        raise AssertionError(f"Unexpected Supabase operation: {method} {path}")


class Runtime:
    API="https://example.invalid/telegram"
    ADMIN_CHAT_ID="1"

    def __init__(self, store):
        self.store=store
        self._sb_request=store.sb
        self.sent=[]
        self.legacy_payments={"id":999,"status":"pending"}
        self._payment_request=lambda rid: self.legacy_payments
        self._latest_pending_payment=lambda cid: self.legacy_payments
        self._new_payment_request=lambda cid,mid=None,amount=5:999
        self._set_payment_note=lambda rid,note:None
        self._mark_payment_request=lambda rid,status,admin_cid="",notes="":None
        self._admin_counts=lambda: {
            "users":len(store.users),"beta":0,"feedback":0,"new_feedback":0,
            "read_feedback":0,"done_feedback":0,
            "pending":123,"paid":100
        }
        self._admin_list=lambda cid,kind="all",page=0:"legacy_list"
        self._admin_user_name=lambda row:row.get("first_name") or "Pengguna"
        self._admin_persistent_users=lambda:[
            {"chat_id":str(uid),"first_name":row.get("first_name","")}
            for uid,row in store.users.items()]
        self._upsert_user=lambda user,cid=None:True
        self._save_beta_feedback=lambda *a:False
        self._feedback_card=lambda *a:None
        self._feedback_counts=lambda:{"total":0,"baru":0,"dibaca":0,"selesai":0}
        self._set_feedback_status=lambda *a:False
        self._feedback_pdf=lambda *a:None
        self.callback=lambda cid,d:"legacy_callback"
        self._is_admin=lambda cid:str(cid)=="1"
        self._ensure_trial_user=self.ensure_trial_user
        self.send_document=lambda *args:None

    def send(self,cid,text,kb=None):
        self.sent.append((cid,text,kb))
        return {"ok":True}

    def ensure_trial_user(self,uid):
        if int(uid) not in self.store.users:
            self.store.users[int(uid)]={
                "telegram_user_id":int(uid),
                "username":None,"first_name":None,"last_name":None,
                "trial_remaining":10
            }
        return self.store.users[int(uid)]["trial_remaining"]


class DurableUserRecordsTests(unittest.TestCase):
    def setUp(self):
        self.settings=patch.dict(os.environ,{"CIKGULAJU_SUPABASE_USER_RECORDS":"1"})
        self.settings.start()
        self.addCleanup(self.settings.stop)
        self.store=FakeStore()
        self.store.users[301]={"telegram_user_id":301,"first_name":"Cikgu A",
            "username":None,"last_name":None,"trial_remaining":7}
        self.runtime=Runtime(self.store)
        self.assertTrue(payments.install(self.runtime))
        self.assertTrue(feedback.install(self.runtime))

    def test_payment_is_stable_across_new_runtime_instance(self):
        first=self.runtime._new_payment_request(301,None,10.00)
        self.assertEqual(first,1)
        self.runtime._set_payment_note(first,"proof_received_admin_notified")
        self.assertEqual(self.runtime._latest_pending_payment(301)["notes"],
                         "proof_received_admin_notified")
        new_runtime=Runtime(self.store)
        self.assertTrue(payments.install(new_runtime))
        self.assertEqual(new_runtime._payment_request(first)["id"],first)
        self.assertEqual(new_runtime._latest_pending_payment(301)["amount"],"10.00")
        new_runtime._mark_payment_request(first,"approved",1,"Verified manually")
        self.assertIsNone(new_runtime._latest_pending_payment(301))
        self.assertEqual(self.runtime._payment_request(first)["status"],"approved")
        self.assertEqual(self.runtime._admin_counts()["pending"],0)
        self.assertEqual(self.runtime._admin_counts()["paid"],1)

    def test_one_pending_request_per_user_with_stable_ids(self):
        self.assertEqual(self.runtime._new_payment_request(301,None,10),
                         self.runtime._new_payment_request(301,None,10))
        self.assertEqual(self.runtime._new_payment_request(302,None,8),2)
        self.assertEqual(len(self.store.requests),2)

    def test_only_admin_can_approve(self):
        pid=self.runtime._new_payment_request(301,None,10)
        with self.assertRaises(PermissionError):
            self.runtime._mark_payment_request(pid,"approved",301,"Unverified")
        self.assertEqual(self.runtime._payment_request(pid)["status"],"pending")

    def test_owner_cancel_only_own_pending_payment(self):
        pid=self.runtime._new_payment_request(301,None,10)
        with self.assertRaises(PermissionError):
            self.runtime._mark_payment_request(pid,"rejected",302,
                                               "Cancelled by user before proof")
        self.assertTrue(self.runtime._mark_payment_request(
            pid,"rejected",301,"Cancelled by user before proof"))
        self.assertEqual(self.runtime._payment_request(pid)["status"],"rejected")

    def test_supabase_outage_does_not_fall_back_to_old_sqlite(self):
        self.store.available=False
        with self.assertRaises(RuntimeError):
            self.runtime._new_payment_request(301,None,10)
        self.assertEqual(self.runtime.legacy_payments["id"],999)

    def test_admin_pending_list_uses_supabase_and_checks_admin(self):
        self.runtime._new_payment_request(301,None,10)
        self.runtime._admin_list(301,"pending",0)
        self.assertIn("Admin",self.runtime.sent[-1][1] if "Admin" in self.runtime.sent[-1][1] else "admin")
        self.runtime._admin_list(1,"pending",0)
        self.assertIn("SUPABASE",self.runtime.sent[-1][1])
        kb=self.runtime.sent[-1][2]
        self.assertTrue(any(b["callback_data"]=="admin_pending|1"
                            for row in kb for b in row))

    def test_profile_names_persist_without_resetting_free_trial(self):
        self.runtime._upsert_user({"id":301,"first_name":"Cikgu Baru",
                                   "username":"guru_test"},301)
        user=self.store.users[301]
        self.assertEqual(user["first_name"],"Cikgu Baru")
        self.assertEqual(user["username"],"guru_test")
        self.assertEqual(user["trial_remaining"],7)

    def test_feedback_survives_restart_and_admin_changes(self):
        self.assertTrue(self.runtime._save_beta_feedback(301,
                        "Sila tambah pilihan jadual", "Cadangan"))
        new_runtime=Runtime(self.store)
        self.assertTrue(payments.install(new_runtime))
        self.assertTrue(feedback.install(new_runtime))
        new_runtime.callback(1,"admin_feedback_view|1")
        self.assertIn("Sila tambah",new_runtime.sent[-1][1])
        new_runtime.callback(1,"admin_feedback_status|1|selesai")
        self.assertEqual(self.store.feedback[0]["status"],"selesai")
        self.assertEqual(new_runtime._feedback_counts()["selesai"],1)

    def test_non_admin_cannot_read_user_feedback(self):
        self.assertTrue(self.runtime._save_beta_feedback(301,"Maklum balas"))
        before=len(self.store.reads)
        self.runtime.callback(301,"admin_feedback_view|1")
        self.assertEqual(len(self.store.reads),before)
        self.assertIn("admin",self.runtime.sent[-1][1].lower())

    def test_unknown_actions_preserve_existing_handlers(self):
        self.assertEqual(self.runtime.callback(1,"quick"),"legacy_callback")


if __name__=="__main__":
    unittest.main()
