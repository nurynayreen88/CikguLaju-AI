"""PJPK 2027 Telegram draft RPH integration and isolation regressions.

Runs entirely offline: no Telegram token, user DB, quota debit or network calls.
"""
import json
import tempfile
import unittest
from pathlib import Path

from web import pjpk_2027_preview_runtime as preview


class PJPKDraftRuntimeTests(unittest.TestCase):
    def test_all_339_numbered_rph_match_current_rpt_manifest(self):
        indexed = preview._manifest(str(preview.ROOT))
        self.assertEqual(len(indexed), 339)
        self.assertIn((6, "pj", 33), indexed)
        self.assertNotIn((2, "pj", 38), indexed)
        expected = {
            (2, "pj"): 37, (3, "pj"): 38, (4, "pj"): 34,
            (5, "pj"): 33, (6, "pj"): 34,
            (2, "pk"): 35, (3, "pk"): 32, (4, "pk"): 32,
            (5, "pk"): 32, (6, "pk"): 32,
        }
        for (year, subject), count in expected.items():
            name = "Pendidikan Jasmani" if subject == "pj" else "Pendidikan Kesihatan"
            with self.subTest(year=year, component=subject):
                rows = preview.list_lessons("Tahun %d" % year, name)
                self.assertEqual(len(rows), count)
                self.assertEqual(len({row["lesson"] for row in rows}), count)
                for row in rows:
                    manifest_entry = indexed[(year, subject, row["lesson"])]
                    self.assertEqual(row["sk"], manifest_entry["sk"])
                    self.assertEqual(row["sp"], manifest_entry["sp"])
                    self.assertEqual(row["title"], manifest_entry["title"])
                    self.assertEqual(len(row["activities"]), 2)
                    self.assertTrue(row["objective"])

    def test_reconciled_year6_pdp33_is_available_as_draft_not_ready(self):
        row = preview._source(6, "pj", 33)
        self.assertIsNotNone(row)
        self.assertEqual(row["sp"], ["3.5.1", "4.5.1", "4.5.2", "5.3.2"])
        self.assertIn("78", row["fields"]["buku teks"])
        self.assertIn("DRAF", row["fields"]["status"])
        self.assertNotIn("terhalang", row["fields"]["status"].casefold())

    def test_unverified_year1_and_extra_aquatic_not_offered(self):
        self.assertEqual(preview.list_lessons("Tahun 1", "Pendidikan Jasmani"), [])
        self.assertIsNone(preview._source(2, "pj", 38))
        self.assertEqual(preview.list_lessons("Tahun 2", "English"), [])

    def test_current_rpt_fail_closed_on_bad_status_or_parent_code(self):
        source = preview.ROOT / preview.MANIFEST
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / preview.MANIFEST
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(source.read_text(encoding="utf-8"))
            first = data["records"][0]
            first["ready"] = True
            dest.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(preview._manifest(tmp), {})
            first["ready"] = False
            first["sp"] = ["9.9.9"]
            dest.write_text(json.dumps(data), encoding="utf-8")
            preview._manifest.cache_clear()
            self.assertEqual(preview._manifest(tmp), {})
            preview._manifest.cache_clear()

    def test_native_rows_keep_teacher_date_class_and_subject_specific_content(self):
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
        self.assertIn("DRAF CADANGAN", out["TAJUK"])

    def test_stale_year_subject_standard_never_leaks_to_other_generation(self):
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

    def test_regular_and_admin_users_share_class_flow_without_credit_mutation(self):
        states = {99: {"year": "Tahun 3"}, 100: {"year": "Tahun 6"}}
        sent, forwarded, generated, class_calls = [], [], [], []

        def previous(cid, data):
            forwarded.append((cid, data))
            return "previous"

        def native_rows(st, *_args, **_kwargs):
            generated.append("native")
            return {"TARIKH": "01/01/2027", "KELAS": "3 Bestari"}

        def to_class(cid):
            class_calls.append(cid)
            return "class selection"

        ns = {
            "callback": previous, "_rph_rows": native_rows,
            "state": states, "send": lambda *a: sent.append(a),
            "_is_admin": lambda cid: cid == 99,
            "_lesson_to_class_v2439": to_class,
        }
        self.assertFalse(preview.install(ns, enabled=False))
        self.assertIs(ns["callback"], previous)
        self.assertTrue(preview.install(ns, enabled=True))
        self.assertEqual(ns["callback"](99, "sub_Pendidikan Jasmani"), None)
        self.assertEqual(ns["callback"](100, "sub_Pendidikan Jasmani"), None)
        self.assertIn("DRAF", sent[-1][1])
        self.assertEqual(ns["callback"](99, "pjpk27pick|001"), "class selection")
        self.assertEqual(ns["callback"](100, "pjpk27pick|033"), "class selection")
        self.assertEqual(class_calls, [99, 100])
        st = states[100]
        self.assertEqual(st["lesson_no"], "33")
        self.assertEqual(st["selected_sp_codes"], ["3.5.1", "4.5.1", "4.5.2", "5.3.2"])
        row = ns["_rph_rows"](st, "text")
        self.assertEqual(row["TARIKH"], "01/01/2027")
        self.assertEqual(row["KELAS"], "3 Bestari")
        self.assertIn("78", row["BAHAN BANTU MENGAJAR"])
        self.assertIn("DRAF CADANGAN", row["TAJUK"])
        self.assertEqual(generated, ["native"])
        self.assertEqual(ns["callback"](100, "unrelated_callback"), "previous")
        self.assertEqual(forwarded, [(100, "unrelated_callback")])
        self.assertTrue(preview.install(ns, enabled=True))

    def test_invalid_selection_fails_closed_without_entering_generation(self):
        state = {100: {"year": "Tahun 2", "subject": "Pendidikan Jasmani"}}
        called = []
        ns = {
            "callback": lambda *_: "previous", "_rph_rows": lambda st: {},
            "state": state, "send": lambda *_: "not allowed",
            "_lesson_to_class_v2439": lambda cid: called.append(cid),
        }
        self.assertTrue(preview.install(ns, enabled=True))
        self.assertEqual(ns["callback"](100, "pjpk27pick|038"), "not allowed")
        self.assertEqual(ns["callback"](100, "pjpk27pick|abc"), "not allowed")
        self.assertFalse(called)
        self.assertNotIn("_pjpk_2027_preview_selection", state[100])


if __name__ == "__main__":
    unittest.main()
