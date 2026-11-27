"""Private immutable RPT93 5P templates; no public files and no legacy mutation."""
import base64
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from zipfile import ZipFile, BadZipFile

from web.kp2027_math_canary_web import FORMATS, PilotUnavailable, _NoRedirects, _settings, _headers, _document

FLAG = "CIKGULAJU_KP2027_ALAM_5P_TEMPLATES_ENABLED"
ARCHIVE_SHA = "9faea9c19d67a2540c7e601d0d498cac9a71905513ae3c816ca1094a0a2a5a45"
ARCHIVE_BYTES = 6078333
PART_LENGTHS = [900000] * 9 + [4444]
TABLE = "kp2027_alam_5p_archive_chunks"

def enabled():
    return os.environ.get(FLAG) == "1"

def decode_archive(rows):
    if not isinstance(rows, list) or len(rows) != len(PART_LENGTHS):
        raise PilotUnavailable("Arkib 5P tidak lengkap")
    for n, (row, size) in enumerate(zip(rows, PART_LENGTHS), 1):
        if (not isinstance(row, dict) or row.get("part_no") != n or
            not isinstance(row.get("content_base64"), str) or len(row["content_base64"]) != size):
            raise PilotUnavailable("Bahagian arkib 5P tidak sah")
    try:
        raw = base64.b64decode("".join(row["content_base64"] for row in rows), validate=True)
    except (ValueError, TypeError) as exc:
        raise PilotUnavailable("Arkib 5P tidak sah") from exc
    if len(raw) != ARCHIVE_BYTES or sha256(raw).hexdigest() != ARCHIVE_SHA:
        raise PilotUnavailable("Integriti arkib 5P gagal")
    return raw

@lru_cache(maxsize=1)
def _read_archive(url, key):
    query = urlencode({"select":"part_no,content_base64","archive_sha256":"eq."+ARCHIVE_SHA,
                       "order":"part_no.asc","limit":"11"})
    req = Request(url+"/rest/v1/"+TABLE+"?"+query, headers=_headers(key), method="GET")
    try:
        with build_opener(_NoRedirects()).open(req, timeout=25) as response:
            if response.status != 200:
                raise PilotUnavailable("Storan 5P tidak tersedia")
            raw = response.read(8300001)
        if len(raw)>8300000:
            raise PilotUnavailable("Saiz arkib 5P tidak sah")
        return decode_archive(json.loads(raw))
    except (OSError, ValueError, TypeError) as exc:
        raise PilotUnavailable("Storan 5P tidak tersedia") from exc

def archive(config):
    return _read_archive(*_settings(config))

def record_index(z):
    m = json.loads(z.read("manifest.json"))
    records = m["records"]
    if len(records)!=93 or {r["rpt_pdp"] for r in records}!=set(range(1,94)):
        raise PilotUnavailable("Indeks RPT 5P tidak lengkap")
    return {r["rpt_pdp"]:r for r in records}

def catalog(config):
    try:
        with ZipFile(BytesIO(archive(config))) as z:
            return [{"no":n,"sp":r["sp"]} for n,r in sorted(record_index(z).items())]
    except (BadZipFile, KeyError, ValueError, TypeError, OSError) as exc:
        raise PilotUnavailable("Indeks 5P tidak tersedia") from exc

def select_document(raw, pdp, fmt):
    if type(pdp) is not int or not 1<=pdp<=93 or fmt not in FORMATS:
        raise PilotUnavailable("Pilihan 5P tidak sah")
    try:
        with ZipFile(BytesIO(raw)) as z:
            row=record_index(z)[pdp]
            stem=f"CIKGULAJU_ALAM_KP2027_T1_PDP{pdp:03d}_5P_QA"
            if row["filename"]!=stem:
                raise PilotUnavailable("Padanan PdP 5P tidak sah")
            name=("Word/" if fmt=="word" else "PDF/")+stem+"."+FORMATS[fmt][0]
            if z.getinfo(name).file_size>300000:
                raise PilotUnavailable("Saiz dokumen tidak sah")
            data=z.read(name)
            if sha256(data).hexdigest()!=row[fmt+"_sha256"]:
                raise PilotUnavailable("Integriti dokumen 5P gagal")
            return _document(data,fmt)
    except (BadZipFile, KeyError, ValueError, TypeError, OSError) as exc:
        raise PilotUnavailable("Dokumen 5P tidak tersedia") from exc

