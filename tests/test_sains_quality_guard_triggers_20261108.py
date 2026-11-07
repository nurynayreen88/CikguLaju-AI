"""Regression: every new authored Sains bank must trigger release checks.

A CI pass does not approve classroom content. The launcher stays protected,
regardless of what source files are already present in Git main.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import check_sains_rph_publication_20261108 as gate

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/sains_quality_release_guard_20261108.yml"
DRAFT_MODULES=(
    "sains_y2_51_activities_draf_20261107",
    "sains_y3_rph_activity_preview_20261106",
    "sains_y4_79_activity_bank_draf_20261107",
    "sains_y6_84_activity_bank_draf_20261107",
)
PATHS=(
    "web/sains_y2_51_activities_draf_20261107.py",
    "web/sains_y3_rph_activity_preview_20261106.py",
    "web/sains_y4_79_activity_bank_draf_20261107.py",
    "web/sains_y5_83_activity_bank_draf_20261107.py",
    "web/sains_y6_84_activity_bank_draf_20261107.py",
    "tools/render_sains_y2_51_rph_draf_20261107.py",
    "tools/render_sains_y3_45_review_pack_20261106.py",
    "tools/render_sains_y4_79_rph_draf_20261107.py",
    "tools/render_sains_y5_83_rph_draf_20261107.py",
    "tools/render_sains_y6_84_rph_draf_20261107.py",
)


class TestAllSainsRPHSourceQualityTriggers(unittest.TestCase):
    def test_pr_and_main_push_gate_all_five_years(self):
        config=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request:",config)
        self.assertIn("push:",config)
        self.assertIn("branches: [main]",config)
        for name in PATHS:
            self.assertEqual(config.count('"'+name+'"'),2,name)
        self.assertEqual(config.count('"web/sains_y6_draf_bank_part*_20261107.tsv"'),2)

    def test_readonly_audit_does_not_claim_342_drafts_are_live(self):
        report=gate.audit()
        self.assertEqual(report["new_source_total"],342)
        self.assertEqual(report["academically_signed_off"],0)
        self.assertEqual(report["not_yet_certified"],342)
        self.assertFalse(report["new_science_public_sources_auto_activated"])
        self.assertTrue(report["all_noncertified_new_rph_are_hold"])

    def test_direct_import_of_any_unapproved_year2_3_4_6_bank_is_rejected(self):
        production=gate.MAIN_LAUNCH.read_text(encoding="utf-8")
        with TemporaryDirectory() as tmp:
            target=Path(tmp)/"launcher.py"
            for module in DRAFT_MODULES:
                with self.subTest(module=module):
                    target.write_text(production+"\n# unauthorized direct import\n"
                                      +"import web."+module+"\n",encoding="utf-8")
                    with patch.object(gate,"MAIN_LAUNCH",target):
                        with self.assertRaises(ValueError):
                            gate.audit()


if __name__=="__main__":
    unittest.main()
