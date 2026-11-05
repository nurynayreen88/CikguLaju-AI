"""Synthetic and real-archive read-only API regression checks."""
import io
import json
import zipfile
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from wsgiref.util import setup_testing_defaults

from staging_gateway import make_gateway,from_environment,StagingConfigurationError
from test_bundle_reader import PIBundleReaderTest
from test_preview_reader import PreviewTests

TOKEN='x'*40

class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=TemporaryDirectory()
        cls.archive=Path(cls.temp.name)/'source.zip'
        cls.preview=Path(cls.temp.name)/'preview.zip'
        PIBundleReaderTest().make_fixture(cls.archive)
        # Add the six held statuses from the real staging catalog to synthetic test data.
        with zipfile.ZipFile(cls.archive) as z:
            files={name:z.read(name) for name in z.namelist()}
        catalog=json.loads(files['KATALOG/catalog.json'])
        held={(2,35),(6,6),(6,14),(6,18),(6,60),(6,117)}
        for rec in catalog:
            rec['rph_state']='TAHAN_SEMAKAN_KANDUNGAN' if (rec['tahun'],rec['lesson']) in held else 'CALON_UJIAN_GURU_DRAF'
        files['KATALOG/catalog.json']=json.dumps(catalog).encode('utf-8')
        with zipfile.ZipFile(cls.archive,'w') as z:
            for name,payload in files.items():z.writestr(name,payload)
        PreviewTests().create_synthetic_zip(cls.preview)
        cls.gateway=make_gateway(cls.archive,cls.preview,staging=True,token=TOKEN)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def call(self,path,query='',method='GET',secret=TOKEN,app=None):
        environ={};setup_testing_defaults(environ)
        environ.update(REQUEST_METHOD=method,PATH_INFO=path,QUERY_STRING=query)
        if secret is not None:environ['HTTP_AUTHORIZATION']='Bearer '+secret
        result=[]
        def start(status,headers):result.append((status,dict(headers)))
        raw=b''.join((app or type(self).gateway)(environ,start))
        return result[0][0],result[0][1],raw

    def test_fail_closed_without_mode_or_token(self):
        with self.assertRaises(StagingConfigurationError):make_gateway(self.archive,self.preview,token=TOKEN)
        with self.assertRaises(StagingConfigurationError):make_gateway(self.archive,self.preview,staging=True,token='too short')
        x=from_environment({})
        r,_,body=self.call('/api/pi/status',app=x)
        self.assertTrue(r.startswith('503'))
        self.assertIn(b'disabled',body)

    def test_auth_required_and_read_only(self):
        for key in (None,'wrong'):
            r,_,body=self.call('/api/pi/lesson','year=2&lesson=1',secret=key)
            self.assertTrue(r.startswith('403'))
            self.assertNotIn(b'lesson',body)
        r,_,_=self.call('/api/pi/status',method='POST')
        self.assertTrue(r.startswith('405'))

    def test_lesson_list_and_metadata(self):
        r,h,data=self.call('/api/pi/lessons','year=3')
        self.assertTrue(r.startswith('200'))
        self.assertIn(b'"total":147',data)
        self.assertIn(b'"has_preview":true',data)
        self.assertIn('no-store',h['Cache-Control'])
        r,_,data=self.call('/api/pi/lesson','year=2&lesson=35')
        self.assertTrue(r.startswith('200'))
        self.assertIn(b'"has_tasmi_guide":true',data)

    def test_preview_and_word_and_guide(self):
        r,h,data=self.call('/api/pi/preview','year=2&lesson=1')
        self.assertTrue(r.startswith('200'))
        self.assertEqual(h['Content-Type'],'application/pdf')
        self.assertTrue(data.startswith(b'%PDF-'))
        self.assertIn('inline',h['Content-Disposition'])
        r,h,data=self.call('/api/pi/word','year=2&lesson=1')
        self.assertTrue(r.startswith('200'))
        self.assertTrue(data.startswith(b'PK'))
        r,_,data=self.call('/api/pi/tasmi','year=2&lesson=35')
        self.assertTrue(r.startswith('200'))
        self.assertTrue(data.startswith(b'%PDF-'))
        r,_,data=self.call('/api/pi/tasmi','year=2&lesson=1')
        self.assertTrue(r.startswith('404'))

    def test_strict_year_lesson_and_invalid_paths(self):
        for q in ('year=1&lesson=1','year=6&lesson=999','year=2&lesson=1&lesson=2',
                  'year=../2&lesson=1','year=2&lesson=01a','year=2&lesson=0'):
            r,_,_=self.call('/api/pi/preview',q)
            self.assertTrue(r.startswith(('400','404')), q)
        r,_,_=self.call('/other','year=2&lesson=1')
        self.assertTrue(r.startswith('404'))

    def test_manifest_protection(self):
        r,_,d=self.call('/api/pi/status')
        self.assertTrue(r.startswith('200'))
        self.assertIn(b'"ready":0',d)
        self.assertIn(b'"publication":"STAGING_ONLY"',d)

    def test_actual_files_optional(self):
        a,b=os.getenv('PI_V5_ARCHIVE'),os.getenv('PI_V5_PREVIEW_ARCHIVE')
        if not(a and b):self.skipTest('Set PI_V5_ARCHIVE and PI_V5_PREVIEW_ARCHIVE for real files')
        gate=make_gateway(a,b,staging=True,token=TOKEN)
        for y,l in [(2,1),(3,145),(4,12),(5,124),(6,143)]:
            environ={};setup_testing_defaults(environ)
            environ['PATH_INFO']='/api/pi/preview';environ['QUERY_STRING']=f'year={y}&lesson={l}'
            environ['HTTP_AUTHORIZATION']='Bearer '+TOKEN
            out=[]
            body=b''.join(gate(environ,lambda s,h:out.append(s)))
            self.assertTrue(out[0].startswith('200'),(y,l,out[0]))
            self.assertTrue(body.startswith(b'%PDF-'))
        environ={};setup_testing_defaults(environ)
        environ.update(PATH_INFO='/api/pi/preview',QUERY_STRING='year=2&lesson=35',
                       HTTP_AUTHORIZATION='Bearer '+TOKEN)
        out=[]
        body=b''.join(gate(environ,lambda s,h:out.append(s)))
        self.assertTrue(out[0].startswith('423'))
        self.assertFalse(body.startswith(b'%PDF-'))
        for fmt, magic in [('pdf',b'%PDF-'),('docx',b'PK')]:
            e={};setup_testing_defaults(e)
            e.update(PATH_INFO='/api/pi/rpt',QUERY_STRING=f'year=6&format={fmt}',
                     HTTP_AUTHORIZATION='Bearer '+TOKEN)
            res=[];data=b''.join(gate(e,lambda s,h:res.append(s)))
            self.assertTrue(res[0].startswith('200'))
            self.assertTrue(data.startswith(magic))

if __name__=='__main__':unittest.main()