def fetch(config,pdp,fmt):
    return select_document(archive(config),pdp,fmt)

def render(config,pdp,fmt,payload):
    from web.kp2027_pilot_teacher_fields import parse_teacher_fields
    from web.kp2027_alam_5p_personalize import personalize
    fields=parse_teacher_fields(payload)
    raw=archive(config)
    word=select_document(raw,pdp,"word")
    pdf=select_document(raw,pdp,"pdf") if fmt=="pdf" else None
    return _document(personalize(word,pdf,fmt,fields),fmt)

PAGE = """<!doctype html><html lang="ms"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>RPH Ringkas 5P | CikguLaju</title>
<style>body{font:16px system-ui;background:#f4f7f3;color:#20332b;margin:2rem auto;max-width:35rem;padding:1rem}select,button,input,textarea{display:block;box-sizing:border-box;width:100%;font:inherit;padding:.7rem;margin:.5rem 0 1rem}textarea[hidden]{display:none}button{background:#315b45;color:white;border:0;border-radius:.4rem}button:disabled{opacity:.5}</style>
<h1>RPH Ringkas 5P</h1><p>Alam dan Manusia • KP2027 Tahun 1. PdP 001–093 mengikut RPT, bukan nombor Lesson sumber. Isi maklumat PdP jika perlu. Refleksi automatik berdasarkan kriteria kejayaan atau isi sendiri. RPH biasa kekal di menu asal.</p><label for="pdp">PdP / SP</label><select id="pdp" disabled></select><label for="fmt">Format</label><select id="fmt"><option value="pdf">PDF</option><option value="word">Word</option></select><label>Kelas <input id="cls" maxlength="40"></label><label>Tarikh <input id="dt" type="date"></label><label>Masa mula <input id="start" type="time"></label><label>Masa tamat <input id="end" type="time"></label><label>Bilangan murid <input id="count" type="number" min="1" max="200"></label><label for="mode">Refleksi</label><select id="mode"><option value="auto">Auto</option><option value="manual">Manual</option></select><textarea id="ref" maxlength="500" hidden></textarea><button id="go" disabled>Download RPH</button><p id="status" role="status"></p><a href="/">Kembali ke CikguLaju</a>
<script>
const base='/api/kp2027/sk/tahun-1/alam-dan-manusia/5p',p=document.getElementById('pdp'),f=document.getElementById('fmt'),b=document.getElementById('go'),s=document.getElementById('status');
(async()=>{try{const r=await fetch(base+'/available',{credentials:'same-origin',cache:'no-store'}),j=await r.json();if(!r.ok||!Array.isArray(j.items)||j.items.length!==93)throw Error(j.error||'Senarai 5P belum tersedia');for(const item of j.items){const o=document.createElement('option');o.value=String(item.no);o.textContent='PdP '+String(item.no).padStart(3,'0')+' • SP '+item.sp;p.append(o)}p.disabled=false;b.disabled=false}catch(e){s.textContent=e.message}})();
const el=id=>document.getElementById(id);el('mode').addEventListener('change',()=>{el('ref').hidden=el('mode').value!=='manual'});
b.addEventListener('click',async()=>{b.disabled=true;try{const r=await fetch(base+'/download',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({pdp:Number(p.value),format:f.value,teacher_class:el('cls').value,teacher_date:el('dt').value,teacher_start:el('start').value,teacher_end:el('end').value,teacher_students:el('count').value,reflection_mode:el('mode').value,reflection:el('mode').value==='manual'?el('ref').value:''})});if(!r.ok){const j=await r.json().catch(()=>({}));throw Error(j.error||'Muat turun gagal')}const u=URL.createObjectURL(await r.blob()),a=document.createElement('a');a.href=u;a.download='CIKGULAJU_ALAM_T1_PDP'+String(p.value).padStart(3,'0')+'_5P.'+(f.value==='pdf'?'pdf':'docx');a.click();setTimeout(()=>URL.revokeObjectURL(u),30000);s.textContent='Semak folder Downloads.'}catch(e){s.textContent=e.message}finally{b.disabled=false}});
</script></html>"""
