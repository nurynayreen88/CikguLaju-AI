"""Offline tests: production startup can migrate only with two approvals."""
from __future__ import annotations
import os
import unittest
from unittest.mock import patch

from tools.stage_private_rpt_word_once import stage_only_when_approved


class StartupPrivateWordMigrationTest(unittest.TestCase):
    def test_migration_disabled_when_both_flags_not_yes(self):
        for env in ({}, {"CIKGULAJU_PRIVATE_WORD_MIGRATION_OK":"YES"},
                    {"CIKGULAJU_PRIVATE_WORD_MIGRATION_ON_STARTUP":"YES"}):
            with self.subTest(env=env), patch.dict(os.environ,env,clear=True), \
                 patch("tools.migrate_rpt_bm_kssr_word_private.migrate") as migrate:
                self.assertFalse(stage_only_when_approved())
                migrate.assert_not_called()

    def test_both_flags_permit_exact_five_years_only(self):
        opts={"CIKGULAJU_PRIVATE_WORD_MIGRATION_OK":"YES",
              "CIKGULAJU_PRIVATE_WORD_MIGRATION_ON_STARTUP":"YES"}
        with patch.dict(os.environ,opts,clear=True), \
             patch("tools.migrate_rpt_bm_kssr_word_private.migrate",return_value=[2,3,4,5,6]) as migrate:
            self.assertTrue(stage_only_when_approved())
            migrate.assert_called_once_with(upload=True)

    def test_incomplete_migration_fails_and_never_claims_success(self):
        opts={"CIKGULAJU_PRIVATE_WORD_MIGRATION_OK":"YES",
              "CIKGULAJU_PRIVATE_WORD_MIGRATION_ON_STARTUP":"YES"}
        with patch.dict(os.environ,opts,clear=True), \
             patch("tools.migrate_rpt_bm_kssr_word_private.migrate",return_value=[2,3]):
            with self.assertRaises(RuntimeError):
                stage_only_when_approved()

if __name__=="__main__":
    unittest.main()
