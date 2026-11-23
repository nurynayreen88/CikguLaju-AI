"""English RPT Word QA cannot be mistaken for a new public paid download.

The GitHub repository itself is public, so keep all new editable English RPT
files outside its tree until private storage + authenticated SHA-checked delivery
are operational. These tests do not assert that existing public BM Word is secret.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"audits/rpt_english_word_y2_y6_private_qa_20261123.json"

class EnglishRPTWordPrivateGate(unittest.TestCase):
    def test_all_five_years_and_800_lessons_remain_qa_only(self):
        a=json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(a["scope"]["years"],[2,3,4,5,6])
        self.assertEqual(a["scope"]["total_lessons"],800)
        self.assertEqual(a["scope"]["lesson_each_year"],160)
        self.assertEqual(a["corrections"]["Y2-Y6"]["date_cells"],800)
        self.assertEqual(a["corrections"]["Y3"]["main_and_complementary_cs_ls_descriptions"],160)
        self.assertTrue(a["corrections"]["Y3"]["no_inferred_standards"])
        self.assertEqual(a["corrections"]["teacher_choice_topics"]["count"],10)
        self.assertEqual(sum(a["corrections"]["teacher_choice_topics"]["by_year"].values()),10)
        self.assertFalse(a["academic_final"])
        self.assertEqual(a["status"],"QA_HOLD_NOT_READY_NOT_WEB_PUBLISHED")

    def test_private_storage_and_web_eligible_flags_are_not_fabricated(self):
        a=json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertTrue(a["storage"]["private_supabase_bucket_exists"])
        self.assertFalse(a["storage"]["english_rpt_private_objects_uploaded"])
        self.assertIn("DO NOT ENABLE",a["storage"]["user_download"])
        self.assertIn("PUBLIC",a["storage"]["public_repository_risk"])
        self.assertTrue(a["quality_checks"]["year3_word_40_week_tables"])
        self.assertEqual(a["quality_checks"]["year3_word_render_pages"],40)
        self.assertTrue(a["quality_checks"]["year3_pages_landscape"])
        self.assertTrue(all(len(v)==64 for k,v in a["quality_checks"].items() if k.endswith("sha256")))

    def test_no_new_premium_english_word_binary_exposed_on_public_github(self):
        dirs=[ROOT/"rpt_2027/english",ROOT/"rpt_2027/kssr_word_premium/english"]
        binaries=[str(p.relative_to(ROOT)) for d in dirs if d.exists() for p in d.rglob("*.docx")]
        self.assertEqual(binaries,[],f"Do not push premium Word to public GitHub: {binaries}")
        server=(ROOT/"web/rpt_2027_all_http.py").read_text(encoding="utf-8")
        self.assertIn('if subject!="bahasa_melayu" or year not in bm_word.YEARS:',server)

if __name__=="__main__":
    unittest.main()
