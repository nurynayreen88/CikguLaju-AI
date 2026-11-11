import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data"

class TestSecondaryLargeBatch(unittest.TestCase):
    def test_batch_integrity(self):
        for form, count in [(2,120),(3,60)]:
            name=f"bm_t{form}_pdp_001_{count:03d}_staging.json"
            d=json.loads((BASE/name).read_text(encoding="utf-8"))
            self.assertEqual(d["rph_count"],count)
            self.assertEqual(d["kurikulum"],"KSSM")
            self.assertEqual(d["release_status"],"DRAF_SEMAK_INDIVIDU_BUKU_TEKS")
            self.assertEqual([x["pdp"] for x in d["lessons"]],list(range(1,count+1)))
            for x in d["lessons"]:
                self.assertEqual(x["status"],d["release_status"])
                self.assertGreater(len(x["aktiviti_1"]),100)
                self.assertGreater(len(x["aktiviti_2"]),100)
                self.assertEqual(x["sk"],".".join(x["sp"].split(".")[:2]))
                self.assertTrue(x["bukti_pbd"])
    def test_source_precedence(self):
        d=json.loads((BASE/"big_batch_20261106_manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(d["for_runtime"])
        self.assertEqual(sum(s["rph_count"] for s in d["series"]),180)

if __name__=="__main__":
    unittest.main()
