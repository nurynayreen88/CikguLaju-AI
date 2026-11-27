"""Export a teacher's saved record snapshots, not a new source RPH."""
from datetime import date
from html import escape
from io import BytesIO

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
    d=Document()
    sec=d.sections[0]
    sec.page_width,sec.page_height=Cm(21),Cm(29.7)
    sec.top_margin=sec.bottom_margin=Cm(1.5)
    sec.left_margin=sec.right_margin=Cm(1.6)
    normal=d.styles['Normal']
    normal.font.name='Arial';normal.font.size=Pt(10)
    normal.paragraph_format.space_after=Pt(4)
    normal.paragraph_format.widow_control=True
    for i,row in enumerate(rows):
        if i:d.add_page_break()
        p=d.add_paragraph()
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        r=p.add_run('REKOD e-RPH');r.bold=True;r.font.size=Pt(15);r.font.color.rgb=RGBColor.from_string('24566B')
        d.add_heading(row['subject_name'],level=2)
        for line in header(row):d.add_paragraph(line)
        for label,value in sections(row):
            p=d.add_paragraph()
            p.paragraph_format.keep_with_next=True
            p.add_run(label).bold=True
            d.add_paragraph(value)
    out=BytesIO();d.save(out)
    return out.getvalue()

def pdf(rows):
    import fitz
    # Use MuPDF's HTML layout; do not truncate content or shrink to fit one page.
    # RTL scripts require a separate verified font/layout pipeline.
    for row in rows:
        for value in (row['subject_name'],*header(row),*(v for _,v in sections(row))):
            if any('\u0590'<=ch<='\u08ff' or '\uFB1D'<=ch<='\uFEFF' for ch in value):
                raise ValueError('Eksport PDF Jawi/Arab belum disahkan. Gunakan Word.')
    def h(s):return escape(s).replace('\n','<br/>')
    out=BytesIO()
    writer=fitz.DocumentWriter(out)
    page=fitz.paper_rect('a4')
    rect=page+ (45,43,-45,-43)
    count=0
    try:
        for row in rows:
            html='<h1>REKOD e-RPH</h1><h2>'+h(row['subject_name'])+'</h2>'
            html+='<p>'+ '<br/>'.join(h(s) for s in header(row))+'</p>'
            html+=''.join('<h3>'+h(label)+'</h3><p>'+h(value)+'</p>' for label,value in sections(row))
            story=fitz.Story(html=html,user_css='body{font-family:sans-serif;font-size:10pt;line-height:1.25}h1{font-size:15pt;color:#24566b;text-align:center}h2{font-size:13pt}h3{font-size:11pt;color:#24566b;margin-bottom:3pt}p{margin-top:0;margin-bottom:7pt;overflow-wrap:break-word}')
            more=True
            while more:
                count+=1
                if count>200:raise ValueError('Eksport terlalu panjang; pilih rekod harian.')
                more,filled=story.place(rect)
                if fitz.Rect(filled).is_empty:raise ValueError('Kandungan PDF tidak muat.')
                device=writer.begin_page(page)
                story.draw(device)
                writer.end_page()
    finally:
        writer.close()
    return out.getvalue()

def render(rows,fmt):
    validate_rows(rows)
    if fmt=='word':return word(rows)
    if fmt=='pdf':return pdf(rows)
    raise ValueError('Format tidak sah.')
