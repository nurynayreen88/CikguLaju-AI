"""2026-layout RPT 2027 source fidelity and PDF structure (STAGING only)."""
import re
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader
from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows
from scripts.build_rpt_2027_standard_preview import (
    build_all, moral_records, psv_records, rbt_records
)


class RPT2026LayoutQA(unittest.TestCase):
    def test_no_fake_dates_or_missing_sk_sp(self):
        self.assertEqual(len(psv_records(2)),42)
        self.assertEqual(len(rbt_records(4)),32)
        self.assertEqual(len(moral_records(3)),96)
        for subject,year,loader in (
            ("psv",2,psv_records),("rbt",4,rbt_records),("moral",3,moral_records)
        ):
            with self.subTest(subject=subject):
                rows=loader(year)
                self.assertTrue(validate_rows(subject,year,rows))
                self.assertTrue(all(r["sk"] and r["sp"] for r in rows))
                self.assertEqual([r["id"] for r in rows],
                                 [f"{i:03d}" for i in range(1,len(rows)+1)])
        self.assertTrue(all(not r["a_start"] and not r["b_start"] and not r["week"]
                            for r in rbt_records(4)))

    def test_no_guessed_or_duplicate_curriculum(self):
        records=psv_records(4)
        with self.assertRaises(ValueError):
            validate_rows("psv",4,[records[0],records[0]])
        with self.assertRaises(ValueError):
            validate_rows("psv",4,[dict(records[0],sp="")])
        with self.assertRaises(ValueError):
            validate_rows("psv",4,[dict(records[0],a_start="2027-99-99")])
        with self.assertRaises(ValueError):
            validate_rows("rbt",3,rbt_records(4))

    def test_all_13_staging_pdfs_have_five_column_layout_and_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            built=build_all(tmp)
            self.assertEqual(len(built),13)
            counts={"psv":0,"moral":0,"rbt":0}
            for subject,year,count,path in built:
                with self.subTest(subject=subject,year=year):
                    counts[subject]+=1
                    self.assertEqual(count,{"psv":42,"moral":96,"rbt":32}[subject])
                    self.assertGreater(path.stat().st_size,8000)
                    pdf=PdfReader(str(path))
                    self.assertGreaterEqual(len(pdf.pages),2)
                    for page in pdf.pages:
                        self.assertGreater(float(page.mediabox.width),float(page.mediabox.height))
                        self.assertAlmostEqual(float(page.mediabox.width),841.89,delta=2)
                    cover=pdf.pages[0].extract_text()
                    body="\n".join(p.extract_text() for p in pdf.pages[1:])
                    self.assertIn("RANCANGAN PENGAJARAN TAHUNAN",cover)
                    self.assertIn("NAMA SEKOLAH",cover)
                    self.assertIn("NAMA GURU",cover)
                    self.assertIn("KUMPULAN A",cover)
                    for head in ("MINGGU / TARIKH","STANDARD KANDUNGAN",
                                 "STANDARD PEMBELAJARAN","CATATAN / BAHAN"):
                        self.assertIn(head,body)
                    numbers=[int(v) for v in re.findall(r"PdP\s+(\d{3})",body)]
                    self.assertEqual(numbers,list(range(1,count+1)),
                                     f"{subject} {year} missing/mixed PdP")
                    if subject=="rbt":
                        self.assertIn("Belum ditentukan",body)
            self.assertEqual(counts,{"psv":5,"rbt":3,"moral":5})

    def test_preview_not_exposed_as_new_live_rpt(self):
        root=Path(__file__).resolve().parents[1]
        names=("rpt_2027/common/format_2026_layout_preview.py",
               "scripts/build_rpt_2027_standard_preview.py")
        for server in ("rpt_2027/english/telegram_downloads.py",
                       "tools/run_telegram_with_curriculum_api.py"):
            text=(root/server).read_text("utf-8")
            self.assertTrue(all(n not in text for n in names))
        self.assertTrue(all("preview" in path for path in names))


if __name__=="__main__":
    unittest.main()
