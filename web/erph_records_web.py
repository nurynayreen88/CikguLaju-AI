"""Private, opt-in teacher-authored e-RPH records. No source generation or quota bypass."""
import json
import os
from datetime import date, time
from uuid import UUID
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from flask import Blueprint, request, jsonify, Response
from web_v1_telegram_auth_routes import COOKIE, _config, _lookup
from web_v1_sessions import verify_session_ticket
from web.kp2027_math_canary_web import _settings, _headers, _NoRedirects

bp = Blueprint('erph_records', __name__)
FLAG = 'CIKGULAJU_ERPH_RECORDS_ENABLED'
ORIGIN = 'https://cikgulaju-web.onrender.com'
FIELDS = ('teaching_date','class_name','subject_name','start_time','end_time',
          'title','standard_content','standard_learning','objectives','activities','reflection','rph_format','status')
LIMITS = dict(class_name=80, subject_name=120, title=200,
              standard_content=4000, standard_learning=4000, objectives=4000, activities=12000, reflection=4000)
SELECT = 'id,' + ','.join(FIELDS) + ',updated_at'

@bp.after_request
def no_store(response):
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Vary'] = 'Cookie'
    return response

def failure(message, status):
    return jsonify(error=message), status

def account():
    if os.environ.get(FLAG) != '1':
        return None, None, failure('e-RPH belum diaktifkan.', 404)
    c = _config()
    if not c or c.get('account_backend') != 'supabase':
        return None, None, failure('Semakan akaun belum tersedia.', 503)
    uid = verify_session_ticket(request.cookies.get(COOKIE), c['CIKGULAJU_WEB_SESSION_SECRET'])
    if type(uid) is not int or uid <= 0:
        return None, None, failure('Sila log masuk.', 401)
    try:
        a = _lookup(c, uid)
    except Exception:
        return None, None, failure('Semakan akaun belum tersedia.', 503)
    if not isinstance(a, dict) or a.get('authenticated') is not True or a.get('telegram_user_id') != uid:
        return None, None, failure('Akaun belum disahkan.', 403)
    return c, uid, None

def validate(data):
    if not isinstance(data, dict) or set(data) != set(FIELDS):
        raise ValueError('Medan e-RPH tidak lengkap.')
    out = {}
    for key, value in data.items():
        if not isinstance(value,str):
            raise ValueError('Medan e-RPH tidak sah.')
        value = value.strip()
        if key in LIMITS and (len(value)>LIMITS[key] or
            (key in ('class_name','subject_name','title') and not value)):
            raise ValueError('Panjang medan tidak sah: '+key)
        if any(ord(ch)<32 and ch not in '\n\t\r' for ch in value):
            raise ValueError('Aksara tidak sah.')
        out[key] = value
    day = date.fromisoformat(out['teaching_date'])
    if not 2000 <= day.year <= 2100:
        raise ValueError('Tarikh tidak sah.')
    for k in ('start_time','end_time'):
        if len(out[k]) != 5 or time.fromisoformat(out[k]).isoformat(timespec='minutes') != out[k]:
            raise ValueError('Masa tidak sah.')
    if out['start_time'] >= out['end_time']:
        raise ValueError('Masa tamat mesti selepas masa mula.')
    if out['rph_format'] not in ('biasa','5p') or out['status'] not in ('draft','saved','completed'):
        raise ValueError('Format atau status tidak sah.')
    if out['status'] in ('saved','completed') and not all(out[k] for k in ('objectives','activities')):
        raise ValueError('Isi objektif dan aktiviti terlebih dahulu.')
    if out['status']=='completed' and not out['reflection']:
        raise ValueError('Isi refleksi selepas PdP.')
    return out

def store(config, uid, method, filters, data=None, *, summary=False):
    url,key = _settings(config)
    # Ownership filter is derived only from verified session. Never accept client owner.
    query = dict(filters, owner_telegram_id='eq.'+str(uid), select='id,teaching_date,status' if summary else SELECT)
    headers = dict(_headers(key), **{'Content-Type':'application/json','Prefer':'return=representation'})
    req = Request(url+'/rest/v1/erph_teacher_records?'+urlencode(query),
                  headers=headers, method=method,
                  data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None)
    with build_opener(_NoRedirects()).open(req, timeout=12) as resp:
        raw=resp.read(4000001)
    if len(raw)>4000000:
        raise ValueError('Respons terlalu besar.')
    rows=json.loads(raw)
    if not isinstance(rows,list):
        raise ValueError('Respons tidak sah.')
    return rows

