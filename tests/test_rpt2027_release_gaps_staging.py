"""A successful gap audit MUST NOT make an unapproved RPT release-ready."""
import json
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path
from scripts.audit_rpt2027_release_gaps_staging import build_audit, write_audit

class RPT2027FailClosedReleaseGapQA(unittest.TestCase):
    def test_current_source_gaps_are_visible_not_silently_filled(self):
        a = build_audit()
        self.assertEqual(a["status"], "STAGING_ONLY_BLOCKED_NOT_RELEASE_READY")
        self.assertIs(a["is_release_ready"], False)
        self.assertIs(a["protect_production"], True)
        self.assertIs(a["change_users_db"], False)
        self.assertEqual(a["arabic"]["pdp_total"], 298)
        self.assertEqual(a["arabic"]["without_full_sk_text"], 298)
        self.assertEqual(a["arabic"]["without_full_sp_text"], 298)
        self.assertEqual(a["arabic"]["source_sp_page_anchors"], 298)
        self.assertEqual(a["arabic"]["without_sourced_calendar_week"], 298)
        self.assertEqual(a["pendidikan_islam"]["withheld_count"], 6)
        self.assertEqual(a["pendidikan_islam"]["years"]["2"]["withheld_ids"], ["035"])
        self.assertEqual(a["pendidikan_islam"]["years"]["6"]["withheld_ids"],
                         ["006","014","018","060","117"])
        self.assertEqual(a["rbt"]["total_pdp"], 96)
        self.assertEqual(a["rbt"]["without_sourced_2027_week"], 96)
        self.assertEqual(a["rbt"]["source_2026_sp_block_entries"], 23)
        self.assertEqual(a["sains"]["partial_pdp"], 342)
        self.assertEqual(a["sains"]["snapshot_status"],
                         "LEGACY_INTERNAL_CODES_NOT_CURRENT_KSSR_VERIFIED")
        self.assertTrue(a["sains"]["kssr2017_original_dskp_edition_conflict"])
        self.assertTrue(a["sains"]["verified_flag_from_database_is_insufficient"])
        self.assertEqual(a["sains"]["external_evidence_conflicts"],6)
        self.assertEqual(a["sains"]["years_requiring_full_code_text_remap"],[4,5,6])
        self.assertFalse(a["sains"]["ready_for_web_telegram"])
        self.assertGreaterEqual(len(a["remaining_releases"]), 6)

    def test_source_derived_arabic_sp_text_is_not_academic_approval(self):
        report = build_audit()
        arabic = report["arabic"]
        # The 2026-11-10 DSKP transcription now populates candidate wording,
        # but 298/298 staged PdP still lack independent visual signoff.
        self.assertEqual(arabic["candidate_sp_text_present_not_approved"], 298)
        self.assertEqual(arabic["without_full_sp_text"], 298)
        self.assertEqual(arabic["without_full_sk_text"], 298)
        self.assertFalse(report["is_release_ready"])
        for year in map(str, range(2, 7)):
            self.assertEqual(
                arabic["years"][year]["with_candidate_sp_text"],
                arabic["years"][year]["pdp"],
            )

    def test_unreviewed_one_record_signoff_cannot_silently_clear_release_gate(self):
        from scripts import audit_rpt2027_release_gaps_staging as mod
        original = mod.arabic_records

        def changed(year):
            rows = deepcopy(original(year))
            if year == 2:
                rows[0]["source_sp_dskp_text_signoff"] = True
            return rows

        with patch.object(mod, "arabic_records", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "Release-gap counts differ"):
                mod.build_audit()

    def test_gap_report_is_machine_readable_and_does_not_write_production(self):
        with tempfile.TemporaryDirectory() as d:
            name=Path(d)/"read_only_gaps.json"
            written=write_audit(name)
            self.assertEqual(written, name)
            parsed=json.loads(written.read_text(encoding="utf-8"))
            self.assertIs(parsed["is_release_ready"],False)
            self.assertFalse(parsed["change_users_db"])

if __name__ == "__main__":
    unittest.main()
