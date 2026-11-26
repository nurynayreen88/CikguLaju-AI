"""Check physical rendering and exact package preservation of BM SJK repeat headers."""
import io,os,re,subprocess,tempfile,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from lxml import etree
from flask import Flask
from docx import Document
import fitz
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint,SJK_RPTS
from web.rpt_sjk_word_header_repair import PINS,COUNTS,W,NS,repair

class BMRepair(unittest.TestCase):
    def test_four(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        folder=ROOT/"sjkc"/"bahasa_melayu"
        definition=SJK_RPTS["bahasa-melayu"]
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        for year in PINS:
            with self.subTest(year=year):
                path=definition.document_path(year,"docx",root=folder)
                raw=path.read_bytes();blob=repair(year,raw)
                with ZipFile(io.BytesIO(raw)) as orig,ZipFile(io.BytesIO(blob)) as changed:
                    self.assertEqual(orig.namelist(),changed.namelist())
                    for name in orig.namelist():
                        if name!="word/document.xml":
                            self.assertEqual(orig.read(name),changed.read(name),name)
                    a=etree.fromstring(orig.read("word/document.xml"))
                    b=etree.fromstring(changed.read("word/document.xml"))
                    markers=b.xpath("//w:tblHeader",namespaces=NS)
                    self.assertEqual(len(markers),sum(COUNTS[year].values()))
                    for marker in markers:
                        parent=marker.getparent();parent.remove(marker)
                        if len(parent)==0 and not parent.attrib:parent.getparent().remove(parent)
                    # Text, row counts, merged cells, cover and styles remain identical.
                    self.assertEqual(a.xpath("//w:t/text()",namespaces=NS),b.xpath("//w:t/text()",namespaces=NS))
                    self.assertEqual(a.xpath("count(//w:tr)",namespaces=NS),b.xpath("count(//w:tr)",namespaces=NS))
                url=f"/api/rpt/2027/sjkc/bahasa-melayu/{year}.docx"
                with patch.dict(os.environ,{"CIKGULAJU_RPT_SJK_BM_REPEAT_HEADERS":"1"}):
                    with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                        self.assertEqual(client.get(url).data,blob)
                    with patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":10},None)):
                        self.assertEqual(client.get(url).status_code,403)
                with tempfile.TemporaryDirectory() as temp:
                    temp=Path(temp)
                    (temp/"repaired.docx").write_bytes(blob)
                    subprocess.run(["libreoffice","-env:UserInstallation="+(temp/"lo").as_uri(),"--headless","--convert-to","pdf","--outdir",str(temp),str(temp/"repaired.docx")],check=True,timeout=150)
                    with fitz.open(temp/"repaired.pdf") as pdf:
                        self.assertGreater(len(pdf),1)
                        for page in pdf:
                            self.assertTrue(page.get_text().strip())
                            for block in page.get_text("blocks"):
                                self.assertGreaterEqual(block[1],0)
                                self.assertLessEqual(block[3],page.rect.height+1)
                        print("BM_SJK_RENDER_OK",year,"pages",len(pdf),"headers",len(markers),flush=True)
if __name__=="__main__":unittest.main()
