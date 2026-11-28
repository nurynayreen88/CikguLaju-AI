"""Sains Year6 original 2021 code check: no false release."""
import unittest
from scripts.audit_sains_y6_original_2021_sp_membership_staging import reconcile
class SainsYear6Original2021CodeQA(unittest.TestCase):
    def test_code_overlap_is_not_release_signoff(self):
        original={"codes":{"2.2.1":[59],"2.2.2":[59],"2.2.6":[60]},"unique_sp_count":3}
        rows=[]
        for i in range(84):
            sp=["2.2.1","2.2.2","3.2.1"][i%3]
            rows.append({"sp":sp,"curriculum_text_matched":False,
                         "display_id":f"SCI-Y6-PDP-{i+1:03d}","topic":"Sistem Saraf"})
        result=reconcile(original,rows)
        self.assertEqual(result["historical_pdp_count"],84)
        self.assertEqual(len(result["historical_pdp_with_missing_official_sp_code"]),28)
        self.assertEqual(result["pdp_sp_statements_visual_signoff"],0)
        self.assertFalse(result["full_rpt_ready"])
    def test_fails_closed_on_false_verified_status(self):
        original={"codes":{"2.2.1":[59]},"unique_sp_count":1}
        records=[{"sp":"2.2.1","curriculum_text_matched":False,
                  "display_id":f"PDP-{i}","topic":"Title"} for i in range(84)]
        records[10]["curriculum_text_matched"]=True
        with self.assertRaises(ValueError):
            reconcile(original,records)
if __name__=="__main__":
    unittest.main()
