"""Eight source-correct supplementary SP PBD worksheets in offline 342-RPH ZIP."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
import json
import unittest
from zipfile import ZipFile

from docx import Document
from pypdf import PdfReader

from tools.build_sains_342_offline_review_pack_20261108 import ZIP,PORTAL
from tools.enrich_sains_342_offline_pbd_20261108 import EXPECTED_MISSING,EXPECTED_SECONDARY
from tools.audit_rph80_sains_first_20261107 import EXPECTED


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.links.extend(value for key,value in attrs if key=="href")


class TestScienceOfflinePbdSupport(unittest.TestCase):
    def test_zip_has_342_rph_and_8_original_support_pbd_not_350_official_pdp(self):
        with ZipFile(ZIP) as archive:
            self.assertIsNone(archive.testzip())
            prefix=PORTAL.name+"/"
            names=set(archive.namelist())
            self.assertEqual(len(names),704)
            ledger=json.loads(archive.read(prefix+"MANIFEST_SHA256.json"))
            self.assertEqual(ledger["status"],"ACADEMIC_HOLD")
            self.assertEqual(ledger["approved"],0)
            self.assertEqual(len(ledger["items"]),342)
            self.assertEqual(Counter(r["year"] for r in ledger["items"]),Counter(EXPECTED))
            self.assertEqual(len(ledger["supplements"]),8)
            self.assertTrue(ledger["no_new_official_pdp"])
            self.assertEqual(ledger["year2_official_missing_sp_supported"],sorted(EXPECTED_MISSING))
            self.assertEqual(sum(x["linked_pdp"] is None for x in ledger["supplements"]),3)
            self.assertEqual(Counter(x["year"] for x in ledger["supplements"]),{2:5,3:3})
            self.assertEqual({x["sp"] for x in ledger["supplements"] if x["source_category"]=="YEAR3_SECONDARY_SP_PBD"},EXPECTED_SECONDARY)
            self.assertEqual({x["sp"] for x in ledger["supplements"] if x["source_category"]=="YEAR2_UNASSIGNED_DSKP_SP"},EXPECTED_MISSING)
            for row in ledger["supplements"]:
                with self.subTest(year=row["year"],sp=row["sp"]):
                    self.assertEqual(row["academic_status"],"DRAF_HOLD")
                    self.assertFalse(row["teacher_approved"])
                    self.assertFalse(row["official_pdp_created"])
                    self.assertFalse(row["official_workbook"])
                    for kind in ("word","pdf"):
                        name=prefix+row[kind]
                        self.assertIn(name,names)
                        binary=archive.read(name)
                        self.assertEqual(sha256(binary).hexdigest(),row[kind+"_sha256"])
                        if kind=="word":
                            word=Document(BytesIO(binary))
                            self.assertGreaterEqual(len(word.tables),1)
                            self.assertAlmostEqual(word.sections[0].page_width.cm,21,delta=0.05)
                        else:
                            pdf=PdfReader(BytesIO(binary))
                            self.assertEqual(len(pdf.pages),1)
                            txt=pdf.pages[0].extract_text()
                            self.assertIn(row["sp"],txt)
                            self.assertIn("Aktiviti 1",txt)
                            self.assertIn("Aktiviti 3",txt)

    def test_browser_links_work_offline_and_filter_distinguishes_pdp_and_support(self):
        with ZipFile(ZIP) as archive:
            prefix=PORTAL.name+"/"
            names=set(archive.namelist())
            index=archive.read(prefix+"index.html").decode("utf-8")
            self.assertIn('id="main-pdp-rows"',index)
            self.assertIn('id="support-rows"',index)
            self.assertIn("#main-pdp-rows tr",index)
            self.assertIn("#support-rows tr",index)
            self.assertIn("8 bahan PBD sokongan",index)
            self.assertIn("Bukan Buku Aktiviti rasmi",index)
            self.assertIn("Belum dijadualkan; tiada PdP baharu",index)
            links=Links();links.feed(index)
            self.assertEqual(len(links.links),702)
            for href in links.links:
                self.assertIn(prefix+href,names)
            self.assertNotIn("https://",index)

    def test_existing_342_rph_csv_and_teachers_approval_unchanged(self):
        import csv
        with ZipFile(ZIP) as archive:
            prefix=PORTAL.name+"/"
            rows=list(csv.DictReader(archive.read(prefix+"SEMAKAN_PANITIA_342.csv").decode("utf-8-sig").splitlines()))
            self.assertEqual(len(rows),342)
            self.assertTrue(all(row["Keputusan"].startswith("HOLD") for row in rows))
            self.assertTrue(all(not row["Semakan guru/panitia"] for row in rows))


if __name__=="__main__":
    unittest.main()
