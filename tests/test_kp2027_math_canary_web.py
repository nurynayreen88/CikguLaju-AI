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
            'sha256_hex': sha256(blob).hexdigest(), 'sp_code': c.expected_entry(group, lesson)['sp'],
            'approval_status': 'CANARY_APPROVED', 'source_archive_sha256': c.SOURCE_SHA}


class Response:
    status = 200
    def __init__(self, value, status=200): self.raw=json.dumps(value).encode(); self.status=status
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n=-1): return self.raw[:n]

class TestPilot(unittest.TestCase):
    def setUp(self):
        # Only tests use tiny synthetic RPH bytes. Production has *immutable*
        # original PDF/Word hashes from the verified 249-file source catalog.
        self.real_expected = c.expected_entry
        synthetic = {fmt: fake_row('A', 1, fmt)['sha256_hex'] for fmt in ('word','pdf')}
        def fixture_entry(group, lesson):
            return {**self.real_expected(group, lesson), **synthetic}
        self.fixture_patch = patch.object(c, 'expected_entry', side_effect=fixture_entry)
        self.fixture_patch.start()
        self.addCleanup(self.fixture_patch.stop)

    def test_strict_selection(self):
        for x in (0, 126, True, '1', '../1', 1.3, None):
            with self.subTest(x=x), self.assertRaises(ValueError): c.valid_selection('A', x, 'pdf')
        for group in ('', 'a', 'Z', None):
            with self.assertRaises(ValueError): c.valid_selection(group, 1, 'word')
        for fmt in ('zip', 'PDF', '../pdf', None):
            with self.assertRaises(ValueError): c.valid_selection('B', 1, fmt)
        self.assertEqual(c.valid_selection('B',124,'word'),('B',124,'word'))
        with self.assertRaises(ValueError):c.valid_selection('B',125,'word')

    def test_refuse_qa_and_bad_identity(self):
        row=fake_row()
        for field,value in [('approval_status','QA_HOLD'),('subject','BM_SK'),('kumpulan','B'),
                            ('lesson',True),('sp_code','9.9.9'),('source_archive_sha256','x'*64)]:
            with self.subTest(field=field), self.assertRaises(c.PilotUnavailable):
                c.verify_private_row({**row,field:value}, 'A', 1, 'word')

    def test_each_lesson_sp_mapping_fail_closed(self):
        self.assertEqual(c.MAX_LESSON, 125)
        for lesson in range(1, 126):
            with self.subTest(lesson=lesson):
                self.assertEqual(c.valid_selection("A", lesson, "pdf"), ("A", lesson, "pdf"))
                original = fake_row("A", lesson, "pdf")
                c.verify_private_row(original, "A", lesson, "pdf")
                changed = {**original, "sp_code": "9.9.9"}
                with self.assertRaises(c.PilotUnavailable):
                    c.verify_private_row(changed, "A", lesson, "pdf")

    def test_full_catalog_immutable_and_groups_differ(self):
        self.assertEqual(len(c._CATALOG['A']), 125)
        self.assertEqual(len(c._CATALOG['B']), 124)
        self.assertEqual(c.expected_entry('A',11)['sp'],'1.1.3')
        self.assertEqual(c.expected_entry('A',13)['sp'],'1.1.4')
        self.assertEqual(c.expected_entry('B',17)['sp'],'1.2.1')
        self.assertNotEqual(c.expected_entry('A',32)['sp'], c.expected_entry('B',32)['sp'])
        self.assertEqual(c._CATALOG['source_archive_sha256'], c.SOURCE_SHA)
        import re
        for group in ('A','B'):
            for lesson in range(1, len(c._CATALOG[group])+1):
                row=c.expected_entry(group,lesson)
                for fmt in ('word','pdf'):
                    self.assertRegex(row[fmt],r'^[0-9a-f]{64}$')

    def test_catalog_only_complete_verified_pairs(self):
        cfg={'account_backend':'supabase','supabase_url':'https://'+c.HOST,'supabase_key':'sb_secret_'+'z'*40}
        def meta(g,n,f):
            row=c.expected_entry(g,n)
            return {'kumpulan':g,'lesson':n,'format':f,'sp_code':row['sp'],
                    'sha256_hex':row[f],'source_archive_sha256':c.SOURCE_SHA,'approval_status':'CANARY_APPROVED'}
        complete=[meta('A',11,'word'),meta('A',11,'pdf'),meta('B',11,'word'),meta('B',11,'pdf')]
        partial=[meta('A',12,'word')]
        catalog=c.fetch_approved_catalog(cfg,opener=lambda req,timeout=12:Response(complete+partial))
        self.assertEqual(catalog,{'A':[11],'B':[11]})
        for bad in ([meta('A',11,'word'),meta('A',11,'word')],
                    [{**meta('A',11,'pdf'),'sha256_hex':'f'*64}],
                    [{**meta('A',11,'pdf'),'sp_code':'9.9.9'}]):
            with self.assertRaises(c.PilotUnavailable):
                c.fetch_approved_catalog(cfg,opener=lambda req,timeout=12,bad=bad:Response(bad))

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
        with patch.object(c, 'expected_entry', side_effect=self.real_expected):
            for g in ('A','B'):
                for n in (1,2,3):
                    for fmt,ext in (('word','docx'),('pdf','pdf')):
                        b=(PILOT/f'MATH_T1_{g}_LESSON{n:03d}.{ext}').read_bytes()
                        r=fake_row(g,n,fmt)
                        r.update(content_base64=base64.b64encode(b).decode(),byte_size=len(b),sha256_hex=sha256(b).hexdigest())
                        self.assertEqual(c.verify_private_row(r,g,n,fmt),b)
        self.assertIn('/api/kp2027/sk/tahun-1/matematik/available',c._PAGE)
        self.assertNotIn('<option value="10">',c._PAGE)

