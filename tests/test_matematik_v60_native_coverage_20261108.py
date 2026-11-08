"""Exercise the read-only release gate using simulated native PdP rows.

This CI cannot claim a live DB audit: staging must supply the real Telegram
runtime before mapping_ready=true can be accepted for release.
"""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from rph_standalone.matematik.v60_source_loader import get_lesson
from web.matematik_v60_native_rows import parse_lesson
from web.matematik_v60_native_coverage import audit_native_mapping, NativeCoverageUnavailable

FLAG = {"CIKGULAJU_ENV": "staging", "CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED": "1"}


def source_row(year, lesson=1):
    source = parse_lesson(get_lesson(year, lesson), year, lesson)
    return {"pdp_sequence_code": f"native-{year}-{lesson:03}",
            "source_sequence_no": lesson,
            "sk_code": source["_sk_code"], "sp_code": source["_sp_code"]}


def runtime(mapping, active=True):
    def reader(year, subject):
        return mapping.get(int(year.split()[-1]), [])
    return SimpleNamespace(CIKGULAJU_MATH_V2599_SOURCE_VERIFIED=active, _sm2542_rows=reader)


class CoverageGateTest(unittest.TestCase):
    def test_partial_coverage_is_reported_not_released(self):
        with patch.dict(os.environ, FLAG):
            report = audit_native_mapping(runtime({2: [source_row(2)]}))
        self.assertEqual(report["source_lessons"], 585)
        self.assertEqual(report["matched"], 1)
        self.assertEqual(report["per_year"]["2"]["unmatched"], 116)
        self.assertFalse(report["mapping_ready"])
        self.assertFalse(report["academic_signoff"])
        self.assertFalse(report["runtime_e2e_passed"])

    def test_duplicate_and_multi_sp_rejected(self):
        first = source_row(2)
        duplicate = dict(first, pdp_sequence_code="duplicate")
        multi = dict(first, pdp_sequence_code=first["pdp_sequence_code"], sp_code="9.9.9")
        with patch.dict(os.environ, FLAG):
            report = audit_native_mapping(runtime({2: [first, duplicate, multi]}))
        self.assertEqual(report["per_year"]["2"]["matched"], 0)
        self.assertGreater(report["per_year"]["2"]["conflicts"], 0)
        self.assertFalse(report["mapping_ready"])

    def test_full_synthetic_mapping_is_not_academic_approval(self):
        mapping = {year: [source_row(year, n) for n in range(1, 118)]
                   for year in range(2, 7)}
        with patch.dict(os.environ, FLAG):
            report = audit_native_mapping(runtime(mapping))
        self.assertTrue(report["mapping_ready"])
        self.assertEqual(report["matched"], 585)
        self.assertFalse(report["academic_signoff"])
        self.assertFalse(report["runtime_e2e_passed"])

    def test_old_science_v26_flag_cannot_authorize_math_mapping(self):
        misleading = SimpleNamespace(
            CIKGULAJU_DB_V2600_ACTIVE=True,
            _sm2542_rows=lambda year, subject: [source_row(2)],
        )
        with patch.dict(os.environ, FLAG):
            with self.assertRaises(NativeCoverageUnavailable):
                audit_native_mapping(misleading)

    def test_no_live_db_or_flag_fails_closed(self):
        with patch.dict(os.environ, FLAG):
            with self.assertRaises(NativeCoverageUnavailable):
                audit_native_mapping(runtime({}, active=False))
        with patch.dict(os.environ, {"CIKGULAJU_ENV": "production",
                                      "CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED": "1"}):
            with self.assertRaises(NativeCoverageUnavailable):
                audit_native_mapping(runtime({}))


if __name__ == "__main__":
    unittest.main()
