"""Export a teacher's saved record snapshots, not a new source RPH."""
from datetime import date
from html import escape
from io import BytesIO
from unicodedata import normalize
from textwrap import wrap

MAX_RECORDS=80
MAX_CHARS=300000
LABELS=(('title','Tajuk'),('standard_content','Standard Kandungan / Kandungan Pembelajaran'),
        ('standard_learning','Standard Pembelajaran'),('objectives','Objektif Pembelajaran'),
        ('activities','Aktiviti PdP'),('reflection','Refleksi'))

def sections(row):
    return [(label,str(row.get(k) or '')) for k,label in LABELS]

def header(row):
    return (
        'Tarikh: '+date.fromisoformat(row['teaching_date']).strftime('%d/%m/%Y'),
        'Kelas: '+row['class_name'],
        'Masa: '+row['start_time'][:5]+' - '+row['end_time'][:5],
        'Format: '+('Ringkas 5P' if row['rph_format']=='5p' else 'Biasa'),
        'Status: '+{'draft':'Draf','saved':'Disediakan','completed':'PdP selesai'}[row['status']],
    )

def validate_rows(rows):
    if not rows or len(rows)>MAX_RECORDS:
        raise ValueError('Pilih antara 1 hingga 80 rekod untuk setiap eksport.')
    if sum(len(str(v)) for row in rows for v in row.values())>MAX_CHARS:
        raise ValueError('Rekod terlalu panjang. Pilih paparan harian.')
    for row in rows:
        header(row)
        if not isinstance(row.get('subject_name'),str):
            raise ValueError('Rekod tidak sah.')

