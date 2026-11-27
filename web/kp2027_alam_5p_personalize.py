"""Populate only empty fields in the pinned Alam 5P template."""
from io import BytesIO
import unicodedata
from docx import Document
from docx.shared import Pt
import fitz

LABELS=('Kelas:','Tarikh:','Masa:','Bil. Murid:')

class LayoutError(ValueError):
    pass

def reflection(criterion, fields):
    if fields['_reflection_mode']=='manual':
        return fields['_reflection']
    return ('Kriteria: '+ ' '.join(criterion.split())+'\n'
            'Menguasai:     Belum menguasai:     Tindakan susulan:')

def word_model(raw):
    doc=Document(BytesIO(raw))
    if len(doc.tables)!=1 or len(doc.tables[0].rows)!=21:
        raise LayoutError('Templat Word 5P tidak sepadan.')
    t=doc.tables[0]
    if t.cell(1,0).text.splitlines()!=list(LABELS) or t.cell(6,0).text!='Kriteria Kejayaan' or t.cell(20,0).text!='Refleksi' or t.cell(20,1).text.strip():
        raise LayoutError('Medan Word 5P tidak sepadan.')
    return doc,t

def pdf_safe(s):
    s=unicodedata.normalize('NFKC',s.translate(str.maketrans({'–':'-','—':'-','’':"'",'‘':"'",'“':'"','”':'"','…':'...'})))
    try:s.encode('latin-1')
    except UnicodeEncodeError as exc:raise LayoutError('Aksara tidak disokong dalam PDF. Gunakan Word.') from exc
    return s

def anchor(page,label):
    matches=[r for r in page.search_for(label) if r.x0<100]
    if len(matches)!=1:raise LayoutError('Medan PDF 5P tidak sepadan.')
    return matches[0]

def fill_pdf(raw,fields,ref):
    with fitz.open(stream=raw,filetype='pdf') as doc:
        if doc.page_count!=1:raise LayoutError('PDF 5P bukan satu halaman.')
        p=doc[0]
        if abs(p.rect.width-595.28)>2 or abs(p.rect.height-841.89)>2:raise LayoutError('Saiz PDF bukan A4.')
        for label in LABELS:
            value=pdf_safe(fields[label]); a=anchor(p,label)
            if not 50<a.y0<130:raise LayoutError('Kedudukan profil 5P tidak sepadan.')
            if not value:continue
            x=a.x1+3
            if fitz.get_text_length(value,fontname='helv',fontsize=9)>156-x:raise LayoutError('Maklumat kelas atau masa terlalu panjang untuk PDF. Gunakan Word.')
            p.insert_text((x,a.y1-2.1),value,fontname='helv',fontsize=9)
        a=anchor(p,'Refleksi')
        boxes={tuple(round(v,2) for v in d['rect']) for d in p.get_drawings() if d['type']=='f' and d['rect'].x0<45 and 155<d['rect'].x1<170 and d['rect'].contains(a)}
        if len(boxes)!=1:raise LayoutError('Ruang refleksi 5P tidak sepadan.')
        x0,y0,x1,y1=boxes.pop(); region=fitz.Rect(x1+5,y0+3,548,y1-3)
        if p.get_text('text',clip=region).strip():raise LayoutError('Ruang refleksi 5P bukan kosong.')
        safe=pdf_safe(ref)
        if p.insert_textbox(region,safe,fontname='helv',fontsize=9,lineheight=1.08)<0:
            raise LayoutError('Refleksi tidak muat pada 9 pt. Ringkaskan refleksi atau guna Word.')
        return doc.tobytes(garbage=4,deflate=True)

def personalize(word,pdf,fmt,fields):
    doc,t=word_model(word)
    ref=reflection(t.cell(6,1).text,fields)
    if fmt=='pdf':return fill_pdf(pdf,fields,ref)
    if fmt!='word':raise LayoutError('Format 5P tidak sah.')
    # A single run holds the header lines in the source template.
    p=t.cell(1,0).paragraphs[0]
    for run in p.runs:run.text=''
    for n,label in enumerate(LABELS):
        if n:p.add_run().add_break()
        r=p.add_run(label);r.bold=True;r.font.size=Pt(10)
        if fields[label]:
            r=p.add_run(' '+fields[label]);r.bold=False;r.font.size=Pt(9)
    cell=t.cell(20,1);cell.text=ref
    for p in cell.paragraphs:
        for r in p.runs:r.font.size=Pt(9)
    out=BytesIO();doc.save(out);return out.getvalue()
