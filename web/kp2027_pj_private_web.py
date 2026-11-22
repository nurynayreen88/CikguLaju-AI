"""CikguLaju KP2027 Tahun 1 Pendidikan Jasmani: private, manifest-pinned RPH.

Serve only approved source ZIP parts from private Supabase rows after a confirmed
login, classroom request validation, SHA-256 verification and shared trial gate.
The sources contain no per-user information. Free trials use the existing atomic
RP H debit AFTER the private and personalized document bytes are verified.
"""
from __future__ import annotations

from base64 import b64decode
from hashlib import sha256
from io import BytesIO
from json import loads as json_loads
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, BadZipFile
import os, json, re

ORIGIN="https://cikgulaju-web.onrender.com"
FEATURE_FLAG="CIKGULAJU_KP2027_PJ_PRIVATE_ENABLED"
FORMATS={"word":("docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
         "pdf":("pdf","application/pdf")}
CATALOG=json.loads(Path(__file__).with_name('kp2027_pj_t1_catalog.json').read_text(encoding='utf-8'))
assert sum(CATALOG['groups'].values())==127 and set(CATALOG['groups'])=={'A','B'}
for group,count in CATALOG['groups'].items():
    assert [x['no'] for x in CATALOG['items'][group]]==list(range(1,count+1))

class PrivateRphUnavailable(ValueError):
    pass

class NoRedirects(__import__('urllib.request',fromlist=['HTTPRedirectHandler']).HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise PrivateRphUnavailable('Unexpected redirect')

def _settings(config):
    base=str(config.get('supabase_url') or '').rstrip('/')
    key=config.get('supabase_key')
    if not base.startswith('https://') or not key or len(key)<20:
        raise PrivateRphUnavailable('Private database unavailable')
    return base,key

def _headers(key):
    h={'apikey':key,'Accept':'application/json'}
    if not key.startswith('sb_secret_'):
        h['Authorization']='Bearer '+key
    return h

def select_group(group,lesson,fmt):
    if group not in ('A','B') or type(lesson) is not int or not 1<=lesson<=CATALOG['groups'][group] or fmt not in FORMATS:
        raise ValueError('Invalid curriculum selection')
    return group,lesson,fmt,(lesson-1)//16+1

def _get_rows(config, params, max_bytes=2000000, opener=None):
    base,key=_settings(config)
    req=Request(base+'/rest/v1/kp2027_pj_private_batches?'+urlencode(params),headers=_headers(key),method='GET')
    call=opener or build_opener(NoRedirects()).open
    try:
        with call(req,timeout=12) as response:
            if getattr(response,'status',None)!=200:
                raise PrivateRphUnavailable('Private inventory unavailable')
            raw=response.read(max_bytes+1)
        if len(raw)>max_bytes:raise PrivateRphUnavailable('Private inventory exceeds limit')
        data=json_loads(raw)
    except (HTTPError,URLError,OSError,ValueError,TypeError) as exc:
        raise PrivateRphUnavailable('Private inventory unavailable') from exc
    if not isinstance(data,list):raise PrivateRphUnavailable('Invalid database response')
    return data

def _catalog_batch(group,batch):
    return CATALOG['batches'][f'{group}{batch}']

def approved_inventory(config,opener=None):
    rows=_get_rows(config,{'select':'group_code,batch_index,first_pdp,last_pdp,archive_bytes,archive_sha256,approval_status',
                           'approval_status':'eq.CANARY_APPROVED','order':'group_code.asc,batch_index.asc','limit':'8'},5000,opener)
    if len(rows)>8:raise PrivateRphUnavailable('Too many approved source archives')
    permitted={'A':set(),'B':set()};seen=set()
    for row in rows:
        if not isinstance(row,dict):raise PrivateRphUnavailable('Unverified metadata')
        group,batch=row.get('group_code'),row.get('batch_index')
        if group not in permitted or type(batch) is not int or not 1<=batch<=4 or (group,batch) in seen:
            raise PrivateRphUnavailable('Malformed private curriculum metadata')
        seen.add((group,batch))
        want=_catalog_batch(group,batch)
        if (row.get('first_pdp')!=want['first'] or row.get('last_pdp')!=want['last'] or
                row.get('archive_bytes')!=want['size'] or row.get('archive_sha256')!=want['sha256'] or
                row.get('approval_status')!='CANARY_APPROVED'):
            raise PrivateRphUnavailable('Source archive metadata mismatch')
        permitted[group].update(range(want['first'],want['last']+1))
    groups={g:sorted(x) for g,x in permitted.items()}
    entries={g:[{k:item[k] for k in ('no','unit','tajuk','sp')} for item in CATALOG['items'][g]
                if item['no'] in permitted[g]] for g in groups}
    return groups,entries

def private_document(config,group,lesson,fmt,opener=None):
    group,lesson,fmt,batch=select_group(group,lesson,fmt)
    rows=_get_rows(config,{'select':'group_code,batch_index,first_pdp,last_pdp,archive_bytes,archive_sha256,archive_name,approval_status,archive_b64',
                           'group_code':'eq.'+group,'batch_index':'eq.'+str(batch),
                           'approval_status':'eq.CANARY_APPROVED','limit':'2'},1900000,opener)
    if len(rows)!=1:raise PrivateRphUnavailable('Private RPH source not approved')
    row=rows[0];want=_catalog_batch(group,batch)
    if (row.get('group_code')!=group or row.get('batch_index')!=batch or
        row.get('first_pdp')!=want['first'] or row.get('last_pdp')!=want['last'] or
        row.get('archive_bytes')!=want['size'] or row.get('archive_sha256')!=want['sha256'] or
        row.get('archive_name')!=want['name'] or row.get('approval_status')!='CANARY_APPROVED'):
        raise PrivateRphUnavailable('Private ZIP metadata mismatch')
    encoded=row.get('archive_b64')
    if not isinstance(encoded,str) or len(encoded)>1800000:
        raise PrivateRphUnavailable('Private ZIP payload too large')
    try:
        payload=b64decode(encoded,validate=True)
    except (ValueError,TypeError) as exc:
        raise PrivateRphUnavailable('Invalid source encoding') from exc
    if len(payload)!=want['size'] or sha256(payload).hexdigest()!=want['sha256']:
        raise PrivateRphUnavailable('Private archive SHA mismatch')
    ext,_=FORMATS[fmt]
    entry=f'{"WORD" if fmt=="word" else "PDF"}/CIKGULAJU_RPH_KP2027_PJ_T1_{group}_PDP{lesson:03d}.{ext}'
    try:
        with ZipFile(BytesIO(payload)) as archive:
            if len(archive.namelist())!=2*(want['last']-want['first']+1)+1:
                raise PrivateRphUnavailable('Private archive item count invalid')
            manifest=json_loads(archive.read('MANIFEST_QA.json'))
            if (manifest.get('group')!=group or manifest.get('first_lesson')!=want['first'] or
                 manifest.get('last_lesson')!=want['last'] or not isinstance(manifest.get('files'),dict)):
                raise PrivateRphUnavailable('Private archive manifest invalid')
            meta=manifest['files'].get(entry)
            if not isinstance(meta,dict) or not 20000<meta.get('bytes',0)<250000:
                raise PrivateRphUnavailable('Private file not listed')
            file_bytes=archive.read(entry)
    except (BadZipFile,KeyError,ValueError,TypeError) as exc:
        raise PrivateRphUnavailable('Private RPH archive unreadable') from exc
    if len(file_bytes)!=meta['bytes'] or sha256(file_bytes).hexdigest()!=meta['sha256']:
        raise PrivateRphUnavailable('Private document SHA mismatch')
    if not file_bytes.startswith(b'PK\x03\x04' if fmt=='word' else b'%PDF-'):
        raise PrivateRphUnavailable('Invalid private file signature')
    return file_bytes


def personalize_pj(original, fmt, data):
    """Only populate user fields, never replace subject or standards."""
    from web.kp2027_pilot_teacher_fields import (
        parse_teacher_fields, TeacherFieldError, _reflection_candidates,
        _word_success_criterion, _pdf_success_criterion, _pdf_safe_reflection,
    )
    fields=parse_teacher_fields(data)
    labels=('Kelas:','Tarikh:','Masa:','Bil. Murid:')
    if fmt=='word':
        from docx import Document
        from docx.shared import Pt
        d=Document(BytesIO(original))
        if len(d.tables)!=1 or len(d.tables[0].rows)!=15 or d.tables[0].cell(0,0).text!='Maklumat PdP':
            raise TeacherFieldError('Templat Word PJ tidak sepadan')
        header=d.tables[0].cell(0,1)
        if not all(k in header.text for k in labels):raise TeacherFieldError('Ruang maklumat Word tiada')
        content='    '.join(x+(' '+fields[x] if fields[x] else '') for x in labels)
        header.text=content
        for p in header.paragraphs:
            for run in p.runs:run.font.size=Pt(7.6)
        if 'Refleksi' not in d.tables[0].cell(14,0).text:raise TeacherFieldError('Ruang refleksi tiada')
        refl=(fields['_reflection'] if fields['_reflection_mode']=='manual' else
              _reflection_candidates(_word_success_criterion(d))[0])
        reflection=d.tables[0].cell(14,1);reflection.text=refl
        for p in reflection.paragraphs:
            for run in p.runs:run.font.size=Pt(7.6)
        out=BytesIO();d.save(out);return out.getvalue()
    if fmt!='pdf':raise TeacherFieldError('Format RPH tidak sah')
    import fitz
    d=fitz.open(stream=original,filetype='pdf')
    try:
        if d.page_count!=1:raise TeacherFieldError('RPH PDF asal bukan satu halaman')
        page=d[0]
        for label in labels:
            value=fields[label]
            if not value:continue
            if not value.isascii():
                raise TeacherFieldError('Gunakan aksara asas untuk nama kelas dalam PDF')
            anchors=page.search_for(label)
            if len(anchors)!=1 or not 85<anchors[0].y0<150 or not 385<anchors[0].x0<420:
                raise TeacherFieldError('Ruang maklumat PDF di luar kawasan dijangka')
            pos=anchors[0]; rect=fitz.Rect(pos.x1+4,pos.y0-1,565,pos.y1+2)
            if page.insert_textbox(rect,value,fontname='helv',fontsize=7.2,lineheight=1.0)<0:
                raise TeacherFieldError('Nama kelas terlalu panjang untuk PDF')
        reflection=next((x for x in page.search_for('Refleksi') if x.x0<120 and 620<x.y0<770),None)
        if reflection is None:raise TeacherFieldError('Ruang refleksi PDF tidak sah')
        footers=[r for r in page.search_for('Rujukan DK rasmi') if r.x0<130 and r.y0>reflection.y1]
        if len(footers)!=1:raise TeacherFieldError('Ruang penutup PDF tidak sah')
        area=fitz.Rect(147,reflection.y0-2,565,footers[0].y0-4)
        candidates=((fields['_reflection'],) if fields['_reflection_mode']=='manual'
                    else _reflection_candidates(_pdf_success_criterion(page)))
        chosen=None
        font_size=None
        for candidate in candidates:
            safe=_pdf_safe_reflection(candidate)
            for size in (8.1,7.7,7.2,6.7,6.2,5.8):
                scratch=fitz.open()
                sp=scratch.new_page(width=page.rect.width,height=page.rect.height)
                val=sp.insert_textbox(area,safe,fontname='helv',fontsize=size,lineheight=1.0)
                scratch.close()
                if val>=0:
                    chosen=safe; font_size=size;break
            if chosen is not None:break
        if chosen is None:raise TeacherFieldError('Refleksi terlalu panjang untuk PDF; ringkaskan atau gunakan Word.')
        page.add_redact_annot(area,fill=(1,1,1),cross_out=False)
        page.apply_redactions(images=0,graphics=0,text=0)
        if page.insert_textbox(area,chosen,fontname='helv',fontsize=font_size,lineheight=1.0)<0:
            raise TeacherFieldError('Refleksi tidak muat')
        return d.tobytes(garbage=4,deflate=True)
    finally:
        d.close()


def create_blueprint():
    from flask import Blueprint,jsonify,request,send_file
    from web.kp2027_pilot_teacher_fields import EXTRA_FIELDS,TeacherFieldError
    from web.kp2027_math_canary_web import debit_shared_trial
    from web.rph_delivery_quota import authorize_rendered_document,has_active_paid_access
    from web_v1_telegram_auth_routes import COOKIE,_config,_lookup
    from web_v1_sessions import verify_session_ticket
    bp=Blueprint('kp2027_pj_private',__name__)

    @bp.after_request
    def secure_headers(response):
        response.headers['Cache-Control']='no-store, private'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Vary']='Cookie'
        return response

    def denied(message,status,code):return jsonify({'error':message,'code':code}),status

    def account_for_request():
        config=_config()
        if not config or config.get('account_backend')!='supabase':
            return None,None,denied('Semakan akaun Web belum tersedia.',503,'LOGIN_BACKEND_UNAVAILABLE')
        uid=verify_session_ticket(request.cookies.get(COOKIE),config['CIKGULAJU_WEB_SESSION_SECRET'])
        if type(uid) is not int or uid<=0:return None,None,denied('Sila log masuk terlebih dahulu.',401,'AUTH_REQUIRED')
        try:account=_lookup(config,uid)
        except Exception:return None,None,denied('Semakan akaun belum tersedia.',503,'ACCOUNT_LOOKUP_FAILED')
        if (not isinstance(account,dict) or account.get('authenticated') is not True or account.get('telegram_user_id')!=uid):
            return None,None,denied('Akaun belum disahkan.',403,'ACCOUNT_NOT_VERIFIED')
        return config,account,None

    @bp.get('/api/kp2027/sk/tahun-1/pendidikan-jasmani/available')
    def available():
        if os.environ.get(FEATURE_FLAG)!='1':return denied('Bahan PJ KP2027 belum diaktifkan.',503,'PJ_DISABLED')
        config,account,error=account_for_request()
        if error is not None:return error
        try:groups,items=approved_inventory(config)
        except PrivateRphUnavailable:return denied('Senarai PJ belum dapat disahkan.',503,'PJ_INVENTORY_UNAVAILABLE')
        return jsonify({'groups':groups,'items':items,'source':'kp2027-pj-v12-sha-pinned'})

    @bp.post('/api/kp2027/sk/tahun-1/pendidikan-jasmani/download')
    def download():
        if os.environ.get(FEATURE_FLAG)!='1':return denied('Penerbitan PJ KP2027 belum diaktifkan.',503,'PJ_DISABLED')
        if request.headers.get('Origin')!=ORIGIN:return denied('Permintaan perlu dibuat dari Web CikguLaju.',403,'ORIGIN_REQUIRED')
        if not request.is_json or not 0<(request.content_length or 0)<=1024:
            return denied('Pilihan PdP tidak sah.',400,'INVALID_REQUEST')
        data=request.get_json(silent=True)
        if (not isinstance(data,dict) or not {'group','lesson','format'}.issubset(data) or
            set(data)-{'group','lesson','format'}-EXTRA_FIELDS):
            return denied('Maklumat RPH tidak lengkap.',400,'INVALID_SELECTION')
        try:group,lesson,fmt,_=select_group(data['group'],data['lesson'],data['format'])
        except ValueError:return denied('PdP PJ belum tersedia.',404,'LESSON_NOT_AVAILABLE')
        config,account,error=account_for_request()
        if error is not None:return error
        paid=has_active_paid_access(account)
        if not paid and (type(account.get('free_remaining')) is not int or not 0<=account['free_remaining']<=10):
            return denied('Baki janaan percuma tidak dapat disahkan.',503,'TRIAL_UNVERIFIED')
        if not paid and account['free_remaining']==0:
            return denied('10 janaan percuma telah habis. Aktifkan langganan.',403,'FREE_TRIAL_EXHAUSTED')
        try:doc=private_document(config,group,lesson,fmt)
        except PrivateRphUnavailable:return denied('RPH PJ masih disemak atau belum tersedia.',503,'PJ_ASSET_UNAVAILABLE')
        try:doc=personalize_pj(doc,fmt,{key:data[key] for key in EXTRA_FIELDS if key in data})
        except TeacherFieldError as exc:return denied(str(exc),400,'INVALID_TEACHER_FIELDS')
        remaining=None
        if not paid:
            try:
                result=authorize_rendered_document(account,account['telegram_user_id'],doc,
                    config['supabase_url'],config['supabase_key'],debit=debit_shared_trial)
            except Exception:return denied('Semakan kuota tidak dapat dipastikan; sila semak baki.',503,'TRIAL_CHARGE_UNCONFIRMED')
            if not result['allowed']:return denied('Kuota RPH percuma telah habis.',403,'FREE_TRIAL_EXHAUSTED')
            remaining=result['remaining']
        ext,mime=FORMATS[fmt]
        response=send_file(BytesIO(doc),mimetype=mime,as_attachment=True,
          download_name=f'CIKGULAJU_KP2027_PJ_T1_{group}_PDP{lesson:03d}.{ext}',conditional=False)
        if remaining is not None:response.headers['X-RPH-Trial-Remaining']=str(remaining)
        return response

    return bp
