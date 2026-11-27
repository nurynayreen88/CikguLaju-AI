"""Quota-gated private KP2027 Year-1 Alam dan Manusia downloads.

One canonical Word/PDF file per Lesson is shared by Kumpulan A and B because
these RPH contain no school-specific dates. Only QA-approved Word+PDF pairs
appear in the authenticated catalog. All source bytes live in Supabase only.
"""
from __future__ import annotations

import base64
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from web.kp2027_math_canary_web import (
    HOST, ORIGIN, FORMATS, PilotUnavailable, _NoRedirects, _headers,
    _settings, _document, debit_shared_trial,
)

SOURCE_SHA = 'b1ae8dcab0894bacc894d7fb310ff5ece27a1077e84846a64a86a61235d3a8ef'
FEATURE_FLAG = 'CIKGULAJU_KP2027_ALAM_CANARY_ENABLED'
CATALOG = json.loads(Path(__file__).with_name('kp2027_alam_v10_catalog.json').read_text(encoding='utf-8'))
if (CATALOG.get('subject') != 'ALAM' or CATALOG.get('source_archive_sha256') != SOURCE_SHA
        or CATALOG.get('lesson_count') != 64 or len(CATALOG.get('items',{})) != 64):
    raise RuntimeError('Alam dan Manusia verified curriculum catalog unavailable')


def expected_entry(lesson):
    if type(lesson) is not int or not 1 <= lesson <= 64:
        raise ValueError('Invalid Alam Lesson')
    item = CATALOG['items'].get(str(lesson))
    if (not isinstance(item, dict) or not isinstance(item.get('codes'),list)
            or not item['codes'] or len(item['codes'])>2 or item.get('sp')!=item['codes'][0]):
        raise ValueError('No verified Alam curriculum mapping')
    return item


def valid_selection(lesson, fmt):
    if fmt not in FORMATS:
        raise ValueError('Format not available')
    expected_entry(lesson)
    return lesson, fmt


def verify_private_row(row, lesson, fmt):
    valid_selection(lesson, fmt)
    expected=expected_entry(lesson)
    if (not isinstance(row,dict) or row.get('subject')!='ALAM' or row.get('kumpulan')!='A'
            or type(row.get('lesson')) is not int or row['lesson']!=lesson or row.get('format')!=fmt
            or row.get('sp_code')!=expected['sp'] or row.get('approval_status')!='CANARY_APPROVED'
            or row.get('source_archive_sha256')!=SOURCE_SHA):
        raise PilotUnavailable('Alam RPH not approved')
    try:
        blob=base64.b64decode(row['content_base64'],validate=True)
    except (TypeError,ValueError,base64.binascii.Error) as exc:
        raise PilotUnavailable('Alam RPH bytes corrupt') from exc
    if (type(row.get('byte_size')) is not int or row['byte_size']!=len(blob)
            or row['byte_size']!=expected.get(fmt+'_bytes')):
        raise PilotUnavailable('Alam RPH size mismatch')
    digest=row.get('sha256_hex')
    if (not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest)
            or digest!=expected[fmt] or sha256(blob).hexdigest()!=digest):
        raise PilotUnavailable('Alam RPH checksum mismatch')
    return _document(blob,fmt)


