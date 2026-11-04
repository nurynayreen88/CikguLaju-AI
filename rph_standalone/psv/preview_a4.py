"""Read-only, explicitly opt-in A4 QA preview for PSV RPH drafts.

Never activated by Telegram: public export refuses every DRAF_SEMAK source.
Run in repository: python rph_standalone/psv/preview_a4.py YEAR PDP OUTDIR --preview
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
STEPS = ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Pengukuhan/Pentaksiran", "Penutup")
STEP_RE = re.compile(r'^\*\*(Set induksi|Aktiviti [12]|Pengukuhan/Pentaksiran(?: PBD)?|Penutup)([^*]*?):\*\*\s*(.+)$')
FIELD_RE = re.compile(r'\*\*([^*]+?):\*\*\s*(.*?)(?=\s+\|\s+\*\*|$)')


def plain(value: str) -> str:
    value = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', value)
    value = value.replace('**', '').replace(chr(96), '').strip()
    return re.sub(r'\s+', ' ', value)


def load(year: int, pdp: int, *, preview: bool = False):
    if type(year) is not int or year not in range(2, 7):
        raise ValueError('PSV year must be 2–6')
    if type(pdp) is not int or pdp not in range(1, 43):
        raise ValueError('PSV PdP must be 001–042')
    path = ROOT / 'rph_standalone' / 'psv' / f'year{year}' / f'lesson_{pdp:03d}.md'
    raw = path.read_text(encoding='utf-8')
    meta = {}
    for line in raw.splitlines():
        if line.startswith('## Langkah PdP'):
            break
        for key, val in FIELD_RE.findall(line):
            meta[key.strip()] = plain(val)
    # Intentional hard gate: this is a QA-only renderer, never a public delivery route.
    # A renamed status alone cannot unlock export without a future approved adapter.
    if not preview:
        raise ValueError(f'RPH {year}/{pdp:03d} is DRAF/unverified; public export is disabled')
    if not meta.get('SP') or not meta.get('SK'):
        raise ValueError('Missing SK/SP')
    obj = re.search(r'## Objektif dan kriteria kejayaan\s*\n(.*?)\n\s*## Langkah PdP', raw, re.S)
    if not obj:
        raise ValueError('No objective section')
    items = []
    for line in raw.splitlines():
        m = STEP_RE.match(line)
        if m:
            items.append((plain(m.group(1) + m.group(2)), plain(m.group(3))))
    if len(items) != 5 or not all(any(k in a for a, _ in items) for k in STEPS):
        raise ValueError('Incomplete lesson stages')
    for extra in ('Pembezaan', 'Keselamatan'):
        match = re.search(r'^\*\*' + extra + r':\*\*\s*(.*)', raw, re.M)
        if match:
            items.append((extra, plain(match.group(1))))
    return {
        'year': year, 'pdp': pdp, 'source': path, 'metadata': meta,
        'objective': plain(obj.group(1)), 'stages': items,
    }


def fields(data):
    meta = data['metadata']
    unit = meta.get('Unit', meta.get('Unit RPT 2026', ''))
    topic = meta.get('Aktiviti/Tajuk', meta.get('Fokus', ''))
    book = meta.get('Buku Teks', meta.get('Rujukan Buku Teks', ''))
    return [
        ('Unit/Tajuk', unit + (' | ' + topic if topic else '')),
        ('SK/SP', meta['SK'] + ' | ' + meta['SP']),
        ('Buku Teks', book),
        ('Tempoh', meta.get('Tempoh', meta.get('Masa', '60 minit'))),
        ('BBM', meta.get('BBM', '')),
    ]


def word(data, path: Path):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.15)
    sec.top_margin, sec.bottom_margin = Cm(0.95), Cm(0.90)
    sec.header_distance, sec.footer_distance = Cm(0.4), Cm(0.4)
    base = doc.styles['Normal']
    base.font.name, base.font.size = 'Arial', Pt(9.1)
    base.paragraph_format.space_after = Pt(3.2)
    base.paragraph_format.line_spacing = 1.08
    head = doc.add_paragraph()
    head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = head.add_run(f'RPH PENDIDIKAN SENI VISUAL TAHUN {data["year"]}  |  PdP {data["pdp"]:03d}')
    run.bold, run.font.size = True, Pt(11.5)
    table = doc.add_table(rows=0, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(2.2)
    table.columns[1].width = Cm(16.35)
    for label, value in fields(data):
        cells = table.add_row().cells
        cells[0].width, cells[1].width = Cm(2.2), Cm(16.35)
        cells[0].vertical_alignment = cells[1].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        c0 = cells[0].paragraphs[0]
        c0.add_run(label).bold = True
        c1 = cells[1].paragraphs[0]
        c1.add_run(value)
        for c in cells:
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
    p = doc.add_paragraph()
    p.add_run('Objektif / Kriteria Kejayaan: ').bold = True
    p.add_run(data['objective'])
    for label, body in data['stages']:
        p = doc.add_paragraph()
        p.add_run(label + ': ').bold = True
        p.add_run(body)
    doc.save(path)


def pdf(data, path: Path):
    font = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    font_bold = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
    if not font.is_file() or not font_bold.is_file():
        raise RuntimeError('Unicode fonts unavailable; refuse malformed PDF')
    if 'PSV-Regular' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('PSV-Regular', str(font)))
        pdfmetrics.registerFont(TTFont('PSV-Bold', str(font_bold)))
    pdfmetrics.registerFontFamily('PSV-Regular', normal='PSV-Regular', bold='PSV-Bold')
    style = ParagraphStyle('text', fontName='PSV-Regular', fontSize=9.0, leading=13.2, spaceAfter=4, alignment=TA_LEFT)
    title_style = ParagraphStyle('title', parent=style, fontName='PSV-Bold', fontSize=10.5, leading=15, spaceAfter=7)
    story = [Paragraph(f'RPH PENDIDIKAN SENI VISUAL TAHUN {data["year"]}  |  PdP {data["pdp"]:03d}', title_style)]
    for label, value in fields(data):
        story.append(Paragraph(f'<b>{html.escape(label)}:</b> {html.escape(value)}', style))
    story.append(Spacer(1, 4))
    story.append(Paragraph('<b>Objektif / Kriteria Kejayaan:</b> ' + html.escape(data['objective']), style))
    for label, body in data['stages']:
        story.append(Paragraph('<b>' + html.escape(label) + ':</b> ' + html.escape(body), style))
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=13*mm, rightMargin=13*mm,
                            topMargin=11*mm, bottomMargin=10*mm)
    doc.build(story)
    pages = len(PdfReader(str(path)).pages)
    if pages != 1:
        path.unlink(missing_ok=True)
        raise RuntimeError(f'PSV PDF is {pages} pages, not one A4; revise compact layout')


def render(year: int, pdp: int, out_dir: Path, *, preview: bool = False):
    source = load(year, pdp, preview=preview)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f'RPH_PSV_Tahun_{year}_PdP_{pdp:03d}'
    docx_path, pdf_path = out_dir / (stem + '.docx'), out_dir / (stem + '.pdf')
    try:
        word(source, docx_path)
        pdf(source, pdf_path)
    except Exception:
        docx_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)
        raise
    return docx_path, pdf_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('year', type=int)
    parser.add_argument('pdp', type=int)
    parser.add_argument('outdir', type=Path)
    parser.add_argument('--preview', action='store_true', help='explicit internal staging preview of DRAF only')
    args = parser.parse_args()
    print(*render(args.year, args.pdp, args.outdir, preview=args.preview), sep='\n')
