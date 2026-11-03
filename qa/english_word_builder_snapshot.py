"""Exact copy of current app.py Word table function for offline layout QA.
The function body is checked for AST parity with the last _create_rph_word
definition in app.py at runtime. Metadata helpers are isolated to avoid
importing live Flask, Telegram, configuration and user database code.
"""
import re
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def _rph_rows(s, rows):
    return dict(rows)

def _rph_title(s):
    return "DAILY LESSON PLAN"

def _rph_display_label(s, key):
    return key.title()

def _word_set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        if edge in kwargs:
            edge_data = kwargs.get(edge)
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key in ['val', 'sz', 'space', 'color']:
                if key in edge_data:
                    element.set(qn('w:{}'.format(key)), str(edge_data[key]))

def _word_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' PAGE '
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)

def _rph_format_activity_lines(value):
    """Normalize RPH numbering without regex look-behind/look-ahead patterns."""
    v=str(value or '').replace('\r\n','\n').replace('\r','\n').strip()
    if not v:
        return v
    # Existing RPH content already carries line boundaries. Only normalize each line;
    # do not use look-around regexes that can fail in runtime regex implementations.
    raw_lines=v.split('\n')
    lines=[]
    for x in raw_lines:
        x=re.sub(r'\s+',' ',x).strip()
        if x:
            lines.append(x)
    out=[]
    for line in lines:
        bare=re.sub(r'^\s*\d+\.\s*','',line).strip()
        if re.match(r'^(?:Aktiviti|Activity)\s+\d+\s*[–—-]',bare,re.I):
            out.append(bare)
            continue
        if re.match(r'^\(?\s*\d+\s*(?:minit|minutes?|mins?)\s*\)?$',bare,re.I):
            out.append(bare)
            continue
        # Preserve genuine step numbering if already present; do not invent numbering
        # for semantic activity paragraphs.
        if re.match(r'^\s*\d+\.\s+',line):
            out.append(line.strip())
        else:
            out.append(bare)
    return '\n'.join(out)

def _rph_attendance_value(total):
    """Print the teacher-entered class size directly."""
    total=str(total or '').strip()
    return total if total else '________________'

def _rph_blank_or_value(value, width=28):
    return str(value).strip() if str(value or '').strip() else ('_' * width)

def _is_english_subject(s): return str((s or {}).get('subject') or '').strip().lower() in ('bahasa inggeris','english')

def _rph_display_value(s,key,value):
    v=str(value or '')
    if key in ('AKTIVITI UTAMA','SET INDUKSI','PENUTUP'):
        v=_rph_format_activity_lines(v)
    if not _is_english_subject(s): return v
    if key=='MATA PELAJARAN': return 'English'
    if key=='TAHUN/TINGKATAN': return re.sub(r'^Tahun\\s+','Year ',v,flags=re.I)
    if key=='TAJUK': return v.replace('Semua Subtopik','All Subtopics')
    return v

