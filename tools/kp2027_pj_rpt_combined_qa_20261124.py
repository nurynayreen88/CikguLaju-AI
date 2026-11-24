"""Build combined A/B PJ KP2027 RPT review copy from structured candidates.
Offline only; not a release document or a route to active downloads.
"""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile
import re
import json
import argparse
import subprocess
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits"
SOURCE = AUDIT / "kp2027_pj_t1_127_rph_structured_candidates_20261124.json"
BASELINE = AUDIT / "kp2027_pj_t1_rpt_127_pdp_source_map_20261124.json"
DELTA = AUDIT / "kp2027_pj_t1_rpt_rph_sp_delta_20261124.json"
COLS = ("MINGGU / KUMPULAN", "TEMA / TAJUK",
        "STANDARD KANDUNGAN & PEMBELAJARAN", "PdP / AKTIVITI / PBD",
        "CATATAN / RUJUKAN")
WIDTHS = (31, 43, 81, 77, 37)
TONE = "E3EFE6"
EDGE = "A0AEA3"


def load_rows():
    m, c, d = (json.loads(p.read_text(encoding="utf-8")) for p in (BASELINE, SOURCE, DELTA))
    if (m["status"], c["status"], d["status"]) != ("QA_RPT_SOURCE_MAP_NOT_PUBLISHED",
            "QA_NEW_SOURCE_NOT_PUBLISHED", "QA_ONLY_NOT_PUBLISHED"):
        raise ValueError("Unapproved QA input status")
    out = {}
    standards = {}
    for group, expected in (("A", 64), ("B", 63)):
        a, b, z = m["groups"][group]["rows"], c["groups"][group], d["groups"][group]["rows"]
        if not len(a) == len(b) == len(z) == expected:
            raise ValueError("Count mismatch")
        result = []
        for idx, (old, new, delta) in enumerate(zip(a, b, z), 1):
            if not old["pdp"] == new["pdp"] == delta["pdp"] == idx or new["group"] != group:
                raise ValueError("PdP identity mismatch")
            if old["sp"] != new["original_sp"] or old["sp"] != delta["current_sp"]:
                raise ValueError("Original SP mismatch")
            codes = [s["code"] for s in new["standards"]]
            if codes != delta["candidate_sp"] or new["status"] != "QA_NOT_READY":
                raise ValueError("Candidate mismatch")
            if old["date"] is not None or new["date"] is not None:
                raise ValueError("Unexpected date")
            for s in new["standards"]:
                if s["code"] in standards and standards[s["code"]] != s["text"]:
                    raise ValueError("Conflicting SP text")
                standards[s["code"]] = s["text"]
            result.append((old, new, delta))
        if len({s["code"] for _, r, _ in result for s in r["standards"]}) != 167:
            raise ValueError("Group SP coverage incomplete")
        out[group] = result
    if len(standards) != 167:
        raise ValueError("SP dictionary incomplete")
    if sum(x[2]["review_status"] == "REVIEW_REQUIRED" for rows in out.values() for x in rows) != 107:
        raise ValueError("Review count changed")
    return out


def xml(parent, name, **attrs):
    e = OxmlElement("w:" + name)
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    parent.append(e)
    return e


def paragraph(p, text, bold=False, size=9):
    r = p.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(size)
    r.bold = bold
    r.font.color.rgb = RGBColor.from_string("23342C")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    return r


def row(table, values, header=False):
    rr = table.add_row()
    xml(rr._tr.get_or_add_trPr(), "cantSplit")
    if header:
        xml(rr._tr.get_or_add_trPr(), "tblHeader")
    for i, (cell, value) in enumerate(zip(rr.cells, values)):
        cell.width = Mm(WIDTHS[i])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        if header:
            xml(cell._tc.get_or_add_tcPr(), "shd", fill=TONE)
        for j, line in enumerate(value.split("\n")):
            paragraph(cell.paragraphs[0] if j == 0 else cell.add_paragraph(), line, header)
    return rr


