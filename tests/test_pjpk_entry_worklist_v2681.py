"""Tests for entry-grouped, read-only PJPK source remediation worklist."""
import unittest
from scripts.pjpk_entry_worklist_v2681 import group_entries

def row(kind, entry=1, year="Tahun 1", subject="Pendidikan Jasmani"):
    return {"record_type":kind,"entry_id":entry,"year":year,"subject":subject,
            "topic":"Unit A","standard_code":"1.1.1","rpt_text":"Source review",
            "evidence_status":"NO_DIRECT_DSKP_TEXT","source_document":"",
            "direct_dskp_text":"","action":"REVIEW"}

class WorklistTests(unittest.TestCase):
    def test_all_scopes_and_unique_entry_not_row_count(self):
        q=[row("SP_SOURCE_REVIEW"),row("SP_SOURCE_REVIEW"),
           row("MISSING_SK_LINK"),row("MISSING_SK_LINK",2, "Tahun 6","Pendidikan Kesihatan")]
        result=group_entries(q)
        self.assertEqual((result["scope_count"],result["review_rows"],result["unique_entries"]),(12,4,2))
        self.assertEqual(result["scopes"][0]["entries"][0]["missing_sk_link"],True)
        self.assertEqual(len(result["scopes"][0]["entries"][0]["sp_reviews"]),2)
        self.assertFalse(result["production_promoted"])
    def test_fail_closed(self):
        for bad in [row("READY"),row("SP_SOURCE_REVIEW",year="Tahun 7"),
                    row("SP_SOURCE_REVIEW",subject="Pendidikan Moral")]:
            with self.subTest(bad=bad),self.assertRaises(ValueError): group_entries([bad])
        with self.assertRaises(ValueError):
            group_entries([row("MISSING_SK_LINK"),row("MISSING_SK_LINK")])
        bad=row("SP_SOURCE_REVIEW");bad["topic"]="Different"
        with self.assertRaises(ValueError):
            group_entries([row("SP_SOURCE_REVIEW"),bad])

if __name__=="__main__":
    unittest.main()
