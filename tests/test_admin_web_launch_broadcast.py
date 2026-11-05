"""No automatic broadcast; exact-once claim, admin confirmation and durable report.

All Telegram and Supabase effects are mocked. Never sends a real user message.
"""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web import admin_web_launch_broadcast as b


class Response:
    def __init__(self, data=None, ok=True, status_code=200):
        self._data=data or {}
        self.ok=ok
        self.status_code=status_code
    def json(self):
        return self._data


class FakeSupabase:
    def __init__(self, ids=(111,222,333)):
        self.users=sorted(ids)
        self.campaign=None
        self.deliveries={}
        self.writes=[]
    def __call__(self, method, path, **kwargs):
        if method=="GET" and path.startswith("cikgulaju_users?"):
            start=int(path.split("offset=")[-1])
            return [{"telegram_user_id":i} for i in self.users[start:start+b.PAGE_SIZE]]
        if method=="GET" and path.startswith("cikgulaju_broadcast_campaigns?"):
            return [dict(self.campaign)] if self.campaign else []
        if method=="GET" and path.startswith("cikgulaju_broadcast_deliveries?"):
            start=int(path.split("offset=")[-1])
            rows=[{"status":self.deliveries[k]} for k in sorted(self.deliveries)]
            return rows[start:start+b.PAGE_SIZE]
        if method=="POST" and path=="rpc/cikgulaju_broadcast_prepare":
            args=kwargs["json"]
            if self.campaign:
                raise RuntimeError("campaign already exists")
            if args["p_expected_count"]!=len(self.users):
                raise RuntimeError("recipient count changed")
            assert args["p_campaign"]==b.CAMPAIGN
            assert args["p_sha256"]==b.MESSAGE_SHA256
            self.campaign={"campaign_id":b.CAMPAIGN,
                            "recipient_count":len(self.users),
                            "confirmed_by":args["p_admin"],
                            "confirmed_at":"2026-11-06T00:00:00Z"}
            self.deliveries={uid:"queued" for uid in self.users}
            self.writes.append("confirm")
            return len(self.users)
        if method=="POST" and path=="rpc/cikgulaju_broadcast_claim":
            next_ids=sorted(i for i,s in self.deliveries.items() if s=="queued")
            if next_ids:
                self.deliveries[next_ids[0]]="sending"
                return [{"telegram_user_id":next_ids[0]}]
            return []
        if method=="PATCH" and path.startswith("cikgulaju_broadcast_deliveries?"):
            uid=int(path.split("telegram_user_id=eq.")[-1].split("&")[0])
            assert self.deliveries[uid]=="sending"
            status=kwargs["json"]["status"]
            self.deliveries[uid]=status
            return [{"telegram_user_id":uid,"status":status}]
        raise AssertionError(f"Unexpected database operation: {method} {path}")


class Thread:
    threads=[]
    def __init__(self, target, args=(), **kwargs):
        self.target=target
        self.args=args
        Thread.threads.append(self)
    def start(self):
        # Deliberately does not run; the tests assert no automatic sends.
        pass
    def run(self):
        return self.target(*self.args)


class StartupOrderTests(unittest.TestCase):
    def test_broadcast_installed_after_durable_users_and_referral(self):
        from pathlib import Path
        code=(Path(__file__).resolve().parents[1] /
              "tools/run_telegram_with_curriculum_api.py").read_text("utf-8")
        self.assertLess(
            code.index("DURABLE_USER_PAYMENT_STORE_ACTIVE = bool("),
            code.index("install_web_announcement("),
        )
        self.assertLess(
            code.index("PRIVATE_REFERRAL_ADMIN_POINTS_ACTIVE = install_private_referral_admin"),
            code.index("install_web_announcement("),
        )
        self.assertIn("preserve_referral=PRIVATE_REFERRAL_ADMIN_POINTS_ACTIVE",code)
        self.assertIn("and install_web_announcement(",code)


