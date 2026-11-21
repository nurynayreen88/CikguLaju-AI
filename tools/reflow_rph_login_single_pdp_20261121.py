"""STRICT QA samples: move original RPH content into approved login-gallery geometry.

This tool does not invent, translate or regenerate SK/SP, objectives or activities.
Existing cell paragraphs are deep-copied. Non-pedagogical source header metadata
may be formatted into separate classroom boxes; the original source is unchanged.
Two supported sample shapes only; fail closed for any unrecognized source.
"""
from __future__ import annotations
import collections
import copy
import io
import re
from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH

PALETTE={"MATH":("EDF0FB","DFE4F8",False),"ARAB":("ECF5EE","D9EBDE",True)}


def shade(cell, hexcode):
    tcPr=cell._tc.get_or_add_tcPr(); sh=tcPr.find(qn('w:shd'))
    if sh is None: sh=OxmlElement('w:shd');tcPr.append(sh)
    sh.set(qn('w:val'),'clear');sh.set(qn('w:fill'),hexcode)


def set_borders(table):
    pr=table._tbl.tblPr; b=pr.find(qn('w:tblBorders'))
    if b is None:b=OxmlElement('w:tblBorders');pr.append(b)
    for side in ('top','left','bottom','right','insideH','insideV'):
        child=b.find(qn('w:'+side))
        if child is None:child=OxmlElement('w:'+side);b.append(child)
        child.set(qn('w:val'),'single');child.set(qn('w:color'),'697681');child.set(qn('w:sz'),'6')


def copy_cell_content(src, dst, *, bold=False):
    for ch in list(dst._tc):
        if ch.tag in (qn('w:p'),qn('w:tbl')):dst._tc.remove(ch)
    for item in src._tc:
        if item.tag not in (qn('w:p'),qn('w:tbl')):continue
        new=copy.deepcopy(item)
        if bold and new.tag==qn('w:p'):
            for run in new.findall('.//'+qn('w:r')):
                pr=run.find(qn('w:rPr'))
                if pr is None:pr=OxmlElement('w:rPr');run.insert(0,pr)
                b=OxmlElement('w:b');b.set(qn('w:val'),'1');pr.append(b)
        dst._tc.append(new)
    if not dst.paragraphs and not dst.tables:dst.add_paragraph('')


def append_source_paras(target,source,*,bold=False):
    for item in source._tc:
        if item.tag!=qn('w:p'):continue
        new=copy.deepcopy(item)
        if bold:
            for run in new.findall('.//'+qn('w:r')):
                pr=run.find(qn('w:rPr'))
                if pr is None:pr=OxmlElement('w:rPr');run.insert(0,pr)
                b=OxmlElement('w:b');b.set(qn('w:val'),'1');pr.append(b)
        target._tc.append(new)


def prepare(document,kind):
    tone,strong,rtl=PALETTE[kind]
    s=document.sections[0];s.page_width=Mm(210);s.page_height=Mm(297)
    s.top_margin=Mm(11);s.bottom_margin=Mm(10);s.left_margin=Mm(13);s.right_margin=Mm(13)
    normal=document.styles['Normal'];normal.font.name='Amiri' if rtl else 'Aptos';normal.font.size=Pt(10 if rtl else 8.5)
    normal.paragraph_format.space_after=Pt(0)
    return tone,strong,rtl


def style_table(table,tone,rtl):
    table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
    table.columns[0].width=Cm(4.8);table.columns[1].width=Cm(13.6)
    set_borders(table)
    if rtl:
        pr=table._tbl.tblPr
        b=pr.find(qn('w:bidiVisual'))
        if b is None:b=OxmlElement('w:bidiVisual');pr.append(b)
        b.set(qn('w:val'),'1')
    for row in table.rows:
        for idx,cell in enumerate(row.cells):
            shade(cell,tone if idx==0 else 'FFFFFF')
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.width=Cm(4.8 if idx==0 else 13.6)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(0)
                p.paragraph_format.space_before=Pt(0)
                if rtl:p.alignment=WD_ALIGN_PARAGRAPH.RIGHT


def source_academic_texts(source, pairs):
    return collections.Counter(
        p.text for table_index, row_ids in pairs
        for row_id in row_ids
        for cell in source.tables[table_index].rows[row_id].cells
        for p in cell.paragraphs if p.text.strip()
    )


