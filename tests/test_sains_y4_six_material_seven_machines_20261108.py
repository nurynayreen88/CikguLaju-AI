"""Exact KPM Year4 DSKP 2018 SP8.2.1 and SP10.2.1 quality regression.

Official owner Drive DSKP PDF (original KPM): 1eXDdb_qSfCKyqoVtl9T4q2I4rKyHtk9D
No certifying of textbook SP pages or teacher approval; authoring drafts HOLD.
"""
from __future__ import annotations
import unittest

from web.sains_y4_79_activity_bank_draf_20261107 import BANK
from tools.render_sains_y4_79_rph_draf_20261107 import get_y4_records
from web.sains_rph_quality_release_gate_20261108 import approved_count

SIX_PROPERTIES=(
    "menyerap air", "terapung", "mengalirkan arus elektrik",
    "penembusan cahaya", "mengalirkan haba", "kekenyalan",
)
SEVEN_MACHINES=(
    "tuas", "gear", "takal", "baji", "skru",
    "satah condong", "roda dan gandar",
)


class SourceSpecificYear4Correction(unittest.TestCase):
    def test_exact_six_kpm_material_properties_and_safe_evidence(self):
        self.assertEqual(len(BANK),79)
        row=BANK["8.2.1"]
        source=" ".join(row.values()).casefold()
        for concept in SIX_PROPERTIES:
            with self.subTest(property=concept):
                self.assertIn(concept,source)
        self.assertIn("enam aspek",row["teacher1"])
        self.assertIn("keenam-enam",row["pupil2"])
        self.assertIn("enam sifat",row["pbd"])
        self.assertIn("sumber bukti",row["pbd"])
        self.assertIn("tidak",row["safety"].casefold())
        self.assertIn("soket rumah",row["safety"])
        self.assertIn("litar pintas",row["safety"])
        self.assertIn("air panas",row["safety"])
        self.assertIn("kit sel kering",row["teacher2"])
        self.assertNotIn("Jadual tiga sifat bahan",row["pbd"])

    def test_exact_seven_kpm_simple_machine_classes_and_examples(self):
        row=BANK["10.2.1"]
        source=" ".join(row.values()).casefold()
        for machine in SEVEN_MACHINES:
            with self.subTest(machine=machine):
                self.assertIn(machine,source)
        self.assertIn("tujuh",row["pupil1"])
        self.assertIn("tujuh jenis",row["pbd"])
        self.assertIn("pengadang pintu baji",row["pupil1"])
        self.assertIn("penutup botol berulir",row["pupil1"])
        self.assertIn("bukan mata pisau",row["safety"])
        self.assertNotIn("Jadual lima mesin ringkas",row["pbd"])

    def test_original_79_identities_preserved_and_all_source_hold(self):
        rows=get_y4_records()
        self.assertEqual(len(rows),79)
        self.assertEqual(len({r["pdp_code"] for r in rows}),79)
        self.assertEqual({r["sp"] for r in rows},set(BANK))
        for r in rows:
            self.assertEqual(r["status"],"DRAF_HOLD")
            self.assertIsNone(r["textbook_pages"])
            self.assertIsNone(r["curriculum_quality_percent"])
        self.assertEqual(approved_count(),0)


if __name__=="__main__":
    unittest.main()
