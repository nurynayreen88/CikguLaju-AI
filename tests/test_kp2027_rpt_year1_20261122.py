"""KP2027 Year 1 RPT A/B: archive integrity and authenticated Web wiring."""
from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import unittest

from web import kp2027_year1_rpt_bundle as src

ROOT=Path(__file__).resolve().parents[1]


class TestKp2027RptYear1(unittest.TestCase):
    def test_archive_sha_and_all_12_documents(self):
        self.assertTrue(src.ready(),"All 12 documents must pass full SHA validation")
        self.assertEqual(sha256(src.BUNDLE.read_bytes()).hexdigest(),src.BUNDLE_SHA)
        self.assertEqual(len(src._approved_files()),12)
        self.assertEqual(set(src.SUBJECTS),{"matematik","bahasa_melayu","alam_dan_manusia"})
        total=0
        for subject in src.SUBJECTS:
            for group in ("A","B"):
                self.assertGreater(src.COUNTS[subject][group],0)
                total+=src.COUNTS[subject][group]
                for fmt in ("pdf","docx"):
                    with self.subTest(subject=subject,group=group,fmt=fmt):
                        payload,name,digest=src.document(subject,group,fmt)
                        self.assertGreater(len(payload),20000)
                        self.assertEqual(sha256(payload).hexdigest(),digest)
                        self.assertIn("_KUMPULAN_"+group+"_",name)
                        self.assertEqual(name.endswith("."+fmt),True)
                        self.assertTrue(payload.startswith(b"%PDF-" if fmt=="pdf" else b"PK\x03\x04"))
        self.assertEqual(total,788)

    def test_each_word_rpt_matches_general_2027_template(self):
        """All six must use the same weekly seven-column general RPT layout."""
        import io
        import re
        import xml.etree.ElementTree as ET
        from zipfile import ZipFile
        heading = ("Minggu / tarikh", "Tema / tajuk", "SK / SP / rujukan",
                   "Aktiviti PdP", "PBD / pentaksiran",
                   "Acara / status / sumber", "Catatan / pindaan")
        for subject in src.SUBJECTS:
            for group in src.GROUPS:
                with self.subTest(subject=subject, group=group):
                    payload, name, digest = src.document(subject,group,"docx")
                    self.assertIn("FORMAT_UMUM_SEMAKAN",name)
                    with ZipFile(io.BytesIO(payload)) as docx:
                        root=ET.fromstring(docx.read("word/document.xml"))
                    texts = [t.text or "" for t in root.iter(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")]
                    body="\n".join(texts)
                    for field in ("NAMA SEKOLAH", "NAMA GURU", "TAHUN / KELAS",
                                  "DISEDIAKAN OLEH", "DISEMAK OLEH", "TARIKH SEMAKAN",
                                  "JADUAL PERANCANGAN PdP", "LOG SEMAKAN"):
                        self.assertIn(field,body)
                    for column in heading:
                        self.assertIn(column,body)
                    ids={int(x) for x in re.findall(r"PdP (\d{3})",body)}
                    self.assertEqual(ids,set(range(1,src.COUNTS[subject][group]+1)))
                    self.assertIn("SEMAKAN PELAKSANAAN",body)
                    self.assertNotIn("STATUS: READY",body)

    def test_group_a_b_different_documents(self):
        for subject in src.SUBJECTS:
            self.assertNotEqual(src.document(subject,"A","pdf")[2],
                                src.document(subject,"B","pdf")[2])

    def test_invalid_group_subject_format_fail_closed(self):
        for args in (("matematik","C","pdf"),("sains","A","pdf"),
                     ("matematik","A","zip"),("matematik","a","docx")):
            with self.subTest(args=args), self.assertRaises(src.BundleUnavailable):
                src.document(*args)

    def test_web_catalog_contains_group_specific_ready_choices(self):
        server=(ROOT/"web/rpt_2027_all_http.py").read_text(encoding="utf-8")
        ast.parse(server)
        self.assertIn('from web import kp2027_year1_rpt_bundle as kp_rpt',server)
        self.assertIn('"alam_dan_manusia"',server)
        self.assertIn('"kp2027_groups": ["A","B"]',server)
        self.assertIn('"/api/rpt/2027/kp2027/tahun-1/<subject>/<group>.<fmt>"',server)
        self.assertIn('account, error = _account()',server)
        self.assertIn('response.headers["X-RPT-Source-SHA256"] = digest',server)
        self.assertIn('response.headers["X-RPT-QA-Status"] = "SEMAKAN-PELAKSANAAN"',server)
        self.assertIn('return jsonify({"error": "Pilihan RPT KP2027 tidak sah."}), 404',server)

    def test_web_unit_group_pdf_word_and_kssr_existing_logic(self):
        page=(ROOT/"web_v1_static_preview/index.html").read_text(encoding="utf-8")
        self.assertIn('id="rpt-kp2027-group"',page)
        self.assertIn('function rptKP2027Url(entry,fmt)',page)
        self.assertIn('function rptDirectPdfUrl(entry)',page)
        self.assertIn('if(rptKP2027Choice(entry))return rptKP2027Url(entry,"pdf")',page)
        self.assertIn('const directUrl=ready?rptDirectPdfUrl(selection):null;',page)
        self.assertIn('rptMobileLink.href=directUrl;',page)
        self.assertIn('function rptKP2027DownloadName(entry,fmt)',page)
        self.assertIn('rptMobileLink.setAttribute("download",rptKP2027DownloadName(selection,"pdf")||"");',page)
        self.assertIn('rptWordLink.setAttribute("download",rptKP2027DownloadName(selection,"docx")||bmKssr||"");',page)
        self.assertIn('if(rptDirectPdfUrl(item))return;',page)
        self.assertNotIn('async function downloadKP2027Rpt(selection)',page)
        self.assertNotIn('window.open("about:blank","_blank")',page)
        self.assertIn('rptWordLink.href=wordUrl',page)
        self.assertIn('window.downloadCikguLajuRPT(selection.item.code',page)
        self.assertIn('Satu RPT mengandungi Kumpulan A dan B',page)
        self.assertIn('/api/rpt/2027/kp2027/tahun-1/gabungan/',page)
        self.assertNotIn('year.year===1||year.coming_soon',page)


if __name__=="__main__":
    unittest.main()