def _create_rph_word(doc, section, s, ai_text, path):
    rph = _rph_rows(s, ai_text)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = p.add_run(_rph_title(s)); rr.bold=True; rr.font.size=Pt(15)
    p.paragraph_format.space_after = Pt(6)

    def add_row(table, label, value):
        cells = table.add_row().cells
        cells[0].width = Cm(4.4); cells[1].width = Cm(12.5)
        p0=cells[0].paragraphs[0]; p0.paragraph_format.space_after=Pt(0); x=p0.add_run(label); x.bold=True
        p1=cells[1].paragraphs[0]; p1.paragraph_format.space_after=Pt(0)
        parts=(value or '—').split('\n')
        p1.add_run(parts[0])
        for part in parts[1:]: p1.add_run('\n'+part)
        for c in cells:
            _word_set_cell_border(c, top={'val':'single','sz':'6','color':'666666'}, bottom={'val':'single','sz':'6','color':'666666'}, left={'val':'single','sz':'6','color':'666666'}, right={'val':'single','sz':'6','color':'666666'})

    table=doc.add_table(rows=0, cols=2); table.alignment=WD_TABLE_ALIGNMENT.CENTER
    _info_labels=(['MATA PELAJARAN','TAHUN/TINGKATAN','TARIKH','HARI','MASA','KELAS','BILANGAN MURID','TAJUK','MAIN CONTENT STANDARD','MAIN LEARNING STANDARD','COMPLEMENTARY CONTENT STANDARD','COMPLEMENTARY LEARNING STANDARD','OBJEKTIF PEMBELAJARAN','KRITERIA KEJAYAAN','PENGETAHUAN SEDIA ADA','BAHAN BANTU MENGAJAR','EMK / NILAI','KBAT / PAK21','PENTAKSIRAN'] if _is_english_subject(s) else ['MATA PELAJARAN','TAHUN/TINGKATAN','TARIKH','HARI','MASA','KELAS','BILANGAN MURID','TAJUK','STANDARD KANDUNGAN','STANDARD PEMBELAJARAN','OBJEKTIF PEMBELAJARAN','KRITERIA KEJAYAAN','PENGETAHUAN SEDIA ADA','BAHAN BANTU MENGAJAR','EMK / NILAI','KBAT / PAK21','PENTAKSIRAN'])
    for label in _info_labels:
        value=(_rph_attendance_value(rph.get(label,'')) if label == 'BILANGAN MURID' else _rph_blank_or_value(rph.get(label,''))) if label in ('TARIKH','HARI','MASA','KELAS','BILANGAN MURID') else rph.get(label,''); add_row(table,_rph_display_label(s,label),_rph_display_value(s,label,value))
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    t2=doc.add_table(rows=1, cols=3); t2.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,h in enumerate((['Phase / Time','Teaching and Learning Activities','Notes'] if _is_english_subject(s) else ['Fasa / Masa','Aktiviti Pengajaran & Pembelajaran','Catatan'])):
        q=t2.rows[0].cells[i].paragraphs[0]; q.alignment=WD_ALIGN_PARAGRAPH.CENTER; z=q.add_run(h); z.bold=True
    phases=([('Set Induction',rph.get('SET INDUKSI','')),('Main Activities',rph.get('AKTIVITI UTAMA','')),('Closure',rph.get('PENUTUP',''))] if _is_english_subject(s) else [('Set Induksi',rph.get('SET INDUKSI','')),('Aktiviti Utama',rph.get('AKTIVITI UTAMA','')),('Penutup',rph.get('PENUTUP',''))])
    for phase,text in phases:
        cells=t2.add_row().cells; cells[0].text=phase; cells[1].text=_rph_format_activity_lines(text) if text else '—'; cells[2].text=''
    for row in t2.rows:
        for c in row.cells:
            _word_set_cell_border(c, top={'val':'single','sz':'6','color':'666666'}, bottom={'val':'single','sz':'6','color':'666666'}, left={'val':'single','sz':'6','color':'666666'}, right={'val':'single','sz':'6','color':'666666'})
    t3=doc.add_table(rows=0, cols=2); t3.alignment=WD_TABLE_ALIGNMENT.CENTER
    add_row(t3,('Remedial / Enrichment' if _is_english_subject(s) else 'Pemulihan / Pengayaan'),rph.get('PEMULIHAN / PENGAYAAN',''))
    add_row(t3,('Reflection' if _is_english_subject(s) else 'Refleksi'),rph.get('REFLEKSI','') or ('____ / ____ pupils achieved the lesson objectives.\n____ / ____ pupils require further support.\nFollow-up action: ______________________________' if _is_english_subject(s) else '____ / ____ murid mencapai objektif.\n____ / ____ murid belum mencapai objektif.\nTindakan susulan: ______________________________'))
    footer=section.footer; fp=footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER; fr=fp.add_run('CikguLaju AI  •  '); fr.font.size=Pt(7.5); _word_page_number(fp)
    # Compact the active (second) Word RPH renderer, preserving all content.
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(0.75)
    section.bottom_margin = Cm(0.75)
    section.left_margin = Cm(1.1)
    section.right_margin = Cm(1.1)
    section.footer_distance = Cm(0.3)
    doc.styles['Normal'].font.size = Pt(8.5)
    doc.styles['Normal'].paragraph_format.space_after = Pt(0)
    doc.styles['Normal'].paragraph_format.space_before = Pt(0)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(2)
    rr.font.size = Pt(12)
    for tbl in doc.tables:
        tbl.autofit = False
        for row in tbl.rows:
            for cell in row.cells:
                tcPr = cell._tc.get_or_add_tcPr()
                mar = tcPr.find(qn('w:tcMar'))
                if mar is None:
                    mar = OxmlElement('w:tcMar'); tcPr.append(mar)
                for side in ('top','bottom','left','right'):
                    el = mar.find(qn('w:'+side))
                    if el is None:
                        el = OxmlElement('w:'+side); mar.append(el)
                    el.set(qn('w:w'), '18' if side in ('top','bottom') else '50')
                    el.set(qn('w:type'), 'dxa')
                for para in cell.paragraphs:
                    para.paragraph_format.space_before = Pt(0)
                    para.paragraph_format.space_after = Pt(0)
                    para.paragraph_format.line_spacing = 1.0
                    for run in para.runs:
                        run.font.size = Pt(8.5)
    # Give activity text most of the page width; Notes remains available.
    for row in t2.rows:
        for cell, width in zip(row.cells, (Cm(2.65), Cm(12.65), Cm(3.45))):
            cell.width = width
    for tbl in (table,t3):
        for row in tbl.rows:
            for cell,width in zip(row.cells,(Cm(5.3),Cm(13.45))):
                cell.width = width
    doc.save(path); return path
