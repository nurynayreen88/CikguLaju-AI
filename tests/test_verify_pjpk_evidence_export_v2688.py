import copy
import unittest
from scripts.pjpk_source_review_packet_v2683 import packet
from scripts.pjpk_verified_evidence_export_v2687 import export
from scripts.verify_pjpk_evidence_export_v2688 import verify
class EvidenceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.original=packet([{"year":"Tahun 3","subject":"Pendidikan Kesihatan","entry_id":7,
          "topic":"A","record_type":"SP_SOURCE_REVIEW","standard_code":"1.1.1",
          "rpt_text":"RPT","evidence_status":"NO_DIRECT_DSKP_TEXT",
          "direct_dskp_text":"","source_document":"","action":"TRANSCRIBE"}])
    def test_pending_empty_export(self):
        reviewed=copy.deepcopy(self.original)
        result=verify(self.original,reviewed,[])
        self.assertEqual((result["verified_rows"],result["blocked_rows"]),(0,1))
        self.assertFalse(result["production_promoted"])
    def test_detect_export_tampering(self):
        reviewed=copy.deepcopy(self.original)
        reviewed[0].update(review_status="SOURCE_VERIFIED",reviewed_dskp_code="1.1.1",
          reviewed_dskp_text="Verified text",source_document="DSKP",source_page="12",
          reviewer="Reviewer")
        exported=export(self.original,reviewed)
        self.assertTrue(verify(self.original,reviewed,exported)["export_matches_review"])
        exported[0]["reviewed_dskp_text"]="Different"
        with self.assertRaises(ValueError):verify(self.original,reviewed,exported)
        with self.assertRaises(ValueError):verify(self.original,reviewed,[])
if __name__=="__main__":unittest.main()