class BroadcastTests(unittest.TestCase):
    def setUp(self):
        Thread.threads.clear()
        self.db=FakeSupabase()
        self.sent=[]
        self.menu_updates=[]
        self.base_menu={"ok":True,"result":{"message_id":88,"reply_markup":{
            "inline_keyboard":[
                [{"text":"Pengguna","callback_data":"admin_list|all|0"}],
                [{"text":"Sistem","callback_data":"admin_system"}],
            ]}}}
        self.runtime=SimpleNamespace(
            _admin_panel=lambda cid: Response(self.base_menu),
            callback=lambda cid,data:"original callback",
            _is_admin=lambda cid:cid==999,
            send=lambda cid,msg,keyboard=None:self.sent.append((cid,msg,keyboard)),
            _sb_request=self.db,
            state={},
            API="https://api.telegram.org/bot12345678:TESTTOKEN",
            CIKGULAJU_SUPABASE_USER_RECORDS_ACTIVE=True,
        )
        self.patch_thread=patch.object(b.threading,"Thread",Thread)
        self.patch_thread.start()
        self.addCleanup(self.patch_thread.stop)
        self.patch_menu=patch.object(b.requests,"post",side_effect=self.fake_http)
        self.patch_menu.start()
        self.addCleanup(self.patch_menu.stop)
        self.assertTrue(b.install(self.runtime))

    def fake_http(self,url,**kwargs):
        if url.endswith("/editMessageReplyMarkup"):
            self.menu_updates.append(kwargs["json"])
            return Response({"ok":True})
        raise AssertionError("Telegram message must not be sent without a test stub")

    def click(self,data,uid=999):
        return self.runtime.callback(uid,data)

    def test_install_and_panel_do_not_send_broadcast(self):
        self.assertEqual(self.db.writes,[])
        self.runtime._admin_panel(999)
        self.assertEqual(len(self.menu_updates),1)
        kb=self.menu_updates[0]["reply_markup"]["inline_keyboard"]
        actions=[x.get("callback_data") for row in kb for x in row]
        self.assertEqual(actions,["admin_list|all|0",b.BUTTON["callback_data"],"admin_system"])
        self.assertEqual(self.db.writes,[])
        self.assertEqual(Thread.threads,[])
        self.runtime._admin_panel(42)
        self.assertEqual(len(self.menu_updates),1)
        self.assertEqual(self.runtime.callback(42,"home"),"original callback")

    def test_final_admin_menu_preserves_referral_after_previous_wrapper(self):
        self.runtime.CIKGULAJU_BROADCAST_INSTALLED=False
        # Reuse the original base menu to emulate the referral wrapper's
        # sendMessage response (it returns original markup after editing).
        self.runtime._admin_panel=lambda cid: Response(self.base_menu)
        self.assertTrue(b.install(self.runtime,preserve_referral=True))
        self.runtime._admin_panel(999)
        updated=self.menu_updates[-1]["reply_markup"]["inline_keyboard"]
        keys=[btn.get("callback_data") for row in updated for btn in row]
        self.assertIn("admin_ref_points|list|0",keys)
        self.assertIn(b.BUTTON["callback_data"],keys)
        self.assertIn("admin_list|all|0",keys)
        self.assertIn("admin_system",keys)
        self.assertEqual(self.db.writes,[])

    def test_non_admin_cannot_preview_confirm_or_resume(self):
        for key in ("admin_web_broadcast|preview","admin_web_broadcast|resume",
                    "admin_web_broadcast|confirm|1234123412341234"):
            self.click(key,uid=42)
        self.assertEqual(self.db.writes,[])
        self.assertEqual(Thread.threads,[])
        self.assertEqual(self.db.deliveries,{})

    def test_preview_and_cancel_do_not_create_deliveries(self):
        self.click("admin_web_broadcast|preview")
        last=self.sent[-1]
        self.assertIn("3",last[1])
        self.assertIn(b.WEB_URL,last[1])
        self.assertIn("SAHKAN",last[1])
        self.assertEqual(self.db.writes,[])
        token=self.runtime.state[999]["web_broadcast_preview"]["token"]
        self.click("admin_web_broadcast|cancel")
        self.click("admin_web_broadcast|confirm|"+token)
        self.assertEqual(self.db.writes,[])
        self.assertEqual(Thread.threads,[])

    def test_confirm_snapshots_once_and_receivers_are_sent_once(self):
        self.click("admin_web_broadcast|preview")
        token=self.runtime.state[999]["web_broadcast_preview"]["token"]
        self.click("admin_web_broadcast|confirm|"+token)
        self.assertEqual(self.db.writes,["confirm"])
        self.assertEqual(len(Thread.threads),1)
        self.assertEqual(set(self.db.deliveries),{111,222,333})
        self.click("admin_web_broadcast|confirm|"+token)
        self.assertEqual(self.db.writes,["confirm"])
        self.assertEqual(len(Thread.threads),1)
        self.click("admin_web_broadcast|preview")
        self.assertEqual(len(Thread.threads),1)
        deliveries=[]
        with patch.object(b,"_send_one",side_effect=lambda api,uid:(deliveries.append(uid) or ("sent",None))), \
             patch.object(b.time,"sleep",return_value=None):
            Thread.threads[0].run()
        self.assertEqual(deliveries,[111,222,333])
        self.assertEqual(set(self.db.deliveries.values()),{"sent"})
        self.assertEqual(b._status(self.db)["sent"],3)
        self.click("admin_web_broadcast|resume")
        with patch.object(b,"_send_one",side_effect=AssertionError("No retries")):
            self.assertEqual(b._next_recipient(self.db),None)

    def test_unknown_telegram_outcome_not_retried_automatically(self):
        self.click("admin_web_broadcast|preview")
        token=self.runtime.state[999]["web_broadcast_preview"]["token"]
        self.click("admin_web_broadcast|confirm|"+token)
        self.db.deliveries[111]="sending"
        self.assertEqual(b._next_recipient(self.db),222)
        self.assertEqual(self.db.deliveries[111],"sending")
        self.assertEqual(b._status(self.db)["sending"],2)
        self.click("admin_web_broadcast|status")
        self.assertIn("Perlu semakan manual",self.sent[-1][1])

    def test_count_change_cannot_send(self):
        self.click("admin_web_broadcast|preview")
        token=self.runtime.state[999]["web_broadcast_preview"]["token"]
        self.db.users.append(444)
        self.click("admin_web_broadcast|confirm|"+token)
        self.assertFalse(self.db.campaign)
        self.assertEqual(self.db.deliveries,{})
        self.assertEqual(Thread.threads,[])

    def test_corrupt_data_fails_closed(self):
        self.db.users=[]
        self.click("admin_web_broadcast|preview")
        self.assertNotIn("web_broadcast_preview",self.runtime.state.get(999,{}))
        self.assertEqual(self.db.writes,[])
        self.assertEqual(Thread.threads,[])

    def test_delivery_classifies_blocked_and_rate_limited(self):
        with patch.object(b.time,"sleep",return_value=None) as pause:
            blocked=Response({"ok":False},ok=False,status_code=403)
            self.assertEqual(b._send_one("https://api.test",111,post=lambda *a,**k:blocked,pause=pause),
                             ("failed","blocked"))
            responses=[
                Response({"ok":False,"parameters":{"retry_after":2}},ok=False,status_code=429),
                Response({"ok":True,"result":{"message_id":22,"chat":{"id":111}}}),
            ]
            sent=[]
            def post(url,**kwargs):
                sent.append(kwargs["json"])
                return responses.pop(0)
            self.assertEqual(b._send_one("https://api.test",111,post=post,pause=pause),
                             ("sent",None))
            self.assertEqual(len(sent),2)
            self.assertEqual(sent[0]["reply_markup"],b.WEB_KEYBOARD)

if __name__=="__main__":
    unittest.main()
