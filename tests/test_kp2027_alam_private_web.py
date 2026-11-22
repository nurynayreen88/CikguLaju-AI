"""Offline + CI Flask contract checks for KP2027 Alam canonical private downloads."""
from __future__ import annotations
import base64
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED
from web import kp2027_alam_private_web as c


def sample(fmt='pdf',lesson=1):
    if fmt=='pdf':data=b'%PDF-1.7\n'+b'0'*1510
    else:
        stream=BytesIO()
        with ZipFile(stream,'w',ZIP_DEFLATED) as z:
            z.writestr('word/document.xml','<document>'+('A'*2800)+'</document>')
            z.writestr('docProps/test.bin',bytes(range(256))*8)
        data=stream.getvalue()
        if len(data)<1000:
            stream=BytesIO()
            with ZipFile(stream,'w',ZIP_DEFLATED) as z:
                z.writestr('word/document.xml', '<document>'+('A'*2800)+'</document>')
                z.writestr('docProps/test.bin',bytes([x%251 for x in range(3000)]),compress_type=0)
            data=stream.getvalue()
    return {'subject':'ALAM','kumpulan':'A','lesson':lesson,'format':fmt,
            'content_base64':base64.b64encode(data).decode('ascii'),'byte_size':len(data),
            'sha256_hex':sha256(data).hexdigest(),'sp_code':c.CATALOG['items'][str(lesson)]['sp'],
            'approval_status':'CANARY_APPROVED','source_archive_sha256':c.SOURCE_SHA}


class Response:
    status=200
    def __init__(self,obj,status=200):self.raw=json.dumps(obj).encode();self.status=status
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n=-1):return self.raw[:n]


class AlamPrivateTests(unittest.TestCase):
    def setUp(self):
        real=c.expected_entry
        def local_expected(n):
            item=real(n)
            return {**item, **{fmt:sample(fmt,n)['sha256_hex'] for fmt in ('pdf','word')},
                    **{fmt+'_bytes':sample(fmt,n)['byte_size'] for fmt in ('pdf','word')}}
        self.patcher=patch.object(c,'expected_entry',side_effect=local_expected)
        self.patcher.start();self.addCleanup(self.patcher.stop)

    def test_catalog_exact_content_pins(self):
        self.assertEqual(c.CATALOG['lesson_count'],64)
        self.assertEqual(len(c.CATALOG['items']),64)
        self.assertEqual(sum(len(x['codes'])==2 for x in c.CATALOG['items'].values()),19)
        self.assertEqual(c.CATALOG['source_archive_sha256'],c.SOURCE_SHA)
        for i in range(1,65):
            item=c.CATALOG['items'][str(i)]
            self.assertEqual(item['codes'][0],item['sp'])
            for fmt in ('word','pdf'):
                self.assertRegex(item[fmt],r'^[0-9a-f]{64}$')

    def test_reject_invalid_selection(self):
        for n in (0,65,True,'3',None,1.5):
            with self.assertRaises(ValueError):c.valid_selection(n,'pdf')
        for fmt in ('PDF','zip','../pdf',None):
            with self.assertRaises(ValueError):c.valid_selection(1,fmt)
        self.assertEqual(c.valid_selection(64,'word'),(64,'word'))

    def test_real_documents_match_source_hashes(self):
        from zipfile import ZipFile
        archive=Path('/mnt/data/CIKGULAJU_KP2027_ALAM_T1_64_LESSON_V10_19_GABUNG_SP_WORD_PDF_QA_20261122.zip')
        if not archive.exists():self.skipTest('Private QA fixture not mounted')
        with ZipFile(archive) as z:
            for n in (1,3,12,33,64):
                item=c.CATALOG['items'][str(n)]
                for fmt,dir_,ext in (('word','Word','docx'),('pdf','PDF','pdf')):
                    blob=z.read(f'{dir_}/ALAM_T1_LESSON{n:03d}.{ext}')
                    self.assertEqual(sha256(blob).hexdigest(),item[fmt])
                    self.assertEqual(len(blob),item[fmt+'_bytes'])

    def test_verified_source_and_hold_fail_closed(self):
        for n in (1,3,64):
            for fmt in ('word','pdf'):
                row=sample(fmt,n)
                self.assertTrue(c.verify_private_row(row,n,fmt))
                for field,wrong in [('approval_status','QA_HOLD'),('kumpulan','B'),('sp_code','9.9.9'),
                                    ('sha256_hex','0'*64),('source_archive_sha256','x'*64),
                                    ('byte_size',12),('subject','MATH')]:
                    with self.subTest(n=n,fmt=fmt,field=field),self.assertRaises(c.PilotUnavailable):
                        c.verify_private_row({**row,field:wrong},n,fmt)

    def test_catalog_excludes_unpaired_files(self):
        config={'account_backend':'supabase','supabase_url':'https://'+c.HOST,'supabase_key':'sb_secret_'+'x'*40}
        def entry(n,fmt):
            row=sample(fmt,n);e=c.expected_entry(n)
            return {k:row[k] for k in ('subject','kumpulan','lesson','format','sha256_hex','sp_code','approval_status','source_archive_sha256','byte_size')}
        good=[entry(1,'pdf'),entry(1,'word'),entry(3,'pdf'),entry(3,'word'),entry(8,'pdf')]
        self.assertEqual(c.fetch_approved_lessons(config,opener=lambda req,timeout=12:Response(good)),[1,3])
        for bad in ([entry(1,'pdf'),entry(1,'pdf')],[{**entry(1,'pdf'),'sha256_hex':'0'*64}],
                    [{**entry(1,'pdf'),'kumpulan':'B'}]):
            with self.assertRaises(c.PilotUnavailable):
                c.fetch_approved_lessons(config,opener=lambda req,timeout=12,bad=bad:Response(bad))

    def test_document_fetch_only_private_approved(self):
        config={'account_backend':'supabase','supabase_url':'https://'+c.HOST,'supabase_key':'sb_secret_'+'x'*40}
        def opener(req,timeout=12):
            self.assertIn('subject=eq.ALAM',req.full_url)
            self.assertIn('kumpulan=eq.A',req.full_url)
            self.assertIn('approval_status=eq.CANARY_APPROVED',req.full_url)
            self.assertNotIn('/storage/v1/object/public/',req.full_url)
            return Response([sample('pdf',1)])
        self.assertTrue(c.fetch_private_document(config,1,'pdf',opener=opener).startswith(b'%PDF-'))
        for rows in ([],[sample('pdf',1)]*2,[{**sample('pdf',1),'approval_status':'QA_HOLD'}]):
            with self.assertRaises(c.PilotUnavailable):
                c.fetch_private_document(config,1,'pdf',opener=lambda req,timeout=12,rows=rows:Response(rows))


