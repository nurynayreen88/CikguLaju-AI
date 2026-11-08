"""DSKP 2017 original Science Y3 SP 5.1.1/5.1.3 plant pedagogy fixes.

Exact curriculum sources: owner Drive KPM DSKP Sains Tahun 3, printed p59-60.
One RPH still corresponds to one original PdP. Academic release remains HOLD.
"""
from __future__ import annotations
import unittest
from web.sains_y3_rph_activity_preview_20261106 import BANK,adapt_rows,source_ledgers

SIX=("spora","biji benih","keratan batang","daun","anak pokok","batang bawah tanah")


class Y3SourceGroundedReproductionQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger,_=source_ledgers()

    @classmethod
    def row_for(cls,sp):
        record=next(row for row in cls.ledger.values() if row["sp_code"]==sp)
        state={"subject":"Sains","year":"Tahun 3","year_label":"Tahun 3",
               "pdp_sequence_code":record["pdp_code"],
               "sk_code":"5.1","sp_code":sp}
        original={"STATUS":"DRAF","REFLEKSI":"Belum dilaksanakan"}
        revised=adapt_rows(state,original)
        return record,state,original,revised

    def test_six_original_dskp_modes_and_individual_evidence(self):
        self.assertEqual(len(BANK),45)
        self.assertEqual(len(BANK["5.1.1"]),7)
        row,state,original,revised=self.row_for("5.1.1")
        self.assertEqual(revised["STANDARD PEMBELAJARAN"],"5.1.1")
        self.assertEqual(revised["STATUS"],"DRAF")
        self.assertEqual(revised["REFLEKSI"],"Belum dilaksanakan")
        self.assertEqual(original,{"STATUS":"DRAF","REFLEKSI":"Belum dilaksanakan"})
        combined=" ".join(BANK["5.1.1"]).lower()
        for mode in SIX:
            with self.subTest(mode=mode):
                self.assertIn(mode,combined)
        self.assertIn("enam cara",revised["AKTIVITI UTAMA"].lower())
        self.assertIn("enam cara",revised["PENTAKSIRAN"].lower())
        self.assertNotIn("lima cara",combined)
        self.assertNotIn("Lima cara pembiakan",revised["PENTAKSIRAN"])

    def test_one_kangkung_species_two_reproduction_methods_with_real_followup(self):
        row,state,original,revised=self.row_for("5.1.3")
        self.assertEqual(revised["STANDARD PEMBELAJARAN"],"5.1.3")
        self.assertEqual(revised["STATUS"],"DRAF")
        content=" ".join(BANK["5.1.3"]).lower()
        self.assertNotIn("ubi keledek",content)
        self.assertGreaterEqual(content.count("kangkung"),5)
        self.assertIn("biji benih kangkung",content)
        self.assertIn("keratan batang kangkung",content)
        self.assertIn("dua pasu",content)
        self.assertIn("tarikh",content)
        self.assertIn("selepas data diperoleh",content)
        self.assertIn("bukan keputusan direka",content)
        self.assertIn("rekod pemerhatian individu",revised["PENTAKSIRAN"].lower())
        self.assertIn("kangkung",revised["AKTIVITI UTAMA"].lower())

    def test_other_source_identity_and_hold_not_touched(self):
        self.assertEqual(len(self.ledger),45)
        self.assertEqual(len(BANK),45)
        for sp in ("5.1.1","5.1.3"):
            row,state,original,revised=self.row_for(sp)
            self.assertTrue(row["pdp_code"].startswith("SCI-Y3-PDP-"))
            self.assertEqual(revised["STANDARD PEMBELAJARAN"],sp)
            self.assertIn("isi/PBD belum disahkan panitia",
                          revised["BAHAN BANTU MENGAJAR"])
            self.assertEqual(revised["STATUS"],"DRAF")
            self.assertIn("Aktiviti 1",revised["AKTIVITI UTAMA"])
            self.assertIn("Aktiviti 2",revised["AKTIVITI UTAMA"])


if __name__=="__main__":
    unittest.main()