def output_has_original_academic(source_texts, out):
    all_texts=collections.Counter(
        p.text for t in out.tables for row in t.rows for cell in row.cells
        for p in cell.paragraphs if p.text.strip()
    )
    for original, count in source_texts.items():
        if all_texts[original]<count:
            # Grouped activity paragraphs are exact text; no paraphrase accepted.
            raise ValueError(f'Unchanged academic paragraph missing: {original[:120]}')


def make_hero(out, title,subtitle,teacher,kind):
    tone,strong,rtl=PALETTE[kind]
    hero=out.add_table(rows=1,cols=2)
    hero.alignment=WD_TABLE_ALIGNMENT.CENTER;hero.autofit=False;set_borders(hero)
    hero.columns[0].width=Cm(12);hero.columns[1].width=Cm(6.4)
    if rtl:
        pr=hero._tbl.tblPr;b=OxmlElement('w:bidiVisual');b.set(qn('w:val'),'1');pr.append(b)
    identity=hero.cell(0,0);identity.text='';identity.width=Cm(12);shade(identity,'FFFFFF')
    p=identity.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT if rtl else WD_ALIGN_PARAGRAPH.LEFT
    run=p.add_run(title);run.bold=True;run.font.size=Pt(16 if rtl else 13)
    p=identity.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.RIGHT if rtl else WD_ALIGN_PARAGRAPH.LEFT
    run=p.add_run(subtitle);run.font.size=Pt(10.5)
    aside=hero.cell(0,1);aside.text='';aside.width=Cm(6.4)
    grid=aside.add_table(rows=4,cols=2);grid.autofit=False;set_borders(grid)
    grid.columns[0].width=Cm(3.3);grid.columns[1].width=Cm(3.1)
    if rtl:
        pr=grid._tbl.tblPr;b=OxmlElement('w:bidiVisual');b.set(qn('w:val'),'1');pr.append(b)
    names=['کلس','تاريخ','ماس','بيلڠن موريد'] if rtl else ['Kelas','Tarikh','Masa','Bil. Murid']
    for j,row in enumerate(grid.rows):
        label,val=row.cells
        label.text=names[j];label.width=Cm(3.3);val.width=Cm(3.1)
        val.text=str(teacher[j] or '')
        shade(label,tone);shade(val,'FFFFFF')
        label.vertical_alignment=val.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for cc in row.cells:
            for p in cc.paragraphs:
                p.paragraph_format.space_after=Pt(0)
                if rtl:p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    return hero


def add_pair(table, key, value_cell, *, label_tone):
    row=table.add_row();row.cells[0].text=key
    copy_cell_content(value_cell,row.cells[1]);return row


def make_math(source):
    if len(source.tables)!=3 or tuple(len(t.rows) for t in source.tables)!=(12,6,2):
        raise ValueError('Math supported only for this single-PdP shape')
    d=source.tables[0]; act=source.tables[1]; extra=source.tables[2]
    if d.cell(5,0).text.strip()!='Standard Kandungan':raise ValueError('Not the expected math source')
    teacher=[d.cell(1,1).text.split('/')[-1].strip(),d.cell(2,1).text.split('|')[0].strip(),d.cell(2,1).text.split('|')[-1].strip(),d.cell(3,1).text]
    academic=source_academic_texts(source,[(0,range(4,12)),(1,range(6)),(2,range(2))])
    out=Document();tone,_,rtl=prepare(out,'MATH')
    make_hero(out,source.paragraphs[0].text,d.cell(0,1).text+' · '+d.cell(1,1).text.split('/')[0].strip(),teacher,'MATH')
    # All original teaching statements are relocated, including the 4th PBD activity.
    detail=out.add_table(rows=0,cols=2)
    for row in d.rows[4:]:
        rowout=detail.add_row()
        for idx in range(2):copy_cell_content(row.cells[idx],rowout.cells[idx])
    style_table(detail,tone,rtl)
    work=out.add_table(rows=0,cols=2)
    row=work.add_row()
    for idx in range(2):copy_cell_content(act.rows[0].cells[idx],row.cells[idx])
    main=work.add_row();main.cells[0].text='Aktiviti Utama';main.cells[1].text=''
    for row in act.rows[1:-1]:
        append_source_paras(main.cells[1],row.cells[0],bold=True)
        append_source_paras(main.cells[1],row.cells[1])
    row=work.add_row()
    for idx in range(2):copy_cell_content(act.rows[-1].cells[idx],row.cells[idx])
    for row in extra.rows:
        newrow=work.add_row()
        for idx in range(2):copy_cell_content(row.cells[idx],newrow.cells[idx])
    style_table(work,tone,rtl)
    # Keep both original metadata paragraphs outside the layout intact.
    for p in source.paragraphs[1:]:
        if p.text.strip():out._body._body.append(copy.deepcopy(p._p))
    # Content from body moved into activity cell without rewriting.
    output_has_original_academic(academic,out)
    return out