def word(rows):
    from docx import Document
    from docx.shared import Cm, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    d=Document()
    sec=d.sections[0]
    sec.page_width,sec.page_height=Cm(21),Cm(29.7)
    sec.top_margin=sec.bottom_margin=Cm(1.5)
    sec.left_margin=sec.right_margin=Cm(1.6)
    normal=d.styles['Normal']
    normal.font.name='Arial';normal.font.size=Pt(10)
    normal.paragraph_format.space_after=Pt(2)
    normal.paragraph_format.line_spacing=1.0
    normal.paragraph_format.widow_control=True
    footer=sec.footer.paragraphs[0]
    footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run('Halaman ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    for i,row in enumerate(rows):
        p=d.add_paragraph()
        if i:p.paragraph_format.page_break_before=True
        p.paragraph_format.keep_with_next=True
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        r=p.add_run('REKOD e-RPH');r.bold=True;r.font.size=Pt(15);r.font.color.rgb=RGBColor.from_string('24566B')
        d.add_heading(row['subject_name'],level=2)
        lines=header(row)
        d.add_paragraph('  |  '.join(lines[:3]))
        d.add_paragraph('  |  '.join(lines[3:]))
        for label,value in sections(row):
            p=d.add_paragraph()
            p.paragraph_format.keep_with_next=True
            p.add_run(label).bold=True
            d.add_paragraph(value.replace('\r\n','\n').replace('\r','\n'))
    out=BytesIO();d.save(out)
    return out.getvalue()

def _compact(text):
    return ''.join(ch for ch in normalize('NFC',text) if not ch.isspace())

def pdf(rows):
    import fitz
    # Use MuPDF's HTML layout; do not truncate content or shrink to fit one page.
    # RTL scripts require a separate verified font/layout pipeline.
    for row in rows:
        for value in (row['subject_name'],*header(row),*(v for _,v in sections(row))):
            if any('\u0590'<=ch<='\u08ff' or '\uFB1D'<=ch<='\uFEFF' for ch in value):
                raise ValueError('Eksport PDF Jawi/Arab belum disahkan. Gunakan Word.')
    def h(s):return escape(s.replace('\r\n','\n').replace('\r','\n')).replace('\n','<br/>')
    out=BytesIO()
    writer=fitz.DocumentWriter(out)
    page=fitz.paper_rect('a4')
    rect=page+ (45,43,-45,-43)
    count=0
    ranges=[]
    try:
        for row in rows:
            first=count
            # Lay out independent, bounded pages: MuPDF Story continuation can
            # omit text for long paragraphs. The final exact-text check stays on.
            nodes=['<h1>REKOD e-RPH</h1>','<h2>'+h(row['subject_name'])+'</h2>',
                   '<p>'+h('  |  '.join(header(row)[:3]))+'<br/>'+h('  |  '.join(header(row)[3:]))+'</p>']
            for label,value in sections(row):
                nodes.append('<h3>'+h(label)+'</h3>')
                for line in value.replace('\r\n','\n').replace('\r','\n').split('\n'):
                    parts=wrap(line,width=80,break_long_words=False,break_on_hyphens=False,replace_whitespace=False) or ['']
                    nodes.extend('<p class="line">'+(h(part) if part else '&nbsp;')+'</p>' for part in parts)
            css='body{font-family:sans-serif;font-size:10pt;line-height:1.1}h1{font-size:15pt;color:#24566b;text-align:center}h2{font-size:13pt}h3{font-size:11pt;color:#24566b;margin-bottom:2pt}p{margin-top:0;margin-bottom:4pt;overflow-wrap:break-word}p.line{margin:0}'
            while nodes:
                size=min(30,len(nodes))
                while size:
                    if size<len(nodes) and nodes[size-1].startswith('<h'):
                        size-=1
                        continue
                    story=fitz.Story(html=''.join(nodes[:size]),user_css=css)
                    more,filled=story.place(rect+(0,4,0,-4))
                    if not more and not fitz.Rect(filled).is_empty:break
                    size-=1
                if not size:raise ValueError('Kandungan PDF tidak muat. Gunakan Word.')
                count+=1
                if count>200:raise ValueError('Eksport terlalu panjang; pilih rekod harian.')
                device=writer.begin_page(page)
                story.draw(device)
                writer.end_page()
                del nodes[:size]
            ranges.append((first,count,row))
    finally:
        writer.close()
    # Fail closed instead of delivering a document with missing or clipped text.
    with fitz.open(stream=out.getvalue(),filetype='pdf') as doc:
        for first,last,row in ranges:
            expected=['REKOD e-RPH',row['subject_name'],'  |  '.join(header(row)[:3]),'  |  '.join(header(row)[3:])]
            for label,value in sections(row):expected.extend((label,value))
            actual=''.join(doc[i].get_text(flags=fitz.TEXTFLAGS_TEXT & ~fitz.TEXT_PRESERVE_LIGATURES) for i in range(first,last))
            if _compact(actual)!=_compact(''.join(expected)):
                raise ValueError('Kandungan PDF tidak sepadan sepenuhnya. Gunakan Word.')
            for i in range(first,last):
                pg=doc[i]
                for block in pg.get_text('dict')['blocks']:
                    for line in block.get('lines',[]):
                        if not (rect.x0-2<=line['bbox'][0] and line['bbox'][2]<=rect.x1+2 and rect.y0-2<=line['bbox'][1] and line['bbox'][3]<=rect.y1+2):
                            raise ValueError('Kandungan PDF melebihi ruang cetak. Gunakan Word.')
        for i,pg in enumerate(doc):
            pg.insert_text((45,pg.rect.height-22),'CikguLaju | Rekod e-RPH',fontsize=8,color=(0.35,0.4,0.45))
            pg.insert_textbox(fitz.Rect(pg.rect.width-160,pg.rect.height-30,pg.rect.width-45,pg.rect.height-13),
                              'Halaman '+str(i+1)+' / '+str(len(doc)),fontsize=8,align=fitz.TEXT_ALIGN_RIGHT,color=(0.35,0.4,0.45))
        return doc.tobytes(garbage=3,deflate=True)

def render(rows,fmt):
    validate_rows(rows)
    if fmt=='word':return word(rows)
    if fmt=='pdf':return pdf(rows)
    raise ValueError('Format tidak sah.')
