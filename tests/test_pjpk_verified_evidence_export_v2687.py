import copy
import unittest
from scripts.pjpk_source_review_packet_v2683 import packet
from scripts.pjpk_verified_evidence_export_v2687 import export
class ExportTests(unittest.TestCase):
    def setUp(self):
        self.original=packet([{"year":"Tahun 1","subject":"Pendidikan Jasmani","entry_id":1,
            "topic":"A","record_type":"SP_SOURCE_REVIEW","standard_code":"1.1.1",
            "rpt_text":"Existing","evidence_status":"NO_DIRECT_DSKP_TEXT",
            "direct_dskp_text":"","source_document":"","action":"TRANSCRIBE"}])
    def test_pending_exports_nothing(self):
        self.assertEqual(export(self.original,copy.deepcopy(self.original)),[])
    def test_verified_exports_exact_scope(self):
        reviewed=copy.deepcopy(self.original)
        reviewed[0].update(review_status="SOURCE_VERIFIED",reviewed_dskp_code="1.1.1",
            reviewed_dskp_text="Exact wording",source_document="DSKP",
            source_page="26",reviewer="Reviewer")
        rows=export(self.original,reviewed)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["reviewed_dskp_code"],"1.1.1")
    def test_conflicting_exact_scope_wording_rejected(self):
        original=copy.deepcopy(self.original)
        second=copy.deepcopy(original[0])
        second["entry_id"]="2"
        original.append(second)
        reviewed=copy.deepcopy(original)
        for row in reviewed:
            row.update(review_status="SOURCE_VERIFIED",reviewed_dskp_code="1.1.1",
                reviewed_dskp_text="Exact wording",source_document="DSKP",
                source_page="26",reviewer="Reviewer")
        reviewed[1]["reviewed_dskp_text"]="Conflicting wording"
        with self.assertRaisesRegex(ValueError,"Contradictory"):
            export(original,reviewed)
    def test_missing_source_rejected(self):
        reviewed=copy.deepcopy(self.original)
        reviewed[0]["review_status"]="SOURCE_VERIFIED"
        with self.assertRaises(ValueError):export(self.original,reviewed)
if __name__=="__main__":unittest.main()
