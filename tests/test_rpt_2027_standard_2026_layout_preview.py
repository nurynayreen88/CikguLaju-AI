"""2026-layout RPT 2027 source fidelity and PDF structure (STAGING only)."""
import re
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader
from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows, normalize_pdf_text
from scripts.build_rpt_2027_standard_preview import (
    build_all, moral_records, psv_records, rbt_records
)


class RPT2026LayoutQA(unittest.TestCase):
    def test_no_fake_dates_or_missing_sk_sp(self):
        self.assertEqual(len(psv_records(2)),42)
        for year in range(2, 7):
            rows = psv_records(year)
            self.assertEqual(len(rows), 42)
            self.assertTrue(all(row["sk_display"].startswith(row["sk"].split(";")[0].strip() + " — ") for row in rows))
            self.assertTrue(all(row["sp_display"].startswith(row["sp"].split(";")[0].strip() + " — ") for row in rows))
            self.assertTrue(all(len(row["sk_display"]) > len(row["sk"]) + 6
                                and len(row["sp_display"]) > len(row["sp"]) + 12
                                for row in rows))
        self.assertEqual(len(rbt_records(4)),32)
        for year in (4, 5, 6):
            rows = rbt_records(year)
            self.assertEqual(len(rows), 32)
            self.assertTrue(all(row["sk_display"].startswith(row["sk"].split("/")[0].strip() + " — ") for row in rows))
            self.assertTrue(all(row["sp_display"].startswith(row["sp"].split("/")[0].strip() + " — ") for row in rows))
            self.assertTrue(all(len(row["sk_display"]) > len(row["sk"]) + 5
                                and len(row["sp_display"]) > len(row["sp"]) + 8 for row in rows))
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
        for year in range(2, 7):
            rows = moral_records(year)
            self.assertEqual(len(rows), 96)
            self.assertTrue(all(r["sk_display"].startswith(r["sk"] + " — ") for r in rows))
            self.assertTrue(all(" — " in r["sp_display"] for r in rows))
            self.assertTrue(all(len(r["sp_display"]) > len(r["sp"]) + 5 for r in rows))
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
                    self.assertIn("LOGO SEKOLAH",cover)
                    self.assertIn("NAMA SEKOLAH",cover)
                    self.assertIn("NAMA GURU",cover)
                    self.assertIn("2027",cover)
                    for unwanted in ("ALAMAT SEKOLAH", "KELAS", "NEGERI / KUMPULAN",
                                     "KUMPULAN A", "KUMPULAN B", "RUJUKAN",
                                     "Sumber:", "DRAF", "Halaman 1", "CIKGULAJU"):
                        self.assertNotIn(unwanted,cover)
                    self.assertNotIn("LOGO SEKOLAH",body)
                    for head in ("MINGGU / TARIKH","SK",
                                 "SP","CATATAN / BAHAN"):
                        self.assertIn(head,body)
                    numbers=[int(v) for v in re.findall(r"(?m)^\s*PdP\s+(\d{3})\s*$",body)]
                    self.assertEqual(numbers,list(range(1,count+1)),
                                     f"{subject} {year} missing/mixed PdP")
                    if subject=="rbt":
                        # Missing timetable remains missing in source; no internal
                        # planning placeholder should be printed for teachers.
                        self.assertNotIn("Belum ditentukan",body)
                    if subject=="moral":
                        self.assertNotIn("RPH_TERSEDIA_BETA80",body)
                        self.assertNotIn("RPH_PENGUKUHAN_DRAF_SUMBER_TOC",body)
                    self.assertNotIn(".. Buku teks:",body)
                    self.assertNotIn(".. Tarikh",body)
            self.assertEqual(counts,{"psv":5,"rbt":3,"moral":5})

    def test_dskp_private_use_bullets_do_not_render_as_blank_glyphs(self):
        self.assertEqual(normalize_pdf_text("A\uf0b7 B"), "A •  B")
        self.assertEqual(normalize_pdf_text("A\uf02d B"), "A -  B")
        self.assertEqual(normalize_pdf_text("Line 1" + chr(10) + "Line 2"), "Line 1" + chr(10) + "Line 2")
        with self.assertRaises(ValueError):
            normalize_pdf_text("Unknown \ue000 character")
        with self.assertRaises(ValueError):
            normalize_pdf_text("Invalid " + chr(0) + " character")

    def test_school_cover_fields_and_optional_logo_image(self):
        from PIL import Image as PILImage
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            logo = folder / "school.png"
            PILImage.new("RGB", (160, 96), (23, 78, 92)).save(logo)
            output = folder / "personalized.pdf"
            build_preview("psv", 2, psv_records(2), output,
                          logo_path=logo, school_name="SEKOLAH CONTOH",
                          teacher_name="GURU CONTOH")
            reader = PdfReader(str(output))
            cover = reader.pages[0].extract_text()
            self.assertIn("SEKOLAH CONTOH", cover)
            self.assertIn("GURU CONTOH", cover)
            self.assertNotIn("LOGO SEKOLAH", cover)
            self.assertGreaterEqual(len(reader.pages[0].images), 1)
            self.assertNotIn("KUMPULAN A", cover)
            self.assertIn("KUMPULAN A", reader.pages[1].extract_text())

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                build_preview("psv", 2, psv_records(2), Path(tmp) / "bad.pdf",
                              logo_path=Path(tmp) / "not-found.png")

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
