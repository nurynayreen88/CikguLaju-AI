#!/usr/bin/env python3
"""RPT 2027 Bahasa Arab T2–T6: teacher-printable, undated A/B draft.

Reuses the 298-source index of 6 Nov 2026, never fabricates week, date, holiday,
timetable or final curriculum certification. Writes files only to --output-dir.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / "rpt_2027" / "bahasa_arab"
COUNTS = {2: 60, 3: 60, 4: 58, 5: 60, 6: 60}
NEGERI = {
    "A": "Kedah · Kelantan · Terengganu",
    "B": "Johor · Melaka · Negeri Sembilan · Pahang · Perak · Perlis · Pulau Pinang · Sabah · Sarawak · Selangor · Kuala Lumpur · Labuan · Putrajaya",
}
NAVY = "12304A"
TEAL = "197B89"
LIGHT = "ECF5F6"
GREY = "66737E"
ARABIC = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]+")


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as fd:
        return list(csv.DictReader(fd))


def load_sources():
    titles = {}
    for record in read_csv(SOURCE / "unit_sequence_DRAF_20261105.csv"):
        key = (int(record["tahun"]), int(record["unit"]))
        assert key not in titles
        titles[key] = record["tajuk_arab"]
    assert len(titles) == 20

    groups = {}
    for group in ("A", "B"):
        rows = read_csv(SOURCE / f"rpt_2027_KUMPULAN_{group}_INDEKS_PDP_DRAF.csv")
        assert len(rows) == 298
        by_year = defaultdict(list)
        keys = set()
        for r in rows:
            year, number, unit = int(r["tahun"]), int(r["pdp"]), int(r["unit"])
            key = (year, number)
            assert r["kumpulan"] == group and year in COUNTS and 1 <= unit <= 4
            assert key not in keys
            keys.add(key)
            assert (year, unit) in titles
            assert r["sk"] and r["sp"].startswith(r["sk"] + ".")
            assert r["fokus"].strip() and r["halaman_buku"].strip()
            assert r["status_rpt"] == "DRAF_TARIKH_BELUM_DISAHKAN"
            assert r["ready"] == "FALSE" and r["kelulusan_guru"] == "FALSE"
            assert not any(r[key] for key in ("tarikh_pdp_2027", "waktu_mula", "waktu_tamat", "negeri"))
            assert (BASE / r["rph_staging"]).is_file()
            by_year[year].append(r)
        assert {year: len(by_year[year]) for year in COUNTS} == COUNTS
        for year in COUNTS:
            indexes = sorted(int(r["pdp"]) for r in by_year[year])
            assert indexes == list(range(1, COUNTS[year] + 1))
            units = [int(r["unit"]) for r in sorted(by_year[year], key=lambda r: int(r["pdp"]))]
            assert units == sorted(units), "Unit order not monotonic"
        groups[group] = by_year
    # A/B refer to the same PdP content; only calendar group differs.
    for year in COUNTS:
        a = sorted(groups["A"][year], key=lambda r: int(r["pdp"]))
        b = sorted(groups["B"][year], key=lambda r: int(r["pdp"]))
        for left, right in zip(a, b):
            assert all(left[k] == right[k] for k in ("pdp", "unit", "sk", "sp", "fokus", "halaman_buku", "rph_staging"))
    return titles, groups


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def run_text(paragraph, value, *, bold=False, size=8.8, color=None):
    segments = re.split(r"([\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]+)", str(value))
    for part in segments:
        if not part:
            continue
        arabic = bool(ARABIC.search(part))
        run = paragraph.add_run(part)
        run.bold = bold
        run.font.name = "Amiri" if arabic else "Carlito"
        run.font.size = Pt(size + (1.2 if arabic else 0))
        if color:
            run.font.color.rgb = RGBColor.from_string(color)
        if arabic:
            rpr = run._element.get_or_add_rPr()
            fonts = rpr.rFonts
            if fonts is None:
                fonts = OxmlElement("w:rFonts")
                rpr.insert(0, fonts)
            fonts.set(qn("w:cs"), "Amiri")
            rtl = OxmlElement("w:rtl")
            rtl.set(qn("w:val"), "1")
            rpr.append(rtl)


def add_text(doc, value, *, size=9, bold=False, color=None, space_after=6, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    run_text(p, value, bold=bold, size=size, color=color)
    return p


def cell_text(cell, value, *, bold=False, size=8.8, fg=None, align=None):
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    if align is not None:
        p.alignment = align
    run_text(p, value, bold=bold, size=size, color=fg)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    mar = cell._tc.get_or_add_tcPr().first_child_found_in("w:tcMar")
    if mar is None:
        mar = OxmlElement("w:tcMar")
        cell._tc.get_or_add_tcPr().append(mar)
    for side in ("top", "bottom", "left", "right"):
        elem = OxmlElement("w:" + side)
        elem.set(qn("w:w"), "100" if side in ("top", "bottom") else "95")
        elem.set(qn("w:type"), "dxa")
        mar.append(elem)


def repeated_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def no_row_split(row):
    pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    pr.append(el)


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._r.addnext(fld)


def create_one(group, year, records, titles, output):
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_height = Cm(21.0)
    section.page_width = Cm(29.7)
    section.top_margin = Cm(1.3)
    section.bottom_margin = Cm(1.3)
    section.left_margin = Cm(1.25)
    section.right_margin = Cm(1.25)
    section.header_distance = Cm(0.62)
    section.footer_distance = Cm(0.7)

    style = doc.styles["Normal"]
    style.font.name = "Carlito"
    style.font.size = Pt(9)
    style.paragraph_format.space_after = Pt(0)

    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_text(hp, f"CIKGULAJU  |  BAHASA ARAB  |  TAHUN {year}  |  KUMPULAN {group}", bold=True, size=8.2, color=GREY)
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_text(fp, "RPT 2027 • DRAF KANDUNGAN • TARIKH BELUM DISAHKAN  |  Halaman ", size=8.0, color=GREY)
    add_page_number(fp)

    # Cover page.
    add_text(doc, "RANCANGAN PENGAJARAN TAHUNAN", size=20, bold=True, color=NAVY, space_after=7)
    add_text(doc, "BAHASA ARAB  •  2027", size=16, bold=True, color=TEAL, space_after=15)
    add_text(doc, f"TAHUN {year}   |   KUMPULAN {group}", size=23, bold=True, color=NAVY, space_after=15)
    add_text(doc, "Sekolah: ____________________________________________________________", size=10, space_after=12)
    add_text(doc, "Guru: ______________________________________________________________", size=10, space_after=12)
    add_text(doc, "Negeri / kumpulan rujukan:", size=10, bold=True, color=TEAL, space_after=3)
    add_text(doc, NEGERI[group], size=9.4, space_after=14)
    add_text(doc, f"{len(records)} PdP calon  |  4 unit  |  Rujukan RPH CikguLaju tersedia", bold=True, size=12, color=NAVY, space_after=18)
    add_text(doc, "STATUS: DRAF UNTUK SEMAKAN GURU", bold=True, size=12, color=TEAL, space_after=8)
    add_text(doc,
             "RPT ini disusun berdasarkan 298 indeks PdP calon Bahasa Arab Tahun 2–6 yang telah dipadankan dalam GitHub staging. "
             "Tarikh, masa, cuti negeri/gantian dan agihan waktu rasmi belum ditetapkan. "
             "Ruang tarikh dibiarkan kosong untuk diisi selepas padanan takwim dan jadual sekolah. "
             "Nombor PdP bukan minggu persekolahan.", size=10.2, space_after=16)
    add_text(doc, "Rujukan: Buku Teks / DSKP / RPT 2026 dalam manifest sumber CikguLaju. "
             "SK/SP dan halaman buku yang tertera ialah calon yang belum semuanya menerima pengesahan individu.", size=9.3, color=GREY)
    doc.add_page_break()

    width = (Cm(1.6), Cm(11.25), Cm(1.85), Cm(2.0), Cm(3.4), Cm(3.15), Cm(3.45))
    for unit in range(1, 5):
        unit_rows = sorted((r for r in records if int(r["unit"]) == unit), key=lambda r: int(r["pdp"]))
        unit_heading = add_text(doc, f"UNIT {unit}  •  {titles[(year, unit)]}", bold=True, size=14, color=NAVY, space_after=4)
        # Page-break-before never creates an orphan blank page when the prior
        # unit fills its final page (unlike an extra empty break paragraph).
        if unit != 1:
            unit_heading.paragraph_format.page_break_before = True
        add_text(doc, f"Tahun {year}  |  Kumpulan {group}  |  {len(unit_rows)} PdP  |  Tarikh diisi oleh guru mengikut jadual sebenar",
                 size=8.8, color=GREY, space_after=9)
        table = doc.add_table(rows=1, cols=7)
        table.style = "Table Grid"
        table.autofit = False
        for col, w in zip(table.columns, width):
            col.width = w
        header = table.rows[0]
        repeated_header(header)
        for cell, label, w in zip(header.cells, ("PdP", "Fokus PdP", "SK", "SP", "Buku Teks", "Tarikh PdP", "Catatan Guru"), width):
            cell.width = w
            shade(cell, NAVY)
            cell_text(cell, label, bold=True, size=8.5, fg="FFFFFF")
        for idx, r in enumerate(unit_rows):
            row = table.add_row()
            no_row_split(row)
            if idx % 2:
                for cell in row.cells:
                    shade(cell, LIGHT)
            values = (f'{int(r["pdp"]):03d}', r["fokus"], r["sk"], r["sp"],
                      "hlm " + r["halaman_buku"], "____ / ____ / 2027", "")
            for cell, value, w in zip(row.cells, values, width):
                cell.width = w
                cell_text(cell, value, size=8.65,
                          align=WD_ALIGN_PARAGRAPH.CENTER if cell == row.cells[0] else None)
        add_text(doc,
            "Nota: Kod SK/SP, fokus dan halaman buku ialah cadangan sumber; guru menyemak kesesuaian dengan DSKP/buku teks sebenar. "
            "Tarikh, cuti dan waktu belum dimuktamadkan.",
            size=8.1, color=GREY, space_after=4)

    doc.core_properties.title = f"RPT 2027 Bahasa Arab Tahun {year} Kumpulan {group} (Draf Boleh Sunting)"
    doc.core_properties.subject = "Indeks PdP sumber RPH; belum RPT tahunan rasmi bertarikh"
    doc.core_properties.comments = "PREMERGE: no deployment; no approved annual RPT dates"
    dest = output / f"RPT_Bahasa_Arab_2027_Tahun{year}_Kumpulan{group}_DRAF.docx"
    doc.save(dest)
    return dest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    titles, groups = load_sources()
    docs = [create_one(group, year, groups[group][year], titles, args.output_dir)
            for group in ("A", "B") for year in COUNTS]
    assert len(docs) == 10 and all(path.is_file() and path.stat().st_size > 10000 for path in docs)
    manifest = {
        "version": "20261106-rpt-ba-a-b-undated-premerge",
        "status": "DRAF_TARIKH_BELUM_DISAHKAN",
        "source_commit_note": "Source index derived from PR #371; use checked out workflow commit",
        "groups": ["A", "B"],
        "per_year": COUNTS,
        "rph_candidate_count": sum(COUNTS.values()),
        "rpt_docx_count": len(docs),
        "source_row_count_a_b": 596,
        "dated_rpt_verified": False,
        "teacher_approved": False,
        "release_authorized": False,
        "files": [p.name for p in docs],
    }
    (args.output_dir / "RPT_BA_2027_PREMERGE_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: 10 editable RPT drafts = Years2-6 x GroupA/B, 596 source rows, no invented dates")


if __name__ == "__main__":
    main()