@bp.get('/api/erph/records')
def records():
    c,uid,error=account()
    if error is not None:return error
    try:
        from datetime import timedelta
        day=date.fromisoformat(request.args.get('date',''))
        scope=request.args.get('scope','day')
        if not 2000<=day.year<=2100 or scope not in ('day','week'):raise ValueError()
        first=day-timedelta(days=(day.weekday()+1)%7) if scope=='week' else day
        last=first+timedelta(days=6) if scope=='week' else first
    except ValueError:return failure('Tarikh tidak sah.',400)
    try:
        filters={'order':'teaching_date.asc,start_time.asc','limit':'701'}
        if scope=='week':filters['and']='(teaching_date.gte.'+first.isoformat()+',teaching_date.lte.'+last.isoformat()+')'
        else:filters['teaching_date']='eq.'+day.isoformat()
        rows=store(c,uid,'GET',filters)
        if len(rows)>700:return failure('Terlalu banyak rekod; pilih paparan harian.',400)
        return jsonify(items=rows,start=first.isoformat(),end=last.isoformat())
    except Exception:return failure('Rekod belum dapat dibaca.',503)

@bp.post('/api/erph/records')
@bp.put('/api/erph/records/<record_id>')
def save(record_id=None):
    c,uid,error=account()
    if error is not None:return error
    if request.headers.get('Origin')!=ORIGIN:return failure('Permintaan tidak sah.',403)
    if not request.is_json or not 0<(request.content_length or 0)<=100000:
        return failure('Permintaan tidak sah.',400)
    from datetime import datetime, timezone
    expected=None
    try:
        data=validate(request.get_json(silent=True))
        if record_id is not None:
            record_id=str(UUID(record_id))
            stamp=request.headers.get('X-eRPH-Version','')
            if not 1<=len(stamp)<=64:
                return failure('Versi rekod diperlukan. Buka semula rekod sebelum menyimpan.',428)
            expected=datetime.fromisoformat(stamp)
            if expected.tzinfo is None:
                raise ValueError('Versi tidak sah.')
            expected=expected.astimezone(timezone.utc).isoformat()
    except (ValueError,TypeError):
        return failure('Semak medan, tarikh, masa dan status.',400)
    data['updated_at']=datetime.now(timezone.utc).isoformat()
    try:
        if record_id is None:
            data['owner_telegram_id']=uid
            rows=store(c,uid,'POST',{},data)
        else:
            rows=store(c,uid,'PATCH',{'id':'eq.'+record_id,'updated_at':'eq.'+expected},data)
        if not rows:
            if record_id is not None:
                # Do not distinguish an inaccessible record from a stale version.
                return failure('Rekod telah berubah atau tidak tersedia. Salin pindaan anda, kemudian buka semula rekod.',409)
            return failure('Rekod tidak ditemui.',404)
        if len(rows)!=1:return failure('Semakan rekod gagal.',503)
        return jsonify(item=rows[0]), 201 if record_id is None else 200
    except Exception:
        return failure('Rekod tidak dapat disimpan. Semak jika slot sudah wujud.',503)

@bp.get('/api/erph/availability')
def availability():
    c,uid,error=account()
    if error is not None:return error
    return jsonify(enabled=True)

@bp.get('/erph')
def page():
    c,uid,error=account()
    if error is not None:return error
    from pathlib import Path
    html=(Path(__file__).resolve().parents[1]/'web_v1_static_preview'/'erph_records.html').read_text(encoding='utf-8')
    return Response(html,mimetype='text/html')

@bp.post('/api/erph/import-word')
def import_word():
    c,uid,error=account()
    if error is not None:return error
    if request.headers.get('Origin')!=ORIGIN:return failure('Permintaan tidak sah.',403)
    from web.erph_word_import import MAX_FILE,extract_docx
    if request.mimetype!='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or not 0<(request.content_length or 0)<=MAX_FILE:
        return failure('Pilih fail Word (.docx), maksimum 2 MB.',400)
    try:
        fields=extract_docx(request.stream.read(MAX_FILE+1))
    except ValueError as exc:return failure(str(exc),400)
    return jsonify(fields=fields,source_verified=False)

