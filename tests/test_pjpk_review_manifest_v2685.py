"""Check 12-scope PJPK review manifest remains fail-closed."""
import copy
import unittest
from scripts.pjpk_source_review_packet_v2683 import packet
from scripts.pjpk_review_manifest_v2685 import manifest
class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.original=packet([{"year":"Tahun 2","subject":"Pendidikan Kesihatan","entry_id":10,
          "topic":"Unit","record_type":"SP_SOURCE_REVIEW","standard_code":"1.1.1",
          "rpt_text":"RPT","evidence_status":"NO_DIRECT_DSKP_TEXT","direct_dskp_text":"",
          "source_document":"","action":"TRANSCRIBE"}])
    def test_pending_across_all_scopes(self):
        result=manifest(self.original,copy.deepcopy(self.original))
        self.assertEqual(result["scope_count"],12)
        self.assertEqual((result["total"],result["still_blocked"],result["verified_for_further_audit"]),(1,1,0))
        self.assertFalse(result["production_promoted"])
        self.assertEqual(result["scopes"][3]["blocked"],1)
    def test_verified_requires_exact_source(self):
        reviewed=copy.deepcopy(self.original)
        reviewed[0].update(review_status="SOURCE_VERIFIED",source_document="DSKP",
            source_page="26",reviewer="Reviewer",reviewed_dskp_code="1.1.1",
            reviewed_dskp_text="Exact source wording")
        result=manifest(self.original,reviewed)
        self.assertEqual((result["still_blocked"],result["verified_for_further_audit"]),(0,1))
        self.assertFalse(result["production_promoted"])
    def test_reject_unreviewed_promotion(self):
        reviewed=copy.deepcopy(self.original);reviewed[0]["review_status"]="SOURCE_VERIFIED"
        with self.assertRaises(ValueError):manifest(self.original,reviewed)
if __name__=="__main__":unittest.main()
