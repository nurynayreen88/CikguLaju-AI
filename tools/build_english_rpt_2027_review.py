"""Build English SK Year 2–6 RPT review copies from the checked-in lesson tables."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import sys

import fitz
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
if not __package__:
    sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "rpt_2027" / "english"
CALENDAR = ROOT / "rpt_2027" / "takwim_pdp_2027_ab_draf.json"
LESSON = re.compile(r"LESSON:\s*(\d+)\b")
DEEPAVALI_WEEK = 39
JUNE_SHORT_WEEK = 20
SHORT_WEEK_SESSIONS = {1: 3, 5: 3, JUNE_SHORT_WEEK: 3, 35: 3, DEEPAVALI_WEEK: 2}
STOP_WEEK = DEEPAVALI_WEEK
PAIR_PLAN = SOURCE / "october_lesson_pairs.json"
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
    if year == 4:
        # The original SK SOW and printed Student's Book both place these activities on p.15.
        for number, activity in ((17, 1), (18, 3)):
            topic, standards, _ = rows[number]
            rows[number] = (topic, standards, [f"Get Smart Plus 4 SB p.15, Activity {activity}"])
    if year == 5:
        from web.english_y5_standalone_runtime import CHOICE_LESSONS
        from web.english_y5_teacher_choice_runtime import DSKP_CODES, load_proposal, selected_standards

        for number in sorted(CHOICE_LESSONS):
            proposal = load_proposal(number)
            if proposal is None:
                raise ValueError(f"Missing Year 5 DSKP selection for Lesson {number}")
            topic, _, references = rows[number]
            standards = ["DSKP standards selected for this plan"]
            for label, (sk, sp) in zip(("MAIN", "COMPLEMENTARY"), selected_standards(proposal), strict=True):
                standards.extend((label, f"SK {sk} · {DSKP_CODES[sk]}", f"SP {sp} · {DSKP_CODES[sp]}"))
            rows[number] = (topic, standards, references)
    return rows


def span(values):
    first, last = map(date.fromisoformat, values)
    start = str(first.day)
    if first.month != last.month:
        start += f" {MONTHS[first.month - 1]}"
    return f"{start}–{last.day} {MONTHS[last.month - 1]}"


def schedule(year):
    calendar = json.loads(CALENDAR.read_text())
    pairs = set(json.loads(PAIR_PLAN.read_text())[str(year)])
    first = 1
    weeks = []
    for row in calendar["minggu"]:
        week = row["minggu"]
        count = 0
        if week <= STOP_WEEK and week not in CLOSED_WEEKS:
            count = SHORT_WEEK_SESSIONS.get(week, 4)
        sessions = []
        for _ in range(count):
            length = 2 if first in pairs else 1
            sessions.append(tuple(range(first, first + length)))
            first += length
        weeks.append((week, span(row["A"]), span(row["B"]), sessions))
    paired_starts = {s[0] for _, _, _, sessions in weeks for s in sessions if len(s) == 2}
    assert first == 161 and len(weeks) == 44 and pairs == paired_starts
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
    write_text(canvas, "One 60-minute session per teaching day. Paired SOW references share one integrated plan.",
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


def cover(canvas, year):
    frame(canvas, year, "ENGLISH SK", f"Rancangan Pengajaran Tahunan 2027 · Year {year}",
          "Kumpulan A & B  /  160 SOW Lessons in 142 teaching sessions")
    canvas.setStrokeColor(LINE)
    canvas.rect(WIDTH / 2 - 48, HEIGHT - 217, 96, 96, stroke=1, fill=0)
    write_text(canvas, "LOGO SEKOLAH", WIDTH / 2 - 31, HEIGHT - 172, size=8, color=MUTED)
    for top, label in ((232, "NAMA SEKOLAH"), (271, "NAMA GURU")):
        write_text(canvas, label, 134, HEIGHT - top - 17, size=9, bold=True, color=TEAL)
        canvas.setStrokeColor(LINE)
        canvas.line(270, HEIGHT - top - 22, 708, HEIGHT - top - 22)
    write_text(canvas, "2027 planning dates", 34, HEIGHT - 325, size=13, bold=True)
    notes = (
        "Final teaching week: 24–28 October (A), 25–29 October (B). Check the school days around Deepavali.",
        "Weeks 40–43: revision, assessment or school activities. Week 44: year-end school activities.",
        "Week 18: 9–13 May (A), 10–14 May (B). Use available slots before school assessment.",
        "Week 19 (Aidiladha and Wesak): no planned Lessons. Week 39: up to two shared sessions.",
        "Plan up to four sessions on different days. Each pair uses one 60-minute RPH.",
        "Teach both sets of learning standards with a shared introduction, assessment and closure.",
        "The plan schedules 142 hours for SOW Lessons. Schools plan the remaining time within their annual allocation.",
        "Sources: KPM calendar, BKPP holidays and English SK SOW.",
    )
    for i, note in enumerate(notes):
        write_text(canvas, note, 34, HEIGHT - 350 - 23 * i, size=9, color=MUTED)
    canvas.showPage()


def lesson_range(numbers):
    return f"{numbers[0]:03d}–{numbers[-1]:03d}"


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
    for i, (week, group_a, group_b, sessions) in enumerate(weeks):
        if i % 2 == 0:
            canvas.setFillColor(PALE)
            canvas.rect(left, y - 17, width, 17, fill=1, stroke=0)
        note = notes.get(week)
        if sessions:
            pairs = [f"{s[0]:03d}+{s[1]:03d}" for s in sessions if len(s) == 2]
            activity = f"{sessions[0][0]:03d}–{sessions[-1][-1]:03d}  /  {len(sessions)} sessions"
            if pairs:
                activity += f"  /  Pairs {' · '.join(pairs)}"
        else:
            activity = note
        for x, value in zip(columns, (str(week), group_a, group_b, activity), strict=True):
            write_text(canvas, value, x, y - 12, size=8.1, bold=x == left + 8)
        y -= 17
    local_notes = (
        ("Weeks 1 and 5: three sessions in the shared plan. Check local school days and the English timetable.",
         "Week 18: use available English slots before assessment. Week 20: three sessions on separate days.")
        if weeks[0][0] == 1 else
        ("Week 35: three sessions in the shared plan. Week 39: two sessions around Deepavali.",
         "A pair such as 021+022 refers to one RPH with combined activities in one session.",
         "Use the school's assessment timetable when assigning the final English sessions.")
    )
    for index, note in enumerate(local_notes):
        write_text(canvas, note, left, y - 14 - 11 * index, size=7.5, color=MUTED)
    canvas.showPage()


def build(year, out):
    rows = source_rows(year)
    weeks = schedule(year)
    numbered = [n for _, _, _, sessions in weeks for session in sessions for n in session]
    assert numbered == list(range(1, 161))
    pdf = Canvas(str(out), pagesize=landscape(A4), pageCompression=1, invariant=1)
    pdf.setTitle(f"RPT English SK Year {year} 2027 / Kumpulan A & B")
    pdf.setAuthor("CikguLaju")
    cover(pdf, year)
    notes = {
        6: "Festival holidays / 0 planned Lessons",
        19: "Aidiladha and Wesak / 0 planned Lessons",
        44: "Year-end activities / 0 new Lessons",
    }
    notes.update(dict.fromkeys(range(STOP_WEEK + 1, 44), "Revision, assessment or school activities / 0 new Lessons"))
    calendar_page(pdf, year, weeks[:22], notes, "2027 calendar · January to June")
    calendar_page(pdf, year, weeks[22:], notes, "2027 calendar · June to December")
    for week, group_a, group_b, sessions in weeks:
        if not sessions:
            continue
        detail = f"Group A: {group_a}   /   Group B: {group_b}   /   {len(sessions)} sessions"
        if week in {WEEK_WITH_ASSESSMENT, DEEPAVALI_WEEK}:
            detail += "   /   Confirm teaching slots"
        numbered_sessions = list(enumerate(sessions, 1))
        groups = (
            [numbered_sessions] if sum(map(len, sessions)) <= 4
            else [numbered_sessions[:2], numbered_sessions[2:]]
        )
        for group in groups:
            lessons = [n for _, session in group for n in session]
            week_rows = []
            for slot, session in group:
                for n in session:
                    topic, standards, references = rows[n]
                    label = f"Session {slot} · 60 min"
                    if len(session) == 2:
                        label = f"Session {slot} · RPH {session[0]:03d}+{session[1]:03d}"
                    week_rows.append(([topic[0], label, *topic[1:]], standards, references))
            frame(pdf, year, "DATED LESSONS", f"Week {week:02d}  ·  {lesson_range(lessons)}", detail)
            draw_rows(pdf, week_rows)
            pdf.showPage()
    pdf.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--year", type=int, choices=range(2, 7))
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("RPT", str(FONTS / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("RPTBold", str(FONTS / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("RPT", normal="RPT", bold="RPTBold")
    for year in (args.year,) if args.year else range(2, 7):
        build(year, output / f"RPT_English_SK_2027_Year_{year}_A_B.pdf")


if __name__ == "__main__":
    main()
