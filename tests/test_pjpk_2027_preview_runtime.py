"""Smoke and regression tests for the PJPK preview bridge.

Run from repo root:
    python -m unittest tests.test_pjpk_2027_preview_runtime -v
No Telegram token, database mutation or network access is used.
"""
import unittest

from web import pjpk_2027_preview_runtime as preview


class PJPKSourceTests(unittest.TestCase):
    def test_inventory_exactly_339_safe_numbered_drafts(self):
        idx = preview._manifest(str(preview.ROOT))
        self.assertEqual(len(idx), 339)
        self.assertIn((6, "pj", 33), idx)
        self.assertNotIn((2, "pj", 38), idx)

    def test_every_staged_numbered_lesson_loads(self):
        expected = {
            (2, "pj"): 37, (3, "pj"): 38, (4, "pj"): 34,
            (5, "pj"): 33, (6, "pj"): 34,
            (2, "pk"): 35, (3, "pk"): 32, (4, "pk"): 32,
            (5, "pk"): 32, (6, "pk"): 32,
        }
        for (year, sub), count in expected.items():
            name = "Pendidikan Jasmani" if sub == "pj" else "Pendidikan Kesihatan"
            with self.subTest(year=year, subject=name):
                rows = preview.list_lessons("Tahun %d" % year, name)
                self.assertEqual(len(rows), count)
                self.assertEqual(len({x["lesson"] for x in rows}), count)
                for entry in rows:
                    self.assertTrue(entry["sp"])
                    self.assertTrue(entry["sk"])
                    self.assertEqual(len(entry["activities"]), 2)
                    self.assertTrue(entry["objective"])

    def test_unverified_year_one_and_aquatic_are_not_offered(self):
        self.assertEqual(preview.list_lessons("Tahun 1", "Pendidikan Jasmani"), [])
        self.assertIsNone(preview._source(2, "pj", 38))
        self.assertIsNotNone(preview._source(6, "pj", 33))
        self.assertEqual(preview.list_lessons("Tahun 2", "Bahasa Inggeris"), [])

    def test_existing_rph_metadata_preserved(self):
        state = {
            "year": "Tahun 2", "subject": "Pendidikan Jasmani",
            "lesson_no": "1", "sp_code": "1.1.1",
            "_pjpk_2027_preview_selection": {"year": 2, "subject": "pj", "lesson": 1},
        }
        rows = {"TARIKH": "10/11/2026", "KELAS": "2 Bestari",
                "OBJEKTIF PEMBELAJARAN": "old"}
        out = preview.adapt_rows(state, rows)
        self.assertEqual(out["TARIKH"], rows["TARIKH"])
        self.assertEqual(out["KELAS"], rows["KELAS"])
        self.assertEqual(out["MATA PELAJARAN"], "Pendidikan Jasmani")
        self.assertIn("1.1.1", out["STANDARD PEMBELAJARAN"])
        self.assertIn("Aktiviti 1", out["AKTIVITI UTAMA"])
        self.assertIn("PRATONTON DRAF", out["TAJUK"])

    def test_no_cross_year_subject_or_stale_standard_leak(self):
        state = {
            "year": "Tahun 2", "subject": "Pendidikan Jasmani",
            "lesson_no": "1", "sp_code": "9.9.9",
            "_pjpk_2027_preview_selection": {"year": 2, "subject": "pj", "lesson": 1},
        }
        base = {"OBJEKTIF PEMBELAJARAN": "unchanged"}
        self.assertIs(preview.adapt_rows(state, base), base)
        state["sp_code"] = "1.1.1"
        state["year"] = "Tahun 3"
        self.assertIs(preview.adapt_rows(state, base), base)
        state["year"] = "Tahun 2"
        state["subject"] = "English"
        self.assertIs(preview.adapt_rows(state, base), base)

    def test_admin_can_select_and_reuse_normal_class_flow(self):
        state = {99: {"year": "Tahun 3"}, 100: {"year": "Tahun 3"}}
        sent, forwarded, generated = [], [], []

        def old_callback(cid, data):
            forwarded.append((cid, data))
            return "previous"

        def original_rows(st, *_args, **_kwargs):
            generated.append("original")
            return {"TARIKH": "01/01/2027"}

        ns = {
            "callback": old_callback,
            "_rph_rows": original_rows,
            "state": state,
            "send": lambda cid, msg, kb=None: sent.append((cid, msg, kb)),
            "_is_admin": lambda cid: cid == 99,
            "_lesson_to_class_v2439": lambda cid: "class selection",
        }
        self.assertFalse(preview.install(ns, enabled=False))
        self.assertIs(ns["callback"], old_callback)
        self.assertTrue(preview.install(ns, enabled=True))
        self.assertTrue(ns["CIKGULAJU_PJPK_2027_PREVIEW_INSTALLED"])
        self.assertEqual(ns["callback"](100, "sub_Pendidikan Jasmani"), "previous")
        self.assertEqual(ns["callback"](99, "sub_Pendidikan Jasmani"), None)
        self.assertTrue(sent)
        self.assertEqual(ns["callback"](99, "pjpk27pick|001"), "class selection")
        st = state[99]
        self.assertEqual(st["lesson_no"], "1")
        self.assertEqual(st["sp_code"], "1.1.1")
        self.assertEqual(st["subject"], "Pendidikan Jasmani")
        self.assertEqual(st["_pjpk_2027_preview_selection"]["lesson"], 1)
        out = ns["_rph_rows"](st, "text")
        self.assertEqual(generated, ["original"])
        self.assertIn("Aktiviti 1", out["AKTIVITI UTAMA"])
        self.assertEqual(out["TARIKH"], "01/01/2027")
        self.assertEqual(ns["callback"](99, "noother"), "previous")
        self.assertTrue(preview.install(ns, enabled=True))  # idempotent
        self.assertNotIn("_pjpk_2027_preview_selection", state[100])

    def test_forged_callback_does_not_bypass_admin(self):
        state = {100: {"year": "Tahun 4", "subject": "Pendidikan Jasmani"}}
        ns = {"callback": lambda *_: "previous", "_rph_rows": lambda s, *_: {},
              "state": state, "send": lambda *_: "not allowed",
              "_is_admin": lambda cid: False,
              "_lesson_to_class_v2439": lambda cid: "class selection"}
        self.assertTrue(preview.install(ns, enabled=True))
        self.assertEqual(ns["callback"](100, "pjpk27pick|001"), "not allowed")
        self.assertNotIn("_pjpk_2027_preview_selection", state[100])


if __name__ == "__main__":
    unittest.main()