def approved_template():
    """Use the exact SHA-verified BM KP2027 document from the approved bundle."""
    archive = ROOT / "rpt_2027/kp2027/year1_rpt_bm_math_alam_gabungan_ab_kulit_asal_20261122.zip"
    data = archive.read_bytes()
    assert sha256(data).hexdigest() == "859a78af79f2741c9caa074cab36fbb16d376028178b77fb2aaf993a297f2ff9"
    name = "CIKGULAJU_RPT_KP2027_T1_BM_SK_KUMPULAN_AB_GABUNGAN_2027.docx"
    with ZipFile(BytesIO(data)) as z:
        payload = z.read("WORD/" + name)
        manifest = json.loads(z.read("MANIFEST_QA.json"))
        assert sha256(payload).hexdigest() == manifest["files"][name]["sha256"]
    return Document(BytesIO(payload))


def replace_paragraph_text(p, value):
    if len(p.runs) != 1:
        raise ValueError("Unexpected approved cover run structure: " + p.text)
    p.runs[0].text = value


def template_cover_and_grid():
    doc = approved_template()
    ps = doc.paragraphs
    assert len(ps) >= 14 and len(doc.tables) >= 2
    assert ps[2].text == "RPT 2027"
    for idx, marker in ((4,"NAMA SEKOLAH:"),(5,"SUBJEK:"),(7,"KUMPULAN:"),
                        (8,"NAMA GURU:"),(10,"Disediakan oleh:")):
        assert ps[idx].text.startswith(marker)
    table = doc.tables[0]
    assert len(table.columns) == 5
    assert tuple(c.text.strip() for c in table.rows[0].cells) == COLS
    # Keep the native cover, page setup, actual table grid, header row and styles.
    cover_nodes = {p._p for p in ps[:12]}
    body = doc.element.body
    for node in list(body):
        if node not in cover_nodes and node is not table._tbl and node.tag != qn("w:sectPr"):
            body.remove(node)
    status_written = False
    for p in ps[:12]:
        orig = p.text
        value = re.sub(r"Bahasa\s+Melayu(?:\s*\(?SK\)?)?", "PENDIDIKAN JASMANI", orig, flags=re.I)
        if p is ps[5]:
            value = "SUBJEK: PENDIDIKAN JASMANI"
        if "SEMAKAN PELAKSANAAN" in value.upper():
            value = re.sub("SEMAKAN PELAKSANAAN", "SALINAN SEMAKAN DALAMAN", value, flags=re.I)
            status_written = True
        if value != orig:
            replace_paragraph_text(p, value)
    if not status_written:
        p = ps[5]
        replace_paragraph_text(p, p.text + " — SALINAN SEMAKAN DALAMAN")
    # Add a page break only if the retained cover does not already end with one.
    if not any('w:type="page"' in p._p.xml for p in ps[:12]):
        br = doc.add_paragraph()
        br.add_run().add_break(WD_BREAK.PAGE)
        table._tbl.addprevious(br._p)
    # The explanatory note belongs on the internal review page, not the cover.
    note = doc.add_paragraph()
    paragraph(note, "127 PdP calon; 167 SP setiap kumpulan. Tarikh dan peruntukan jadual belum diluluskan. "
              "107 padanan SP memerlukan semakan akademik.", False, 9)
    table._tbl.addprevious(note._p)
    source_row = next(r for r in table.rows[1:] if r.cells[0].text.strip() == "KUMPULAN A")
    row_template = deepcopy(source_row._tr)
    for r in list(table.rows)[1:]:
        table._tbl.remove(r._tr)
    header = table.rows[0]
    for cell in header.cells:
        pr = cell._tc.get_or_add_tcPr()
        shading = pr.find(qn("w:shd"))
        if shading is None:
            shading = xml(pr, "shd", fill=TONE)
        else:
            shading.set(qn("w:fill"), TONE)
    # Footer/header must not retain another subject's identity.
    for sec in doc.sections:
        for part in (sec.header, sec.footer):
            for p in part.paragraphs:
                value = re.sub(r"Bahasa\s+Melayu(?:\s*\(?SK\)?)?", "PENDIDIKAN JASMANI", p.text, flags=re.I)
                if value != p.text:
                    replace_paragraph_text(p, value)
    return doc, table, row_template


