"""Optional RPH 5P layout (owner-approved V5 structure); no live installation.

The input is a reviewed, lesson-specific 5P companion to a source RPH.
Never infer or rename generic Activity 1/2/3 into 5P. Existing RPH remains
the authority for curriculum fields, teacher information and access checks.
"""
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import re
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_DIRECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

MS_LABELS = (
    "RANCANGAN PENGAJARAN HARIAN", "Kelas", "Tarikh", "Masa", "Bil. Murid",
    "Bidang / Tajuk", "Standard Kandungan", "Standard Pembelajaran",
    "Objektif", "Kriteria Kejayaan", "Aktiviti PdP\n(5P)",
    "Penglibatan", "Penerokaan", "Penerangan", "Pengembangan", "Penilaian",
    "Penutup", "BBM / PAK21 / EMK", "Pemulihan / Pengayaan", "Refleksi",
)
EN_LABELS = (
    "DAILY LESSON PLAN", "Class", "Date", "Time", "No. of pupils",
    "Theme / Topic", "Content Standard", "Learning Standard",
    "Learning Objective", "Success Criteria", "Learning Activities\n(5E)",
    "Engagement", "Exploration", "Explanation", "Elaboration", "Evaluation",
    "Closure", "Teaching Aids / 21st Century Learning / CCE", "Remedial / Enrichment", "Reflection",
)
FIELDS = ("topic", "sk", "sp", "objective", "criteria", "closure",
          "aids_pak21_emk", "remedial_enrichment", "reflection")
