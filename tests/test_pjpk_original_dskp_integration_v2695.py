import unittest
from pathlib import Path
from pjpk_dskp_evidence_v2676 import load_evidence, reconcile_sp_text

class OriginalDSKPIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=load_evidence(Path(__file__).resolve().parents[1])
    def test_original_sources_preserved_for_each_year(self):
        cases={
            "Tahun 1":("1.1.7","Melakukan pergerakan yang berbeza penggunaan daya antara ringan dengan berat."),
            "Tahun 2":("1.1.1","Melakukan pergerakan ke ruang am yang telah ditetapkan."),
            "Tahun 3":("1.1.1","Melakukan imbangan dinamik jambatan panjang (long bridge) dan kereta sorong."),
            "Tahun 4":("1.1.1","Melakukan imbangan dinamik toe-tug walk secara individu dan pergerakan lipan secara berkumpulan."),
            "Tahun 5":("1.1.1","Melakukan imbangan dinamik flip-flop dan kereta sorong berganda (double wheelbarrow)."),
            "Tahun 6":("1.1.1","Melakukan imbangan dinamik single-leg circle dan kereta sorong dua arah (two-way wheelbarrow)."),
        }
        for year,(code,wording) in cases.items():
            with self.subTest(year=year):
                rows=self.evidence[(year,"Pendidikan Jasmani",code)]
                self.assertTrue(any(r["sp_text"]==wording and r["source_file_id"] for r in rows))
    def test_no_cross_year_source_substitution(self):
        t2=self.evidence[("Tahun 2","Pendidikan Jasmani","1.1.1")]
        self.assertFalse(any("jambatan panjang" in r["sp_text"] for r in t2))
    def test_conflicts_fail_closed(self):
        evidence={("Tahun 1","Pendidikan Jasmani","1.1.1"):[
            {"sp_text":"A","source_status":"DIRECT_DSKP_TEXT_TRANSCRIBED","source_document":"2015"},
            {"sp_text":"B","source_status":"DIRECT_DSKP_TEXT_TRANSCRIBED","source_document":"2017"}]}
        result=reconcile_sp_text("Tahun 1","Pendidikan Jasmani","1.1.1","A",evidence)
        self.assertEqual(result["status"],"CONFLICT_REVIEW")
if __name__=="__main__":unittest.main()
