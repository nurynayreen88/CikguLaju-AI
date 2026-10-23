"""Tests for independent lossless PJPK batch verification."""
import copy
import unittest
from scripts.pjpk_12_scope_summary_v2680 import summarize
from scripts.pjpk_entry_worklist_v2681 import group_entries
from scripts.verify_pjpk_batch_v2682 import verify

def row(kind, entry=1):
    return {"record_type":kind,"entry_id":entry,"year":"Tahun 1",
            "subject":"Pendidikan Jasmani","topic":"Unit A",
            "standard_code":"1.1.1","rpt_text":"Text",
            "evidence_status":"NO_DIRECT_DSKP_TEXT","source_document":"",
            "direct_dskp_text":"","action":"REVIEW"}

class BatchVerificationTests(unittest.TestCase):
    def setUp(self):
        self.rows=[row("SP_SOURCE_REVIEW"),row("MISSING_SK_LINK"),row("SP_SOURCE_REVIEW",2)]
        self.queue={"items":self.rows,"queue_count":len(self.rows),"read_only":True,"production_promoted":False}
        self.summary=summarize(self.rows)
        self.worklist=group_entries(self.rows)
    def test_valid_lossless_batch(self):
        result=verify(self.queue,self.summary,self.worklist)
        self.assertEqual(result["review_rows"],3)
        self.assertEqual(result["unique_entries"],2)
        self.assertFalse(result["production_promoted"])
    def test_missing_sp_detected(self):
        worklist=copy.deepcopy(self.worklist)
        worklist["scopes"][0]["entries"][1]["sp_reviews"].clear()
        with self.assertRaises(ValueError):verify(self.queue,self.summary,worklist)
    def test_unapproved_promotion_flag_detected(self):
        summary=copy.deepcopy(self.summary)
        summary["production_promoted"]=True
        with self.assertRaises(ValueError):verify(self.queue,summary,self.worklist)
    def test_duplicate_review_detected(self):
        worklist=copy.deepcopy(self.worklist)
        worklist["scopes"][0]["entries"][0]["sp_reviews"].append(
            copy.deepcopy(worklist["scopes"][0]["entries"][0]["sp_reviews"][0]))
        with self.assertRaises(ValueError):verify(self.queue,self.summary,worklist)

if __name__=="__main__":unittest.main()
