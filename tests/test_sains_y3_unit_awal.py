import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from web.sains_y3_unit_awal import LESSONS, SP, add_opening_units, install
from web.telegram_verified_sequence_rph_bridge import (
    _build_state, _source, _source_text, _unit_token,
)


class ScienceOpeningUnitTests(unittest.TestCase):
    def setUp(self):
        self.base = [{"unit_code": "3.1", "unit_title": "Manusia", "sk_code": "3.1",
                      "sp_code": "3.1.1", "pdp_sequence_code": "ST3-PDP-005"}]
        self.runtime = SimpleNamespace(
            CIKGULAJU_DB_V2600_ACTIVE=True,
            _sm2542_rows=Mock(return_value=self.base),
            _sm2542_unique_units=lambda rows: list(dict.fromkeys(
                (row["unit_code"], row["unit_title"]) for row in rows)),
            _commit_multi_sp=self.commit,
            _local_rph_text=Mock(return_value="x" * 500),
            _rph_rows=lambda *args: {"REFLEKSI": "Catatan guru", "AKTIVITI UTAMA": "Generik"},
        )

    @staticmethod
    def commit(state, mapped):
        state["sp_code"] = mapped[0]["sp_code"]
        state["grouped_sp_codes"] = [row["sp_code"] for row in mapped]

    def test_supplement_covers_each_opening_standard_once_and_keeps_original_rows(self):
        rows, units = _source(self.runtime, 3, "SCIENCE")
        self.assertEqual(rows[:1], self.base)
        self.assertEqual(len(self.base), 1)
        self.assertEqual([r["sp_code"] for r in rows[1:]], list(SP))
        self.assertEqual(len({r["pdp_sequence_code"] for r in rows[1:]}), 9)
        self.assertIn(("2.1", "Peraturan Bilik Sains"), units)
        self.assertEqual(_source(self.runtime, 4, "SCIENCE")[0], self.base)
        self.assertEqual(add_opening_units([]), [])

    def test_existing_source_sk_and_pdp_codes_take_precedence(self):
        already_mapped = [
            {"sk_code": "2.1", "pdp_sequence_code": "existing-rules"},
            {"sk_code": "3.1", "pdp_sequence_code": LESSONS[0].code},
        ]
        supplemental = add_opening_units(already_mapped)[2:]
        self.assertFalse(any(r["sk_code"] == "2.1" for r in supplemental))
        self.assertFalse(any(r["pdp_sequence_code"] == LESSONS[0].code for r in supplemental))

    def test_authored_activities_and_full_standards_reach_native_rows(self):
        install(self.runtime)
        for lesson in LESSONS:
            with self.subTest(pdp=lesson.number):
                token = _unit_token(lesson.sk, lesson.unit)
                state = _build_state(self.runtime, 3, "SCIENCE", token, lesson.code, {
                    "class": "", "date": "", "time": "", "students": "",
                })
                text = _source_text(self.runtime, state)
                self.assertGreater(len(text), 500)
                rows = self.runtime._rph_rows(state, text)
                self.assertIn(lesson.guided, rows["AKTIVITI UTAMA"])
                self.assertIn(lesson.independent, rows["AKTIVITI UTAMA"])
                self.assertEqual(rows["PENTAKSIRAN"], lesson.assessment)
                self.assertEqual(rows["REFLEKSI"], "Catatan guru")
                self.assertEqual(rows["STANDARD PEMBELAJARAN"].splitlines(),
                                 [f"{sp} {SP[sp]}" for sp in lesson.standards])
        self.runtime._local_rph_text.assert_not_called()
        self.assertEqual(self.runtime._rph_rows({}, "")["AKTIVITI UTAMA"], "Generik")
