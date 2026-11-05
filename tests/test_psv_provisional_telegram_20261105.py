"""Isolated integration checks for the owner-approved provisional PSV Telegram route."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from web import psv_2027_provisional_runtime as bridge
from web import psv_2027_rph_release_bridge as strict

ROOT = Path(__file__).resolve().parents[1]


class TestProvisionalPSV(unittest.TestCase):
    def fake(self):
        seen = []
        state = {}
        base = {"KELAS": "5 Amanah", "TARIKH": "05/11/2026",
                "HARI": "Khamis", "MASA": "8:00 – 9:00",
                "REFLEKSI": "Isi selepas PdP", "CATATAN": "Jangan ubah"}
        def send(cid, text, keyboard=None):
            seen.append((cid, text, keyboard))
            return "sent"
        def callback(cid, data):
            return ("original", data)
        def subjects(cid, label):
            return ("original_subjects", label)
        def to_class(cid):
            return ("class", cid)
        def rows(s, *args, **kwargs):
            return base
        return {"state": state, "send": send, "callback": callback,
                "subjects": subjects,
                "SUBJECTS_BY_GRADE": {
                    "Tahun %d" % year: ["Bahasa Melayu", "Sains"]
                    for year in range(1, 7)
                },
                "SUBJECT_LABEL": {
                    "Bahasa Melayu": "Bahasa Melayu", "Sains": "Sains"
                },
                "_CIKGULAJU_DEV_SUBJECTS_V2617": {
                    "Pendidikan Seni Visual": (1, 2, 3, 4, 5, 6),
                    "Pendidikan Muzik": (1, 2, 3, 4, 5, 6)
                },
                "_lesson_to_class_v2439": to_class, "_rph_rows": rows}, seen, base

    def test_unlocked_navigation_and_210_source_rows(self):
        ns, seen, base = self.fake()
        self.assertTrue(bridge.install(ns, enabled=True))
        for year in range(2, 7):
            for number in range(1, 43):
                with self.subTest(year=year, pdp=number):
                    ns["state"][99] = {"year": "Tahun %d" % year,
                                       "subject": "Pendidikan Jasmani"}
                    ns["callback"](99, "sub_Pendidikan Seni Visual")
                    self.assertIn("PdP", seen[-1][1])
                    result = ns["callback"](99, "psv27pick|%d|%03d" % (year, number))
                    self.assertEqual(result, ("class", 99))
                    chosen = ns["state"][99]
                    self.assertEqual(chosen["lesson_no"], str(number))
                    source = strict.load_candidate(year, number, preview=True)
                    self.assertIsNotNone(source)
                    rows = ns["_rph_rows"](chosen, "irrelevant AI text")
                    self.assertEqual(rows["STANDARD KANDUNGAN"], source["sk"])
                    self.assertEqual(rows["STANDARD PEMBELAJARAN"], source["sp"])
                    self.assertEqual(rows["OBJEKTIF PEMBELAJARAN"], source["objective"])
                    self.assertEqual(rows["KRITERIA KEJAYAAN"], source["evidence"])
                    self.assertIn("Aktiviti 1", rows["AKTIVITI UTAMA"])
                    self.assertIn("Aktiviti 2", rows["AKTIVITI UTAMA"])
                    for key, value in base.items():
                        self.assertEqual(rows[key], value)
                    self.assertNotIn("DRAF", " ".join(map(str, rows.values())))
        self.assertEqual(ns["callback"](99, "other_action"), ("original", "other_action"))

    def test_v2617_old_development_callback_and_new_subject_menu(self):
        """Exact Telegram symptom: v26.17 had a devsub2617_ PSV blocker."""
        ns, seen, base = self.fake()
        self.assertTrue(bridge.install(ns, enabled=True))
        for year in range(2, 7):
            with self.subTest(year=year):
                cid = 300 + year
                self.assertEqual(ns["subjects"](
                    cid, "Tahun %d" % year), "sent")
                content, keyboard = seen[-1][1], seen[-1][2]
                flat = [b for row in keyboard for b in row]
                psv = [b for b in flat if
                       "Pendidikan Seni Visual" in b["text"]]
                self.assertEqual(len(psv), 1)
                self.assertEqual(psv[0]["callback_data"],
                                 "sub_Pendidikan Seni Visual")
                self.assertNotIn("Dalam Pembangunan", psv[0]["text"])
                self.assertIn("sub_Bahasa Melayu",
                              [b["callback_data"] for b in flat])
                self.assertIn("devsub2617_Pendidikan Muzik",
                              [b["callback_data"] for b in flat])
                self.assertIn("Pilih subjek", content)
                # Click a previously-sent Telegram button: accept old data.
                self.assertEqual(ns["callback"](
                    cid, "devsub2617_Pendidikan Seni Visual"), "sent")
                self.assertIn("PdP", seen[-1][1])
                self.assertEqual(ns["callback"](
                    cid, "psv27pick|%d|001" % year), ("class", cid))
                plan = strict.load_candidate(year, 1, preview=True)
                rows = ns["_rph_rows"](ns["state"][cid], "rph")
                self.assertEqual(rows["STANDARD PEMBELAJARAN"], plan["sp"])
        # KP2027 Year1 and secondary remain on their previous routes.
        self.assertEqual(ns["subjects"](301, "Tahun 1"),
                         ("original_subjects", "Tahun 1"))
        ns["state"][301] = {"year": "Tahun 1"}
        self.assertEqual(ns["callback"](
            301, "devsub2617_Pendidikan Seni Visual"),
            ("original", "devsub2617_Pendidikan Seni Visual"))
        self.assertEqual(ns["subjects"](302, "Tingkatan 1"),
                         ("original_subjects", "Tingkatan 1"))
        self.assertEqual(ns["callback"](
            302, "devsub2617_Pendidikan Muzik"),
            ("original", "devsub2617_Pendidikan Muzik"))

    def test_legacy_menu_patch_disabled_or_installed_twice(self):
        ns, seen, base = self.fake()
        self.assertTrue(bridge.install(ns, enabled=True))
        patched = ns["subjects"]
        self.assertTrue(bridge.install(ns, enabled=True))
        self.assertIs(ns["subjects"], patched)
        with patch.dict(os.environ, {bridge.FLAG: "0"}):
            ns2, _, _ = self.fake()
            original = ns2["subjects"]
            self.assertFalse(bridge.install(ns2))
            self.assertIs(ns2["subjects"], original)

    def test_stale_or_other_subject_never_overrides(self):
        ns, seen, base = self.fake()
        self.assertTrue(bridge.install(ns, enabled=True))
        st = ns["state"].setdefault(101, {"year": "Tahun 4"})
        self.assertEqual(ns["callback"](101, "sub_Pendidikan Seni Visual"), "sent")
        self.assertEqual(ns["callback"](101, "psv27pick|4|011"), ("class", 101))
        self.assertIsNot(ns["_rph_rows"](st, "x"), base)
        st["subject"] = "Pendidikan Islam"
        self.assertIs(ns["_rph_rows"](st, "x"), base)
        st["subject"] = "Pendidikan Seni Visual"
        st["sp_code"] = "999.9.9"
        self.assertIs(ns["_rph_rows"](st, "x"), base)
        st["sp_code"] = strict.load_candidate(4, 11, preview=True)["sp"].split("; ")[0]
        st["lesson_no"] = "12"
        self.assertIs(ns["_rph_rows"](st, "x"), base)
        self.assertEqual(ns["callback"](101, "psv27pick|5|012"), "sent")
        self.assertIs(ns["_rph_rows"]({"subject": "Pendidikan Moral"}, "x"), base)

    def test_emergency_off_and_strict_release_still_closed(self):
        ns, seen, base = self.fake()
        with patch.dict(os.environ, {bridge.FLAG: "0"}):
            self.assertFalse(bridge.install(ns))
        self.assertNotIn("PSV_2027_PROVISIONAL_TELEGRAM_ACTIVE", ns)
        self.assertFalse(strict._approved(ROOT))
        self.assertIsNone(strict.load_candidate(6, 39))
        # Provisional availability never rewrites DRAF source or official release gate.
        self.assertIn("**Status:** DRAF",
                      (ROOT / "rph_standalone/psv/year6/lesson_039.md").read_text(encoding="utf-8"))

    def test_no_db_payment_or_user_change_at_source_level(self):
        source = (ROOT / "web/psv_2027_provisional_runtime.py").read_text(encoding="utf-8")
        self.assertNotIn("sqlite3", source)
        self.assertNotIn("supabase", source.casefold())
        self.assertNotIn("_activate_access(", source)
        self.assertNotIn("_consume_free", source)
        self.assertNotIn("update rph_cache", source.casefold())


if __name__ == "__main__":
    unittest.main()
