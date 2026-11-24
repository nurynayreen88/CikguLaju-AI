"""QA-only: move per-lesson SJKC/DLP source paragraphs to login-gallery grid.

Requires the exact, already-extracted one-lesson DOCX. Never invents
teaching activities. Not a production API or batch publisher.
"""
from __future__ import annotations
from io import BytesIO
from copy import deepcopy
from pathlib import Path
import re
from docx import Document
from docx.oxml.ns import qn
from tools.reflow_rph_login_single_pdp_20261121 import (
    PALETTE, make_hero, style_table, append_source_paras, copy_cell_content,
    prepare,
)
PALETTE['SJKC_MATH']=('EDF0FB','DFE4F8',False)
PALETTE['DLP_SCIENCE']=('EAF5F0','D8EBDF',False)


def clone_original_paragraphs(target_cell,paragraphs):
    target_cell.text=''
    for p in paragraphs:
        target_cell._tc.append(deepcopy(p._p))


def insert_original_paragraph(target_cell,paragraph):
    target_cell._tc.append(deepcopy(paragraph._p))


def valued_row(table,label,paragraphs):
    row=table.add_row()
    row.cells[0].text=label
    clone_original_paragraphs(row.cells[1],paragraphs)
    return row


def convert_sjkc(src):
    if len(src.tables)!=1 or (len(src.tables[0].rows),len(src.tables[0].columns))!=(6,3):
        raise ValueError('Not the expected one-PdP SJKC RPH')
    paragraphs=[p for p in src.paragraphs if p.text.strip()]
    if len(paragraphs)!=9 or not re.match(r'PdP\s+\d{3}',paragraphs[1].text):
        raise ValueError('SJKC metadata does not match the checked source format')
    original_texts=[p.text for p in paragraphs[4:]] + [
        cell.text for row in src.tables[0].rows[1:] for cell in row.cells]
    out=Document()
    tone,_,rtl=prepare(out,'SJKC_MATH')
    hero=make_hero(out,'','',['','','',''],'SJKC_MATH')
    clone_original_paragraphs(hero.cell(0,0),paragraphs[:3])
    details=out.add_table(rows=0,cols=2)
    for label,p in [
        ('Standard Kandungan / Pembelajaran',paragraphs[4]),
        ('Objektif Pembelajaran',paragraphs[5]),
        ('Bahan Bantu Mengajar',paragraphs[6]),
        ('Buku Teks / Buku Aktiviti',paragraphs[7]),
    ]: valued_row(details,label,[p])
    style_table(details,tone,rtl)
    work=out.add_table(rows=0,cols=2)
    original=src.tables[0]
    for ridx in (1,5):
        row=original.rows[ridx]
        label=(row.cells[0].text+'  ·  '+row.cells[1].text).strip()
        r=work.add_row();r.cells[0].text=label
        copy_cell_content(row.cells[2],r.cells[1])
    # Put the original 3 activity labels in the one Approved Main Activity cell.
    main=work.add_row()
    main.cells[0].text='Aktiviti Utama';main.cells[1].text=''
    for ridx in (2,3,4):
        row=original.rows[ridx]
        label=main.cells[1].add_paragraph()
        label.add_run(row.cells[0].text+'  ·  '+row.cells[1].text).bold=True
        append_source_paras(main.cells[1],row.cells[2])
    # Move Closure above Activity Main? Login example order is Set Induction / Main / Closure.
    closure=work.rows[1]._tr
    work._tbl.remove(closure)
    work._tbl.append(closure)
    valued_row(work,'Refleksi',[paragraphs[8]])
    style_table(work,tone,rtl)
    if len(out.tables)!=3:raise ValueError('Not hero + 2 content grids')
    out_text='\n'.join(cell.text for t in out.tables for row in t.rows for cell in row.cells)
    for txt in original_texts:
        if not txt.strip():continue
        if txt.strip() not in out_text:
            raise ValueError('Academic source disappeared: '+txt[:80])
    return out


def convert_dlp(src):
    if len(src.tables)!=3 or tuple((len(t.rows),len(t.columns)) for t in src.tables)!=((8,2),(5,3),(1,2)):
        raise ValueError('Not the expected one-Lesson DLP source')
    ps=[p for p in src.paragraphs if p.text.strip()]
    if len(ps)!=3 or ps[0].text.strip()!='Daily Lesson Plan':
        raise ValueError('DLP source headers do not match expected structure')
    original_texts=[p.text for p in ps]
    tab0,tab1,tab2=src.tables
    for ridx in (0,1,2,4,5,6,7):
        original_texts += [cell.text for cell in tab0.rows[ridx].cells]
    for ridx in range(1,5):
        original_texts += [cell.text for cell in tab1.rows[ridx].cells]
    original_texts += [cell.text for cell in tab2.rows[0].cells]
    out=Document();tone,_,rtl=prepare(out,'DLP_SCIENCE')
    hero=make_hero(out,'','',['','','',''],'DLP_SCIENCE')
    clone_original_paragraphs(hero.cell(0,0),ps[:3])
    details=out.add_table(rows=0,cols=2)
    for ridx in (0,1,2,4,5,6,7):
        row=details.add_row()
        for k in (0,1):copy_cell_content(tab0.rows[ridx].cells[k],row.cells[k])
    style_table(details,tone,rtl)
    work=out.add_table(rows=0,cols=2)
    def phase(ridx):
        r=tab1.rows[ridx];dst=work.add_row()
        copy_cell_content(r.cells[0],dst.cells[0])
        dst.cells[1].text=''
        append_source_paras(dst.cells[1],r.cells[1])
        append_source_paras(dst.cells[1],r.cells[2])
        return dst
    phase(1)
    main=work.add_row();main.cells[0].text='Main activity';main.cells[1].text=''
    for idx in (2,3):
        r=tab1.rows[idx]
        label=main.cells[1].add_paragraph();label.add_run(r.cells[0].text).bold=True
        append_source_paras(main.cells[1],r.cells[1])
        append_source_paras(main.cells[1],r.cells[2])
    phase(4)
    r=work.add_row()
    for k in (0,1):copy_cell_content(tab2.rows[0].cells[k],r.cells[k])
    style_table(work,tone,rtl)
    if len(out.tables)!=3:raise ValueError('Not hero + 2 content grids')
    out_text='\n'.join(cell.text for t in out.tables for row in t.rows for cell in row.cells)
    for txt in original_texts:
        if txt.strip() and txt.strip() not in out_text:
            raise ValueError('Academic source disappeared: '+txt[:85])
    return out


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('input',type=Path)
    parser.add_argument('--kind',choices=['SJKC_MATH','DLP_SCIENCE'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    src=Document(args.input)
    result=convert_sjkc(src) if args.kind=='SJKC_MATH' else convert_dlp(src)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    result.save(args.output)
    print(args.output)
