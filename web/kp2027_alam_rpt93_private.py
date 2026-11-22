"""Secure KP2027 Alam Year 1 RPT-session mapping and 29 private Word/PDF supplements.

No public binary archive or private browser URL. Release requires all 64 original
approved sources AND all 12 vetted QA ZIP parts in the private Supabase table.
The 2026 audit records 93 RPT sessions covering 83 exact SP in 64 source RPH.
"""
from __future__ import annotations
from base64 import b64decode
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, BadZipFile
import json
import re

from web.kp2027_math_canary_web import _settings, _headers, _NoRedirects

AUDIT=json.loads((Path(__file__).resolve().parents[1]/'audits/kp2027_alam_t1_rpt93_source64_83sp_qa29_20261122.json').read_text(encoding='utf-8'))
CATALOG=json.loads(Path(__file__).with_name('kp2027_alam_v10_catalog.json').read_text(encoding='utf-8'))
LABELS=json.loads(Path(__file__).with_name('kp2027_pdp_source_labels_v1.json').read_text(encoding='utf-8'))['sp_labels']['ALAM']
SOURCE_ID='ALAM_RPT93_29_v4'
SOURCE_SHA='9ca8ef259c83b2551f62e03b019c8c72cb03d267b1f600e19eda8aa5dbf14c1f'
SOURCE_BYTES=2297418
SOURCE_PARTS=12
SOURCE_B64_CHARS=3063224
SOURCE_ARCHIVE='CIKGULAJU_KP2027_ALAM_T1_29_RPH_REFLEKSI_V4_20261122.zip'
TABLE='kp2027_alam_rpt93_zip_parts'
QA_TITLES={
 '1.1.1':'Anggota Tubuh Saya','1.1.4':'Deria dan Anggota Tubuh',
 '1.1.9':'Lagu Keluarga Saya','1.1.14':'Kasih Sayang dalam Keluarga',
 '2.1.2':'Amalan Kebersihan dan Kepentingannya',
 '2.1.3':'Demonstrasi Kebersihan Diri','2.1.8':'Kepentingan Hidangan Utama',
 '2.1.10':'Bina Model Makanan','2.1.13':'Postur Badan yang Betul',
 '3.1.3':'Maklumat Peribadi Perlu Dilindungi','3.1.5':'Kenali Sentuhan Tidak Selamat',
 '3.1.7':'Tindakan Ketika Tidak Selamat','3.1.11':'Karya Pasukan Keselamatan',
 '4.1.1':'Hidup atau Bukan Hidup','4.1.3':'Keperluan Asas Hidupan',
 '4.1.8':'Keperluan dan Kehendak','4.1.9':'Bunyi di Sekeliling',
 '4.1.12':'Gabungan Bunyi daripada Objek','4.1.17':'Lakaran Emosi',
 '4.1.18':'Lagu Tentang Emosi','5.1.3':'Aktiviti Terang dan Gelap',
 '5.1.7':'Kraf Menggunakan Cahaya','5.1.8':'Kraf Cahaya Saya',
 '5.2.3':'Mercu Tanda Dunia','5.2.7':'Langkah Bina Model Mercu Tanda',
 '5.2.8':'Pameran Mercu Tanda','6.1.3':'Rancang Penyelesaian Masalah',
 '6.2.3':'Persediaan Pembentangan Produk',
}
MAP={m['rpt_pdp']:m for m in AUDIT['mappings']}
QA={n for n,m in MAP.items() if m['mapping_reason']!='existing_source'}
if (set(MAP)!=set(range(1,94)) or len(QA)!=29
        or len({m['sp'] for m in MAP.values()})!=83
        or set(m['source_rph'] for m in MAP.values() if m['mapping_reason']=='existing_source')!=set(range(1,65))
        or AUDIT['checks']['qa_split_sessions']!=20
        or AUDIT['checks']['qa_reinforcement_sessions']!=9):
    raise RuntimeError('Unverified Alam RPT93 source mapping')
for n,m in MAP.items():
    src=CATALOG['items'].get(str(m['source_rph']))
    if (not src or m['sp'] not in src['codes']
            or m['source_codes']!=src['codes']
            or (n in QA)!=(m['draft_qa_rph']==n)):
        raise RuntimeError('Alam RPT93 source SP mapping mismatch')

class SupplementUnavailable(ValueError):
    pass

def valid_rpt_lesson(lesson,fmt):
    if type(lesson) is not int or lesson not in MAP or fmt not in ('word','pdf'):
        raise ValueError('Invalid Alam RPT lesson or format')
    return MAP[lesson]

def _retrieve(config,params,max_bytes=3800000,opener=None):
    url,key=_settings(config)
    req=Request(url+'/rest/v1/'+TABLE+'?'+urlencode(params),headers=_headers(key),method='GET')
    do_open=opener or build_opener(_NoRedirects()).open
    try:
        with do_open(req,timeout=15) as response:
            if getattr(response,'status',None)!=200:
                raise SupplementUnavailable('Private supplement unavailable')
            raw=response.read(max_bytes+1)
        if len(raw)>max_bytes:raise SupplementUnavailable('Private supplement oversized')
        rows=json.loads(raw)
    except (HTTPError,URLError,OSError,TypeError,ValueError) as exc:
        raise SupplementUnavailable('Private supplement inventory unavailable') from exc
    if not isinstance(rows,list):raise SupplementUnavailable('Invalid private supplement inventory')
    return rows

