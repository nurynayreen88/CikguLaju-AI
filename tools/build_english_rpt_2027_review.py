"""Read-only English RPT source and schedule helpers, ported from the verified original builder."""
from datetime import date
import json
from pathlib import Path
import re
import fitz
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"rpt_2027"/"english"
CALENDAR=ROOT/"rpt_2027"/"takwim_pdp_2027_ab_draf.json"
LESSON=re.compile(r"LESSON:\s*(\d+)\b")
DEEPAVALI_WEEK=39
JUNE_SHORT_WEEK=20
SHORT_WEEK_SESSIONS={1:3,5:3,JUNE_SHORT_WEEK:3,35:3,DEEPAVALI_WEEK:2}
STOP_WEEK=DEEPAVALI_WEEK
PAIR_PLAN=SOURCE/"october_lesson_pairs.json"
CLOSED_WEEKS={6,19}
MONTHS=("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
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


