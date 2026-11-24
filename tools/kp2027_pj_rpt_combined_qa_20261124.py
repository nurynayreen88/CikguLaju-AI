"""Build combined A/B PJ KP2027 RPT review copy from structured candidates.
Offline only; not a release document or a route to active downloads.
"""
from pathlib import Path
from collections import Counter
import json
import argparse
import subprocess
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
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


def build(output):
    groups = load_rows()
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(297), Mm(210)
    sec.left_margin = sec.right_margin = Mm(14)
    sec.top_margin = sec.bottom_margin = Mm(14)
    for txt, size in (("RANCANGAN PENGAJARAN TAHUNAN 2027", 26),
                      ("PENDIDIKAN JASMANI", 21), ("KP2027 • TAHUN 1", 17),
                      ("KUMPULAN A DAN B", 14), ("SALINAN SEMAKAN DALAMAN", 12)):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(14)
        r = paragraph(p, txt, True, size)
        p.paragraph_format.space_before = Pt(14)
    for label in ("NAMA SEKOLAH:", "NEGERI:", "NAMA GURU:", "KELAS:", "DISEDIAKAN OLEH:", "DISEMAK OLEH:"):
        p = doc.add_paragraph()
        paragraph(p, label, True, 11)
    paragraph(doc.add_paragraph(),
              "127 PdP calon, 167 SP setiap kumpulan. Tarikh dan peruntukan jadual belum diluluskan. "
              "107 padanan SP berubah daripada katalog aktif dan memerlukan semakan akademik.", False, 10)
    doc.add_page_break()
    t = doc.add_table(rows=0, cols=5)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for col, width in zip(t.columns, WIDTHS):
        col.width = Mm(width)
    pr = t._tbl.tblPr
    w = pr.find(qn("w:tblW"))
    w.set(qn("w:type"), "dxa")
    w.set(qn("w:w"), str(Mm(sum(WIDTHS)).twips))
    borders = xml(pr, "tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        xml(borders, side, val="single", sz="4", color=EDGE)
    row(t, COLS, True)
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
            row(t, ("KUMPULAN " + group, old["bidang"] + "\n" + lesson["title"],
                    learning, activity, notes))
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    # A Word readback confirms exact rows, no lost standards, activities or group identity.
    result = Document(output)
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