def make_arab(source):
    if len(source.tables)!=1 or len(source.tables[0].rows)!=15:raise ValueError('Arab supported only for single 15-row source')
    table=source.tables[0]
    if table.cell(4,0).text.strip()!='SK / SP':raise ValueError('Unexpected Arabic source')
    # Technical draft label is not part of lesson content. Preserve it only
    # in the admin source; do not include reviewer labels on teacher PDF.
    title=re.sub(r'\s*[•·]\s*DRAF UNTUK SEMAKAN GURU\s*
    academic=source_academic_texts(source,[(0,[2,3,4,6,7,8,9,10,11,12,13,14])])
    out=Document();tone,_,rtl=prepare(out,'ARAB')
    make_hero(out,title,table.cell(2,1).text,['','','',''],'ARAB')
    details=out.add_table(rows=0,cols=2)
    for i in [0,1,2,3,4,6,7,13]:
        row=details.add_row()
        for idx in range(2):copy_cell_content(table.rows[i].cells[idx],row.cells[idx])
    style_table(details,tone,rtl)
    act=out.add_table(rows=0,cols=2)
    def move(i):
        src=table.rows[i]; row=act.add_row()
        for k in range(2):copy_cell_content(src.cells[k],row.cells[k])
    move(8)
    main=act.add_row();main.cells[0].text='Aktiviti Utama';main.cells[1].text=''
    for i in (9,10):
        append_source_paras(main.cells[1],table.rows[i].cells[0],bold=True)
        append_source_paras(main.cells[1],table.rows[i].cells[1])
    for i in (11,12,14):move(i)
    style_table(act,tone,rtl)
    output_has_original_academic(academic,out)
    return out


def save_example(source_path,kind,destination):
    source=Document(source_path)
    doc=make_math(source) if kind=='MATH' else make_arab(source)
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    doc.save(destination)
    check=Document(destination)
    if len(check.tables)!=3:raise RuntimeError('Not header + two grids')
    return str(destination)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(
        description='Reflow an existing ONE-PdP Word source to approved login RPH geometry; academic text unchanged.')
    parser.add_argument('source',type=Path)
    parser.add_argument('--subject',choices=('MATH','ARAB'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(save_example(args.source,args.subject,args.output))
, '', source.paragraphs[0].text, flags=re.I).strip()
    academic=source_academic_texts(source,[(0,[2,3,4,6,7,8,9,10,11,12,13,14])])
    out=Document();tone,_,rtl=prepare(out,'ARAB')
    make_hero(out,title,table.cell(2,1).text,['','','',''],'ARAB')
    details=out.add_table(rows=0,cols=2)
    for i in [0,1,2,3,4,6,7,13]:
        row=details.add_row()
        for idx in range(2):copy_cell_content(table.rows[i].cells[idx],row.cells[idx])
    style_table(details,tone,rtl)
    act=out.add_table(rows=0,cols=2)
    def move(i):
        src=table.rows[i]; row=act.add_row()
        for k in range(2):copy_cell_content(src.cells[k],row.cells[k])
    move(8)
    main=act.add_row();main.cells[0].text='Aktiviti Utama';main.cells[1].text=''
    for i in (9,10):
        append_source_paras(main.cells[1],table.rows[i].cells[0],bold=True)
        append_source_paras(main.cells[1],table.rows[i].cells[1])
    for i in (11,12,14):move(i)
    style_table(act,tone,rtl)
    output_has_original_academic(academic,out)
    return out


def save_example(source_path,kind,destination):
    source=Document(source_path)
    doc=make_math(source) if kind=='MATH' else make_arab(source)
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    doc.save(destination)
    check=Document(destination)
    if len(check.tables)!=3:raise RuntimeError('Not header + two grids')
    return str(destination)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(
        description='Reflow an existing ONE-PdP Word source to approved login RPH geometry; academic text unchanged.')
    parser.add_argument('source',type=Path)
    parser.add_argument('--subject',choices=('MATH','ARAB'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(save_example(args.source,args.subject,args.output))
