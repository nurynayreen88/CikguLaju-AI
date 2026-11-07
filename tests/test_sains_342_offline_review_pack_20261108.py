"""Verify 342 Word/PDF offline portal is fully usable while academic HOLD."""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import json
import zipfile
import unittest

from tools.audit_rph80_sains_first_20261107 import EXPECTED
from tools.build_sains_342_offline_review_pack_20261108 import ZIP,PORTAL


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.hrefs.extend(value for k,value in attrs if k=="href")


class Test342OfflineRPHReview(unittest.TestCase):
    def test_all_342_usable_pdf_word_links_and_source_sha(self):
        self.assertTrue(ZIP.is_file())
        with zipfile.ZipFile(ZIP) as archive:
            self.assertIsNone(archive.testzip())
            root=PORTAL.name
            members=set(archive.namelist())
            self.assertEqual(len(members),688)
            index=archive.read(root+"/index.html").decode("utf-8")
            manifest=json.loads(archive.read(root+"/MANIFEST_SHA256.json"))
            self.assertEqual(manifest["approved"],0)
            self.assertEqual(manifest["status"],"ACADEMIC_HOLD")
            self.assertEqual(len(manifest["items"]),342)
            self.assertEqual(Counter(x["year"] for x in manifest["items"]),Counter(EXPECTED))
            self.assertEqual(len({x["pdp_code"] for x in manifest["items"]}),342)
            links=Links();links.feed(index)
            self.assertEqual(len(links.hrefs),686)
            for link in links.hrefs:
                self.assertIn(root+"/"+link,members)
            for row in manifest["items"]:
                self.assertTrue(row["draft"])
                self.assertFalse(row["teacher_approved"])
                for key in ("pdf","word"):
                    name=root+"/"+row[key]
                    self.assertIn(name,members)
                    binary=archive.read(name)
                    self.assertGreater(len(binary),500)
                    self.assertEqual(sha256(binary).hexdigest(),row[key+"_sha256"])
            self.assertIn("DRAF / UNTUK SEMAKAN DALAMAN SAHAJA",index)
            self.assertIn("data-year",index)
            self.assertIn('id="q"',index)
            self.assertNotIn("https://",index)

    def test_review_csv_contains_all_342_and_explicit_holds(self):
        import csv,io
        with zipfile.ZipFile(ZIP) as archive:
            text=archive.read(PORTAL.name+"/SEMAKAN_PANITIA_342.csv").decode("utf-8-sig")
            lines=list(csv.DictReader(io.StringIO(text)))
            self.assertEqual(len(lines),342)
            self.assertTrue(all(r["Keputusan"].startswith("HOLD") for r in lines))
            self.assertTrue(all(not r["Semakan guru/panitia"] for r in lines))
            self.assertTrue(all(not r["Mata SK/SP (maks 25)"] for r in lines))


if __name__=="__main__":
    unittest.main()
