"""Build English SK Year 2–6 RPT review copies from the checked-in lesson tables."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re

import fitz
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rpt_2027" / "english"
CALENDAR = ROOT / "rpt_2027" / "takwim_pdp_2027_ab_draf.json"
LESSON = re.compile(r"LESSON:\s*(\d+)\b")
SHORT_WEEKS = {1, 5, 10, 11, 20, 35}
STOP_WEEK = 38
WEEK_WITH_ASSESSMENT = 18
CLOSED_WEEKS = {6, 19}
WIDTH, HEIGHT = landscape(A4)
NAVY = HexColor("#142C44")
TEAL = HexColor("#086B66")
MUTED = HexColor("#4C6074")
LINE = HexColor("#D9E3EA")
PALE = HexColor("#EFF6F7")
FONTS = Path("/usr/share/fonts/truetype/dejavu")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def source_rows(year):
    path = SOURCE / f"RPT_ENGLISH_TAHUN_{year}_2027_UNTUK_GURU.pdf"
    rows = {}
    with fitz.open(path) as document:
        for page in document:
            lines = [
                (line["bbox"], "".join(span["text"] for span in line["spans"]).strip())
                for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", ())
            ]
            cells = sorted(
                {
                    (item[1].y0, item[1].y1)
                    for drawing in page.get_drawings()
                    for item in drawing["items"]
                    if item[0] == "re" and abs(item[1].x0 - 125.4) < 0.2 and item[1].x1 > 804
                }
            )
            for top, bottom in cells:
                row_lines = [(bounds[0], value) for bounds, value in lines if top < bounds[1] < bottom]
                columns = tuple(
                    [value for x, value in row_lines if left <= x < right]
                    for left, right in ((128, 291), (291, 658), (658, 805))
                )
                match = LESSON.fullmatch(columns[0][0]) if columns[0] else None
                if match:
                    number = int(match[1])
                    if number in rows:
                        raise ValueError(f"Duplicate source Lesson {year}/{number}")
                    rows[number] = columns
    if list(rows) != list(range(1, 161)):
        raise ValueError(f"Incomplete source sequence for Year {year}")
    return rows


def span(values):
    first, last = map(date.fromisoformat, values)
    start = str(first.day)
    if first.month != last.month:
        start += f" {MONTHS[first.month - 1]}"
    return f"{start}–{last.day} {MONTHS[last.month - 1]}"


def schedule():
    calendar = json.loads(CALENDAR.read_text())
    first = 1
    weeks = []
    for row in calendar["minggu"]:
        week = row["minggu"]
        count = 3 if week in SHORT_WEEKS else 4
        if week > STOP_WEEK or week in CLOSED_WEEKS:
            count = 0
        lessons = tuple(range(first, first + count))
        weeks.append((week, span(row["A"]), span(row["B"]), lessons))
        first += count
    assert first == 139 and len(weeks) == 44
    return weeks


def write_text(canvas, text, x, y, *, size=10, bold=False, color=NAVY):
    canvas.setFillColor(color)
    canvas.setFont("RPTBold" if bold else "RPT", size)
    canvas.drawString(x, y, text)


def paragraph(lines, *, size=7.6):
    text = "<br/>".join(
        f"<b>{escape(line)}</b>" if LESSON.fullmatch(line) or line in {"MAIN", "COMPLEMENTARY"}
        else escape(line)
        for line in lines if line
    )
    return Paragraph(text, ParagraphStyle(
        "RPT row", fontName="RPT", fontSize=size, leading=size + 2.1, textColor=NAVY,
    ))


def frame(canvas, year, section, title, detail):
    write_text(canvas, f"CIKGULAJU  /  ENGLISH SK YEAR {year}  /  2027", 34, HEIGHT - 28,
               size=9, bold=True, color=TEAL)
    canvas.setFillColor(TEAL)
    canvas.roundRect(WIDTH - 177, HEIGHT - 36, 143, 18, 5, fill=1, stroke=0)
    write_text(canvas, section, WIDTH - 170, HEIGHT - 30, size=7.4, bold=True, color=white)
    write_text(canvas, title, 34, HEIGHT - 64, size=20, bold=True)
    write_text(canvas, detail, 34, HEIGHT - 84, size=9, color=MUTED)
    canvas.setStrokeColor(LINE)
    canvas.line(34, 37, WIDTH - 34, 37)
    write_text(canvas, "One planned Lesson is 60 minutes. Check the class timetable and local holidays.",
               34, 22, size=7.5, color=MUTED)
    write_text(canvas, str(canvas.getPageNumber()), WIDTH - 50, 22, size=8, bold=True)


def draw_rows(canvas, rows):
    left = 34
    widths = (170, 445, WIDTH - 68 - 615)
    positions = (left, left + widths[0], left + widths[0] + widths[1])
    y = HEIGHT - 105
    canvas.setFillColor(NAVY)
    canvas.rect(left, y - 23, sum(widths), 23, fill=1, stroke=0)
    for x, title in zip(positions, ("LESSON / THEME / TOPIC", "CONTENT AND LEARNING STANDARDS", "REFERENCE / MATERIALS"), strict=True):
        write_text(canvas, title, x + 8, y - 15, size=8, bold=True, color=white)
    y -= 23
    for index, row in enumerate(rows):
        cells = [paragraph(lines) for lines in row]
        wrapped = [cell.wrap(width - 16, HEIGHT)[1] for cell, width in zip(cells, widths, strict=True)]
        height = max(wrapped) + 16
        if index % 2 == 0:
            canvas.setFillColor(PALE)
            canvas.rect(left, y - height, sum(widths), height, fill=1, stroke=0)
        canvas.setStrokeColor(LINE)
        canvas.line(left, y - height, WIDTH - 34, y - height)
        for cell, x, cell_height in zip(cells, positions, wrapped, strict=True):
            cell.drawOn(canvas, x + 8, y - 8 - cell_height)
        y -= height
    if y < 48:
        raise ValueError(f"Lesson table extends past the page area: {y:.1f}")


def cover(canvas, year, scheduled_count):
    frame(canvas, year, "PLANNING COPY",
          f"Rancangan Pengajaran Tahunan 2027 · English SK Year {year}",
          f"Kumpulan A & B  /  {scheduled_count} dated Lessons and {160 - scheduled_count} Lessons awaiting timetable slots")
    y = HEIGHT - 134
    labels = (
        ("SCHOOL", "TEACHER"),
        ("CLASS", "STATE / GROUP"),
    )
    for pair in labels:
        for x, label in zip((34, 424), pair, strict=True):
            write_text(canvas, label, x, y, size=8.4, bold=True, color=TEAL)
            canvas.setStrokeColor(LINE)
            canvas.line(x, y - 29, x + 355, y - 29)
        y -= 65
    write_text(canvas, "2027 planning dates", 34, y - 5, size=13, bold=True)
    notes = (
        "Group A (Kedah, Kelantan and Terengganu): teaching target 21 October.",
        "Group B (other states and federal territories): teaching target 22 October.",
        "Week 18: 9–13 May (A), 10–14 May (B). Use for school assessment or the available English sessions.",
        "Week 19 (Aidiladha and Wesak): 0 planned Lessons. Review takes place on available days in Week 39.",
        "Early November: school assessment as applicable. Keep the following two weeks free of new Lessons.",
        f"The plan assigns up to four Lesson periods a week through October. Lesson {scheduled_count + 1:03d}–160",
        "need an agreed timetable adjustment. If Week 18 is used for assessment, four further Lessons need slots.",
        "Sources: KPM Academic Calendar 2027 and CikguLaju's KSSR English SK Scheme of Work index.",
    )
    for i, note in enumerate(notes):
        write_text(canvas, note, 34, y - 31 - 23 * i, size=9, color=MUTED)
    canvas.showPage()


def calendar_page(canvas, year, weeks, notes, title):
    frame(canvas, year, "GROUPS A & B", title,
          "Dates shown are school-week ranges. Use the available teaching days and school timetable.")
    left = 34
    columns = (left + 8, 120, 251, 390)
    width = WIDTH - 68
    y = HEIGHT - 105
    canvas.setFillColor(NAVY)
    canvas.rect(left, y - 21, width, 21, fill=1, stroke=0)
    for x, label in zip(columns, ("WEEK", "GROUP A", "GROUP B", "LESSON RANGE / SCHOOL ACTIVITY"), strict=True):
        write_text(canvas, label, x, y - 14, size=8, bold=True, color=white)
    y -= 21
    for i, (week, group_a, group_b, numbers) in enumerate(weeks):
        if i % 2 == 0:
            canvas.setFillColor(PALE)
            canvas.rect(left, y - 17, width, 17, fill=1, stroke=0)
        activity = notes.get(week)
        if activity is None:
            activity = f"{numbers[0]:03d}–{numbers[-1]:03d}  /  {len(numbers)} Lessons"
        for x, value in zip(columns, (str(week), group_a, group_b, activity), strict=True):
            write_text(canvas, value, x, y - 12, size=8.1, bold=x == left + 8)
        y -= 17
    canvas.showPage()


def build(year, out):
    rows = source_rows(year)
    weeks = schedule()
    numbered = [n for _, _, _, lessons in weeks for n in lessons]
    assert numbered == list(range(1, len(numbered) + 1))
    pdf = Canvas(str(out), pagesize=landscape(A4), pageCompression=1, invariant=1)
    pdf.setTitle(f"RPT English SK Year {year} 2027 / Kumpulan A & B")
    pdf.setAuthor("CikguLaju")
    cover(pdf, year, len(numbered))
    notes = {
        6: "Festival holidays / 0 planned Lessons",
        WEEK_WITH_ASSESSMENT: "061–064 if English slots are available / school assessment",
        19: "Aidiladha and Wesak / 0 planned Lessons",
        39: "Revision on available school days",
        40: "School assessment or UASA, where applicable",
        41: "School assessment or post-assessment activities",
        42: "Year-end activities / 0 new Lessons",
        43: "Year-end activities / 0 new Lessons",
        44: "Year-end activities / 0 new Lessons",
    }
    calendar_page(pdf, year, weeks[:22], notes, "2027 calendar · January to June")
    calendar_page(pdf, year, weeks[22:], notes, "2027 calendar · June to December")
    for week, group_a, group_b, lessons in weeks:
        if lessons:
            detail = f"Group A: {group_a}   /   Group B: {group_b}   /   {len(lessons)} Lessons"
            if week == WEEK_WITH_ASSESSMENT:
                detail += "   /   If English slots are available"
            frame(pdf, year, "DATED LESSONS", f"Week {week:02d}  ·  {lessons[0]:03d}–{lessons[-1]:03d}", detail)
            draw_rows(pdf, (rows[n] for n in lessons))
            pdf.showPage()
    pending = list(range(len(numbered) + 1, 161))
    for offset in range(0, len(pending), 4):
        numbers = pending[offset:offset + 4]
        frame(pdf, year, "TIMETABLE SLOTS NEEDED", f"Lessons {numbers[0]:03d}–{numbers[-1]:03d}",
              "Agree on timetable placement or an integrated teaching plan before the revision window.")
        draw_rows(pdf, (rows[n] for n in numbers))
        pdf.showPage()
    pdf.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("RPT", str(FONTS / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("RPTBold", str(FONTS / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("RPT", normal="RPT", bold="RPTBold")
    for year in range(2, 7):
        build(year, output / f"RPT_English_SK_2027_Year_{year}_A_B.pdf")


if __name__ == "__main__":
    main()
