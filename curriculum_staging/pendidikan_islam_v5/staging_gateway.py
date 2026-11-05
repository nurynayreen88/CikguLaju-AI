"""Read-only, opt-in WSGI staging preview for Pendidikan Islam 2027.

No production bot route, API key, customer profile, subscription, quota, database,
Telegram callback, or external network service is read or modified. No CORS.

Security: env gates + long staging secret + draft/held guards + ZIP SHA validation.
For local test: PI_V5_STAGING_GATEWAY=1, PI_V5_STAGING_TOKEN=<32-byte secret>,
PI_V5_ARCHIVE and PI_V5_PREVIEW_ARCHIVE must exist. Never use in production.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs

from bundle_reader import PIBundleV5, BundleValidationError
from preview_reader import PIPreviewBundleV5, PreviewBundleError

MAX_SERVED_BYTES = 8 * 1024 * 1024
VALID_COUNTS = {2: 112, 3: 147, 4: 151, 5: 143, 6: 143}
STATUS_HELD = 'TAHAN_SEMAKAN_KANDUNGAN'
STATUS_EXPECTED = {"CALON_UJIAN_GURU_DRAF", "SEMAKAN_KEUTAMAAN", STATUS_HELD}

class StagingConfigurationError(RuntimeError):
    pass


def make_gateway(archive_path, preview_archive_path, *, staging=False, token=''):
    """Return stdlib WSGI application, disabled unless explicitly staged."""
    if staging is not True:
        raise StagingConfigurationError('PI V5 staging must be opt-in')
    if not isinstance(token, str) or len(token) < 24 or len(token.encode('utf-8')) > 512:
        raise StagingConfigurationError('Strong staging token required')
    bundle = PIBundleV5(archive_path, staging=True)
    previews = PIPreviewBundleV5(preview_archive_path, staging=True)
    if set(bundle.lesson_ids()) != set(previews._index):
        raise StagingConfigurationError('RPH and PDF preview catalog IDs mismatch')
    counts = Counter(y for y, _ in bundle.lesson_ids())
    if dict(counts) != VALID_COUNTS:
        raise StagingConfigurationError('Unexpected lesson distribution')
    statuses = Counter(bundle.record(y,l).get('rph_state') for y,l in bundle.lesson_ids())
    if not set(statuses) <= STATUS_EXPECTED:
        raise StagingConfigurationError('Unknown approval status')
    if statuses.get(STATUS_HELD, 0) != 6:
        raise StagingConfigurationError('Expected six withheld source lessons')
    if sum(1 for y,l in bundle.lesson_ids() if bundle.record(y,l).get('optional_tasmi_guide')) != 8:
        raise StagingConfigurationError('Guide count mismatch')

    def respond(start, code, data, *, mime='application/json; charset=utf-8', filename=None, inline=False):
        if isinstance(data, dict):
            payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        else:
            payload = data
        hdr = [('Content-Type', mime), ('Content-Length', str(len(payload))),
               ('Cache-Control', 'private, no-store, max-age=0'),
               ('Pragma', 'no-cache'), ('X-Content-Type-Options', 'nosniff'),
               ('Referrer-Policy', 'no-referrer'),
               ('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'")]
        if filename:
            hdr.append(('Content-Disposition', ('inline' if inline else 'attachment') + f'; filename="{filename}"'))
        start(code, hdr)
        return [payload]

    def one(qs, key, *, fmt=r'[0-9]{1,3}'):
        values = qs.get(key, [])
        if len(values) != 1 or not re.fullmatch(fmt, values[0], flags=re.ASCII):
            raise ValueError('invalid ' + key)
        return values[0]

    def years_and_lesson(environ, *, require_lesson=True):
        qs = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=True, max_num_fields=4)
        year = int(one(qs, 'year', fmt='[2-6]'))
        lesson = int(one(qs, 'lesson')) if require_lesson else None
        if require_lesson and (year, lesson) not in bundle._catalog:
            raise KeyError('lesson not found')
        return year, lesson, qs

    def limited_pdf_from_archive(path):
        with zipfile.ZipFile(bundle.path) as z:
            info = z.getinfo(path)
            if info.file_size > MAX_SERVED_BYTES:
                raise BundleValidationError('Large staged file')
            data = z.read(path)
        if not data.startswith(b'%PDF-') or len(data) > MAX_SERVED_BYTES:
            raise BundleValidationError('PDF failed integrity check')
        return data

    def limited_rpt(year, suffix):
        if suffix == 'pdf':
            name = f'RPT_2027_PDF_DRAF_V3/RPT_Pendidikan_Islam_Tahun_{year}_2027_BERMUKA_DEPAN_DRAF.pdf'
            data = limited_pdf_from_archive(name)
            return data, 'application/pdf', f'PI_RPT_Tahun_{year}_2027_DRAF.pdf'
        if suffix == 'docx':
            name = f'RPT_2027_WORD_DRAF/Tahun_{year}/RPT_PI_T{year}_2027_HITAM_PUTIH_QA_V4_DRAF.docx'
            with zipfile.ZipFile(bundle.path) as z:
                info = z.getinfo(name)
                if info.file_size > MAX_SERVED_BYTES:
                    raise BundleValidationError('Large staged Word file')
                data = z.read(name)
            if not data.startswith(b'PK\x03\x04') or len(data) > MAX_SERVED_BYTES:
                raise BundleValidationError('Invalid Word file')
            return data, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', f'PI_RPT_Tahun_{year}_2027_DRAF.docx'
        raise ValueError('invalid format')

    def wsgi(environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path == '/health':
            return respond(start_response, '200 OK', {'status':'STAGING_ONLY', 'published':False})
        # Explicit auth before file/lesson queries, fail closed for all routes.
        auth = environ.get('HTTP_AUTHORIZATION', '')
        if not isinstance(auth, str) or not hmac.compare_digest(auth.encode('utf-8'), ('Bearer ' + token).encode('utf-8')):
            return respond(start_response, '403 Forbidden', {'error':'staging access denied'})
        if environ.get('REQUEST_METHOD', 'GET') != 'GET':
            return respond(start_response, '405 Method Not Allowed', {'error':'read-only endpoint'})
        try:
            if path == '/api/pi/status':
                return respond(start_response, '200 OK', {'year_counts':VALID_COUNTS, 'total':696,
                    'held':statuses.get(STATUS_HELD,0), 'draft':696-statuses.get(STATUS_HELD,0),
                    'ready':0,'tasmi_guides':8,'publication':'STAGING_ONLY'})
            if path == '/api/pi/lessons':
                year,_,_=years_and_lesson(environ,require_lesson=False)
                items=[{'lesson':l,'state':'HELD' if bundle.record(y,l).get('rph_state')==STATUS_HELD else 'DRAF',
                        'has_preview':bundle.record(y,l).get('rph_state')!=STATUS_HELD,
                        'has_tasmi_guide':bool(bundle.record(y,l).get('optional_tasmi_guide'))}
                       for y,l in bundle.lesson_ids() if y==year]
                return respond(start_response, '200 OK', {'year':year,'total':len(items),'lessons':items})
            if path in ('/api/pi/lesson','/api/pi/preview','/api/pi/word','/api/pi/tasmi'):
                year,lesson,_=years_and_lesson(environ)
                record=bundle.record(year,lesson)
                held=record.get('rph_state')==STATUS_HELD
                if path == '/api/pi/lesson':
                    return respond(start_response,'200 OK',{'year':year,'lesson':lesson,'id':record['lesson_id'],
                        'state':'HELD' if held else 'DRAF','has_preview':not held,
                        'has_tasmi_guide':bool(record.get('optional_tasmi_guide')), 'final_ready':False})
                if path == '/api/pi/tasmi':
                    data=bundle.read_optional_tasmi_guide(year,lesson)
                    if data is None:return respond(start_response,'404 Not Found',{'error':'no supplemental guide'})
                    return respond(start_response,'200 OK',data,mime='application/pdf',filename=f'PI_T{year}_L{lesson:03d}_TASMI_CADANGAN.pdf',inline=True)
                if held:
                    return respond(start_response,'423 Locked',{'error':'lesson pending content verification'})
                if path == '/api/pi/preview':
                    data=previews.read_preview_pdf(year,lesson,allow_teacher_draft=True)
                    return respond(start_response,'200 OK',data,mime='application/pdf',filename=f'PI_T{year}_L{lesson:03d}_DRAF.pdf',inline=True)
                data=bundle.read_rph(year,lesson,allow_teacher_draft=True)
                return respond(start_response,'200 OK',data,
                    mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    filename=f'PI_T{year}_L{lesson:03d}_DRAF.docx')
            if path == '/api/pi/rpt':
                year,_,qs=years_and_lesson(environ,require_lesson=False)
                fmt=one(qs, 'format',fmt='(pdf|docx)')
                data,mime,name=limited_rpt(year,fmt)
                return respond(start_response,'200 OK',data,mime=mime,filename=name,inline=fmt=='pdf')
        except (ValueError,KeyError,OverflowError) as exc:
            return respond(start_response,'400 Bad Request' if not isinstance(exc,KeyError) else '404 Not Found',
                           {'error':'invalid staging selection'})
        except (OSError,zipfile.BadZipFile,BundleValidationError,PreviewBundleError):
            return respond(start_response,'503 Service Unavailable',{'error':'staging archive unavailable or invalid'})
        return respond(start_response,'404 Not Found',{'error':'staging route not found'})
    return wsgi


def _closed_gateway(environ,start_response):
    data=b'{"error":"PI staging gateway disabled"}'
    start_response('503 Service Unavailable',[('Content-Type','application/json'),('Cache-Control','no-store'),
                      ('Content-Length',str(len(data))),('X-Content-Type-Options','nosniff')])
    return [data]


def from_environment(env=None):
    env = dict(os.environ if env is None else env)
    if env.get('PI_V5_STAGING_GATEWAY') != '1':
        return _closed_gateway
    try:
        return make_gateway(env.get('PI_V5_ARCHIVE'),env.get('PI_V5_PREVIEW_ARCHIVE'),
                            staging=True,token=env.get('PI_V5_STAGING_TOKEN',''))
    except (StagingConfigurationError,BundleValidationError,PreviewBundleError,ValueError,OSError,TypeError):
        return _closed_gateway

# Standalone staging-only WSGI app (gunicorn staging_gateway:application); never imported by bot.
application=from_environment()