def _check_meta(rows,has_content=False):
    if not isinstance(rows,list) or len(rows)!=SOURCE_PARTS:
        raise SupplementUnavailable('Alam RPT93 requires 12 approved ZIP parts')
    found=set()
    for row in rows:
        if (not isinstance(row,dict) or row.get('source_id')!=SOURCE_ID
                or row.get('archive_name')!=SOURCE_ARCHIVE
                or row.get('total_parts')!=SOURCE_PARTS
                or row.get('archive_bytes')!=SOURCE_BYTES
                or row.get('archive_sha256')!=SOURCE_SHA
                or row.get('approval_status')!='CANARY_APPROVED'
                or type(row.get('part_index')) is not int
                or row['part_index'] in found or not 0<=row['part_index']<SOURCE_PARTS):
            raise SupplementUnavailable('Alam RPT93 source metadata failed verification')
        if has_content and (not isinstance(row.get('content_base64'),str)
                            or len(row['content_base64'])>262144):
            raise SupplementUnavailable('Alam ZIP chunk invalid')
        found.add(row['part_index'])
    if found!=set(range(SOURCE_PARTS)):
        raise SupplementUnavailable('Alam RPT93 source archive parts incomplete')
    return True

def supplement_inventory_approved(config,opener=None):
    rows=_retrieve(config,{'select':'source_id,part_index,total_parts,archive_name,archive_sha256,archive_bytes,approval_status',
         'source_id':'eq.'+SOURCE_ID,'approval_status':'eq.CANARY_APPROVED','order':'part_index.asc','limit':'12'},
         max_bytes=7500,opener=opener)
    return _check_meta(rows)

def fetch_supplement(config,rpt_no,fmt,opener=None):
    m=valid_rpt_lesson(rpt_no,fmt)
    if rpt_no not in QA:raise SupplementUnavailable('Not a supplemental Alam RPH')
    rows=_retrieve(config,{'select':'source_id,part_index,total_parts,archive_name,archive_sha256,archive_bytes,approval_status,content_base64',
         'source_id':'eq.'+SOURCE_ID,'approval_status':'eq.CANARY_APPROVED','order':'part_index.asc','limit':'12'},
         max_bytes=3600000,opener=opener)
    _check_meta(rows,True)
    chunks=''.join(row['content_base64'] for row in sorted(rows,key=lambda r:r['part_index']))
    if len(chunks)!=SOURCE_B64_CHARS:
        raise SupplementUnavailable('Alam RPT93 supplement size mismatch')
    try:blob=b64decode(chunks,validate=True)
    except (ValueError,TypeError) as exc:raise SupplementUnavailable('Private Alam supplement encoding invalid') from exc
    if len(blob)!=SOURCE_BYTES or sha256(blob).hexdigest()!=SOURCE_SHA:
        raise SupplementUnavailable('Private Alam supplement checksum mismatch')
    directory,ext=('Word','docx') if fmt=='word' else ('PDF','pdf')
    filename=f'CIKGULAJU_ALAM_KP2027_T1_RPT_PDP{rpt_no:03d}.{ext}'
    expected_name=f'{directory}/{filename}'
    try:
        with ZipFile(BytesIO(blob)) as z:
            if len(z.namelist())!=61:raise SupplementUnavailable('Unexpected Alam archive entries')
            manifest=json.loads(z.read('MANIFEST_QA_ONLY.json'))
            if (manifest.get('version')!='2026-11-22-v4'
                or len(manifest.get('entries',[]))!=29
                or manifest.get('source_dk_pdf_id')!='1FO2UkgGeDEDYwiwlfpjc1SFfNOw-pcrs'):
                raise SupplementUnavailable('Unverified Alam manifest')
            academic=next((e for e in manifest['entries'] if e.get('number')==rpt_no),None)
            if not isinstance(academic,dict) or academic.get('sp')!=m['sp']:
                raise SupplementUnavailable('Alam supplemental SP failed verification')
            listed=manifest['files'].get(filename)
            if not isinstance(listed,dict):raise SupplementUnavailable('Unlisted Alam document')
            data=z.read(expected_name)
    except (BadZipFile,KeyError,ValueError,TypeError) as exc:
        raise SupplementUnavailable('Alam supplemental file unavailable') from exc
    if (len(data)!=listed['bytes'] or sha256(data).hexdigest()!=listed['sha256']
       or not data.startswith(b'%PDF-' if fmt=='pdf' else b'PK\x03\x04')):
        raise SupplementUnavailable('Alam supplemental file SHA mismatch')
    return data

def make_rpt_inventory(approved_source_numbers):
    if set(approved_source_numbers)!=set(range(1,65)):
        raise SupplementUnavailable('All 64 approved original RPH required for RPT93')
    items=[]
    for n in range(1,94):
        entry=MAP[n]
        src=CATALOG['items'][str(entry['source_rph'])]
        label=LABELS.get(src['sp'])
        if not isinstance(label,dict) or not label.get('unit') or not label.get('tajuk'):
            raise SupplementUnavailable('Original Alam title not source-verified')
        if n in QA:
            title=QA_TITLES.get(entry['sp'])
            if not title:raise SupplementUnavailable('Supplemental title not mapped')
            if entry['mapping_reason']=='qa_reinforcement':title='Pengukuhan: '+title
        else:title=label['tajuk']
        item={'no':n,'unit':label['unit'],'tajuk':title,'sp':entry['sp']}
        if any(len(item[k])>150 for k in ('unit','tajuk')):
            raise SupplementUnavailable('Alam title too long')
        items.append(item)
    return items