PHASE_KEYS = ("engagement", "exploration", "explanation", "elaboration", "evaluation")
HEX = re.compile(r"^[0-9A-Fa-f]{6}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True)
class Palette:
    title: str
    header: str
    label: str
    border: str

# Exact approved Mathematics V5 sample. Other subjects must pass their
# existing verified subject palette; no universal green override.
MATH_V5 = Palette("DCECEB", "F2F7F6", "EDF5F4", "9AB2B7")

def _element(name, **attrs):
    e=OxmlElement("w:"+name)
    for k,v in attrs.items():
        e.set(qn("w:"+k),str(v))
    return e

def validate(source, companion, *, source_bytes):
    if not isinstance(source_bytes, bytes) or not source_bytes:
        raise ValueError("Original source bytes required")
    digest=sha256(source_bytes).hexdigest()
    if companion.get("source_sha256")!=digest or not DIGEST.fullmatch(digest):
        raise ValueError("5P source changed")
    for key in ("subject", "year", "lesson_id", "curriculum"):
        if not source.get(key) or companion.get(key)!=source[key]:
            raise ValueError("5P lesson identity mismatch: "+key)
    for k in FIELDS:
        if not isinstance(source.get(k),str):
            raise ValueError("Missing source field: "+k)
        if k not in ("reflection",) and not source[k].strip():
            raise ValueError("Blank source field: "+k)
    phases=companion.get("phases")
    if not isinstance(phases,dict) or set(phases)!=set(PHASE_KEYS):
        raise ValueError("Exactly five separate reviewed phases required")
    if any(not isinstance(v,str) or not v.strip() for v in phases.values()):
        raise ValueError("Empty 5P phase")
    if len({v.strip() for v in phases.values()})!=5:
        raise ValueError("Repeated 5P phases")
    # Caller must independently verify academic review and entitlement.
    # A candidate is deliberately NOT marked ready by this renderer.
    return phases

def render_word(source,companion,*,source_bytes,palette,subject_heading,
                labels=MS_LABELS,rtl=False,font="Arial",profile=None):
    phases=validate(source,companion,source_bytes=source_bytes)
    if len(labels)!=20 or not all(isinstance(x,str) and x.strip() for x in labels):
        raise ValueError("Complete verified language labels required")
    if rtl and (labels in (MS_LABELS,EN_LABELS) or font!="Amiri"):
        raise ValueError("RTL requires verified Jawi/Arabic labels and Amiri")
    if not isinstance(subject_heading,str) or not subject_heading.strip():
        raise ValueError("Subject heading required")
    if not all(HEX.fullmatch(getattr(palette,k)) for k in ("title","header","label","border")):
        raise ValueError("Invalid subject palette")
    profile=profile or {}
    doc=Document()
    sec=doc.sections[0]
    sec.page_width,sec.page_height=Cm(21),Cm(29.7)
    sec.left_margin=sec.right_margin=Cm(1.5)
    sec.top_margin=sec.bottom_margin=Cm(1.4)
    style=doc.styles["Normal"]
    style.font.name=font
    style.font.size=Pt(10)
    style.paragraph_format.space_before=Pt(0)
    style.paragraph_format.space_after=Pt(0)
    style.paragraph_format.line_spacing=1.0
    t=doc.add_table(rows=21,cols=2)
    t.style="Table Grid"
    t.autofit=False
    t.alignment=WD_TABLE_ALIGNMENT.CENTER
    if rtl:
        t.table_direction=WD_TABLE_DIRECTION.RTL
    for j,w in enumerate((4.2,13.8)):
        t.columns[j].width=Cm(w)
        for row in t.rows: row.cells[j].width=Cm(w)
    pr=t._tbl.tblPr
    borders=_element("tblBorders")
    for side in ("top","left","bottom","right","insideH","insideV"):
        borders.append(_element(side,val="single",sz=5,color=palette.border))
    pr.append(borders)
    margins=_element("tblCellMar")
    for side,w in (("top",95),("bottom",95),("left",130),("right",130)):
        margins.append(_element(side,w=w,type="dxa"))
    pr.append(margins)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(_element("cantSplit"))
    def put(cell,value,*,bold=False,fill=None,size=10,center=False):
        cell.text=""
        cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        if fill: cell._tc.get_or_add_tcPr().append(_element("shd",fill=fill,val="clear"))
        p=cell.paragraphs[0]
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else (WD_ALIGN_PARAGRAPH.RIGHT if rtl else WD_ALIGN_PARAGRAPH.LEFT)
        if rtl: p._p.get_or_add_pPr().append(_element("bidi"))
        r=p.add_run(value)
        r.bold=bold
        r.font.name=font
        r.font.size=Pt(size)
        if rtl:
            r._r.get_or_add_rPr().append(_element("rtl"))
            r._r.get_or_add_rPr().append(_element("szCs",val=size*2))
            r._r.get_or_add_rPr().rFonts.set(qn("w:cs"),font)
    put(t.cell(0,0).merge(t.cell(0,1)),labels[0],bold=True,fill=palette.title,size=15,center=True)
    info="\n".join(f"{label}: {profile.get(key,'')}".rstrip()
                   for label,key in zip(labels[1:5],("class","date","time","students")))
    # Keep the profile on the physical left and subject on the right even
    # for RTL documents; all body label cells mirror for right-to-left.
    put(t.cell(1,1 if rtl else 0),info,bold=True,fill=palette.header)
    put(t.cell(1,0 if rtl else 1),subject_heading,bold=True,fill=palette.header,size=13,center=True)
    for i,key in enumerate(FIELDS[:5],2):
        put(t.cell(i,0),labels[i+3],bold=True,fill=palette.label)
        put(t.cell(i,1),source[key])
    put(t.cell(7,0).merge(t.cell(16,0)),labels[10],bold=True,fill=palette.label,center=True)
    for i,key in enumerate(PHASE_KEYS):
        put(t.cell(7+2*i,1),labels[11+i],bold=True,fill=palette.label)
        put(t.cell(8+2*i,1),phases[key])
    for i,key in enumerate(FIELDS[5:],17):
        put(t.cell(i,0),labels[i-1],bold=True,fill=palette.label)
        value=source[key] if key!="reflection" else source[key] or "\n\n"
        put(t.cell(i,1),value)
    if source.get("reference"):
        p=doc.add_paragraph(source["reference"])
        p.runs[0].font.size=Pt(8)
    out=BytesIO()
    doc.save(out)
    return out.getvalue()
