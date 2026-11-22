"""Read-only, source-pinned Bahasa Melayu SK KP2027 Year 1 RPH from RPT 2027.

Serves A=178/B=175 PdP with Word/PDF, individual SP/SK descriptions,
structured activities and full RPH table. The original source and ZIP archive
are kept in private Google Drive for rollback. Outputs remain SEMAKAN.
"""
from __future__ import annotations
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from html import escape
import json
import re

SOURCE=Path(__file__).with_name('kp2027_bm_rph_rpt_aligned_20261122.json')
SOURCE_SHA='7984d6e36fffcc71f9ff000871d985477e3713f803e17b1ff2b586e96d992571'
COUNTS={'A':178,'B':175}
FMTS={'word':('docx','application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
      'pdf':('pdf','application/pdf')}

class Unavailable(ValueError):pass

@lru_cache(maxsize=1)
def approved_source():
    if SOURCE.is_symlink() or not SOURCE.is_file() or not 300000<=SOURCE.stat().st_size<=750000:
        raise Unavailable('Sumber RPH BM SK KP2027 belum tersedia')
    data=SOURCE.read_bytes()
    if sha256(data).hexdigest()!=SOURCE_SHA:raise Unavailable('SHA sumber RPH BM SK tidak sah')
    try:root=json.loads(data)
    except (ValueError,UnicodeError) as ex:raise Unavailable('Sumber RPH tidak sah') from ex
    if (root.get('version')!='2026-11-22' or root.get('status')!='SEMAKAN_PELAKSANAAN'
            or root.get('subject')!='BM_SK' or root.get('year')!=1 or root.get('counts')!=COUNTS):
        raise Unavailable('Sumber RPH tidak diperakui')
    records=root.get('records')
    if not isinstance(records,dict) or set(records)!=set(COUNTS):raise Unavailable('Kumpulan A/B tidak lengkap')
    for group,count in COUNTS.items():
        if not isinstance(records[group],dict) or set(records[group])!={str(i) for i in range(1,count+1)}:
            raise Unavailable('Urutan PdP A/B tidak lengkap')
        for i in range(1,count+1):
            r=records[group][str(i)]
            if (not isinstance(r,dict) or r.get('group')!=group or r.get('lesson')!=i
                or not re.fullmatch(r'[1-4]\.\d\.\d',str(r.get('sp_code','')))
                or not isinstance(r.get('activities'),list) or len(r['activities'])!=3
                or not all(isinstance(s,str) and 20<len(s)<650 for s in r['activities'])
                or any(not isinstance(r.get(key),str) or not r[key] or len(r[key])>650
                       for key in ['sp','sk','sk_code','title','unit','induction','criteria','pbd','closure','material'])):
                raise Unavailable('Rekod PdP tidak disahkan')
    return records

def ready():
    try:approved_source();return True
    except (Unavailable,OSError):return False

def lesson(group,n):
    if group not in COUNTS or type(n) is not int or not 1<=n<=COUNTS[group]:
        raise Unavailable('Pilihan PdP BM SK tidak sah')
    return approved_source()[group][str(n)]

def _safe_value(fields,key):
    return fields.get(key,'') or ''

def _reflection(r,fields):
    mode=fields.get('_reflection_mode','auto')
    if mode=='manual':return fields.get('_reflection','')
    # Do not infer mastery counts from the teacher's class size or RPT.
    return ('PdP dijalankan berdasarkan kriteria kejayaan: '+r['criteria']+' '
            'Bilangan murid menguasai:    Bilangan murid belum menguasai:    '
            'Tindakan susulan: '+r['remedial'])

def _activity_titles(r):return [f'Aktiviti 1 – {r["title"]}','Aktiviti 2 – Bimbingan dan Kerjasama','Aktiviti 3 – Aplikasi Individu']

def _docx(r,fields):
    from docx import Document
    from docx.shared import Cm, Pt, RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    d=Document();sec=d.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.left_margin=Cm(1.25);sec.right_margin=Cm(1.25);sec.top_margin=Cm(1.05);sec.bottom_margin=Cm(1.0)
    d.styles['Normal'].font.name='Aptos';d.styles['Normal'].font.size=Pt(8.3)
    def para(text,size=9,bold=False):
        p=d.add_paragraph();p.alignment=1;p.paragraph_format.space_after=Pt(3)
        q=p.add_run(text);q.bold=bold;q.font.size=Pt(size);q.font.name='Aptos'
    para('BAHASA MELAYU SK  •  TAHUN 1',9,True)
    para('RANCANGAN PENGAJARAN HARIAN',14,True)
    para(f'KUMPULAN {r["group"]}  •  PdP {r["lesson"]:03d}  •  {r["title"]}',9,True)
    def sh(cell,fill):
        tc=cell._tc.get_or_add_tcPr();node=OxmlElement('w:shd');node.set(qn('w:fill'),fill);tc.append(node)
    def grid(cell):
        tc=cell._tc.get_or_add_tcPr();bd=OxmlElement('w:tcBorders')
        for side in ('top','left','bottom','right'):
            item=OxmlElement('w:'+side);item.set(qn('w:val'),'single');item.set(qn('w:sz'),'5');item.set(qn('w:color'),'BAC7D0');bd.append(item)
        tc.append(bd)
    head=d.add_table(rows=2,cols=4);head.autofit=False;head.alignment=WD_TABLE_ALIGNMENT.CENTER
    for col,w in zip(head.columns,[2.1,7.2,2.1,7.1]):col.width=Cm(w)
    pairs=[(('Kelas',_safe_value(fields,'Kelas:')),('Tarikh',_safe_value(fields,'Tarikh:'))),
           (('Masa',_safe_value(fields,'Masa:')),('Bil. Murid',_safe_value(fields,'Bil. Murid:')))]
    for j,pair in enumerate(pairs):
        for k,(label,value) in enumerate(pair):
            hc=head.cell(j,2*k);hc.text=label;sh(hc,'F2F5F7');grid(hc)
            vc=head.cell(j,2*k+1);vc.text=value;grid(vc)
    d.add_paragraph().paragraph_format.space_after=Pt(0)
    rows=[('Kandungan / Tajuk',r['unit']+' • '+r['title']),
      ('Standard Kandungan (SK)',r['sk_code']+' '+r['sk']),
      ('Standard Pembelajaran (SP)',r['sp_code']+' '+r['sp']),
      ('Objektif Pembelajaran',r['objective']),('Kriteria Kejayaan',r['criteria']),
      ('EMK / Nilai','Bahasa; komunikasi berhemah; kerjasama; hormat-menghormati; tanggungjawab.'),
      ('PAK21 / KBAT','Kolaborasi, komunikasi, pemikiran kritis; menerangkan sebab dan membuat pilihan yang bersesuaian.'),
      ('Bahan / BBM',r['material']),('Set Induksi',r['induction']),
      ('Aktiviti Utama',None),('Pengukuhan / PBD',r['pbd']),('Penutup',r['closure']),
      ('Pemulihan',r['remedial']),('Pengayaan',r['extension']),
      ('Refleksi',_reflection(r,fields))]
    t=d.add_table(rows=len(rows),cols=2);t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.columns[0].width=Cm(4.45);t.columns[1].width=Cm(14.05)
    for j,(label,value) in enumerate(rows):
        c0,c1=t.rows[j].cells;c0.width=Cm(4.45);c1.width=Cm(14.05)
        c0.text=label;sh(c0,'F4EDE6');grid(c0);grid(c1)
        for p in c0.paragraphs:
            for run in p.runs:run.bold=True
        if value is not None:c1.text=value
        else:
            c1.text=''
            for i,(title,body) in enumerate(zip(_activity_titles(r),r['activities'])):
                p=c1.paragraphs[0] if i==0 else c1.add_paragraph();q=p.add_run(title);q.bold=True
                p2=c1.add_paragraph(body);p2.paragraph_format.space_after=Pt(2)
            c1.add_paragraph(r['hint'])
    buffer=BytesIO();d.save(buffer)
    return buffer.getvalue()

def _pdf(r,fields):
    import fitz
    raw=lambda s:escape(str(s),quote=True)
    header_rows=[[('Kelas',_safe_value(fields,'Kelas:')),('Tarikh',_safe_value(fields,'Tarikh:'))],
                 [('Masa',_safe_value(fields,'Masa:')),('Bil. Murid',_safe_value(fields,'Bil. Murid:'))]]
    head='<table class="head" width="100%">'+''.join('<tr>'+''.join('<th width="12%" bgcolor="#F2F5F7">'+raw(a)+'</th><td width="38%">'+raw(b)+'</td>' for a,b in row)+'</tr>' for row in header_rows)+'</table>'
    steps=''.join('<p><b>'+raw(t)+'</b><br/>'+raw(body)+'</p>' for t,body in zip(_activity_titles(r),r['activities']))
    steps+='<p>'+raw(r['hint'])+'</p>'
    rows=[('Kandungan / Tajuk',r['unit']+' • '+r['title']),
      ('Standard Kandungan (SK)',r['sk_code']+' '+r['sk']),
      ('Standard Pembelajaran (SP)',r['sp_code']+' '+r['sp']),
      ('Objektif Pembelajaran',r['objective']),('Kriteria Kejayaan',r['criteria']),
      ('EMK / Nilai','Bahasa; komunikasi berhemah; kerjasama; hormat-menghormati; tanggungjawab.'),
      ('PAK21 / KBAT','Kolaborasi, komunikasi, pemikiran kritis; menerangkan sebab dan membuat pilihan yang bersesuaian.'),
      ('Bahan / BBM',r['material']),('Set Induksi',r['induction']),
      ('Aktiviti Utama',None),('Pengukuhan / PBD',r['pbd']),('Penutup',r['closure']),
      ('Pemulihan',r['remedial']),('Pengayaan',r['extension']),
      ('Refleksi',_reflection(r,fields))]
    body=''.join('<tr><th width="24%" bgcolor="#F4EDE6">'+raw(k)+'</th><td width="76%">'+(steps if v is None else raw(v))+'</td></tr>' for k,v in rows)
    html=f'''<html><head><style>body{{font-family:Arial,sans-serif;font-size:9pt;color:#253748;}}
    .top{{text-align:center;font-size:8pt;font-weight:bold;margin:0;}}
    h1{{font-size:14pt;text-align:center;margin:4px 0;}}
    h2{{font-size:9pt;text-align:center;margin:3px 0 10px 0;}}
    table{{width:100%;border-collapse:collapse;table-layout:fixed;margin-top:8px;}}
    th,td{{font-size:8pt;text-align:left;vertical-align:top;padding:4px 6px;border:0.5pt solid #b7c7d2;}}
    .head th{{background:#f2f5f7;width:11%;}}.head td{{width:39%;}}
    .main th{{background:#f4ede6;width:24%;}}.main td{{width:76%;}}
    .main p{{margin:0 0 4px 0;}}.foot{{font-size:7pt;color:#4a5b6d;margin:6px 0;}}
    </style></head><body><p class="top">BAHASA MELAYU SK • TAHUN 1</p>
    <h1>RANCANGAN PENGAJARAN HARIAN</h1><h2>KUMPULAN {raw(r['group'])} • PdP {r['lesson']:03d} • {raw(r['title'])}</h2>
    {head}<table width="100%" class="main">{body}</table>
    </body></html>'''
    out=BytesIO();w=fitz.DocumentWriter(out)
    story=fitz.Story(html)
    def page_rect(page,filled):return fitz.Rect(0,0,595.28,841.89),fitz.Rect(31,30,564,810),None
    try:story.write(w,page_rect)
    finally:w.close()
    result=out.getvalue()
    if not result.startswith(b'%PDF-'):raise Unavailable('PDF RPH tidak dapat disahkan')
    return result

def render(group,n,fmt,fields=None):
    if fmt not in FMTS:raise Unavailable('Format RPH tidak sah')
    from web.kp2027_pilot_teacher_fields import parse_teacher_fields
    data=lesson(group,n)
    valid=parse_teacher_fields(fields or {})
    output=_docx(data,valid) if fmt=='word' else _pdf(data,valid)
    if not 2000<=len(output)<=200000:raise Unavailable('Saiz RPH tidak sah')
    return output
