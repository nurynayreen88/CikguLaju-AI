"""Regression gates on newly prepared source PDFs, all Arabic KSSR RPT years 2–6."""
from __future__ import annotations
import json
import unittest
from pathlib import Path
import fitz
from scripts.repair_rpt2027_arabic_grid_20261123 import (
    ROOT, YEARS, cells, check_final, digest, links_snapshot
)


class ArabicRPTGridTest(unittest.TestCase):
    def test_five_years_keep_draft_pdf_hashes_and_vertical_cell_dividers(self):
        manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
        cover=json.loads((ROOT/"original_cover_layout_verified.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["count"],56)
        self.assertFalse(manifest["academic_final_approved"])
        self.assertEqual(manifest["status"],"DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL")
        self.assertEqual(set(cover["source_sha256_by_subject_year"]),
                         set(manifest["files"]))
        total_links=0
        for year in YEARS:
            with self.subTest(year=year):
                key=f"bahasa_arab:{year}"
                info=manifest["files"][key]
                file=ROOT/info["path"]
                data=file.read_bytes()
                self.assertEqual(digest(data),info["sha256"])
                self.assertEqual(len(data),info["bytes"])
                self.assertEqual(cover["source_sha256_by_subject_year"][key],info["sha256"])
                with fitz.open(stream=data,filetype="pdf") as pdf:
                    self.assertEqual(len(pdf),info["pages"])
                    self.assertGreater(check_final(pdf),40)
                    self.assertIn("NAMA SEKOLAH",pdf[0].get_text())
                    self.assertIn("LOGO SEKOLAH",pdf[0].get_text())
                    links=sum(map(len,links_snapshot(pdf)))
                    self.assertEqual(links,{2:60,3:60,4:58,5:60,6:60}[year])
                    total_links+=links
                    for page in list(pdf)[1:]:
                        rows,expected,existing=cells(page)
                        self.assertEqual(existing,len(expected))
                        self.assertEqual(page.rect.width>page.rect.height,True)
        self.assertEqual(total_links,298)

    def test_all_51_non_arabic_assets_have_unchanged_manifest_scope(self):
        manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]),56)
        for key,entry in manifest["files"].items():
            if key.startswith("bahasa_arab:"):
                continue
            self.assertEqual(digest((ROOT/entry["path"]).read_bytes()),entry["sha256"])


if __name__=="__main__":
    unittest.main()
