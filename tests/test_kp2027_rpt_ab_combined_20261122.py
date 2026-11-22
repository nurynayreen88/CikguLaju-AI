"""Ensure KP2027 RPT Year 1 has exactly one combined A/B RPT per subject."""
from __future__ import annotations

import ast
from collections import defaultdict
from hashlib import sha256
import io
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from web import kp2027_year1_rpt_combined as r

ROOT=Path(__file__).resolve().parents[1]
NS={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class CombinedRPTQA(unittest.TestCase):
    def test_all_six_documents_sha_match(self):
        self.assertTrue(r.ready())
        self.assertEqual(sha256(r.BUNDLE.read_bytes()).hexdigest(),r.BUNDLE_SHA)
        self.assertEqual(len(r._approved()),6)
        self.assertEqual(sum(sum(x) for x in r.COUNTS.values()),788)
        for subject in r.SUBJECTS:
            for fmt in r.FORMATS:
                with self.subTest(subject=subject,fmt=fmt):
                    data,name,digest=r.document(subject,fmt)
                    self.assertEqual(sha256(data).hexdigest(),digest)
                    self.assertIn("_KUMPULAN_AB_GABUNGAN_2027.",name)

    def test_three_word_files_each_preserve_both_group_pdp_sequences(self):
        columns=("Minggu / tarikh","Tema / tajuk","SK / SP / rujukan",
                 "Aktiviti PdP","PBD / pentaksiran","Acara / status / sumber",
                 "Catatan / pindaan")
        for subject in r.SUBJECTS:
            with self.subTest(subject=subject):
                content,_,_=r.document(subject,"docx")
                with ZipFile(io.BytesIO(content)) as z:
                    tree=ET.fromstring(z.read("word/document.xml"))
                fulltext=" ".join(x.text or "" for x in tree.findall(".//w:t",NS))
                self.assertIn("Kumpulan A",fulltext)
                self.assertIn("Kumpulan B",fulltext)
                self.assertIn("M06",fulltext)
                self.assertIn("SEMAKAN PELAKSANAAN",fulltext)
                for col in columns:self.assertIn(col,fulltext)
                tables=tree.findall(".//w:tbl",NS)
                self.assertGreaterEqual(len(tables),2)
                pdp=defaultdict(list)
                for tr in tables[1].findall("./w:tr",NS):
                    cells=tr.findall("./w:tc",NS)
                    text=[" ".join(x.text or "" for x in cell.findall(".//w:t",NS))
                          for cell in cells]
                    if len(text)<4 or text[0] not in ("A","B"):continue
                    match=re.search(r"PdP\s+(\d{3})",text[3])
                    if match:pdp[text[0]].append(int(match.group(1)))
                self.assertEqual(pdp["A"],list(range(1,r.COUNTS[subject][0]+1)))
                self.assertEqual(pdp["B"],list(range(1,r.COUNTS[subject][1]+1)))

    def test_route_and_ui_use_one_file_without_group_selection(self):
        backend=(ROOT/"web/rpt_2027_all_http.py").read_text("utf-8")
        html=(ROOT/"web_v1_static_preview/index.html").read_text("utf-8")
        ast.parse(backend)
        self.assertIn('from web import kp2027_year1_rpt_combined as kp_ab',backend)
        self.assertIn('"kp2027_combined": True',backend)
        self.assertIn('"/api/rpt/2027/kp2027/tahun-1/gabungan/<subject>.<fmt>"',backend)
        self.assertIn("account,error=_account()",backend)
        self.assertIn("X-RPT-Source-SHA256",backend)
        self.assertIn("/api/rpt/2027/kp2027/tahun-1/gabungan/",html)
        self.assertIn('rptKp2027GroupWrap.hidden=true',html)
        self.assertIn('rptKp2027Group.disabled=true',html)
        self.assertIn('Satu RPT mengandungi Kumpulan A dan B',html)
        self.assertNotIn("Pilih Kumpulan A atau B dahulu",html)
        self.assertIn('window.downloadCikguLajuRPT(selection.item.code',html)


if __name__=="__main__":
    unittest.main()
