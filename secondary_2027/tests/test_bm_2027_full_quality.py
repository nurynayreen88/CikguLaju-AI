"""Offline QA for BM KSSM secondary source-backed staging. No production imports."""
import json
import re
import unittest
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parents[1] / "data"
PACKS = [
    ("bm_t2_rpt_full_177_draft.json", 2, 177, None),
    ("bm_t3_rpt_full_079_draft.json", 3, 79, None),
    ("bm_t4_dskp_54sp_108rph_draft.json", 4, 108, 54),
    ("bm_t5_dskp_48sp_96rph_draft.json", 5, 96, 48),
]
FIELDS = ("objektif","set_induksi","aktiviti_1","aktiviti_2",
          "pengukuhan_penilaian","penutup","pemulihan","pengayaan","bahan","bukti_pbd")

class BMFullStagingTests(unittest.TestCase):
    def test_all_records(self):
        for filename, form, expected, n_standards in PACKS:
            doc = json.loads((BASE/filename).read_text(encoding="utf-8"))
            with self.subTest(file=filename):
                self.assertEqual(doc["tingkatan"],form)
                self.assertEqual(doc["kurikulum"],"KSSM")
                self.assertEqual(doc["rph_count"],expected)
                self.assertFalse(doc["usable_in_runtime"])
                self.assertEqual(len(doc["lessons"]),expected)
                ids, keys = set(), set()
                codes=Counter()
                for i, rec in enumerate(doc["lessons"],1):
                    self.assertEqual(rec["pdp"],i)
                    self.assertEqual(rec["tingkatan"],form)
                    self.assertNotEqual(rec["status"],"READY")
                    self.assertEqual(rec["sk"],".".join(rec["sp"].split(".")[:2]))
                    self.assertTrue(re.fullmatch(r"[1-5]\.\d{1,2}\.\d{1,2}",rec["sp"]))
                    self.assertNotIn(rec["lesson_id"],ids)
                    ids.add(rec["lesson_id"])
                    for field in FIELDS:
                        self.assertIsInstance(rec[field],str)
                        self.assertGreaterEqual(len(rec[field].strip()),40,(filename,i,field))
                    self.assertEqual(rec["langkah"],["Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan/Penilaian","Penutup"])
                    self.assertGreaterEqual(len(rec["aktiviti_1"]),100)
                    self.assertGreaterEqual(len(rec["aktiviti_2"]),100)
                    codes[rec["sp"]]+=1
                    if form in (4,5):
                        self.assertIsNone(rec["halaman_buku_teks"])
                        self.assertIsNone(rec["unit"])
                    else:
                        key=(rec["tajuk"],rec["halaman_rpt"],rec["sp"])
                        self.assertNotIn(key,keys)
                        keys.add(key)
                if n_standards is not None:
                    self.assertEqual(len(codes),n_standards)
                    self.assertTrue(all(n==2 for n in codes.values()))
    def test_distinct_files_and_release_gates(self):
        manifest=json.loads((BASE/"bm_full_460_master_manifest_20261107.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["for_runtime"])
        self.assertEqual(sum(p["rph_count"] for p in manifest["packs"]),460)
        self.assertEqual(len(manifest["packs"]),4)
        self.assertTrue(manifest["requires_manual_approval"])
        self.assertEqual({p["tingkatan"] for p in manifest["packs"]},{2,3,4,5})

if __name__ == "__main__":
    unittest.main()
