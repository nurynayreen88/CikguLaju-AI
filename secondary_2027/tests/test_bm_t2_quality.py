import json
from pathlib import Path
import unittest

DATA = json.loads((Path(__file__).resolve().parents[1] / "data" / "bm_t2_pdp_001_005.json").read_text(encoding="utf-8"))

class BMSecondaryPilotQA(unittest.TestCase):
    def test_scope_and_gate(self):
        self.assertEqual(DATA["kurikulum"], "KSSM")
        self.assertEqual(DATA["tingkatan"], 2)
        self.assertEqual(DATA["release_status"], "DRAF_SEMAK_BUKU_TEKS")
    def test_sequence_unique(self):
        ids = [r["pdp"] for r in DATA["lessons"]]
        self.assertEqual(ids, list(range(1, len(ids) + 1)))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(DATA["lesson_count"], len(ids))
    def test_full_rph(self):
        fields = ("tajuk","kemahiran","sk","sp","sk_teks","sp_teks","objektif","set_induksi","aktiviti_1","aktiviti_2","pengukuhan_penilaian","penutup","pemulihan","pengayaan","bahan","bukti_pbd")
        for r in DATA["lessons"]:
            with self.subTest(pdp=r["pdp"]):
                self.assertTrue(all(isinstance(r.get(k),str) and len(r[k].strip())>0 for k in fields))
                self.assertGreater(r["halaman"],0)
                self.assertGreaterEqual(len(r["objektif"]), 40)
                self.assertGreaterEqual(len(r["aktiviti_1"]), 100)
                self.assertGreaterEqual(len(r["aktiviti_2"]), 100)
                self.assertTrue(r["sp"].startswith(r["sk"]+"."))
                self.assertEqual(r["rph_status"], DATA["release_status"])
                self.assertEqual(r["langkah"], ["Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan/Penilaian","Penutup"])

if __name__ == "__main__":
    unittest.main()
