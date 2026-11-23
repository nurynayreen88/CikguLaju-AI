"""Safety tests for one-time migration. No network or Storage write."""
from __future__ import annotations
import os
from unittest import TestCase
from unittest.mock import patch

from web.rpt_kssr_bm_private_storage import PrivateWordUnavailable
from tools.migrate_rpt_bm_kssr_word_private import migrate, _request

class MigrationSafetyTests(TestCase):
    def test_default_only_validates_local_verified_docs(self):
        self.assertEqual(migrate(upload=False),[2,3,4,5,6])

    def test_upload_requires_explicit_one_time_flag(self):
        with patch.dict(os.environ,{"CIKGULAJU_PRIVATE_WORD_MIGRATION_OK":"NO"}):
            with self.assertRaises(PrivateWordUnavailable):
                migrate(upload=True,opener=lambda *_a,**_k:self.fail("Unexpected network"))

    def test_api_upload_request_forbids_upsert(self):
        req=_request("https://soxakntcanbycjoygrcx.supabase.co/storage/v1/object/cikgulaju-materials/test", "sb_secret_"+"s"*48, data=b"word",method="POST")
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(req.get_header("X-upsert"),"false")
        self.assertNotIn("Authorization",req.headers)
        self.assertEqual(req.data,b"word")
