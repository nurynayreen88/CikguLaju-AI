"""Offline security tests for the narrowly scoped KP2027 Math Web pilot."""
from __future__ import annotations
import base64
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from web import kp2027_math_canary_web as c

ROOT = Path(__file__).resolve().parents[1]
PILOT = Path('/mnt/data/kp2027_pilot_math')


def fake_row(group='A', lesson=1, fmt='word'):
    if fmt == 'pdf':
        blob = b'%PDF-1.7\n' + b'0' * 1500
    else:
        from zipfile import ZipFile, ZIP_DEFLATED
        b = BytesIO()
        with ZipFile(b, 'w', ZIP_DEFLATED) as z:
            z.writestr('word/document.xml', '<x/>'+'x'*1200)
        blob = b.getvalue()
        if len(blob) < 1000:
            with ZipFile(b, 'a') as z:
                z.writestr('docProps/core.xml', 'x'*1300)
            blob = b.getvalue()
    return {'subject': 'MATH', 'kumpulan': group, 'lesson': lesson, 'format': fmt,
            'content_base64': base64.b64encode(blob).decode('ascii'), 'byte_size': len(blob),
            'sha256_hex': sha256(blob).hexdigest(), 'sp_code': '1.1.1',
            'approval_status': 'CANARY_APPROVED', 'source_archive_sha256': c.SOURCE_SHA}


class Response:
    status = 200
    def __init__(self, value, status=200): self.raw=json.dumps(value).encode(); self.status=status
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n=-1): return self.raw[:n]

class TestPilot(unittest.TestCase):
    def test_strict_selection(self):
        for x in (0, 4, True, '1', '../1', 1.3, None):
            with self.subTest(x=x), self.assertRaises(ValueError): c.valid_selection('A', x, 'pdf')
        for group in ('', 'a', 'Z', None):
            with self.assertRaises(ValueError): c.valid_selection(group, 1, 'word')
        for fmt in ('zip', 'PDF', '../pdf', None):
            with self.assertRaises(ValueError): c.valid_selection('B', 1, fmt)
        self.assertEqual(c.valid_selection('B',3,'word'),('B',3,'word'))

    def test_refuse_qa_and_bad_identity(self):
        row=fake_row()
        for field,value in [('approval_status','QA_HOLD'),('subject','BM_SK'),('kumpulan','B'),
                            ('lesson',True),('sp_code','9.9.9'),('source_archive_sha256','x'*64)]:
            with self.subTest(field=field), self.assertRaises(c.PilotUnavailable):
                c.verify_private_row({**row,field:value}, 'A', 1, 'word')

    def test_checksums_and_bad_docs(self):
        for fmt in ('word','pdf'):
            row=fake_row(fmt=fmt)
            c.verify_private_row(row,'A',1,fmt)
            for field,value in [('sha256_hex','0'*64),('byte_size',17),('content_base64','not-base64'),
                                ('content_base64',42)]:
                with self.subTest(fmt=fmt,field=field), self.assertRaises(c.PilotUnavailable):
                    c.verify_private_row({**row,field:value},'A',1,fmt)
        p=fake_row(fmt='pdf'); blob=b'STOLEN'+b' ' * 1200
        p.update(content_base64=base64.b64encode(blob).decode(),byte_size=len(blob),sha256_hex=sha256(blob).hexdigest())
        with self.assertRaises(c.PilotUnavailable):c.verify_private_row(p,'A',1,'pdf')

    def test_host_and_credentials(self):
        valid={'account_backend':'supabase','supabase_url':'https://'+c.HOST,'supabase_key':'sb_secret_'+'z'*40}
        self.assertEqual(c._settings(valid)[0],valid['supabase_url'])
        for host in ('http://'+c.HOST,'https://evil.example','https://'+c.HOST+'.evil.example',
                     'https://'+c.HOST+'/evil','https://'+c.HOST+':8443'):
            with self.assertRaises(c.PilotUnavailable):c._settings({**valid,'supabase_url':host})
        with self.assertRaises(c.PilotUnavailable):c._settings({**valid,'account_backend':'sqlite'})
        self.assertNotIn('Authorization',c._headers(valid['supabase_key']))
        self.assertIn('Authorization',c._headers('eyJ'+('a'*50)))

    def test_rest_only_exact_row_and_no_redirect(self):
        config={'account_backend':'supabase','supabase_url':'https://'+c.HOST,'supabase_key':'sb_secret_'+'z'*40}
        inspected=[]
        def open_ok(req,timeout=12):
            inspected.append(req.full_url)
            self.assertNotIn('/storage/v1/object/public/',req.full_url)
            self.assertEqual(req.get_header('Apikey'),config['supabase_key'])
            return Response([fake_row(fmt='pdf')])
        result=c.fetch_private_document(config,'A',1,'pdf',opener=open_ok)
        self.assertTrue(result.startswith(b'%PDF-'))
        self.assertIn('lesson=eq.1',inspected[0])
        for result in ([], [fake_row(fmt='pdf')]*2, [fake_row(fmt='pdf')]):
            def bad(req,timeout=12, result=result):
                return Response(result if len(result)!=1 else [{**result[0],'approval_status':'QA_HOLD'}])
            with self.assertRaises(c.PilotUnavailable):c.fetch_private_document(config,'A',1,'pdf',opener=bad)

    def test_real_docs_source_digest_if_locally_mounted(self):
        if not PILOT.is_dir():self.skipTest('No private test fixtures')
        for g in ('A','B'):
            for n in (1,2,3):
                for fmt,ext in (('word','docx'),('pdf','pdf')):
                    b=(PILOT/f'MATH_T1_{g}_LESSON{n:03d}.{ext}').read_bytes()
                    r=fake_row(g,n,fmt);r.update(content_base64=base64.b64encode(b).decode(),byte_size=len(b),sha256_hex=sha256(b).hexdigest())
                    self.assertEqual(c.verify_private_row(r,g,n,fmt),b)
        self.assertIn('Lesson 001',c._PAGE)
        self.assertNotIn('Lesson 004',c._PAGE)

if __name__=='__main__':unittest.main()
