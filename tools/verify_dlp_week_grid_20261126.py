"""Check all real DLP Word table cells independently of PDF renderer."""
import json
from io import BytesIO
from unittest.mock import patch
from docx import Document
from docx.oxml.ns import qn
from tools.build_rpt_dlp_native_20261126 import ROOT,PINS
from tools.build_rpt_dlp_full_standards_20261126 import build_word
from tools.rpt_dlp_week_column_20261126 import fix_week_column

def snapshot(table):
    return [tuple("".join(tc.xpath(".//w:t/text()")) for tc in tr.tc_lst) for tr in table._tbl.tr_lst]

def main():
    manifest=json.loads((ROOT/"full_standards_dlp_pdf_2027/manifest.json").read_text())
    for key in PINS:
        subject,y=key.split(":");year=int(y)
        sizes=manifest["page_groups"][key]
        with patch("tools.rpt_dlp_week_column_20261126.fix_week_column",lambda t:None):
            original,*_=build_word(subject,year,whole_weeks=True,compact_sizes=sizes)
        corrected,*_=build_word(subject,year,whole_weeks=True,compact_sizes=sizes)
        before=Document(BytesIO(original));after=Document(BytesIO(corrected))
        assert len(before.tables)==len(after.tables)==len(sizes)+1,key
        assert [snapshot(t) for t in before.tables]==[snapshot(t) for t in after.tables],key
        # Compare actual lesson-row cells, not the repeated text that python-docx
        # resolves from a merged cell. All weekly labels and body text stay exact.
        for i,(a,b) in enumerate(zip(before.tables[:-1],after.tables[:-1],strict=True)):
            old=[tr.tc_lst[0] for tr in a._tbl.tr_lst]
            new=[tr.tc_lst[0] for tr in b._tbl.tr_lst]
            assert len(old)==len(new) and all(tc.vMerge is None for tc in new)
            assert b._tbl.tr_lst[0].trPr.find(qn("w:tblHeader")) is not None
            assert len([tc for tc in new[1:] if "".join(tc.xpath(".//w:t/text()")).startswith("Week ")])==sizes[i]
            for j,tc in enumerate(new[1:],1):
                edges=tc.tcPr.find(qn("w:tcBorders"))
                assert edges is not None
                assert edges.find(qn("w:top")).get(qn("w:val"))==("nil" if old[j].vMerge=="continue" else "single")
                assert edges.find(qn("w:bottom")).get(qn("w:val"))==("nil" if j+1<len(old) and old[j+1].vMerge=="continue" else "single")
            assert new[-1].tcPr.find(qn("w:tcBorders")).find(qn("w:bottom")).get(qn("w:val"))=="single"
        print("DLP_WORD_WEEK_GRID_OK",key,"tables",len(sizes),"weeks",sum(sizes),flush=True)

if __name__=="__main__":main()