if __name__=='__main__':unittest.main()

class TestFlaskDownloadContract(unittest.TestCase):
    """Runs in production-like CI with Flask installed; offline containers skip."""
    def setUp(self):
        try:
            from flask import Flask
            import web.rph_delivery_quota
            import web_v1_telegram_auth_routes
            import web_v1_sessions
        except ImportError:
            self.skipTest('Flask/auth stack is not installed in this offline test runner')
        self.F = Flask
        self.config = {'account_backend':'supabase', 'supabase_url':'https://'+c.HOST,
                       'supabase_key':'sb_secret_'+'x'*40,
                       'CIKGULAJU_WEB_SESSION_SECRET':'z'*48}
        self.account={'authenticated':True,'telegram_user_id':123,'rakan_pembangun':True,
                      'free_remaining':10,'vip_until':None,'vip_expires_at':None}

    def _client(self, *, paid=True, asset=b'%PDF-1.7\n'+b'0'*1500):
        import web.rph_delivery_quota as quota
        import web_v1_telegram_auth_routes as auth
        import web_v1_sessions as sessions
        self.stack = [patch.object(auth,'_config',return_value=self.config),
                      patch.object(auth,'_lookup',return_value=self.account),
                      patch.object(sessions,'verify_session_ticket',return_value=123),
                      patch.object(quota,'has_active_paid_access',return_value=paid),
                      patch.object(quota,'authorize_rendered_document',return_value={'allowed':True,'remaining':9}),
                      patch.object(c,'fetch_private_document',return_value=asset),
                      # Synthetic bytes exercise auth/quota; real-layout tests own personalization.
                      patch.object(c,'personalize_approved_rph',side_effect=lambda data,fmt,fields:data)]
        self.mocks=[p.start() for p in self.stack]
        self.addCleanup(lambda:[p.stop() for p in reversed(self.stack)])
        app=self.F(__name__); app.testing=True
        app.register_blueprint(c.create_blueprint())
        client=app.test_client()
        try: client.set_cookie('cikgulaju_web_v1_session','session')
        except TypeError: client.set_cookie('localhost','cikgulaju_web_v1_session','session')
        return client

    def test_availability_login_and_no_quota_charge(self):
        client=self._client()
        with patch.object(c, 'fetch_approved_catalog',return_value={'A':[1,2,11],'B':[1,11]}) as feed:
            with patch.dict('os.environ',{c.FEATURE_FLAG:'1'}):
                res=client.get('/api/kp2027/sk/tahun-1/matematik/available')
                self.assertEqual(res.status_code,200)
                self.assertEqual(res.get_json()['groups']['A'],[1,2,11])
                self.assertEqual(self.mocks[4].call_count,0)  # no trial debit for inventory
                feed.assert_called_once()
                self.mocks[2].return_value=None
                res2=client.get('/api/kp2027/sk/tahun-1/matematik/available')
                self.assertEqual(res2.status_code,401)

    def test_no_publish_flag_remains_disabled(self):
        client=self._client()
        with patch.dict('os.environ',{c.FEATURE_FLAG:'0'}):
            r=client.post('/api/kp2027/sk/tahun-1/matematik/download',
                          json={'group':'A','lesson':1,'format':'pdf'},headers={'Origin':c.ORIGIN})
        self.assertEqual(r.status_code,503)

    def test_same_origin_and_logged_in_required(self):
        client=self._client()
        with patch.dict('os.environ',{c.FEATURE_FLAG:'1'}):
            no_origin=client.post('/api/kp2027/sk/tahun-1/matematik/download',
                                  json={'group':'A','lesson':1,'format':'pdf'})
            self.assertEqual(no_origin.status_code,403)
            self.mocks[2].return_value=None
            anonymous=client.post('/api/kp2027/sk/tahun-1/matematik/download',
                                  json={'group':'A','lesson':1,'format':'pdf'},headers={'Origin':c.ORIGIN})
            self.assertEqual(anonymous.status_code,401)

    def test_paid_download_and_non_paid_quota_reuse(self):
        client=self._client(paid=True)
        with patch.dict('os.environ',{c.FEATURE_FLAG:'1'}):
            r=client.post('/api/kp2027/sk/tahun-1/matematik/download',
                          json={'group':'A','lesson':1,'format':'pdf'},headers={'Origin':c.ORIGIN})
            self.assertEqual(r.status_code,200)
            self.assertIn('LESSON001.pdf',r.headers['Content-Disposition'])
            self.assertTrue(r.data.startswith(b'%PDF-'))
            self.assertNotIn('X-RPH-Trial-Remaining',r.headers)
        import web.rph_delivery_quota as quota
        self.mocks[3].return_value=False
        with patch.dict('os.environ',{c.FEATURE_FLAG:'1'}):
            r=client.post('/api/kp2027/sk/tahun-1/matematik/download',
                          json={'group':'A','lesson':1,'format':'pdf'},headers={'Origin':c.ORIGIN})
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.headers['X-RPH-Trial-Remaining'],'9')
