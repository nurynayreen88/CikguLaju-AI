"""Exact copy of current app.py Word table function for offline layout QA.
The active builder and its layout helpers are checked for AST parity.
English metadata helpers are isolated to avoid
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

_EN_RPH_LABELS={
'MATA PELAJARAN':'Subject','TAHUN/TINGKATAN':'Year / Form','TARIKH':'Date','HARI':'Day','MASA':'Time','KELAS':'Class','BILANGAN MURID':'Number of Pupils','TAJUK':'Topic',
'STANDARD KANDUNGAN':'Content Standard','STANDARD PEMBELAJARAN':'Learning Standard','MAIN CONTENT STANDARD':'Main Content Standard','MAIN LEARNING STANDARD':'Main Learning Standard','COMPLEMENTARY CONTENT STANDARD':'Complementary Content Standard','COMPLEMENTARY LEARNING STANDARD':'Complementary Learning Standard','OBJEKTIF PEMBELAJARAN':'Learning Objectives','KRITERIA KEJAYAAN':'Success Criteria','PENGETAHUAN SEDIA ADA':'Prior Knowledge','BAHAN BANTU MENGAJAR':'Teaching and Learning Materials','EMK / NILAI':'Cross-Curricular Elements / Values','KBAT / PAK21':'HOTS / 21st Century Learning','PENTAKSIRAN':'Assessment','SET INDUKSI':'Set Induction','AKTIVITI UTAMA':'Main Activities','PENUTUP':'Closure','PEMULIHAN / PENGAYAAN':'Remedial / Enrichment','REFLEKSI':'Reflection'}

def _rph_display_label(s,key): return _EN_RPH_LABELS.get(key,key.title()) if _is_english_subject(s) else (key if key in ('EMK / NILAI','KBAT / PAK21') else key.title())

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
    if key=='TAHUN/TINGKATAN': return re.sub(r'^Tahun\s+','Year ',v,flags=re.I)
    if key=='TAJUK': return v.replace('Semua Subtopik','All Subtopics')
    return v

def _rph_phase_time_v25179(phase, text):
    """Format the phase for the downloadable RPH without timing annotations."""
    from web.rph_phase_display import activity_without_schedule

    return phase, activity_without_schedule(_rph_format_activity_lines(text or ''))


def _pi_primary_v25210(state):
    # This isolated snapshot validates English documents.
    return False


# Science styling does not apply to the isolated English rows.
def sequence_year(state):
    return None


def _rph_document_rows(s, rows):
    raw_title = rows.get('TAJUK') or ''
    title = re.sub(r'^(?:CADANGAN CIKGULAJU \(DRAF\)|DRAF CADANGAN)\s*[—–-]\s*', '', raw_title)
    title = re.sub(r'\s*(?:\[DRAF CADANGAN — SEMAK GURU\]|\(DRAF(?: UNTUK SEMAKAN)?\))$', '', title)
    if title != raw_title:
        rows = {**rows, 'TAJUK': title}
    if s.get('subject') == 'Bahasa Melayu':
        fields = ('STANDARD KANDUNGAN', 'STANDARD PEMBELAJARAN')
        rows = {**rows, **{
            key: re.sub(r'(?<![\d.])(\d+(?:\.\d+)+)(?:[ \t]+\1(?![\d.]))+',
                        r'\1', rows[key])
            for key in fields if isinstance(rows.get(key), str)
        }}
    if s.get('subject') == 'Sains':
        from web.sains_rph_standard_descriptions import describe_rows
        rows = describe_rows(s, rows)
    if _pi_primary_v25210(s):
        # Replace the generator's own source labels without altering the lesson anchors.
        wording = {
            'STANDARD PEMBELAJARAN': (' مڠيکوت RPT 2026', ''),
            'OBJEKTIF PEMBELAJARAN': ('فوکوس RPT', 'فوکوس ڤدڤ'),
            'BAHAN BANTU MENGAJAR': ('، باهن RPT دان', ' دان'),
            'AKTIVITI UTAMA': ('توݢسن RPT يڠ دصحکن', 'توݢسن ڤمبلاجرن'),
        }
        rows = {**rows, **{key: (rows.get(key) or '').replace(old, new)
                           for key, (old, new) in wording.items()}}
    return rows


def _rph_table_labels(s, pi_primary):
    if pi_primary:
        return (
            ('فاسا', 'اکتيۏيتي ڤڠاجرن دان ڤمبلاجرن', 'چاتتن'),
            ('ست ايندوکسي', 'اکتيۏيتي اوتام', 'ڤنوتوڤ'),
            ('ڤموليهن / ڤڠاياءن', 'رفليكسي'),
        )
    if _is_english_subject(s):
        return (
            ('Phase', 'Teaching and Learning Activities', 'Notes'),
            ('Set Induction', 'Main Activities', 'Closure'),
            ('Remedial / Enrichment', 'Reflection'),
        )
    return (
        ('Fasa', 'Aktiviti Pengajaran & Pembelajaran', 'Catatan'),
        ('Set Induksi', 'Aktiviti Utama', 'Penutup'),
        ('Pemulihan / Pengayaan', 'Refleksi'),
    )


def _create_rph_word(doc, section, s, ai_text, path):
    from docx.enum.table import WD_TABLE_DIRECTION
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from web.sains_rph_standard_descriptions import sequence_year

    rph = _rph_rows(s, ai_text)
    rph = _rph_document_rows(s, rph)
    body_size = 9.25 if rph.get('CATATAN AKTIVITI UTAMA') else 8.5
    pi_primary = _pi_primary_v25210(s)
    science_primary = bool(sequence_year(s))
    label_fill = _PI_RPH_FILL if pi_primary else _SAINS_RPH_FILL if science_primary else None
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
        value = rph.get(label, '')
        if label == 'BILANGAN MURID':
            value = _rph_attendance_value(value)
        elif label in ('TARIKH', 'HARI', 'MASA', 'KELAS'):
            value = _rph_blank_or_value(value)
        elif pi_primary and label == 'STANDARD PEMBELAJARAN':
            value = _dedup_standard_lines_v25216(value).replace('<br/>', '\n')
        add_row(table, _rph_display_label(s, label), _rph_display_value(s, label, value))
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    t2=doc.add_table(rows=1, cols=3); t2.alignment=WD_TABLE_ALIGNMENT.CENTER
    activity_header, phase_labels, tail_labels = _rph_table_labels(s, pi_primary)
    for i,h in enumerate(activity_header):
        q=t2.rows[0].cells[i].paragraphs[0]; q.alignment=WD_ALIGN_PARAGRAPH.CENTER; z=q.add_run(h); z.bold=True
    for phase, key in zip(phase_labels, ('SET INDUKSI', 'AKTIVITI UTAMA', 'PENUTUP')):
        cells = t2.add_row().cells
        cells[0].text = phase
        _, activity = _rph_phase_time_v25179(phase, rph.get(key, ''))
        activity = activity or '—'
        note = rph.get(f'CATATAN {key}', '')
        if key == 'AKTIVITI UTAMA' and pi_primary:
            paragraph = cells[1].paragraphs[0]
            for index, (line, heading) in enumerate(_pi_rph_activity_lines(activity)):
                if index:
                    paragraph.add_run().add_break()
                run = paragraph.add_run(line)
                run.font.rtl = True
                if heading:
                    run.bold = True
                    run.font.cs_bold = True
        elif note:
            paragraph = cells[1].paragraphs[0]
            for index, line in enumerate(activity.splitlines()):
                if index:
                    paragraph.add_run().add_break()
                paragraph.add_run(line).bold = line in ('Activity 1', 'Activity 2', 'Activity 3')
        else:
            cells[1].text = activity
        cells[2].text = note
    for row in t2.rows:
        for c in row.cells:
            _word_set_cell_border(c, top={'val':'single','sz':'6','color':'666666'}, bottom={'val':'single','sz':'6','color':'666666'}, left={'val':'single','sz':'6','color':'666666'}, right={'val':'single','sz':'6','color':'666666'})
    t3=doc.add_table(rows=0, cols=2); t3.alignment=WD_TABLE_ALIGNMENT.CENTER
    add_row(t3,tail_labels[0],rph.get('PEMULIHAN / PENGAYAAN',''))
    add_row(t3,tail_labels[1],rph.get('REFLEKSI','') or ('____ / ____ pupils achieved the lesson objectives.\n____ / ____ pupils require further support.\nFollow-up action: ______________________________' if _is_english_subject(s) else '____ / ____ murid mencapai objektif.\n____ / ____ murid belum mencapai objektif.\nTindakan susulan: ______________________________'))
    footer=section.footer; fp=footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER; fr=fp.add_run('CikguLaju AI  •  '); fr.font.size=Pt(7.5); _word_page_number(fp)
    # Compact the active (second) Word RPH renderer, preserving all content.
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(0.75)
    section.bottom_margin = Cm(0.75)
    section.left_margin = Cm(1.1)
    section.right_margin = Cm(1.1)
    section.footer_distance = Cm(0.3)
    doc.styles['Normal'].font.size = Pt(body_size)
    if pi_primary:
        rpr = doc.styles['Normal'].element.get_or_add_rPr()
        size_cs = rpr.find(qn('w:szCs'))
        if size_cs is None:
            size_cs = OxmlElement('w:szCs')
            rpr.append(size_cs)
        size_cs.set(qn('w:val'), '20')
    doc.styles['Normal'].paragraph_format.space_after = Pt(0)
    doc.styles['Normal'].paragraph_format.space_before = Pt(0)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(2)
    rr.font.size = Pt(12)

    def align_pi(paragraph):
        if _has_jawi_v25213(paragraph.text):
            props = paragraph._p.get_or_add_pPr()
            props.insert_element_before(OxmlElement('w:bidi'), 'w:jc')
            props.get_or_add_jc().set(qn('w:val'), 'start')
        else:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    if pi_primary:
        align_pi(p)
        rr.font.cs_bold = True
    for tbl in (table, t2, t3):
        tbl.autofit = False
        if pi_primary:
            tbl.table_direction = WD_TABLE_DIRECTION.RTL
        for row_index, row in enumerate(tbl.rows):
            for column_index, cell in enumerate(row.cells):
                tcPr = cell._tc.get_or_add_tcPr()
                pi_label_cell = pi_primary and (column_index == 0 or (tbl is t2 and row_index == 0))
                if label_fill and (column_index == 0 or (tbl is t2 and row_index == 0)):
                    shade = OxmlElement('w:shd')
                    shade.set(qn('w:val'), 'clear')
                    shade.set(qn('w:fill'), label_fill)
                    tcPr.insert_element_before(shade, 'w:tcMar')
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
                    if pi_primary:
                        align_pi(para)
                    para.paragraph_format.space_before = Pt(0)
                    para.paragraph_format.space_after = Pt(0)
                    para.paragraph_format.line_spacing = 0.96 if pi_primary else 1.0
                    for run in para.runs:
                        run.font.size = Pt(body_size)
                        if pi_label_cell:
                            run.bold = True
                            run.font.cs_bold = True
    tight_science_notes = science_primary and not any(
        rph.get('CATATAN ' + phase) for phase in ('SET INDUKSI', 'AKTIVITI UTAMA', 'PENUTUP')
    )
    phase_widths = (2.65, 14.55, 1.55) if tight_science_notes else (2.65, 12.65, 3.45)
    # Keep the same Word grid and cell widths for RPH with populated Notes.
    if pi_primary or science_primary or rph.get('CATATAN AKTIVITI UTAMA'):
        for tbl, widths in ((t2, phase_widths), (table, (5.3, 13.45)), (t3, (5.3, 13.45))):
            for column, width in zip(tbl.columns, widths):
                column.width = Cm(width)
    # Give activity text most of the page width; Notes remains available.
    for row in t2.rows:
        for cell, width in zip(row.cells, phase_widths):
            cell.width = Cm(width)
    for tbl in (table,t3):
        for row in tbl.rows:
            for cell,width in zip(row.cells,(Cm(5.3),Cm(13.45))):
                cell.width = width
    doc.save(path); return path
