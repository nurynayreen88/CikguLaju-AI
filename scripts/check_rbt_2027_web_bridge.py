#!/usr/bin/env python3
"""Web RBT 2027 smoke test: no network, credentials, account or charge writes.

Tests authenticated server-side proxy against a deliberately fake Telegram API.
The actual Web RPH route's debit-after-success behavior is unchanged.
"""
import io
import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit, parse_qs
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from docx import Document
from web import native_telegram_rbt_2027_client as c


class FakeResponse:
    def __init__(self,status,data,mimetype="application/json"):
        self.status=status
        self.data=data
        self.headers={"Content-Type":mimetype}
    def read(self,lim=-1):
        return self.data[:lim] if lim>=0 else self.data
    def __enter__(self):return self
    def __exit__(self,*_):return False


class FakeOpen:
    def __init__(self):
        self.failure=False
        self.requests=[]
    def open(self,req,timeout=None):
        self.requests.append(req)
        if self.failure:raise URLError("Telegram down")
        assert req.get_header("Authorization")=="Bearer private-test-token"
        parsed=urlsplit(req.full_url)
        q=parse_qs(parsed.query)
        assert parsed.path.startswith("/internal/rph/v1/rbt/")
        part=parsed.path.split("/")[-1]
        year=int(q["year"][0]) if "year" in q else 5
        if part=="units":
            result={"source":c.SOURCE,"status":"DRAF","items":[
                {"value":"u01","label":"Unit 1: Teknologi Rumah Tangga"},
                {"value":"u02","label":"Unit 2: Tenaga Boleh Baharu"},
                {"value":"u03","label":"Unit 3: Pengaturcaraan"}]}
        elif part=="lessons":
            result={"source":c.SOURCE,"status":"DRAF","items":[
                {"value":"001","label":"PdP 001: Mata jahitan tangan",
                 "textbook_ref":"Buku Teks calon m/s: 4, 6 (belum sah visual)",
                 "status":"DRAF"}]}
        elif part=="availability":
            result={"available":True,"status":"DRAF","generator":"telegram-native"}
        elif part=="render":
            payload=json.loads(req.data)
            assert set(payload)=={"selection","teacher","format"}
            assert payload["selection"]=={"year":5,"unit":"u01","lesson":"001"}
            if payload["format"]=="pdf":
                document=b"%PDF-1.7\n"+b"PDF-DRAF "*250
                return FakeResponse(200,document,"application/pdf")
            d=Document()
            d.add_paragraph("CikguLaju RBT DRAF "+("x"*2500))
            out=io.BytesIO();d.save(out)
            return FakeResponse(200,out.getvalue(),c.MIMES["word"])
        else:raise AssertionError(part)
        return FakeResponse(200,json.dumps(result).encode())


def test():
    orig=c._backend
    c._backend=lambda:("https://private.test","private-test-token")
    fake=FakeOpen()
    try:
        units=c.list_rbt_units(5,opener=fake)
        assert len(units)==3
        lessons=c.list_rbt_lessons(5,"u01",opener=fake)
        assert lessons[0]["value"]=="001"
        assert c.rbt_available(5,"u01","001",opener=fake)
        teacher={"class":"5 Amanah","date":"2027-01-04",
                 "time":"08:00-09:00","students":"24"}
        selected={"source":"telegram-native-rbt-2027","year":5,
                  "unit":"u01","lesson":"001","teacher":teacher}
        for fmt in ("word","pdf"):
            data=c.request_rbt_rph(selected,fmt,opener=fake)
            assert len(data.getvalue())>1000
            if fmt=="word":
                with ZipFile(io.BytesIO(data.getvalue())) as z:
                    assert "word/document.xml" in z.namelist()
            else:assert data.getvalue().startswith(b"%PDF-")
        assert all(req.get_header("Authorization")=="Bearer private-test-token" for req in fake.requests)
        for invalid in ((3,None,None),(5,"u77",None),(5,"u01","099")):
            try:c._validate(*invalid)
            except ValueError:pass
            else:raise AssertionError("Accepted invalid RBT source")
        fake.failure=True
        try:c.list_rbt_units(5,opener=fake)
        except c.NativeRPHUnavailable:pass
        else:raise AssertionError("Network fallback unexpectedly available")
        web=ROOT/"web/unified_rph_web.py"
        options=ROOT/"tools/run_web_v1_preview.py"
        ui=ROOT/"web_v1_static_preview/index.html"
        code=web.read_text(encoding="utf-8")
        assert 'if subject == "RBT":' in code
        assert 'request_rbt_rph(selected,fmt)' in code
        assert 'source":"telegram-native-rbt-2027"' in code
        assert "authorize_rendered_document(" in code
        assert code.index("authorize_rendered_document(")>code.index("request_rbt_rph(selected,fmt)")
        assert "10 janaan RPH percuma" in code
        assert "list_rbt_units(year)" in options.read_text(encoding="utf-8")
        assert 'RBT:"Unit"' in ui.read_text(encoding="utf-8")
        print("PASS Web RBT: 3 Unit, explicit PdP, private token, Word/PDF proxy, fail-closed, existing trial gate retained.")
    finally:
        c._backend=orig

if __name__=="__main__":test()
