"""Local gated-source and authorization primitives for KP2027 PJ RPH."""
import base64
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs,urlparse
from zipfile import ZipFile,ZIP_DEFLATED

from web import kp2027_pj_private_web as pj

class Response:
    def __init__(self,data): self.stream=BytesIO(json.dumps(data).encode());self.status=200
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,n):return self.stream.read(n)

class PJSourceTest(unittest.TestCase):
    def setUp(self):
        self.config={'supabase_url':'https://private.example.supabase.co','supabase_key':'sb_secret_'+'t'*40}

    def test_catalog_complete_no_dummy_content(self):
        self.assertEqual(pj.CATALOG['groups'],{'A':64,'B':63})
        self.assertEqual(sum(len(x) for x in pj.CATALOG['items'].values()),127)
        for group,count in pj.CATALOG['groups'].items():
            self.assertEqual([x['no'] for x in pj.CATALOG['items'][group]],list(range(1,count+1)))
            self.assertTrue(all(x['all_sp'] and x['sp']==x['all_sp'][0] for x in pj.CATALOG['items'][group]))
        self.assertEqual(len(pj.CATALOG['batches']),8)
        self.assertIn('PJ_PRIVATE_ENABLED',pj.FEATURE_FLAG)

    def test_invalid_selection_does_not_query_private_records(self):
        for case in [('B',64,'pdf'),('A',0,'pdf'),('A',True,'word'),('A','1','word'),('C',1,'pdf'),('A',1,'exe')]:
            with self.assertRaises(ValueError):pj.select_group(*case)
        self.assertEqual(pj.select_group('A',64,'word'),('A',64,'word',4))
        self.assertEqual(pj.select_group('B',63,'pdf'),('B',63,'pdf',4))

    def test_inventory_uses_metadata_only_and_checks_hash(self):
        b=pj.CATALOG['batches']['A1']
        row={'group_code':'A','batch_index':1,'first_pdp':1,'last_pdp':16,
             'archive_bytes':b['size'],'archive_sha256':b['sha256'],'approval_status':'CANARY_APPROVED'}
        urls=[]
        def opening(req,timeout):
            urls.append(req.full_url);return Response([row])
        groups,items=pj.approved_inventory(self.config,opener=opening)
        self.assertEqual(groups['A'],list(range(1,17)))
        self.assertEqual(groups['B'],[])
        self.assertEqual(len(items['A']),16)
        self.assertNotIn('archive_b64',urls[0]);self.assertIn('eq.CANARY_APPROVED',urls[0]);self.assertNotIn('/storage/v1/',urls[0])
        row['archive_sha256']='0'*64
        with self.assertRaises(pj.PrivateRphUnavailable):pj.approved_inventory(self.config,opener=opening)

    def test_archive_checksum_and_manifest_gate(self):
        # Synthetic private ZIP: tests actual guard, not paid source bytes.
        filenames={}
        with BytesIO() as stream:
            with ZipFile(stream,'w',ZIP_DEFLATED) as zipf:
                for lesson in range(1,17):
                    for kind,ext in (('WORD','docx'),('PDF','pdf')):
                        name=f'{kind}/CIKGULAJU_RPH_KP2027_PJ_T1_A_PDP{lesson:03d}.{ext}'
                        body=(b'PK\x03\x04' if kind=='WORD' else b'%PDF-')+str(lesson).encode().ljust(32000,b'x')
                        zipf.writestr(name,body)
                        filenames[name]={'bytes':len(body),'sha256':sha256(body).hexdigest()}
                zipf.writestr('MANIFEST_QA.json',json.dumps({'group':'A','first_lesson':1,'last_lesson':16,'files':filenames}))
            raw=stream.getvalue()
        original=pj.CATALOG['batches']['A1']
        fake={**original,'name':'synthetic_private.zip','size':len(raw),'sha256':sha256(raw).hexdigest()}
        def opening(req,timeout):
            u=urlparse(req.full_url);q=parse_qs(u.query)
            self.assertEqual(q['approval_status'],['eq.CANARY_APPROVED'])
            return Response([{'group_code':'A','batch_index':1,'first_pdp':1,'last_pdp':16,
                 'archive_bytes':fake['size'],'archive_sha256':fake['sha256'],
                 'archive_name':fake['name'],'approval_status':'CANARY_APPROVED',
                 'archive_b64':base64.b64encode(raw).decode()}])
        with patch.dict(pj.CATALOG['batches'],{'A1':fake}):
            pdf=pj.private_document(self.config,'A',4,'pdf',opener=opening)
            self.assertTrue(pdf.startswith(b'%PDF-'))
            word=pj.private_document(self.config,'A',4,'word',opener=opening)
            self.assertTrue(word.startswith(b'PK\x03\x04'))
            wrong={**fake,'sha256':'f'*64}
            with patch.dict(pj.CATALOG['batches'],{'A1':wrong}):
                with self.assertRaises(pj.PrivateRphUnavailable):
                    pj.private_document(self.config,'A',4,'pdf',opener=opening)

if __name__=='__main__':unittest.main()
