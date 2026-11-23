"""Regression for source-backed PI live Word/PDF activity rows, not 696."""
import unittest
from types import SimpleNamespace

from web.pi_verified_rpt_activity_restore_20261123 import (
    _source_steps, restore_verified_pi_activity_rows, install,
)

NOTE = ("1. ممباچ اية سچارا تلقي دان مشافهة "
        "2. ممبتولكن باچاءن يڠ كورڠ فصيح "
        "3. ممبيمبيڠ راكن سباي "
        "4. ݢورو مريكوت ڤنچاڤاين موريد.")

ACTIVITY = (
    "اکتيۏيتي 1 - ڤڠاکتيفن ڤڠتاهوان\n"
    "1. ممباچ اية سچارا تلقي دان مشافهة 2.\n"
    "اکتيۏيتي 2 - ڤنروکاءن فوکس\n"
    "1. ݢورو ممبيمبيڠ موريد مڽلسايکن توݢسن ڤمبلاجرن:\n"
    "2. ممباچ اية سچارا تلقي دان مشافهة 2.\n"
    "اکتيۏيتي 3 - اڤليکاسي\n"
    "1. موريد مڠاڤليکاسيکن ڤمبلاجرن.\n"
    "اکتيۏيتي 4 - ڤنتاکسيرن\n"
    "1. موريد منونجوقکن ڤڠواساءن."
)


def state():
    return {
        "subject": "Pendidikan Islam",
        "task": "rph",
        "rpt_entry_id": 1275,
        "_quick_selected_rpt_row_v2388": {
            "id": 1275, "verified": 1,
            "activity_note": NOTE,
            "assessment_note": "ڤنتاکسيرن ملالوي باچاءن موريد",
        },
        "sp_code": "",
        "rph_teacher_reflection": "Refleksi guru dikekalkan.",
    }


def rows():
    return {"AKTIVITI UTAMA": ACTIVITY,
            "STANDARD PEMBELAJARAN": "ختام / تسميع",
            "REFLEKSI": "Refleksi guru dikekalkan.",
            "OBJEKTIF PEMBELAJARAN": "ممباچ سورة البقرة."}


class VerifiedPIRestorationTests(unittest.TestCase):
    def test_source_has_all_four_nonempty_original_numbered_steps(self):
        items = _source_steps(NOTE)
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0], "ممباچ اية سچارا تلقي دان مشافهة")
        self.assertEqual(items[1], "ممبتولكن باچاءن يڠ كورڠ فصيح")
        self.assertEqual(items[2], "ممبيمبيڠ راكن سباي")
        self.assertEqual(items[3], "ݢورو مريكوت ڤنچاڤاين موريد.")

    def test_restores_original_steps_2_to_4_only_into_truncated_activity(self):
        before = rows()
        fixed = restore_verified_pi_activity_rows(state(), before)
        self.assertIsNot(fixed, before)
        self.assertEqual(before["AKTIVITI UTAMA"], ACTIVITY)
        value = fixed["AKTIVITI UTAMA"]
        self.assertNotIn("مشافهة 2.", value)
        for number, action in enumerate(_source_steps(NOTE), 1):
            self.assertIn(f"{number}. {action}", value)
        self.assertEqual(value.count("1. ممباچ اية"), 1)
        self.assertIn("اکتيۏيتي 1 - ڤڠاکتيفن", value)
        self.assertIn("اکتيۏيتي 4 - ڤنتاکسيرن", value)
        for key in before.keys() - {"AKTIVITI UTAMA"}:
            self.assertEqual(fixed[key], before[key])
        self.assertIs(restore_verified_pi_activity_rows(state(), fixed), fixed)

    def test_no_change_for_other_subjects_invalid_row_or_no_truncation(self):
        standard = rows()
        other = state()
        other["subject"] = "Sains"
        self.assertIs(restore_verified_pi_activity_rows(other, standard), standard)
        other = state()
        other["rpt_entry_id"] = 1276
        self.assertIs(restore_verified_pi_activity_rows(other, standard), standard)
        other = state()
        other["_quick_selected_rpt_row_v2388"]["verified"] = 0
        self.assertIs(restore_verified_pi_activity_rows(other, standard), standard)
        other = state()
        other["_quick_selected_rpt_row_v2388"]["activity_note"] = (
            "1. ممباچ اية سچارا تلقي دان مشافهة 2. لاتيهن صحيح")
        self.assertIs(restore_verified_pi_activity_rows(other, standard), standard)
        complete = dict(standard)
        complete["AKTIVITI UTAMA"] = "\n".join(f"{i}. {item}"
            for i, item in enumerate(_source_steps(NOTE), 1))
        self.assertIs(restore_verified_pi_activity_rows(state(), complete), complete)

    def test_real_number_in_verse_reference_is_never_dropped(self):
        original = rows()
        original["AKTIVITI UTAMA"] += "\nسورة البقرة آية 2. جمڤولن 2. مڽمق"
        result = restore_verified_pi_activity_rows(state(), original)
        self.assertIn("آية 2.", result["AKTIVITI UTAMA"])
        self.assertIn("جمڤولن 2.", result["AKTIVITI UTAMA"])

    def test_installer_is_idempotent_and_preserves_source_state(self):
        calls = []
        def original_rph_rows(s, text):
            calls.append((s, text))
            return rows()
        runtime = SimpleNamespace(_rph_rows=original_rph_rows)
        self.assertTrue(install(runtime))
        self.assertTrue(install(runtime))
        original_state = state()
        rendered = runtime._rph_rows(original_state, "NATIVE_SOURCE")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], (original_state, "NATIVE_SOURCE"))
        self.assertEqual(original_state["_quick_selected_rpt_row_v2388"]["activity_note"], NOTE)
        self.assertIn("3. ممبيمبيڠ راكن سباي", rendered["AKTIVITI UTAMA"])


if __name__ == "__main__":
    unittest.main()
