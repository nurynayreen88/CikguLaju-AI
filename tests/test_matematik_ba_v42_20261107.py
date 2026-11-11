"""Staging v42 gate: 234 topic-linked BA RPH candidates; no fake release approval."""
import csv
from collections import Counter
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1] / "audits"

def read(name):
    with (BASE / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

class V42StagingCandidates(unittest.TestCase):
    def test_all_234_lessons_are_mapped_once(self):
        data = read("matematik_ba_v42_234_candidate_manifest_20261107.csv")
        self.assertEqual(len(data), 234)
        self.assertEqual(Counter(x["year"] for x in data), {"2":117,"3":117})
        self.assertEqual({x["lesson_id"] for x in data},
            {f"T{y}-L{n:03d}" for y in (2,3) for n in range(1,118)})

    def test_page_ranges_exist_in_scanned_contents_index(self):
        refs = read("matematik_ba_t2_t3_visual_toc_20261107.csv")
        supported = {(x["year"],x["toc_topic"],x["printed_page_start"],x["printed_page_end"]) for x in refs}
        for x in read("matematik_ba_v42_234_candidate_manifest_20261107.csv"):
            with self.subTest(lesson=x["lesson_id"]):
                pages = x["ba_printed_pages"].replace("–","-").split("-")
                self.assertIn((x["year"],x["ba_toc_topic"],pages[0],pages[-1]),supported)
                self.assertEqual(x["topic_page_toc_checked"],"YES")
                self.assertEqual(x["academic_semantic_approved"],"NO")
                self.assertEqual(x["release_state"],"DRAF_DO_NOT_DEPLOY")
                self.assertEqual(x["v41_actual_word_pdf_generated"],"YES_STAGING_ONLY")

if __name__=="__main__":
    unittest.main()
