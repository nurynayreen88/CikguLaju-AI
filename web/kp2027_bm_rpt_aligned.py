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

# Reviewed first-occurrence source rows: demonstration, guided practice,
# then application. These are original activities, not generated replacements.
_ACTIVITY_ORDER_ANCHORS = {
    "1.1.1": 1, "2.1.1": 2, "3.1.1": 3, "4.1.1": 4,
    "3.1.2": 5, "2.1.2": 6, "1.1.2": 13, "4.1.2": 16,
    "3.1.3": 17, "1.1.3": 23, "2.1.3": 24, "4.1.3": 26,
    "3.2.1": 27, "1.2.1": 28, "2.2.1": 29, "4.2.1": 31,
    "3.2.2": 32, "2.2.2": 33, "1.2.2": 40, "4.2.2": 43,
    "3.2.3": 44, "2.3.1": 45, "1.2.3": 52, "2.3.2": 57,
    "1.2.4": 63, "2.3.3": 69,
}


def _ordered_activities(record, source):
    """Only restore reviewed ordering when all three original steps match."""
    anchor_no = _ACTIVITY_ORDER_ANCHORS.get(record.get("sp_code"))
    anchor = source.get("A", {}).get(str(anchor_no), {})
    original = record.get("activities")
    preferred = anchor.get("activities")
    if (anchor.get("sp_code") != record.get("sp_code")
            or not isinstance(original, list) or not isinstance(preferred, list)
            or len(original) != 3 or len(preferred) != 3
            or not all(isinstance(step, str) for step in original + preferred)
            or sorted(original) != sorted(preferred)
            or original == preferred):
        return record
    return {**record, "activities": list(preferred)}


def lesson(group,n):
    if group not in COUNTS or type(n) is not int or not 1<=n<=COUNTS[group]:
        raise Unavailable('Pilihan PdP BM SK tidak sah')
    record = approved_source()[group][str(n)]
    # DK BPK KPM 2026, BM SK Tahun 1, ISBN 978-967-420-797-7,
    # printed pp.39 and 44. Preserve the SHA-pinned penataran source and
    # every other lesson field; only correct the two exact legacy SK labels.
    corrected = {
        "3.2": ("Membaca dan memahami pelbagai maklumat penting dengan jelas dan tepat.",
                "Membaca dan memahami pelbagai maklumat penting secara jelas dan tepat."),
        "4.1": ("Menulis ayat secara mekanis.",
                "Menulis ayat secara mekanis dengan betulnya dan kemasnya."),
    }.get(record["sk_code"])
    if corrected and record["sk"] == corrected[0]:
        record = {**record, "sk": corrected[1]}
    return _ordered_activities(record, approved_source())

def _safe_value(fields,key):
    return fields.get(key,'') or ''

def _reflection(r,fields):
    mode=fields.get('_reflection_mode','auto')
    if mode=='manual':return fields.get('_reflection','')
    # Do not infer mastery counts from the teacher's class size or RPT.
    return (r['criteria']+'\n'
            'Bilangan murid menguasai:        Bilangan murid belum menguasai:        \n'
            'Tindakan susulan: '+r['remedial'])

def _activity_titles(r):return [f'Aktiviti 1 – {r["title"]}','Aktiviti 2 – Bimbingan dan Kerjasama','Aktiviti 3 – Aplikasi Individu']

