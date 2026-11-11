"""Fail-closed audit invariants for the Sains Tahun 6 2021 source probe.

These tests never fetch copyrighted text and cannot grant academic approval.
"""
import unittest
from scripts.probe_sains_y6_2021_96_sp_anyflip_20261110 import (
    source_code_coverage_complete,
)


class SourceCoverageGuardTests(unittest.TestCase):
    def candidate(self):
        return {
            "expected_unique_sp": 96,
            "academic_release_approved": False,
            "sources": [{
                "http_status": 200,
                "official_unique_code_hits": 96,
                "text_chars": 20000,
                "missing_codes": [],
                "matching_code_contexts": {str(n): [{"context": "source"}]
                                           for n in range(96)},
            }],
        }

    def test_complete_code_coverage_is_only_preliminary_source_gate(self):
        self.assertTrue(source_code_coverage_complete(self.candidate()))

    def test_403_with_zero_sources_can_never_be_green(self):
        report = self.candidate()
        report["sources"] = [{"http_status": 403,
                              "error": "HTTPError: Forbidden"}]
        self.assertFalse(source_code_coverage_complete(report))

    def test_partial_or_empty_matches_cannot_be_green(self):
        for defect in ("official_unique_code_hits", "text_chars",
                       "missing_codes", "matching_code_contexts", "http_status"):
            with self.subTest(defect=defect):
                report = self.candidate()
                item = report["sources"][0]
                item[defect] = {
                    "official_unique_code_hits": 95,
                    "text_chars": 0,
                    "missing_codes": ["2.1.1"],
                    "matching_code_contexts": {},
                    "http_status": 404,
                }[defect]
                self.assertFalse(source_code_coverage_complete(report))

    def test_never_accept_academic_approved_or_wrong_expected_total(self):
        a = self.candidate()
        a["academic_release_approved"] = True
        self.assertFalse(source_code_coverage_complete(a))
        b = self.candidate()
        b["expected_unique_sp"] = 95
        self.assertFalse(source_code_coverage_complete(b))


if __name__ == "__main__":
    unittest.main()