class AlamFlaskContract(unittest.TestCase):
    def setUp(self):
        try:
            from flask import Flask
            import web.rph_delivery_quota
            import web_v1_telegram_auth_routes
            import web_v1_sessions
        except ImportError:self.skipTest('Flask/auth stack not available locally')
        self.Flask=Flask
        self.config={'account_backend':'supabase','supabase_url':'https://'+c.HOST,'supabase_key':'sb_secret_'+'x'*40,
                     'CIKGULAJU_WEB_SESSION_SECRET':'z'*48}
        self.account={'authenticated':True,'telegram_user_id':123,'rakan_pembangun':True,
                      'free_remaining':10,'vip_until':None,'vip_expires_at':None}

    def client(self,paid=True):
        import web.rph_delivery_quota as quota
        import web_v1_telegram_auth_routes as auth
        import web_v1_sessions as sessions
        patches=[patch.object(auth,'_config',return_value=self.config),patch.object(auth,'_lookup',return_value=self.account),
                 patch.object(sessions,'verify_session_ticket',return_value=123),
                 patch.object(quota,'has_active_paid_access',return_value=paid),
                 patch.object(quota,'authorize_rendered_document',return_value={'allowed':True,'remaining':9}),
                 patch.object(c,'fetch_private_document',return_value=b'%PDF-1.7\n'+b'0'*1500),
                 patch.object(c,'fetch_approved_lessons',return_value=[1,3]),
                 # Synthetic bytes exercise auth/quota; real-layout tests own personalization.
                 patch('web.kp2027_pilot_teacher_fields.personalize_approved_rph',side_effect=lambda data,fmt,fields:data)]
        mocks=[p.start() for p in patches]
        self.addCleanup(lambda:[p.stop() for p in reversed(patches)])
        app=self.Flask(__name__);app.testing=True;app.register_blueprint(c.create_blueprint())
        client=app.test_client()
        try:client.set_cookie('cikgulaju_web_v1_session','token')
        except TypeError:client.set_cookie('localhost','cikgulaju_web_v1_session','token')
        return client,mocks

    def test_flag_disabled_denies_post(self):
        client,_=self.client()
        with patch.dict(os.environ,{c.FEATURE_FLAG:'0'}):
            res=client.post('/api/kp2027/sk/tahun-1/alam-dan-manusia/download',json={'lesson':1,'format':'pdf'},headers={'Origin':c.ORIGIN})
        self.assertEqual(res.status_code,503)

    def test_reject_origin_and_missing_login(self):
        client,mocks=self.client()
        with patch.dict(os.environ,{c.FEATURE_FLAG:'1'}):
            res=client.post('/api/kp2027/sk/tahun-1/alam-dan-manusia/download',json={'lesson':1,'format':'pdf'},headers={'Origin':'https://evil.example'})
            self.assertEqual(res.status_code,403)
            res=client.post('/api/kp2027/sk/tahun-1/alam-dan-manusia/download',json={'lesson':1,'format':'pdf'})
            self.assertEqual(res.status_code,403)
            mocks[2].return_value=None
            res=client.get('/api/kp2027/sk/tahun-1/alam-dan-manusia/available')
            self.assertEqual(res.status_code,401)

    def test_success_and_existing_quota(self):
        client,mocks=self.client(paid=False)
        with patch.dict(os.environ,{c.FEATURE_FLAG:'1'}):
            inventory=client.get('/api/kp2027/sk/tahun-1/alam-dan-manusia/available')
            self.assertEqual(inventory.status_code,200)
            self.assertEqual(inventory.json['lessons'],[1,3])
            success=client.post('/api/kp2027/sk/tahun-1/alam-dan-manusia/download',json={'lesson':3,'format':'pdf'},headers={'Origin':c.ORIGIN})
            self.assertEqual(success.status_code,200)
            self.assertEqual(success.headers['X-RPH-Trial-Remaining'],'9')
            self.assertEqual(mocks[4].call_count,1)

if __name__=='__main__':unittest.main()
