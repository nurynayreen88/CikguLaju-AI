"""Fail-closed tests for PJPK reviewed evidence import."""
import copy
import unittest
from scripts.pjpk_source_review_packet_v2683 import packet
from scripts.validate_pjpk_source_review_v2684 import validate
class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.original=packet([{"year":"Tahun 1","subject":"Pendidikan Jasmani","entry_id":1,
          "topic":"Unit A","record_type":"SP_SOURCE_REVIEW","standard_code":"1.1.1",
          "rpt_text":"Existing wording","evidence_status":"NO_DIRECT_DSKP_TEXT",
          "direct_dskp_text":"","source_document":"","action":"TRANSCRIBE"},
          {"year":"Tahun 1","subject":"Pendidikan Jasmani","entry_id":1,
          "topic":"Unit A","record_type":"MISSING_SK_LINK","standard_code":"",
          "rpt_text":"","evidence_status":"MISSING_SK_LINK",
          "direct_dskp_text":"","source_document":"","action":"LOCATE"}])
    def test_pending_not_promoted(self):
        x=validate(self.original,copy.deepcopy(self.original))
        self.assertEqual((x["still_blocked"],x["source_verified_for_further_audit"]),(2,0))
        self.assertFalse(x["production_promoted"])
    def test_verified_requires_evidence(self):
        rows=copy.deepcopy(self.original)
        rows[0]["review_status"]="SOURCE_VERIFIED"
        with self.assertRaises(ValueError):validate(self.original,rows)
        rows[0].update(source_document="DSKP",source_page="26",reviewer="Reviewer",
                       reviewed_dskp_code="1.1.1",reviewed_dskp_text="Exact source text")
        x=validate(self.original,rows)
        self.assertEqual((x["source_verified_for_further_audit"],x["still_blocked"]),(1,1))
    def test_reject_source_mutation_and_identity_changes(self):
        rows=copy.deepcopy(self.original);rows[0]["rpt_sp_text"]="fabricated"
        with self.assertRaises(ValueError):validate(self.original,rows)
        rows=copy.deepcopy(self.original);rows[0]["sp_code"]="9.9.9"
        with self.assertRaises(ValueError):validate(self.original,rows)
        with self.assertRaises(ValueError):validate(self.original,self.original[:1])
    def test_sk_needs_full_code_and_wording(self):
        rows=copy.deepcopy(self.original)
        rows[1].update(review_status="SOURCE_VERIFIED",source_document="DSKP",
                       source_page="27",reviewer="Reviewer",reviewed_sk_code="1.1")
        with self.assertRaises(ValueError):validate(self.original,rows)
if __name__=="__main__":unittest.main()
