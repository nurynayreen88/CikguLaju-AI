"""Runtime contract for Sejarah 2027 Telegram DRAF RPH, without bot imports."""
import copy
import unittest

from web.sejarah_2027_user_runtime import (
    _catalog, _lesson, _selected, adapt_rows, install, year_number, SELECTION,
)


class SejarahUserRuntimeTest(unittest.TestCase):
    def test_all_108_sources_and_immutability(self):
        for y in (4, 5, 6):
            rows = _catalog(y, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
            self.assertEqual(len(rows), 36)
            self.assertEqual([r["pdp"] for r in rows], list(range(1, 37)))
            for n, entry in enumerate(rows, 1):
                self.assertEqual(entry["id"], f"SEJ-T{y}-PDP-{n:03d}")
                self.assertFalse(entry["rph"]["teacher_approval"])
                self.assertFalse(entry["rph"]["textbook_page_verified"])
                self.assertTrue(entry["rph"]["status"].startswith("DRAF"))
                self.assertTrue(entry["rph"]["textbook_reference"]["checked_focus_pages"]["printed_page_range"])

    def test_only_year_4_to_6(self):
        self.assertEqual(year_number("Tahun 5"), 5)
        self.assertEqual(year_number("6"), 6)
        for invalid in ("Tahun 1", "Tingkatan 4", "Tahun 7", "2027", "1"):
            self.assertIsNone(year_number(invalid))
        self.assertIsNone(_lesson(2, 1))
        self.assertIsNone(_lesson(5, 37))

    def test_all_native_rows_preserve_specific_content(self):
        for y in (4, 5, 6):
            for n in range(1, 37):
                entry = _lesson(y, n)
                r = entry["rph"]
                state = {
                    "subject": "Sejarah", "year": f"Tahun {y}",
                    "lesson_no": str(n), "sp_code": r["sp_codes"][0],
                    "sk_code": r["sk"], SELECTION: {"year": y, "pdp": n},
                }
                original = {"KELAS": "5 Bestari", "TARIKH": "22/03/2027",
                            "MASA": "08:00-09:00", "REFLEKSI": "Original generic"}
                outcome = adapt_rows(state, original)
                self.assertEqual(outcome["KELAS"], "5 Bestari")
                self.assertEqual(outcome["TARIKH"], "22/03/2027")
                self.assertEqual(outcome["MASA"], "08:00-09:00")
                self.assertEqual(outcome["STANDARD PEMBELAJARAN"], ", ".join(r["sp_codes"]))
                self.assertEqual(outcome["SET INDUKSI"], r["set_induksi"]["activity"])
                self.assertEqual(outcome["PENTAKSIRAN"], r["pengukuhan_pbd"]["activity"])
                self.assertEqual(outcome["PENUTUP"], r["penutup"]["activity"])
                self.assertIn(r["aktiviti_1"]["activity"], outcome["AKTIVITI UTAMA"])
                self.assertIn(r["aktiviti_2"]["activity"], outcome["AKTIVITI UTAMA"])
                self.assertIn(r["pengukuhan_pbd"]["activity"], outcome["AKTIVITI UTAMA"])
                self.assertIn(r["textbook_reference"]["checked_focus_pages"]["printed_page_range"],
                              outcome["BAHAN BANTU MENGAJAR"])
                self.assertIn("DRAF", outcome["TAJUK"])
                self.assertTrue(outcome["REFLEKSI"] == r["reflection"])
                self.assertEqual(original["REFLEKSI"], "Original generic")

    def test_stale_source_selection_does_not_replace_another_subject(self):
        year, n = 5, 7
        r = _lesson(year, n)["rph"]
        state = {
            "subject": "Sejarah", "year": "Tahun 5",
            "lesson_no": "8", "sp_code": r["sp_codes"][0],
            "sk_code": r["sk"], SELECTION: {"year": year, "pdp": n},
        }
        original = {"TAJUK": "Unrelated plan"}
        self.assertEqual(adapt_rows(state, original), original)
        state["lesson_no"] = str(n)
        state["subject"] = "Matematik"
        self.assertEqual(adapt_rows(state, original), original)

    def test_menu_pdp_and_existing_class_flow(self):
        calls = []
        original_calls = []
        subjects = {f"Tahun {y}": ["Bahasa Melayu", "Matematik"] for y in range(1, 7)}
        state = {17: {"year": "Tahun 5"}}

        def send(cid, text, kb=None):
            calls.append((cid, text, kb))
            return "sent"

        def original_cb(cid, action):
            original_calls.append((cid, action))
            return "original"

        def original_rows(st, *args, **kwargs):
            return {"KELAS": "5 Bestari", "TAJUK": "Old source"}

        def class_gate(cid):
            return "class-selection"

        ns = dict(callback=original_cb, send=send, _rph_rows=original_rows,
                  _lesson_to_class_v2439=class_gate,
                  SUBJECTS_BY_GRADE=subjects, state=state)
        self.assertFalse(install(ns, enabled=False))
        self.assertTrue(install(ns, enabled=True))
        for y in (4, 5, 6):
            self.assertEqual(subjects[f"Tahun {y}"].count("Sejarah"), 1)
        self.assertNotIn("Sejarah", subjects["Tahun 3"])
        self.assertTrue(install(ns, enabled=True))
        self.assertEqual(subjects["Tahun 5"].count("Sejarah"), 1)

        self.assertEqual(ns["callback"](17, "sub_Sejarah"), "sent")
        self.assertIn("Sejarah Tahun 5", calls[-1][1])
        self.assertEqual(ns["callback"](17, "sej27u|02"), "sent")
        self.assertIn("PdP", calls[-1][1])
        self.assertEqual(ns["callback"](17, "sej27p|007"), "class-selection")
        self.assertEqual(state[17][SELECTION], {"year": 5, "pdp": 7})
        self.assertEqual(state[17]["sp_code"], _lesson(5, 7)["rph"]["sp_codes"][0])
        formatted = ns["_rph_rows"](state[17])
        self.assertIn("PdP 007", formatted["TAJUK"])
        self.assertEqual(formatted["MATA PELAJARAN"], "Sejarah")
        self.assertEqual(ns["callback"](17, "home"), "original")
        self.assertEqual(original_calls[-1], (17, "home"))

        # Old buttons from another year must not create a wrong RPH.
        state[17]["year"] = "Tahun 6"
        self.assertEqual(ns["_rph_rows"](state[17])["TAJUK"], "Old source")


if __name__ == "__main__":
    unittest.main()
