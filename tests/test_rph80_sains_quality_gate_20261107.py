"""Unit regression checks for read-only Sains-first 80% audit staging."""
from __future__ import annotations

import unittest
from tools.audit_rph80_sains_first_20261107 import (
    EXPECTED, WEIGHTS, build_queue, grade_from_evidence,
)
from web.sains_y3_rph_activity_preview_20261106 import (
    BANK, adapt_rows, source_ledgers,
)


def staged_fixture():
    rows = []
    for year, count in EXPECTED.items():
        for num in range(1, count + 1):
            rows.append({
                "tahun": year,
                "pdp_code": f"SCI-Y{year}-PDP-{num:03d}",
                "pdp_number": num,
                "unit": f"Unit {year}",
                "sp": "3.1.1",
                "tajuk": f"PdP {num}",
                "keputusan": "HOLD",
                "isu": "TEXTBOOK_PAGE_VISUAL_QA_PENDING",
            })
    return rows


class TestSains80Queue(unittest.TestCase):
    def test_342_exact_and_297_missing(self):
        queue = build_queue(staged_fixture())
        self.assertEqual(len(queue), 342)
        self.assertEqual(sum(r["tahun"] != 3 for r in queue), 297)
        self.assertEqual(sum(r["tahun"] == 3 for r in queue), 45)
        self.assertTrue(all(r["quality_percent"] == "" for r in queue))
        self.assertEqual([x["tahun"] for x in queue[:3]], [6, 6, 6])
        self.assertEqual(queue[-1]["tahun"], 3)
        self.assertTrue(all(x["teacher_signoff"] == "MISSING" for x in queue))

    def test_generated_stage_130_not_approved_and_167_pending(self):
        rows=staged_fixture()
        generated={
            2:{f"SCI-Y2-PDP-{i:03d}" for i in range(1,52)},
            4:{f"SCI-Y4-PDP-{i:03d}" for i in range(1,80)},
        }
        queue=build_queue(rows,generated=generated)
        self.assertEqual(sum(r["source_status"].startswith("STAGING_STANDALONE")
                             for r in queue),130)
        self.assertEqual(sum(r["source_status"]=="NO_INDIVIDUALLY_AUDITED_STANDALONE_RPH"
                             for r in queue),167)
        self.assertTrue(all(r["quality_percent"]=="" for r in queue))
        self.assertTrue(all(r["teacher_signoff"]=="MISSING" for r in queue))

    def test_duplicate_code_fails_closed(self):
        rows = staged_fixture()
        rows[-1]["pdp_code"] = rows[0]["pdp_code"]
        with self.assertRaises(ValueError):
            build_queue(rows)

    def test_false_ready_fails_closed(self):
        rows = staged_fixture()
        rows[0]["keputusan"] = "READY"
        with self.assertRaises(ValueError):
            build_queue(rows)

    def test_incomplete_review_is_not_scored(self):
        self.assertIsNone(grade_from_evidence({k: v for k, v in WEIGHTS.items()}, {}))
        signed = {"reviewer": "guru", "review_date": "2026-11-07",
                  "dskp": "source_a", "textbook_pages": "source_b",
                  "specific_activities_pbd": "source_c", "rendered_word_pdf": "source_d",
                  "runtime_parity": "source_e",
                  "review_is_for_exact_source_sha": True}
        self.assertIsNone(grade_from_evidence({**WEIGHTS, "word_pdf": 16}, signed))
        self.assertEqual(grade_from_evidence(WEIGHTS, signed), 100)
        self.assertEqual(grade_from_evidence({**WEIGHTS, "sk_sp": 5}, signed), 80)


class TestSainsY3Pedagogy(unittest.TestCase):
    def test_experiment_safety_and_pbd(self):
        self.assertIn("tidak merasa", BANK["7.1.3"][1])
        self.assertIn("bekas penyukat plastik", BANK["6.1.6"][6].lower())
        self.assertIn("tidak berada di bawah beban", BANK["10.1.4"][1])
        self.assertIn("Zuhrah lebih panas daripada Utarid", BANK["9.1.2"][2])

    def test_existing_pdp_identity_preserved_and_individual_pbd(self):
        pages, _fixes = source_ledgers()
        entry = next(x for x in pages.values() if x["sp_code"] == "6.1.6")
        state = {
            "subject": "Sains", "year": "Tahun 3",
            "year_label": "Tahun 3",
            "pdp_sequence_code": entry["pdp_code"],
            "sp_code": "6.1.6", "sk_code": "6.1",
        }
        orig = {"PENTAKSIRAN": "PENTAKSIRAN ASAL", "LAIN": "JANGAN SENTUH"}
        result = adapt_rows(state, orig)
        self.assertIsNot(result, orig)
        self.assertEqual(orig["PENTAKSIRAN"], "PENTAKSIRAN ASAL")
        self.assertEqual(result["LAIN"], "JANGAN SENTUH")
        self.assertIn("setiap murid", result["PENTAKSIRAN"])
        self.assertIn("bekas penyukat plastik", result["BAHAN BANTU MENGAJAR"].lower())
        self.assertIn("Aktiviti 1", result["AKTIVITI UTAMA"])
        self.assertIn("Aktiviti 2", result["AKTIVITI UTAMA"])
        state["subject"] = "Matematik"
        self.assertIs(adapt_rows(state, orig), orig)


if __name__ == "__main__":
    unittest.main()
