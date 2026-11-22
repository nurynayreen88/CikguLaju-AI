"""KP2027 Alam 93-RPT private supplement and exact SP mapping regression."""
from base64 import b64encode
from hashlib import sha256
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED
import json
import unittest

from web import kp2027_alam_rpt93_private as r


class Response:
    status=200
    def __init__(self,rows,status=200):self.data=json.dumps(rows).encode();self.status=status
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.data[:n]

class AlamRPT93Tests(unittest.TestCase):
    def setUp(self):
        self.config={'supabase_url':'https://private.example.supabase.co','supabase_key':'sb_secret_'+'x'*40}

    def test_all_93_exact_rpt_sp_mappings(self):
        self.assertEqual(len(r.MAP),93)
        self.assertEqual(len(r.QA),29)
        self.assertEqual(len({x['sp'] for x in r.MAP.values()}),83)
        self.assertEqual(sum(x['mapping_reason']=='qa_split' for x in r.MAP.values()),20)
        self.assertEqual(sum(x['mapping_reason']=='qa_reinforcement' for x in r.MAP.values()),9)
        self.assertEqual({x['source_rph'] for x in r.MAP.values() if x['mapping_reason']=='existing_source'},set(range(1,65)))
        for n,m in r.MAP.items():
            self.assertEqual(m['rpt_pdp'],n)
            self.assertIn(m['sp'],r.CATALOG['items'][str(m['source_rph'])]['codes'])
        self.assertEqual(r.valid_rpt_lesson(93,'pdf')['sp'],'6.2.4')
        for bad in (0,94,'2',True,None):
            with self.assertRaises(ValueError):r.valid_rpt_lesson(bad,'pdf')

    def test_93_catalog_only_with_full_64_approved_origins(self):
        with self.assertRaises(r.SupplementUnavailable):r.make_rpt_inventory(list(range(1,64)))
        items=r.make_rpt_inventory(list(range(1,65)))
        self.assertEqual([x['no'] for x in items],list(range(1,94)))
        self.assertEqual([x['sp'] for x in items],[r.MAP[i]['sp'] for i in range(1,94)])
        self.assertEqual(items[4]['sp'],'1.1.4')
        self.assertIn('Deria',items[4]['tajuk'])
        self.assertTrue(items[1]['tajuk'].startswith('Pengukuhan:'))
        self.assertTrue(all(0<len(x['unit'])<=150 and 0<len(x['tajuk'])<=150 for x in items))

    def test_reject_qa_hold_or_partial_archive(self):
        rows=[{'source_id':r.SOURCE_ID,'part_index':i,'total_parts':r.SOURCE_PARTS,
               'archive_name':r.SOURCE_ARCHIVE,'archive_sha256':r.SOURCE_SHA,
               'archive_bytes':r.SOURCE_BYTES,'approval_status':'CANARY_APPROVED'}
              for i in range(r.SOURCE_PARTS)]
        self.assertTrue(r._check_meta(rows))
        for bad in (rows[:-1],[{**rows[0],'approval_status':'QA_HOLD'},*rows[1:]],
                    [{**rows[0],'archive_sha256':'0'*64},*rows[1:]],
                    [{**rows[0],'part_index':1},*rows[1:]]):
            with self.assertRaises(r.SupplementUnavailable):r._check_meta(bad)
        with patch.object(r,'_retrieve',return_value=rows):
            self.assertTrue(r.supplement_inventory_approved(self.config))

    def test_private_zip_manifest_exact_source_hash_and_two_formats(self):
        entries=[]
        files={}
        source={}
        for no in sorted(r.QA):
            entries.append({'number':no,'sp':r.MAP[no]['sp']})
            for ext,prefix in (('docx',b'PK\x03\x04'),('pdf',b'%PDF-1.7\n')):
                filename=f'CIKGULAJU_ALAM_KP2027_T1_RPT_PDP{no:03d}.{ext}'
                raw=prefix+(f'private-{no}-{ext}'.encode()*100)
                source[('Word' if ext=='docx' else 'PDF')+'/'+filename]=raw
                files[filename]={'bytes':len(raw),'sha256':sha256(raw).hexdigest()}
        manifest={'version':'2026-11-22-v4','source_dk_pdf_id':'1FO2UkgGeDEDYwiwlfpjc1SFfNOw-pcrs',
                  'entries':entries,'files':files}
        with BytesIO() as out:
            with ZipFile(out,'w',ZIP_DEFLATED) as z:
                z.writestr('BACA_DULU.txt','QA')
                z.writestr('PADANAN_RPT_93_PDP.json','{}')
                z.writestr('MANIFEST_QA_ONLY.json',json.dumps(manifest))
                for name,data in source.items():z.writestr(name,data)
            blob=out.getvalue()
        self.assertEqual(len(source),58)
        b64=b64encode(blob).decode()
        part_size=((len(b64)//12)+4)//4*4
        rows=[]
        chunks=[b64[i*part_size:(i+1)*part_size] for i in range(11)]
        chunks.append(b64[11*part_size:])
        self.assertEqual(len(chunks),12)
        for i,part in enumerate(chunks):
            rows.append({'source_id':r.SOURCE_ID,'part_index':i,'total_parts':12,
               'archive_name':r.SOURCE_ARCHIVE,'archive_sha256':sha256(blob).hexdigest(),
               'archive_bytes':len(blob),'approval_status':'CANARY_APPROVED',
               'content_base64':part})
        with patch.multiple(r,SOURCE_SHA=sha256(blob).hexdigest(),SOURCE_BYTES=len(blob),SOURCE_B64_CHARS=len(b64)):
            with patch.object(r,'_retrieve',return_value=rows):
                self.assertEqual(r.fetch_supplement(self.config,5,'word'),source['Word/CIKGULAJU_ALAM_KP2027_T1_RPT_PDP005.docx'])
                self.assertEqual(r.fetch_supplement(self.config,5,'pdf'),source['PDF/CIKGULAJU_ALAM_KP2027_T1_RPT_PDP005.pdf'])
            with patch.object(r,'_retrieve',return_value=[{**rows[0],'content_base64':'corrupt'},*rows[1:]]):
                with self.assertRaises(r.SupplementUnavailable):r.fetch_supplement(self.config,5,'pdf')

if __name__=='__main__':unittest.main()
