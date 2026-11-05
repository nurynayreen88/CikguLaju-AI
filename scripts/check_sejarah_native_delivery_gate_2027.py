#!/usr/bin/env python3
"""End-to-end protected Telegram RPH API denies unapproved Sejarah 2027.

No production Flask process, database, user or Telegram bot is started.
All calls occur against an in-memory Flask test client and fake renderer.
"""
from pathlib import Path
import os
import re
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from flask import Flask
from web.native_rph_telegram_api import build_native_input, create_native_rph_blueprint
from web.sejarah_2027_native_layout_adapter import internal_preview_layout, approved_native_payload
from web.rph_shared_source_identity import source_fingerprint

class FakeRenderer:
    def __init__(self): self.calls=0
    def create_word_file(self,*args,**kwargs):
        self.calls+=1
        raise AssertionError("Unapproved Sejarah reached native Word")
    def create_pdf_file(self,*args,**kwargs):
        self.calls+=1
        raise AssertionError("Unapproved Sejarah reached native PDF")

renderer=FakeRenderer()
app=Flask(__name__)
app.register_blueprint(create_native_rph_blueprint(renderer))
teacher={"class":"5 Bestari","date":"2027-03-22","time":"08:00-09:00"}
count=0
with patch.dict(os.environ,{"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1","CIKGULAJU_AUTHORITATIVE_API_TOKEN":"Z"*48}):
    client=app.test_client()
    for year in (4,5,6):
        for pdp in range(1,37):
            digest=source_fingerprint(year,"SEJARAH",pdp)
            assert digest is not None and re.fullmatch("[0-9a-f]{64}",digest)
            payload={
                "subject":"SEJARAH","component":None,"year":year,"lesson":pdp,
                "unit":"Unit Sejarah", "teacher":teacher,
                "layout":internal_preview_layout(year,pdp,teacher),
                "format":"word","source_digest":digest,
            }
            try:
                build_native_input(payload)
            except ValueError:
                pass
            else:
                raise AssertionError("Draft passed native input validation")
            response=client.post("/internal/rph/v1/render",json=payload,headers={"Authorization":"Bearer "+"Z"*48})
            assert response.status_code in (400,503),(year,pdp,response.status_code)
            assert response.headers.get("Cache-Control")=="no-store, private"
            count+=1
    assert renderer.calls==0
assert count==108
print("Sejarah native authenticated endpoint: 108/108 drafts rejected; zero renderer calls")
