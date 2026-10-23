import unittest
from scripts.pjpk_source_priority_v2686 import plan
from scripts.pjpk_source_review_packet_v2683 import packet
class PriorityTests(unittest.TestCase):
    def test_all_scopes_and_lossless_priority(self):
        base={"year":"Tahun 1","subject":"Pendidikan Jasmani","topic":"Unit","rpt_text":"",
            "direct_dskp_text":"","source_document":"","action":"REVIEW"}
        a=dict(base,entry_id=1,record_type="SP_SOURCE_REVIEW",standard_code="1.1.1",evidence_status="CONFLICT_REVIEW")
        b=dict(base,entry_id=2,record_type="MISSING_SK_LINK",standard_code="",evidence_status="MISSING_SK_LINK")
        x=plan(packet([a,b]))
        self.assertEqual((x["scope_count"],x["review_rows"]),(12,2))
        self.assertEqual(x["scopes"][0]["work"][0]["entry_id"],"1")
        self.assertFalse(x["production_promoted"])
    def test_unknown_type_rejected(self):
        with self.assertRaises(ValueError):plan([{"year_label":"Tahun 1","subject":"Pendidikan Jasmani",
          "record_type":"READY","review_status":"PENDING_SOURCE_REVIEW","entry_id":"1"}])
if __name__=="__main__":unittest.main()
