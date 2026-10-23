"""Ensure source review packet never invents evidence or marks rows READY."""
import unittest
from scripts.pjpk_source_review_packet_v2683 import packet,FIELDS
class PacketTests(unittest.TestCase):
    def test_review_only_fields_and_source_preservation(self):
        r={"year":"Tahun 3","subject":"Pendidikan Kesihatan","entry_id":8,
           "topic":"Kesihatan","record_type":"SP_SOURCE_REVIEW","standard_code":"1.1.1",
           "rpt_text":"RPT wording","evidence_status":"NO_DIRECT_DSKP_TEXT",
           "direct_dskp_text":"","source_document":"","action":"TRANSCRIBE"}
        result=packet([r])[0]
        self.assertEqual(set(result),set(FIELDS))
        self.assertEqual(result["rpt_sp_text"],"RPT wording")
        self.assertEqual(result["review_status"],"PENDING_SOURCE_REVIEW")
        for field in ("reviewed_dskp_code","reviewed_dskp_text","reviewed_sk_code",
                      "reviewed_sk_text","source_document","source_page","reviewer"):
            self.assertEqual(result[field],"")
    def test_reject_unknown_type(self):
        r={"record_type":"READY"}
        with self.assertRaises(ValueError):packet([r])
if __name__=="__main__":unittest.main()