def _docx(r,fields):
    from docx import Document
    from docx.shared import Cm, Pt, Twips
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    d=Document();sec=d.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.left_margin=Cm(1.25);sec.right_margin=Cm(1.25);sec.top_margin=Cm(1.05);sec.bottom_margin=Cm(1.0)
    d.styles['Normal'].font.name='Times New Roman';d.styles['Normal'].font.size=Pt(9)
    d.styles['Normal'].paragraph_format.space_after=Pt(0)
    def para(text,size=9,bold=False):
        p=d.add_paragraph();p.alignment=1;p.paragraph_format.space_after=Pt(3)
        q=p.add_run(text);q.bold=bold;q.font.size=Pt(size);q.font.name='Times New Roman'
    para('RANCANGAN PENGAJARAN HARIAN',14,True)
    def sh(cell,fill):
        tc=cell._tc.get_or_add_tcPr();node=OxmlElement('w:shd');node.set(qn('w:fill'),fill);tc.append(node)
    def grid(cell):
        tc=cell._tc.get_or_add_tcPr();bd=OxmlElement('w:tcBorders')
        for side in ('top','left','bottom','right'):
            item=OxmlElement('w:'+side);item.set(qn('w:val'),'single');item.set(qn('w:sz'),'5');item.set(qn('w:color'),'BAC7D0');bd.append(item)
        tc.append(bd)
    head=d.add_table(rows=1,cols=2);head.autofit=False;head.alignment=WD_TABLE_ALIGNMENT.CENTER
    # Use the exact same total twip width as the main grid.
    right=Cm(12.6).twips;left=Cm(4.2).twips+Cm(14.3).twips-right
    for col,w in zip(head.columns,[left,right]):col.width=Twips(w)
    info,hero=head.rows[0].cells
    info.width=Twips(left);hero.width=Twips(right)
    sh(hero,'DBE8F5');sh(info,'F4F7FA');grid(hero);grid(info)
    for j,(value,bold,size) in enumerate((
        ('BAHASA MELAYU SK',True,11),
        ('Tahun 1',False,9),
        ('Tajuk: '+r['title'],False,9),
        ('Kandungan: '+r['unit'],False,9),
    )):
        p=hero.paragraphs[0] if j==0 else hero.add_paragraph()
        q=p.add_run(value);q.bold=bold;q.font.size=Pt(size)
    info.paragraphs[0].add_run('Maklumat PdP').bold=True
    for label in ('Kelas:','Tarikh:','Masa:','Bil. Murid:'):
        p=info.add_paragraph()
        p.add_run(label+' ')
        p.add_run(_safe_value(fields,label))
    gap=d.add_paragraph()
    gap.paragraph_format.space_after=Pt(0)
    gap.paragraph_format.line_spacing=Pt(1)
    gap.add_run(' ').font.size=Pt(1)
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
    t.columns[0].width=Cm(4.2);t.columns[1].width=Cm(14.3)
    for j,(label,value) in enumerate(rows):
        c0,c1=t.rows[j].cells;c0.width=Cm(4.2);c1.width=Cm(14.3)
        c0.text=label;sh(c0,'EDF3FA');grid(c0);grid(c1)
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
    # PyMuPDF is already installed in production. Measure each cell at its
    # fixed width before drawing, rather than letting HTML tables collapse
    # empty teacher fields. No additional renderer dependency is required.
    import fitz
    normal_css=("body{font-family:serif;font-size:9pt;line-height:1.25;"
                "margin:0;padding:0;color:#253748;}p{margin:0;padding:0;}")
    title_css=normal_css+"body{font-size:15pt;text-align:center;}"
    hero_css=normal_css+"body{font-size:9.5pt;line-height:1.3;}b.subject{font-size:11pt;}"
    label_css=normal_css+"body{font-size:9.5pt;}"
    tone=(237/255,243/255,250/255);strong=(219/255,232/255,245/255)
    border=(186/255,199/255,208/255)
    page_w,page_h=595.28,841.89
    left=37.14;total=521.0;bottom=page_h-23
    def raw(value):return escape(str(value),quote=False).replace('\n','<br/>')
    def measure(html,width,css):
        story=fitz.Story(html,user_css=css)
        more,filled=story.place(fitz.Rect(0,0,width,750))
        if more:raise Unavailable('Kandungan sel RPH melebihi satu halaman')
        return filled[3]-filled[1]+1.5
    def place(page,rect,html,css):
        spare,scale=page.insert_htmlbox(rect,html,css=css,scale_low=1)
        if spare<0 or scale!=1:raise Unavailable('Ruang teks RPH tidak dapat disahkan')
    document=fitz.open()
    def new_page():
        page=document.new_page(width=page_w,height=page_h)
        title='<b>RANCANGAN PENGAJARAN HARIAN</b>'
        h=measure(title,total,title_css)
        place(page,fitz.Rect(left,23,left+total,23+h),title,title_css)
        return page,max(75,23+h+5)
    page,y=new_page()
    identity=('<b class="subject">BAHASA MELAYU SK</b><br/>Tahun 1<br/>'
        +raw('Tajuk: '+r['title'])+'<br/>'+raw('Kandungan: '+r['unit']))
    info='<b>Maklumat PdP</b><br/>'+'<br/>'.join(raw(k)+' '+raw(_safe_value(fields,k))
        for k in ('Kelas:','Tarikh:','Masa:','Bil. Murid:'))
    def row_height(cells,widths,styles):
        return max(measure(value,w-14,css) for value,w,css in zip(cells,widths,styles))+8
    def draw_row(page,y,cells,widths,styles,fills):
        h=row_height(cells,widths,styles)
        x=left
        for value,w,css,fill in zip(cells,widths,styles,fills):
            page.draw_rect(fitz.Rect(x,y,x+w,y+h),color=border,fill=fill,width=.55)
            text_h=measure(value,w-14,css)
            inset=(h-text_h)/2
            place(page,fitz.Rect(x+7,y+inset,x+w-7,y+inset+text_h),value,css)
            x+=w
        return y+h
    y=draw_row(page,y,[info,identity],[166,355],[hero_css,hero_css],[(244/255,247/255,250/255),strong])
    steps='<br/>'.join('<b>'+raw(heading)+'</b><br/>'+raw(body)
        for heading,body in zip(_activity_titles(r),r['activities']))
    steps+='<br/>'+raw(r['hint'])
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
    try:
        for label,value in rows:
            cells=['<b>'+raw(label)+'</b>',steps if value is None else raw(value)]
            widths=[118,403];styles=[label_css,normal_css]
            h=row_height(cells,widths,styles)
            if y+h>bottom:page,y=new_page()
            if y+h>bottom:raise Unavailable('Kandungan RPH tidak dapat dimuatkan pada A4')
            y=draw_row(page,y,cells,widths,styles,[tone,(1,1,1)])
        result=document.tobytes(garbage=4,deflate=True)
    finally:
        document.close()
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