def fetch_private_document(config,lesson,fmt,*,opener=None):
    lesson,fmt=valid_selection(lesson,fmt)
    url,key=_settings(config)
    query=urlencode({'select':'subject,kumpulan,lesson,format,content_base64,byte_size,sha256_hex,sp_code,approval_status,source_archive_sha256',
         'subject':'eq.ALAM','kumpulan':'eq.A','lesson':'eq.'+str(lesson),'format':'eq.'+fmt,'approval_status':'eq.CANARY_APPROVED','limit':'2'})
    req=Request(url+'/rest/v1/kp2027_private_pilot_assets?'+query,headers=_headers(key),method='GET')
    do_open=opener or build_opener(_NoRedirects()).open
    try:
        with do_open(req,timeout=12) as resp:
            if getattr(resp,'status',None)!=200:raise PilotUnavailable('Alam data unavailable')
            raw=resp.read(450001)
        if len(raw)>450000:raise PilotUnavailable('Oversize Alam data')
        rows=json.loads(raw)
    except (HTTPError,URLError,OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        raise PilotUnavailable('Private Alam source unavailable') from exc
    if not isinstance(rows,list) or len(rows)!=1:raise PilotUnavailable('No approved Alam document')
    return verify_private_row(rows[0],lesson,fmt)


def fetch_approved_lessons(config,*,opener=None):
    """Return ONLY complete and hash-pinned approved Word/PDF pairs, no bytes."""
    url,key=_settings(config)
    query=urlencode({'select':'subject,kumpulan,lesson,format,sha256_hex,sp_code,approval_status,source_archive_sha256,byte_size',
         'subject':'eq.ALAM','kumpulan':'eq.A','approval_status':'eq.CANARY_APPROVED','limit':'150'})
    req=Request(url+'/rest/v1/kp2027_private_pilot_assets?'+query,headers=_headers(key),method='GET')
    do_open=opener or build_opener(_NoRedirects()).open
    try:
        with do_open(req,timeout=12) as resp:
            if getattr(resp,'status',None)!=200:raise PilotUnavailable('Alam inventory unavailable')
            raw=resp.read(70001)
        if len(raw)>70000:raise PilotUnavailable('Alam inventory oversized')
        records=json.loads(raw)
    except (HTTPError,URLError,OSError,TypeError,ValueError,json.JSONDecodeError) as exc:
        raise PilotUnavailable('Alam inventory unavailable') from exc
    if not isinstance(records,list) or len(records)>128:raise PilotUnavailable('Invalid Alam inventory')
    found={}
    for row in records:
        if not isinstance(row,dict) or row.get('subject')!='ALAM' or row.get('kumpulan')!='A':
            raise PilotUnavailable('Invalid Alam inventory row')
        lesson,fmt=row.get('lesson'),row.get('format')
        try:valid_selection(lesson,fmt)
        except ValueError:raise PilotUnavailable('Invalid Alam Lesson') from None
        expected=expected_entry(lesson)
        if (row.get('approval_status')!='CANARY_APPROVED' or row.get('source_archive_sha256')!=SOURCE_SHA
            or row.get('sp_code')!=expected['sp'] or row.get('sha256_hex')!=expected[fmt]
            or row.get('byte_size')!=expected[fmt+'_bytes']):
            raise PilotUnavailable('Alam metadata verification failed')
        formats=found.setdefault(lesson,set())
        if fmt in formats:raise PilotUnavailable('Duplicate Alam metadata')
        formats.add(fmt)
    return sorted(n for n,formats in found.items() if formats==set(FORMATS))


_PAGE='''<!doctype html><html lang="ms"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Alam dan Manusia Tahun 1 KP2027 | CikguLaju</title>
<style>body{margin:0;font:16px system-ui,sans-serif;background:#f5f7fa;color:#1a2735}.wrap{max-width:560px;margin:36px auto;background:#fff;border-radius:12px;padding:28px;box-shadow:0 6px 22px #19324916}h1{font-size:24px;margin:0 0 10px}p{line-height:1.55}label{display:block;margin:17px 0 7px;font-weight:600}select,button{width:100%;padding:13px;border-radius:7px;font:inherit}select{border:1px solid #bac6d2;background:white}button{margin-top:24px;border:0;background:#193755;color:white;font-weight:700;cursor:pointer}button:disabled{opacity:.55}small{color:#586779}.status{min-height:26px;margin-top:18px}a{color:#1c528e}</style></head>
<body><main class="wrap"><h1>Alam dan Manusia • KP2027 Tahun 1</h1><p>Pilih PdP mengikut RPT Kumpulan A/B apabila penyelarasan 93 PdP telah diluluskan; RPH sumber asal kekal ketika penyelarasan belum selesai.</p>
<label for="lesson">Lesson / PdP</label><select id="lesson" disabled><option>Semak senarai Lesson...</option></select>
<label for="fmt">Format</label><select id="fmt"><option value="pdf">PDF</option><option value="word">Word (.docx)</option></select>
<button id="download" type="button" disabled>Download RPH</button><p class="status" id="message" role="status" aria-live="polite"></p>
<small>Download memerlukan login CikguLaju dan menggunakan kelayakan/kuota yang sama. <a href="/">Kembali ke CikguLaju / Log masuk</a>.</small></main>
<script>
const l=document.getElementById('lesson'),f=document.getElementById('fmt'),b=document.getElementById('download'),m=document.getElementById('message');
(async()=>{try{const r=await fetch('/api/kp2027/sk/tahun-1/alam-dan-manusia/available',{credentials:'same-origin',headers:{Accept:'application/json'}});const j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.error||'Senarai RPH belum tersedia ('+r.status+')');if(!Array.isArray(j.lessons))throw Error('Senarai Lesson tidak sah');l.replaceChildren();for(const n of j.lessons){const opt=document.createElement('option');opt.value=String(n);opt.textContent=(j.catalog_mode==='rpt93'?'PdP ':'RPH sumber ')+String(n).padStart(3,'0');l.appendChild(opt)}l.disabled=j.lessons.length===0;b.disabled=l.disabled;m.textContent=j.lessons.length?j.lessons.length+' Lesson tersedia.':'Tiada Lesson yang diluluskan.';}catch(e){m.textContent=e.message}})();
b.addEventListener('click',async()=>{if(l.disabled||!l.value)return;b.disabled=true;m.textContent='Menyediakan fail...';const lesson=Number(l.value),format=f.value;try{const r=await fetch('/api/kp2027/sk/tahun-1/alam-dan-manusia/download',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','Accept':'application/octet-stream'},body:JSON.stringify({lesson,format})});if(!r.ok){const j=await r.json().catch(()=>({}));throw Error(j.error||'RPH tidak tersedia ('+r.status+')')}const data=await r.blob();const ext=format==='pdf'?'pdf':'docx',u=URL.createObjectURL(data),a=document.createElement('a');a.href=u;a.download='CIKGULAJU_KP2027_ALAM_T1_PDP'+String(lesson).padStart(3,'0')+'.'+ext;a.click();setTimeout(()=>URL.revokeObjectURL(u),30000);m.textContent='Fail disediakan. Semak folder Downloads.';}catch(e){m.textContent=e.message}finally{b.disabled=l.disabled}});
</script></body></html>'''


def create_blueprint():
    from flask import Blueprint,current_app,jsonify,make_response,request,send_file
    from web import kp2027_alam_5p_templates as five_p
    from web.rph_delivery_quota import authorize_rendered_document,has_active_paid_access
    from web.kp2027_pilot_teacher_fields import EXTRA_FIELDS, TeacherFieldError, personalize_approved_rph
    from web.kp2027_pdp_catalog import alam_approved_items
    from web.kp2027_alam_rpt93_private import (
        MAP as RPT93_MAP, valid_rpt_lesson, fetch_supplement,
        supplement_inventory_approved, make_rpt_inventory, SupplementUnavailable,
    )
    from web_v1_telegram_auth_routes import COOKIE,_config,_lookup
    from web_v1_sessions import verify_session_ticket

    bp=Blueprint('kp2027_alam_private',__name__)

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
            return None,None,denied('Semakan akses Web belum tersedia.',503,'LOGIN_BACKEND_UNAVAILABLE')
        uid=verify_session_ticket(request.cookies.get(COOKIE),config['CIKGULAJU_WEB_SESSION_SECRET'])
        if type(uid) is not int or uid<=0:return None,None,denied('Sila log masuk terlebih dahulu.',401,'AUTH_REQUIRED')
        try:account=_lookup(config,uid)
        except Exception:return None,None,denied('Semakan akaun belum tersedia.',503,'ACCOUNT_LOOKUP_FAILED')
        if (not isinstance(account,dict) or account.get('authenticated') is not True
                or account.get('telegram_user_id')!=uid):
            return None,None,denied('Akaun belum disahkan.',403,'ACCOUNT_NOT_VERIFIED')
        return config,account,None

    @bp.get('/kp2027/tahun-1/alam-dan-manusia')
    def page():
        res=make_response(_PAGE)
        res.headers['Content-Type']='text/html; charset=utf-8'
        res.headers['Content-Security-Policy']=("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                                                "connect-src 'self'; img-src 'self' blob:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        return res

    @bp.get('/api/kp2027/sk/tahun-1/alam-dan-manusia/available')
    def available():
        if os.environ.get(FEATURE_FLAG)!='1':return denied('Bahan Alam dan Manusia belum diaktifkan.',503,'ALAM_DISABLED')
        config,account,error=account_for_request()
        if error is not None:return error
        try:
            source_lessons=fetch_approved_lessons(config)
            # Retain the previous 64-source catalog until all 93 RPT entries
            # are safely available; QA_HOLD never exposes supplements.
            rpt_ready=False
            if len(source_lessons)==64:
                try:
                    supplement_inventory_approved(config)
                    rpt_ready=True
                except SupplementUnavailable:
                    pass
            if rpt_ready:
                items=make_rpt_inventory(source_lessons)
                lessons=[entry['no'] for entry in items]
            else:
                lessons=source_lessons
                items=alam_approved_items(source_lessons,CATALOG['items'])
        except (PilotUnavailable,SupplementUnavailable,ValueError,KeyError):
            return denied('Senarai PdP belum tersedia. Cuba lagi.',503,'ALAM_INVENTORY_UNAVAILABLE')
        return jsonify({'lessons':lessons,'items':items,'catalog_mode':'rpt93' if rpt_ready else 'source64',
            'five_p_templates':five_p.enabled(),
            'source':'verified-private-alam-rpt93-v4' if rpt_ready else 'verified-private-kp2027-alam-v10'})

    @bp.post('/api/kp2027/sk/tahun-1/alam-dan-manusia/download')
    def download():
        if os.environ.get(FEATURE_FLAG)!='1':return denied('Penerbitan Alam dan Manusia belum diaktifkan.',503,'ALAM_DISABLED')
        if request.headers.get('Origin')!=ORIGIN:return denied('Permintaan mestilah daripada Web CikguLaju.',403,'ORIGIN_REQUIRED')
        if not request.is_json or not 0<(request.content_length or 0)<=1024:
            return denied('Pilihan PdP tidak sah.',400,'INVALID_REQUEST')
        payload=request.get_json(silent=True)
        if (not isinstance(payload,dict) or not {'lesson','format'}.issubset(payload)
                or set(payload)-{'lesson','format'}-EXTRA_FIELDS):
            return denied('Pilihan PdP atau maklumat PdP tidak lengkap.',400,'INVALID_SELECTION')
        lesson,fmt=payload['lesson'],payload['format']
        if type(lesson) is not int or fmt not in FORMATS or not 1<=lesson<=93:
            return denied('PdP belum tersedia.',404,'LESSON_NOT_AVAILABLE')
        config,account,error=account_for_request()
        if error is not None:return error
        paid=has_active_paid_access(account)
        if not paid and (type(account.get('free_remaining')) is not int or not 0<=account['free_remaining']<=10):
            return denied('Baki janaan tidak dapat disahkan.',503,'TRIAL_UNVERIFIED')
        if not paid and account['free_remaining']==0:
            return denied('10 janaan percuma telah habis. Aktifkan langganan.',403,'FREE_TRIAL_EXHAUSTED')
        try:
            # Session 001–093 follows RPT only when *all* 64 original documents
            # and the private 29-document archive are approved and verified.
            source_lessons=fetch_approved_lessons(config)
            rpt_ready=False
            if len(source_lessons)==64:
                try:
                    supplement_inventory_approved(config)
                    rpt_ready=True
                except SupplementUnavailable:
                    pass
            if rpt_ready:
                mapping=valid_rpt_lesson(lesson,fmt)
                if lesson in RPT93_MAP and mapping['mapping_reason']!='existing_source':
                    document=fetch_supplement(config,lesson,fmt)
                else:
                    document=fetch_private_document(config,mapping['source_rph'],fmt)
            else:
                valid_selection(lesson,fmt)
                document=fetch_private_document(config,lesson,fmt)
        except (PilotUnavailable,SupplementUnavailable,ValueError):
            return denied('RPH masih dalam semakan atau belum tersedia.',503,'ALAM_UNAVAILABLE')
        try:
            document=personalize_approved_rph(document,fmt,{key:payload[key] for key in EXTRA_FIELDS if key in payload})
        except TeacherFieldError as exc:
            return denied(str(exc),400,'INVALID_TEACHER_FIELDS')
        remaining=None
        if not paid:
            try:charged=authorize_rendered_document(account,account['telegram_user_id'],document,
                        config['supabase_url'],config['supabase_key'],debit=debit_shared_trial)
            except Exception:return denied('Status kuota belum dapat disahkan. Sila semak akaun.',503,'TRIAL_CHARGE_UNCONFIRMED')
            if not charged['allowed']:return denied('Kuota percuma telah habis.',403,'FREE_TRIAL_EXHAUSTED')
            remaining=charged['remaining']
        ext,mime=FORMATS[fmt]
        resp=send_file(BytesIO(document),mimetype=mime,as_attachment=True,
            download_name=(f'CIKGULAJU_KP2027_ALAM_T1_RPT_PDP{lesson:03d}.{ext}' if rpt_ready
                 else f'CIKGULAJU_KP2027_ALAM_T1_LESSON{lesson:03d}.{ext}'),conditional=False)
        if remaining is not None:resp.headers['X-RPH-Trial-Remaining']=str(remaining)
        return resp
    @bp.get('/kp2027/tahun-1/alam-dan-manusia/5p')
    def page_5p():
        if not five_p.enabled():return denied('RPH 5P belum diaktifkan.',404,'ALAM_5P_DISABLED')
        config,account,error=account_for_request()
        if error is not None:return error
        res=make_response(five_p.PAGE)
        res.headers['Content-Type']='text/html; charset=utf-8'
        res.headers['Content-Security-Policy']=("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        return res

    @bp.get('/api/kp2027/sk/tahun-1/alam-dan-manusia/5p/available')
    def available_5p():
        if not five_p.enabled():return denied('RPH 5P belum diaktifkan.',404,'ALAM_5P_DISABLED')
        config,account,error=account_for_request()
        if error is not None:return error
        try:items=five_p.catalog(config)
        except PilotUnavailable:return denied('Senarai PdP 5P belum tersedia.',503,'ALAM_5P_UNAVAILABLE')
        return jsonify({'items':items,'catalog_mode':'rpt93','template_only':False})

    @bp.post('/api/kp2027/sk/tahun-1/alam-dan-manusia/5p/download')
    def download_5p():
        if not five_p.enabled():return denied('RPH 5P belum diaktifkan.',404,'ALAM_5P_DISABLED')
        if request.headers.get('Origin')!=ORIGIN:return denied('Permintaan mestilah daripada Web CikguLaju.',403,'ORIGIN_REQUIRED')
        if not request.is_json or not 0<(request.content_length or 0)<=1024:return denied('Pilihan PdP tidak sah.',400,'INVALID_REQUEST')
        payload=request.get_json(silent=True)
        if not isinstance(payload,dict) or not {'pdp','format'}.issubset(payload) or set(payload)-{'pdp','format'}-EXTRA_FIELDS:
            return denied('Pilihan 5P tidak sah.',400,'INVALID_SELECTION')
        pdp,fmt=payload['pdp'],payload['format']
        if type(pdp) is not int or not 1<=pdp<=93 or not isinstance(fmt,str) or fmt not in FORMATS:
            return denied('PdP belum tersedia.',404,'LESSON_NOT_AVAILABLE')
        config,account,error=account_for_request()
        if error is not None:return error
        paid=has_active_paid_access(account)
        if not paid and (type(account.get('free_remaining')) is not int or not 0<=account['free_remaining']<=10):
            return denied('Baki janaan tidak dapat disahkan.',503,'TRIAL_UNVERIFIED')
        if not paid and account['free_remaining']==0:
            return denied('10 janaan percuma telah habis. Aktifkan langganan.',403,'FREE_TRIAL_EXHAUSTED')
        try:
            from web.kp2027_alam_5p_personalize import LayoutError
            fields={key:payload[key] for key in EXTRA_FIELDS if key in payload}
            document=five_p.render(config,pdp,fmt,fields)
        except (TeacherFieldError,LayoutError) as exc:return denied(str(exc),400,'INVALID_TEACHER_FIELDS')
        except (PilotUnavailable,OSError,RuntimeError,ValueError,KeyError,TypeError):return denied('Fail 5P tidak dapat disahkan.',503,'ALAM_5P_UNAVAILABLE')
        remaining=None
        if not paid:
            try:charged=authorize_rendered_document(account,account['telegram_user_id'],document,
                        config['supabase_url'],config['supabase_key'],debit=debit_shared_trial)
            except Exception:return denied('Status kuota belum dapat disahkan.',503,'TRIAL_CHARGE_UNCONFIRMED')
            if not charged['allowed']:return denied('Kuota percuma telah habis.',403,'FREE_TRIAL_EXHAUSTED')
            remaining=charged['remaining']
        ext,mime=FORMATS[fmt]
        resp=send_file(BytesIO(document),mimetype=mime,as_attachment=True,
                       download_name=f'CIKGULAJU_KP2027_ALAM_T1_PDP{pdp:03d}_5P.{ext}',conditional=False)
        if remaining is not None:resp.headers['X-RPH-Trial-Remaining']=str(remaining)
        return resp

    return bp