@bp.post('/erph/import-preview')
def import_preview():
    c,uid,error=account()
    if error is not None:return error
    if request.headers.get('Origin')!=ORIGIN or not 0<(request.content_length or 0)<=200000:
        return failure('Permintaan tidak sah.',403)
    try:
        draft=json.loads(request.form.get('draft',''))
        if not isinstance(draft,dict) or set(draft)!=set(FIELDS):
            raise ValueError()
        for k,v in draft.items():
            if not isinstance(v,str) or len(v)>LIMITS.get(k,80):
                raise ValueError()
        draft['status']='draft'
    except (TypeError,ValueError):return failure('Draf tidak sah.',400)
    from pathlib import Path
    html=(Path(__file__).resolve().parents[1]/'web_v1_static_preview'/'erph_records.html').read_text(encoding='utf-8')
    # JSON is encoded into a non-executable script element; escape all tag delimiters.
    data=json.dumps(draft,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    marker='<script id="erph-initial-draft" type="application/json"></script>'
    if marker not in html:return failure('Editor belum tersedia.',503)
    return Response(html.replace(marker,'<script id="erph-initial-draft" type="application/json">'+data+'</script>',1),mimetype='text/html')

@bp.get('/api/erph/export')
def export_records():
    c,uid,error=account()
    if error is not None:return error
    from datetime import timedelta
    from io import BytesIO
    from flask import send_file
    from web.erph_export import render,MAX_RECORDS
    try:
        if set(request.args)-{'date','scope','format'} or any(len(request.args.getlist(k))!=1 for k in request.args):
            raise ValueError()
        day=date.fromisoformat(request.args.get('date',''))
        scope=request.args.get('scope','day')
        fmt=request.args.get('format','')
        if not 2000<=day.year<=2100 or scope not in ('day','week') or fmt not in ('word','pdf'):
            raise ValueError()
        first=day-timedelta(days=(day.weekday()+1)%7) if scope=='week' else day
        last=first+timedelta(days=6) if scope=='week' else first
    except ValueError:return failure('Pilihan eksport tidak sah.',400)
    filters={'order':'teaching_date.asc,start_time.asc','limit':str(MAX_RECORDS+1)}
    if scope=='week':filters['and']='(teaching_date.gte.'+first.isoformat()+',teaching_date.lte.'+last.isoformat()+')'
    else:filters['teaching_date']='eq.'+day.isoformat()
    try:
        rows=store(c,uid,'GET',filters)
        if not rows:return failure('Tiada rekod untuk dieksport.',404)
        data=render(rows,fmt)
    except ValueError as exc:return failure(str(exc),400)
    except Exception:return failure('Eksport belum dapat disediakan.',503)
    ext,mime=('docx','application/vnd.openxmlformats-officedocument.wordprocessingml.document') if fmt=='word' else ('pdf','application/pdf')
    return send_file(BytesIO(data),mimetype=mime,as_attachment=True,
      download_name='CIKGULAJU_eRPH_'+first.isoformat()+'_'+last.isoformat()+'.'+ext,conditional=False)

@bp.get('/api/erph/summary')
def summary_records():
    c,uid,error=account()
    if error is not None:return error
    from calendar import monthrange
    from datetime import timedelta
    try:
        if set(request.args)-{'date','scope'} or any(len(request.args.getlist(k))!=1 for k in request.args):
            raise ValueError()
        day=date.fromisoformat(request.args.get('date',''))
        scope=request.args.get('scope','')
        if not 2000<=day.year<=2100 or scope not in ('month','year'):
            raise ValueError()
        first=date(day.year,day.month if scope=='month' else 1,1)
        last=date(day.year,day.month,monthrange(day.year,day.month)[1]) if scope=='month' else date(day.year,12,31)
    except ValueError:return failure('Pilihan ringkasan tidak sah.',400)
    counts={}
    cursor=first
    while cursor<=last:
        key=cursor.isoformat() if scope=='month' else cursor.isoformat()[:7]
        counts.setdefault(key,dict(draft=0,saved=0,completed=0))
        cursor+=timedelta(days=1)
    try:
        # Only dates/status/IDs, not teaching content. Keyset pagination with
        # a stable unique ordering avoids hidden 1000-row PostgREST truncation.
        after=None
        for page in range(21):
            filters={'order':'id.asc','limit':'500','and':'(teaching_date.gte.'+first.isoformat()+',teaching_date.lte.'+last.isoformat()+')'}
            if after:filters['id']='gt.'+after
            rows=store(c,uid,'GET',filters,summary=True)
            if not rows:break
            if len(rows)>500 or page==20:raise ValueError('Rekod terlalu banyak. Pilih ringkasan bulanan.')
            for row in rows:
                rid=str(UUID(row['id']))
                if after and rid<=after:raise ValueError('Susunan ringkasan tidak sah.')
                after=rid
                record_day=date.fromisoformat(row['teaching_date'])
                if not first<=record_day<=last:raise ValueError('Tarikh rekod tidak sah.')
                key=record_day.isoformat() if scope=='month' else record_day.isoformat()[:7]
                counts[key][row['status']]+=1
        return jsonify(scope=scope,start=first.isoformat(),end=last.isoformat(),
          items=[dict(period=key,**value,total=sum(value.values())) for key,value in counts.items()])
    except ValueError as exc:return failure(str(exc),400)
    except Exception:return failure('Ringkasan belum dapat dibaca.',503)
