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
    from docx.shared import Cm, Pt, RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    d=Document();sec=d.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.left_margin=Cm(1.25);sec.right_margin=Cm(1.25);sec.top_margin=Cm(1.05);sec.bottom_margin=Cm(1.0)
    d.styles['Normal'].font.name='Arial';d.styles['Normal'].font.size=Pt(9)
    d.styles['Normal'].paragraph_format.space_after=Pt(0)
    def para(text,size=9,bold=False):
        p=d.add_paragraph();p.alignment=1;p.paragraph_format.space_after=Pt(3)
        q=p.add_run(text);q.bold=bold;q.font.size=Pt(size);q.font.name='Arial'
    para('RANCANGAN PENGAJARAN HARIAN',14,True)
    def sh(cell,fill):
        tc=cell._tc.get_or_add_tcPr();node=OxmlElement('w:shd');node.set(qn('w:fill'),fill);tc.append(node)
    def grid(cell):
        tc=cell._tc.get_or_add_tcPr();bd=OxmlElement('w:tcBorders')
        for side in ('top','left','bottom','right'):
            item=OxmlElement('w:'+side);item.set(qn('w:val'),'single');item.set(qn('w:sz'),'5');item.set(qn('w:color'),'BAC7D0');bd.append(item)
        tc.append(bd)
    head=d.add_table(rows=1,cols=2);head.autofit=False;head.alignment=WD_TABLE_ALIGNMENT.CENTER
    for col,w in zip(head.columns,[11.5,7.0]):col.width=Cm(w)
    hero,info=head.rows[0].cells
    hero.width=Cm(11.5);info.width=Cm(7.0)
    sh(hero,'DBE8F5');sh(info,'EDF3FA');grid(hero);grid(info)
    for j,(value,bold,size) in enumerate((
        ('BAHASA MELAYU SK • TAHUN 1',True,11),
        (f'PdP {r["lesson"]:03d} • Kumpulan {r["group"]}',True,9),
        (r['title'],False,9),
    )):
        p=hero.paragraphs[0] if j==0 else hero.add_paragraph()
        q=p.add_run(value);q.bold=bold;q.font.size=Pt(size)
    for j,label in enumerate(('Kelas:','Tarikh:','Masa:','Bil. Murid:')):
        p=info.paragraphs[0] if j==0 else info.add_paragraph()
        p.add_run(label+' ').bold=True
        p.add_run(_safe_value(fields,label))
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
    # Explicit physical widths and fills; no HTML table auto-sizing.
    from reportlab import __file__ as reportlab_file
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    fonts=Path(reportlab_file).parent/'fonts'
    for name,filename in (('CikguBmRegular','Vera.ttf'),('CikguBmBold','VeraBd.ttf')):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name,str(fonts/filename)))
    pdfmetrics.registerFontFamily('CikguBmRegular',normal='CikguBmRegular',bold='CikguBmBold')
    ink=colors.HexColor('#253748')
    tone=colors.HexColor('#EDF3FA');strong=colors.HexColor('#DBE8F5')
    border=colors.HexColor('#BAC7D0')
    normal=ParagraphStyle('BmText',fontName='CikguBmRegular',fontSize=8.5,leading=10.8,textColor=ink)
    label=ParagraphStyle('BmLabel',parent=normal,fontName='CikguBmBold')
    title=ParagraphStyle('BmTitle',parent=label,fontSize=14,leading=17,alignment=TA_CENTER)
    hero=ParagraphStyle('BmHero',parent=normal,fontSize=10,leading=13)
    def raw(value):return escape(str(value),quote=False).replace('\n','<br/>')
    def para(value,style=normal):return Paragraph(raw(value),style)
    def table(rows,widths):
        t=Table(rows,colWidths=widths,hAlign='CENTER',splitByRow=1)
        t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.55,border),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),
            ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),4),
            ('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        return t
    identity=Paragraph('<b>BAHASA MELAYU SK • TAHUN 1</b><br/>'
        +raw(f'PdP {r["lesson"]:03d} • Kumpulan {r["group"]}')+'<br/>'+raw(r['title']),hero)
    info=Paragraph('<br/>'.join('<b>'+raw(k)+'</b> '+raw(_safe_value(fields,k))
        for k in ('Kelas:','Tarikh:','Masa:','Bil. Murid:')),normal)
    header=table([[identity,info]],[324,197])
    header.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),strong),('BACKGROUND',(1,0),(1,0),tone)]))
    steps=[]
    for heading,body in zip(_activity_titles(r),r['activities']):
        steps.append(Paragraph('<b>'+raw(heading)+'</b><br/>'+raw(body),normal))
        steps.append(Spacer(1,2))
    steps.append(para(r['hint']))
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
    body=table([[para(k,label),steps if v is None else para(v)] for k,v in rows],[125,396])
    body.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),tone)]))
    out=BytesIO()
    doc=SimpleDocTemplate(out,pagesize=(595.28,841.89),leftMargin=31,rightMargin=31,topMargin=23,bottomMargin=23)
    doc.build([para('RANCANGAN PENGAJARAN HARIAN',title),Spacer(1,5),header,Spacer(1,6),body])
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
