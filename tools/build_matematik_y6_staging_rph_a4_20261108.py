"""Create isolated A4 Word review proofs from 13 existing Year6 Markdown drafts.

No database or production access. These QA proofs are NOT user-ready RPH.
PDF conversion and strict single-page verification are CI-only.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    "rph_standalone/matematik/staging_draf_y6_pdp006_pola_nombor_20261108.md",
    "rph_standalone/matematik/staging_draf_y6_pdp007_012_dskp_bukuteks_20261108.md",
    "rph_standalone/matematik/staging_draf_y6_pdp079_081_nisbah_kadaran_20261108.md",
    "rph_standalone/matematik/staging_draf_y6_rpt2027_wang_3_sumber_primer_20261108.md",
    "rph_standalone/matematik/staging_draf_y6_9_pdp_dskp2021_sumber_primer_20261108.md",
    "rph_standalone/matematik/staging_draf_y6_5_pdp_semantic_gap_20261108.md",
]
# The page and SP fields are SOURCE-REVIEW CANDIDATES, not accepted remaps.
CANDIDATES = {
    "MT6-PDP-006": ("1.4.1", "1.1.2", "4–8"),
    "MT6-PDP-007": ("1.5.1", "1.2.1", "15–18"),
    "MT6-PDP-008": ("1.5.2", "1.2.1", "19–21"),
    "MT6-PDP-009": ("1.6.1", "1.2.1", "27–29"),
    "MT6-PDP-010": ("1.5.3", "1.2.1", "22–24"),
    "MT6-PDP-011": ("1.5.4", "1.2.1", "25–26"),
    "MT6-PDP-012": ("1.6.2", "1.2.1", "30–34"),
    "MT6-PDP-079": ("8.1.1", "7.2.1", "191–196"),
    "MT6-PDP-080": ("8.2.1", "7.3.1", "197–200"),
    "MT6-PDP-081": ("8.3.1", "7.4.1", "201–204"),
    "FIN-T6-01": ("TIADA", "3.1.1", "103–106"),
    "FIN-T6-02": ("TIADA", "3.2.1", "121–122"),
    "FIN-T6-03": ("TIADA", "3.3.1", "123–130"),
    "DSKP6-01": ("TIADA", "2.1.1", "61–67"),
    "DSKP6-02": ("TIADA", "4.1.1", "141–143"),
    "DSKP6-03": ("TIADA", "4.1.2", "144–147"),
    "DSKP6-04": ("TIADA", "6.1.2", "165–167"),
    "DSKP6-05": ("TIADA", "6.2.1", "178–179"),
    "DSKP6-06": ("TIADA", "7.1.1", "187–190"),
    "DSKP6-07": ("TIADA", "8.1.1", "207–212"),
    "DSKP6-08": ("TIADA", "8.2.1", "213–215"),
    "DSKP6-09": ("TIADA", "8.2.2", "216–219"),
    "FIX6-01": ("TIADA", "2.2.1", "68–69"),
    "FIX6-02": ("TIADA", "2.2.2", "70–72"),
    "FIX6-03": ("TIADA", "2.3.1", "73–74"),
    "FIX6-04": ("TIADA", "2.3.3", "77–79"),
    "FIX6-05": ("TIADA", "5.1.1", "155–157"),
}
HEADING = re.compile(
    r"(?m)^## (?:PdP|Calon) (?P<code>(?:MT6-PDP-\d{3}|FIN-T6-\d{2}|DSKP6-\d{2}|FIX6-\d{2}))\s+—\s+(?P<title>.+)$"
)

@dataclass(frozen=True)
class Draft:
    code: str
    title: str
    body: str
    source: str

def _draft(code, title, content, source):
    match = re.search(r"\*\*Objektif(?: pembelajaran)?:\*\*", content)
    if not match:
        raise ValueError("Missing objective for "+code)
    body = content[match.start():]
    # Source writers use both **Status:** and **Status: ...**.
    # Neither review status nor the subsequent academic notes belong in RPH body.
    body = re.split(
        r"\*\*(?:Status|Status kelulusan|Pagar keselamatan|Peraturan penerbitan)\b|\n---\s*\n|^#{2,3}\s+(?:Pagar|Peraturan)",
        body, maxsplit=1, flags=re.M
    )[0]
    # Source authors placed BBM before the objective in some Year6 drafts.
    # Retain original BBM as a separate teaching paragraph instead of losing it.
    if "BBM" not in body:
        m = re.search(r"\*\*BBM:\*\*\s*([^\n]+)", content)
        if m:
            body += "\n\n**BBM:** " + m.group(1).strip()
    for label in ("Objektif", "Set induksi", "Aktiviti 1", "Aktiviti 2",
                  "Aktiviti 3", "PBD", "Penutup", "BBM"):
        if label.casefold() not in body.casefold():
            raise ValueError(code+" missing "+label)
    return Draft(code, title.strip(), body.strip(), source)

def load_drafts(root=ROOT):
    out = []
    for source in SOURCES:
        text = (root / source).read_text(encoding="utf-8")
        headings = list(HEADING.finditer(text))
        if not headings:
            if "pdp006" not in source:
                raise ValueError("Unexpected single draft "+source)
            m = re.search(r"^# .*PdP 006\s+—\s+(.+)$", text, re.M)
            if not m:
                raise ValueError("Missing PdP006 source title")
            out.append(_draft("MT6-PDP-006", m.group(1), text, source))
            continue
        for i, h in enumerate(headings):
            end = headings[i+1].start() if i+1<len(headings) else len(text)
            out.append(_draft(h.group("code"), h.group("title"),
                              text[h.end():end], source))
    ids = [d.code for d in out]
    if len(ids)!=27 or len(set(ids))!=27 or set(ids)!=set(CANDIDATES):
        raise ValueError("Expected exactly 27 source-grounded draft IDs: "+repr(ids))
    return sorted(out, key=lambda d:(d.code.startswith("FIN"),d.code.startswith("DSKP"),d.code.startswith("FIX"),d.code))

def _inline_md(paragraph, text):
    from docx.shared import RGBColor
    for j, part in enumerate(re.split(r"\*\*(.*?)\*\*", text)):
        part = part.replace(chr(96), "").replace("*", "")
        if not part:
            continue
        run = paragraph.add_run(part)
        if j%2:
            run.bold = True
            run.font.color.rgb = RGBColor(25, 60, 97)

def build_word(draft, output):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt, RGBColor
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.top_margin, s.bottom_margin = Cm(1.18), Cm(1.04)
    s.left_margin, s.right_margin = Cm(1.25), Cm(1.25)
    s.header_distance, s.footer_distance = Cm(.42), Cm(.4)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Aptos", Pt(10.2)
    normal.paragraph_format.line_spacing = 1.12
    normal.paragraph_format.space_after = Pt(4.2)
    p = doc.add_paragraph()
    p.paragraph_format.space_after=Pt(1.5)
    r=p.add_run("RANCANGAN PENGAJARAN HARIAN  •  MATEMATIK TAHUN 6")
    r.bold=True; r.font.size=Pt(11.8); r.font.color.rgb=RGBColor(25,60,97)
    p=doc.add_paragraph()
    p.paragraph_format.space_after=Pt(2.4)
    r=p.add_run(draft.code+"  —  "+draft.title)
    r.bold=True; r.font.size=Pt(10.9)
    p=doc.add_paragraph()
    p.paragraph_format.space_after=Pt(4)
    r=p.add_run("DRAF QA STAGING  |  BELUM DILULUSKAN  |  BUKAN RPH PENGGUNA")
    r.bold=True; r.font.size=Pt(8.1); r.font.color.rgb=RGBColor(155,24,32)
    original, candidate, pages = CANDIDATES[draft.code]
    table=doc.add_table(rows=1,cols=3)
    table.style="Table Grid"
    cells=table.rows[0].cells
    for cell,(label,value) in zip(cells,(
        ("MASA","60 minit (cadangan)"),
        ("BUKU TEKS","Tahun 6, m/s "+pages),
        ("SP CALON","DSKP "+candidate),
    )):
        cell.text=label+": "+value
        for p2 in cell.paragraphs:
            p2.paragraph_format.space_after=Pt(0)
            for run in p2.runs:
                run.font.size=Pt(8.6)
    p=doc.add_paragraph()
    p.paragraph_format.space_after=Pt(3)
    r=p.add_run("SP asal Telegram: "+original+
        ("  |  Cadangan sahaja, bukan perubahan DB." if original!="TIADA"
         else "  |  Calon semakan DSKP/RPT tanpa ID PdP Telegram rasmi."))
    r.italic=True; r.font.size=Pt(8.1)

    # Preserve all complete original teaching paragraphs, no summarization.
    for raw in re.split(r"\n\s*\n",draft.body):
        raw=" ".join(raw.strip().splitlines())
        if not raw:
            continue
        p=doc.add_paragraph()
        p.paragraph_format.space_after=Pt(4.6)
        _inline_md(p,raw)
    footer=s.footer.paragraphs[0]
    footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=footer.add_run(
        "CIKGULAJU  •  SEMAKAN 08-11-2026  •  SK/SP, RPT, Buku Teks, BA dan E2E perlu signoff sebelum READY"
    )
    r.font.size=Pt(6.3)
    r.font.color.rgb=RGBColor(105,114,126)
    doc.core_properties.title=draft.code+" - DRAF QA"
    output.parent.mkdir(parents=True,exist_ok=True)
    doc.save(output)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    drafts=load_drafts()
    manifest=[]
    for draft in drafts:
        name="CIKGULAJU_RPH_T6_"+draft.code+"_DRAF_QA.docx"
        build_word(draft,out/name)
        original, candidate, pages=CANDIDATES[draft.code]
        manifest.append(dict(
            code=draft.code,title=draft.title,source_markdown=draft.source,
            docx=name,pdf=name.replace(".docx",".pdf"),
            sp_telegram=original,sp_candidate=candidate,printed_pages=pages,
            academic_signoff=False,teacher_ready=False))
    (out/"manifest.json").write_text(json.dumps({
        "schema":"cikgulaju.math.27_rph_a4_qa.v1",
        "count":27,"status":"ACADEMIC_HOLD",
        "production_modified":False,"items":manifest,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("CREATED 27 DOCX REVIEW PROOFS, NOT USER READY")

if __name__=="__main__":
    main()
