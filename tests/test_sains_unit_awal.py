import unittest
from collections import Counter
from types import SimpleNamespace
from unittest.mock import Mock

from web.sains_unit_awal import LESSONS, add_opening_units, install
from web.telegram_verified_sequence_rph_bridge import (
    _build_state, _source, _source_text, _unit_token,
)


class ScienceOpeningUnitTests(unittest.TestCase):
    def setUp(self):
        self.base = [{"unit_code": "3.1", "unit_title": "Existing",
                      "sk_code": "3.1", "sp_code": "3.1.1",
                      "pdp_sequence_code": "existing"}]
        self.runtime = SimpleNamespace(
            CIKGULAJU_DB_V2600_ACTIVE=True,
            _sm2542_rows=Mock(return_value=self.base),
            _sm2542_unique_units=lambda rows: list(dict.fromkeys(
                (row["unit_code"], row["unit_title"]) for row in rows)),
            _commit_multi_sp=self.commit,
            _local_rph_text=Mock(side_effect=AssertionError("Unexpected fallback")),
            _rph_rows=lambda *args: {"REFLEKSI": "Catatan guru", "AKTIVITI UTAMA": "Asal"},
        )

    @staticmethod
    def commit(state, mapped):
        state["sp_code"] = mapped[0]["sp_code"]
        state["grouped_sp_codes"] = [row["sp_code"] for row in mapped]

    def test_each_required_standard_is_reachable_once(self):
        process = {f"1.1.{n}" for n in range(1, 13)}
        manipulative = {f"1.2.{n}" for n in range(1, 6)}
        expected = {
            1: {"1.1.1", "1.1.2"} | manipulative,
            2: {"1.1.1", "1.1.2", "1.1.3", "1.1.4", "2.1.1"} | manipulative,
            4: process, 5: process, 6: process,
        }
        for year, standards in expected.items():
            with self.subTest(year=year):
                rows, units = _source(self.runtime, year, "SCIENCE")
                self.assertEqual(rows[:1], self.base)
                self.assertEqual(len(self.base), 1)
                self.assertEqual(Counter(r["sp_code"] for r in rows[1:]),
                                 Counter(standards))
                self.assertEqual(("2.1", "Peraturan Bilik Sains") in units, year == 2)
        self.assertEqual(_source(self.runtime, 1, "MATH")[0], self.base)
        self.assertEqual(add_opening_units(1, []), [])

    def test_existing_catalogue_groups_and_codes_take_precedence(self):
        source = [
            {"sk_code": "1.1", "sp_code": "1.1.1", "pdp_sequence_code": "existing-1"},
            {"sk_code": "3.1", "sp_code": "3.1.1", "pdp_sequence_code": "ST2-PDP-056"},
            {"sk_code": "2.1", "sp_code": "", "pdp_sequence_code": "incomplete"},
        ]
        rows = add_opening_units(2, source)
        self.assertEqual(rows[:3], source)
        self.assertFalse(any(r["sk_code"] == "1.1" for r in rows[3:]))
        self.assertFalse(any(r["pdp_sequence_code"] == "ST2-PDP-056" for r in rows[3:]))
        self.assertIn("2.1.1", {r["sp_code"] for r in rows[3:]})
        self.assertEqual(add_opening_units(2, rows), rows)

    def test_each_plan_supplies_its_own_activities_standards_and_assessment(self):
        self.assertTrue(install(self.runtime))
        for plan in LESSONS:
            with self.subTest(pdp=plan.code):
                state = _build_state(
                    self.runtime, plan.year, "SCIENCE",
                    _unit_token(plan.sk, plan.unit), plan.code,
                    {"class": "", "date": "", "time": "", "students": ""},
                )
                text = _source_text(self.runtime, state)
                self.assertGreater(len(text), 500)
                rows = self.runtime._rph_rows(state, text)
                self.assertEqual(state["selected_sp_codes"], list(plan.standards))
                self.assertIn(plan.guided, rows["AKTIVITI UTAMA"])
                self.assertIn(plan.independent, rows["AKTIVITI UTAMA"])
                self.assertIn(plan.pages, rows["BAHAN BANTU MENGAJAR"])
                self.assertEqual(rows["PENTAKSIRAN"], plan.assessment)
                self.assertEqual(rows["REFLEKSI"], "Catatan guru")
        self.assertEqual(self.runtime._rph_rows({}, "")["AKTIVITI UTAMA"], "Asal")