def template_row(table, row_template, values):
    tr = deepcopy(row_template)
    table._tbl.append(tr)
    rr = table.rows[-1]
    pr = tr.get_or_add_trPr()
    for tag in ("trHeight", "tblHeader", "cantSplit"):
        for element in list(pr.findall(qn("w:"+tag))):
            pr.remove(element)
    xml(pr, "cantSplit")
    for cell, value in zip(rr.cells, values):
        # Retain the exact cell geometry and first paragraph styling.
        p0 = cell.paragraphs[0]
        style = deepcopy(p0._p.pPr) if p0._p.pPr is not None else None
        rstyle = deepcopy(p0.runs[0]._r.rPr) if p0.runs and p0.runs[0]._r.rPr is not None else None
        cell.text = ""
        for j, line in enumerate(value.split("\n")):
            p = cell.paragraphs[0] if j == 0 else cell.add_paragraph()
            if style is not None:
                p._p.insert(0, deepcopy(style))
            run = p.add_run(line)
            if rstyle is not None:
                run._r.insert(0, deepcopy(rstyle))
            # Row text must remain readable and wrap rather than disappear.
            p.paragraph_format.keep_with_next = False
    return rr


def build(output):
    groups = load_rows()
    doc, t, row_template = template_cover_and_grid()
    for group, items in groups.items():
        for old, lesson, delta in items:
            sp = "\n".join(s["code"] + " " + s["text"] for s in lesson["standards"])
            # The source supplies SP statements but does not supply SK statements.
            # Retain SK code prefixes, do not manufacture official SK wording.
            sk = list(dict.fromkeys(s["code"].rsplit(".", 1)[0] for s in lesson["standards"]))
            learning = "SK: " + ", ".join(sk) + "\nSP:\n" + sp
            activity = ("PdP %03d" % lesson["pdp"]) + "\n" + "\n".join(
                a["title"] + ": " + a["body"] for a in lesson["activities"]) + "\nPBD: " + lesson["pbd"]
            notes = "DK hlm. " + ", ".join(map(str, old["dk_pages"])) + " (peta asal)"
            if delta["review_status"] == "REVIEW_REQUIRED":
                notes += "\nSemak padanan SP calon."
            template_row(t, row_template, ("KUMPULAN " + group, old["bidang"] + "\n" + lesson["title"],
                    learning, activity, notes))
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    # A Word readback confirms exact rows, no lost standards, activities or group identity.
    result = Document(output)
    reference = approved_template()
    assert result.tables[0]._tbl.tblGrid.xml == reference.tables[0]._tbl.tblGrid.xml
    assert result.paragraphs[2].text == reference.paragraphs[2].text
    for idx in (4,7,8,10):
        assert result.paragraphs[idx].text == reference.paragraphs[idx].text
    rows = result.tables[0].rows
    assert len(rows) == 128
    k = 1
    for group, items in groups.items():
        for _, lesson, delta in items:
            cells = rows[k].cells
            assert cells[0].text == "KUMPULAN " + group
            assert ("PdP %03d" % lesson["pdp"]) in cells[3].text
            assert all(s["code"] + " " + s["text"] in cells[2].text for s in lesson["standards"])
            assert all(a["body"] in cells[3].text for a in lesson["activities"])
            assert lesson["pbd"] in cells[3].text
            k += 1
    return output


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=Path("qa-pj-rpt"))
    p.add_argument("--pdf", action="store_true")
    args = p.parse_args()
    file = build(args.out / "QA_RPT_KP2027_PJ_T1_AB_2027.docx")
    if args.pdf:
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf",
                        "--outdir", str(args.out.resolve()), str(file.resolve())],
                       check=True, timeout=120)
        assert file.with_suffix(".pdf").is_file()
    print("QA: 127 PdP, 167 SP per group, 107 changes on review hold")
