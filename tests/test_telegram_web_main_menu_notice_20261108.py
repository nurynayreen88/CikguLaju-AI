"""Offline/synthetic validation of Telegram's active main menu Web announcement.
Never imports the large runtime or touches a real Telegram token/account.
"""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"app.py"
URL="https://cikgulaju-web.onrender.com/"

class TelegramWebMenuNoticeQA(unittest.TestCase):
    def _run_menu(self,*,active,admin,show_persistent=False):
        src=APP.read_text(encoding="utf-8")
        tree=ast.parse(src)
        menus=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="menu"]
        self.assertGreaterEqual(len(menus),2)
        self.assertGreater(menus[-1].lineno,46000)
        node=menus[-1]
        context={"_is_admin":lambda cid:admin,
                 "_access_info":lambda cid:{"active":active},
                 "_is_permanent_vip_v25267":lambda cid:False,
                 "_trial_balance":lambda cid:7}
        calls=[];persistent=[]
        context["send"]=lambda cid,body,kb:calls.append((cid,body,kb)) or {"ok":True}
        context["install_menu_button"]=lambda cid:persistent.append(cid)
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(APP),"exec"),context)
        context["menu"](101,show_persistent=show_persistent)
        self.assertEqual(len(calls),1)
        self.assertEqual(persistent,[101] if show_persistent else [])
        return calls[0]

    def test_active_free_user_menu_shows_exactly_one_web_link_and_status(self):
        _,body,kb=self._run_menu(active=False,admin=False,show_persistent=True)
        self.assertEqual(sum(1 for row in kb for b in row
                             if b.get("url")==URL),1)
        web=[b for row in kb for b in row if b.get("url")==URL][0]
        self.assertEqual(web["text"],"🌐 BUKA CIKGULAJU WEB")
        self.assertNotIn("callback_data",web)
        callbacks=[b.get("callback_data") for row in kb for b in row
                   if "callback_data" in b]
        self.assertEqual(callbacks,
                         ["quick","rpt2027_home","account","pioneer_join"])
        self.assertIn("🌐 <b>CIKGULAJU WEB SUDAH TERSEDIA</b>",body)
        self.assertIn(URL,body)
        self.assertIn("Log masuk menggunakan Telegram.",body)
        self.assertIn("Baki janaan RPH dikongsi",body)
        self.assertIn("Cikgu digalakkan menggunakan Web untuk urusan lebih mudah",body)
        self.assertIn("pilih Lesson/PdP, gunakan RPH Hari Ini",body)
        self.assertIn("RPT asas boleh dimuat turun percuma",body)
        self.assertIn("muka depan berprofil memerlukan akses berbayar.",body)
        self.assertEqual(body.count("🌐 <b>CIKGULAJU WEB SUDAH TERSEDIA</b>"),1)
        self.assertIn("Baki janaan RPH: 7/10",body)
        self.assertNotIn("🛠️ ADMIN PANEL",str(kb))
        self.assertLess(len(body),4096)

    def test_vip_and_admin_menus_keep_quota_and_privileged_button(self):
        _,body,kb=self._run_menu(active=True,admin=True)
        self.assertIn("Akses tanpa had",body)
        self.assertNotIn("Baki janaan RPH: 7/10",body)
        self.assertEqual(sum(1 for row in kb for b in row
                             if b.get("url")==URL),1)
        self.assertIn("admin_panel",[b.get("callback_data") for row in kb
                                    for b in row])
        self.assertEqual(sum(1 for row in kb for b in row
                             if b.get("callback_data")=="pioneer_join"),1)

    def test_no_new_commands_callbacks_or_legacy_menu_overrides(self):
        source=APP.read_text(encoding="utf-8")
        nodes=ast.parse(source).body
        menus=[n for n in nodes if isinstance(n,ast.FunctionDef)
               and n.name=="menu"]
        self.assertEqual(len(menus),14)
        self.assertEqual(source.count("🌐 BUKA CIKGULAJU WEB"),1)
        self.assertEqual(source.count("🌐 <b>CIKGULAJU WEB SUDAH TERSEDIA</b>"),1)
        self.assertEqual(source.count(URL),2)
        self.assertEqual(source.count("def callback("),75)

if __name__=="__main__":
    unittest.main()
