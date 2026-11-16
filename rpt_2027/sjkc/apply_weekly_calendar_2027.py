"""Apply the SK-style weekly KPM calendar to existing 2027 SJK RPT Word files."""
from argparse import ArgumentParser
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.table import _Row


KPM_SOURCE = "https://www.moe.gov.my/surat-siaran-kpm-bil1-tahun-2027-kalendar-akademik"
# Lampiran A and B show 9, 10, 12 and 13 teaching weeks in the four periods.
SCHOOL_PERIODS = (
    (date(2027, 1, 4), date(2027, 3, 4), date(2027, 1, 4), date(2027, 3, 5), 9),
    (date(2027, 3, 14), date(2027, 5, 20), date(2027, 3, 15), date(2027, 5, 21), 10),
    (date(2027, 6, 6), date(2027, 8, 26), date(2027, 6, 7), date(2027, 8, 27), 12),
    (date(2027, 9, 5), date(2027, 12, 2), date(2027, 9, 6), date(2027, 12, 3), 13),
)
TERM_BREAKS = {
    10: ("Cuti Penggal 1", "05/03–13/03", "06/03–14/03"),
    20: ("Cuti Pertengahan Tahun", "21/05–05/06", "22/05–06/06"),
    32: ("Cuti Penggal 2", "27/08–04/09", "28/08–05/09"),
}
FESTIVAL_NOTES = {
    5: "Cuti tambahan Tahun Baharu Cina pada 05/02 (Kumpulan B).",
    6: "Tahun Baharu Cina.",
    10: "Cuti tambahan Hari Raya Aidilfitri pada 14/03 (Kumpulan A).",
    19: "Hari Raya Aidiladha, Hari Wesak dan cuti tambahan KPM.",
    20: "Awal Muharam dan Hari Keputeraan Yang di-Pertuan Agong.",
    30: "Maulidur Rasul dan cuti ganti mengikut negeri.",
    33: "Hari Malaysia pada 16/09.",
    39: "Deepavali dan cuti tambahan KPM mengikut negeri.",
}
DATE_TEXT = re.compile(r"\d{2}[./]\d{2}[./]2027")


def week_windows():
    """Return calendar windows, keeping holiday weeks numbered as in the SK RPT."""
    windows = {}
    for a_start, a_end, b_start, b_end, count in SCHOOL_PERIODS:
        monday = b_start
        for _ in range(count):
            a_start_this_week = max(monday - timedelta(days=1), a_start)
            a_end_this_week = min(monday + timedelta(days=3), a_end)
            b_end_this_week = min(monday + timedelta(days=4), b_end)
            windows[monday] = (len(windows) + 1, a_start_this_week, a_end_this_week,
                               monday, b_end_this_week)
            monday += timedelta(days=7)
        if monday - timedelta(days=3) != b_end:
            raise ValueError("The KPM period does not agree with the weekly range.")
    return windows


def replace_paragraph(paragraph, text):
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(text)


def replace_cell(cell, text):
    replace_paragraph(cell.paragraphs[0], text)
    for paragraph in cell.paragraphs[1:]:
        paragraph._p.getparent().remove(paragraph._p)


def prior_date(cell):
    match = DATE_TEXT.search(cell.text)
    if not match:
        raise ValueError(f"Expected one original date in {cell.text!r}")
    return datetime.strptime(match.group().replace(".", "/"), "%d/%m/%Y").date()


def monday_for(day):
    return day - timedelta(days=day.weekday())


def add_band(table, text, *, before=None, pale=False, keep_next=True):
    row = table.add_row()
    if before is not None:
        before.addprevious(row._tr)
    cell = row.cells[0].merge(row.cells[-1])
    paint = OxmlElement("w:shd")
    paint.set(qn("w:fill"), "E8EDF4" if pale else "DFEAF6")
    cell._tc.get_or_add_tcPr().append(paint)
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fmt = paragraph.paragraph_format
    fmt.keep_with_next = keep_next
    fmt.space_before = Pt(1)
    fmt.space_after = Pt(1)
    run = paragraph.add_run(text)
    run.bold = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor.from_string("183654")
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def weekly_label(window, counts, chinese):
    number, a_start, a_end, b_start, b_end = window
    count = counts[number]
    tail = f"{count} PdP" if count else "Tiada PdP dijadualkan"
    if number == 1 and not count:
        tail += " · Pengisian sekolah"
    if number in FESTIVAL_NOTES:
        tail += f" · {FESTIVAL_NOTES[number]}"
    if chinese:
        tail = f"第{number}周  ·  {tail}"
    return (
        f"Minggu {number:02d}   |   Kumpulan A  {a_start:%d/%m}–{a_end:%d/%m}"
        f"   |   Kumpulan B  {b_start:%d/%m}–{b_end:%d/%m}   |   {tail}"
    )


def remove_date_column(table, index, grow_index):
    grid = table._tbl.tblGrid
    old, grow = grid.gridCol_lst[index], grid.gridCol_lst[grow_index]
    grow_width = int(grow.w) + int(old.w)
    grow.w = grow_width
    for row in table.rows:
        cells = row.cells
        cells[grow_index].width = grow_width
        row._tr.remove(cells[index]._tc)
    grid.remove(old)


def edit(source, output):
    document = Document(source)
    windows = week_windows()
    main_tables = []
    counts = Counter()
    expected_id = 1
    chinese = source.parent.name != "bahasa_melayu"
    for table in document.tables:
        headings = [cell.text for cell in table.rows[0].cells]
        if headings[0] == "PdP dan tarikh":
            date_column = 0
        elif len(headings) >= 5 and headings[0].startswith("PdP") and (
            headings[1].startswith("Tarikh") or headings[1] == "日期"
        ):
            date_column = 1
        else:
            continue

        entries = []
        for row in table.rows[1:]:
            lesson = row.cells[0].text.splitlines()[0]
            if int(lesson) != expected_id:
                raise ValueError(f"Expected PdP {expected_id}, got {lesson} in {source}")
            expected_id += 1
            number = windows[monday_for(prior_date(row.cells[date_column]))][0]
            counts[number] += 1
            entries.append((row._tr, number, lesson))

        if date_column == 0:
            replace_cell(table.rows[0].cells[0], "PdP")
            for tr, _, lesson in entries:
                replace_cell(_Row(tr, table).cells[0], lesson)
        else:
            grow_column = max(range(2, len(headings)), key=lambda i: table.columns[i].width)
            remove_date_column(table, date_column, grow_column)
        main_tables.append((table, entries))

    if not main_tables:
        raise ValueError(f"No PdP tables found in {source}")

    ordered_windows = list(windows.values())
    previous_number = 0
    for table, entries in main_tables:
        for tr, number, _ in entries:
            for next_number in range(previous_number + 1, number + 1):
                if next_number in TERM_BREAKS:
                    name, a, b = TERM_BREAKS[next_number]
                    add_band(table, f"{name}   |   Kumpulan A  {a}   |   Kumpulan B  {b}",
                             before=tr, pale=True)
                add_band(table, weekly_label(ordered_windows[next_number - 1], counts, chinese),
                         before=tr, pale=not counts[next_number])
            previous_number = number
    # Let Word flow the source's fixed-size table chunks naturally once the weekly
    # bands add vertical space. Keep the cover break and appendix starts.
    body = document._element.body
    tables = {table._tbl for table, _ in main_tables}
    started = False
    for element in list(body):
        if element in tables:
            started = True
        elif started and element.tag == qn("w:p"):
            following = element.getnext()
            while following is not None and following.tag == qn("w:p"):
                following = following.getnext()
            if following in tables and not element.xpath(".//w:t") and element.xpath('.//w:br[@w:type="page"]'):
                body.remove(element)
            elif following in tables:
                for marker in element.xpath("./w:pPr/w:pageBreakBefore"):
                    marker.set(qn("w:val"), "0")
            elif element.getprevious() is main_tables[-1][0]._tbl and not element.xpath(".//w:t") and element.xpath('.//w:br[@w:type="page"]'):
                heading = element.getnext()
                if heading is not None and heading.tag == qn("w:p"):
                    heading.get_or_add_pPr().get_or_add_pageBreakBefore().val = True
                    body.remove(element)
    last_table = main_tables[-1][0]
    for next_number in range(previous_number + 1, len(ordered_windows) + 1):
        add_band(last_table, weekly_label(ordered_windows[next_number - 1], counts, chinese),
                 pale=True, keep_next=False)
    add_band(last_table, "Cuti Akhir Persekolahan   |   Kumpulan A  03/12–31/12"
             "   |   Kumpulan B  04/12–31/12", pale=True, keep_next=False)

    for table in document.tables:
        headings = [cell.text for cell in table.rows[0].cells]
        if headings[:2] == ["PdP", "Tarikh"]:
            replace_cell(table.rows[0].cells[1], "Minggu")
            for row in table.rows[1:]:
                number = windows[monday_for(prior_date(row.cells[1]))][0]
                replace_cell(row.cells[1], f"{number:02d}")

    for paragraph in document.paragraphs:
        original = paragraph.text
        if "W.P. Kuala Lumpur" in original and "Kumpulan B" in original:
            delimiter = next(marker for marker in ("•", "·", "|") if marker in original)
            prefix = original.split(delimiter)[0].rstrip()
            replace_paragraph(paragraph, f"{prefix}  {delimiter}  Kumpulan A dan B")
        elif original.startswith(("Tarikh ialah cadangan", "Cadangan tarikh berdasarkan",
                                  "Tarikh dalam RPT ialah cadangan")):
            replace_paragraph(paragraph, "Julat minggu mengikut takwim KPM 2027. Susun sesi PdP mengikut cuti negeri dan jadual waktu sekolah.")
        elif original.startswith("日期为建议日期"):
            replace_paragraph(paragraph, "每周日期根据教育部校历。各校可按州属假期及课程表安排教学。")
        elif original.startswith("Tarikh simpanan"):
            replace_paragraph(paragraph, "Gunakan slot kosong untuk PdP gantian mengikut takwim sekolah.")

    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("use distinct source and output paths")
    edit(args.source, args.output)


if __name__ == "__main__":
    main()
