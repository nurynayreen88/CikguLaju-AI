"""Reflow the Jawi-corrected Telegram PDFs against the Web RPT schedule.

Run from the repository root with PyMuPDF. Point the first argument at a
checkout of PR #776 at 1e7e6c0, and the second at the Web suggestions JSON
at 034d0e0. The output directory must differ from the source directory.
"""

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import fitz

from rpt_2027.pendidikan_islam.telegram_downloads import FILE_TEMPLATE


CALENDAR = Path("rpt_2027/pendidikan_moral/induk_minggu_2027_ab.json")
CLOSURES = {6: "Cuti Tahun Baharu Cina", 19: "Cuti Hari Raya Aidiladha dan Hari Wesak"}
SHORT_WEEKS = {1, 5, 10, 20, 35}
DEEPAVALI = 39
COUNTS = {2: 112, 3: 147, 4: 151, 5: 143, 6: 143}
# The matching SK/SP rows in RPT Pendidikan Islam Tahun 6 (SK) 2026
# show one hour each. See the source citations in the audit.
RESTORE_HOUR = {60, 87}
COLUMNS = (32.8, 317.9, 482.8, 648.4, 736.3, 792.4)
LESSON = re.compile(r"PdP (\d{3})")
WEEK = re.compile(r"^M(\d{2})  ")
NUM = rb"(-?[\d.]+)"
TEXT = re.compile(rb"\bBT\s+(.*?)\s+ET\b", re.S)
ORIGIN = re.compile(NUM + rb"\s+" + NUM + rb"\s+Td\b")
BOTTOM = 565


def page_bands(page):
    boundaries = sorted({round(y, 3) for d in page.get_drawings()
                         if d["rect"].width > 680 and d["rect"].x0 < 34
                         for y in (d["rect"].y0, d["rect"].y1)})
    if len(boundaries) < 3:
        raise ValueError(f"Missing table grid on page {page.number + 1}")
    return boundaries


def band_spans(page, boundaries):
    result = defaultdict(list)
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", ()):
            for span in line["spans"]:
                result[bisect_right(boundaries, span["origin"][1])].append(span)
    return result


def lesson_numbers(spans):
    return [int(match[1]) for span in spans if span["origin"][0] > COLUMNS[-2]
            and (match := LESSON.fullmatch(span["text"]))]


def band_minutes(spans):
    field = " ".join(span["text"].strip() for span in sorted(
        spans, key=lambda item: (item["origin"][1], -item["origin"][0]))
        if COLUMNS[3] < span["origin"][0] < COLUMNS[4])
    return sum(int(value) * (60 if unit == "جم" else 1)
               for value, unit in re.findall(r"(\d+)\s*(جم|مينيت)", field))


def cell_text(spans, omit_restored_time=False):
    return Counter((span["text"], span["font"], span["size"], round(span["origin"][0], 2))
                   for span in spans if not (omit_restored_time and span["text"] == "1 جم"
                                             and COLUMNS[3] < span["origin"][0] < COLUMNS[4]))


def original_rows(pdf, year):
    rows = {}
    headers = []
    content = {}
    one_hour = []
    for page in pdf:
        boundaries = page_bands(page)
        spans = band_spans(page, boundaries)
        operations = defaultdict(list)
        for operation in TEXT.findall(page.read_contents()):
            match = ORIGIN.search(operation)
            if match is None:
                raise ValueError(f"Unexpected text operation on page {page.number + 1}")
            baseline = page.rect.height - float(match[2])
            operations[bisect_right(boundaries, baseline)].append(operation)
            if year == 6 and page.number == 1 and abs(baseline - 94.251) < 0.01:
                if COLUMNS[3] < float(match[1]) < COLUMNS[4]:
                    one_hour.append(operation)
        headers.append([(y, operations[i]) for i, y in enumerate(boundaries[:2])])
        for i in range(2, len(boundaries)):
            labels = lesson_numbers(spans[i])
            if not labels:
                continue
            (number,) = labels
            if number != len(rows) + 1 or not operations[i]:
                raise ValueError(f"Unexpected PdP {number:03} on page {page.number + 1}")
            minutes = band_minutes(spans[i])
            if not minutes and year == 6 and number in RESTORE_HOUR:
                if len(one_hour) != 2:
                    raise ValueError("Expected the original 1 جم text from Year 6 PdP 003")
                cell_baseline = next(s["origin"][1] for s in spans[i]
                                     if COLUMNS[3] < s["origin"][0] < COLUMNS[4])
                for template in one_hour:
                    x, _ = ORIGIN.search(template).groups()
                    position = b"%s %.4f Td" % (x, page.rect.height - cell_baseline - 20.85)
                    operations[i].append(ORIGIN.sub(position, template, count=1))
                minutes = 60
            if not minutes:
                raise ValueError(f"Missing duration for Year {year} PdP {number:03}")
            rows[number] = (boundaries[i - 1], boundaries[i], operations[i], minutes)
            content[number] = cell_text(spans[i])
    if len(rows) != COUNTS[year]:
        raise ValueError(f"Year {year}: expected {COUNTS[year]} PdP, found {len(rows)}")
    return rows, content, headers[0], headers[1][1]


def translated_operation(operation, offset):
    # PDF text matrices use bottom-up coordinates. Translate the full BT/ET
    # block at draw time, including any positions within ActualText sequences.
    return b"q 1 0 0 1 0 %.4f cm\nBT\n" % offset + operation + b"\nET\nQ\n"


def write_operations(page, operations, offset):
    if not operations:
        return
    doc = page.parent
    xref = doc.get_new_xref()
    doc.update_object(xref, "<<>>")
    doc.update_stream(xref, b"".join(translated_operation(op, offset) for op in operations))
    # Appending streams avoids rebuilding hard-shaped Amiri glyphs.
    contents = " ".join(f"{ref} 0 R" for ref in [*page.get_contents(), xref])
    doc.xref_set_key(page.xref, "Contents", f"[{contents}]")


def calendar_windows():
    groups = json.loads(CALENDAR.read_text(encoding="utf-8"))["weeks"]
    windows = []
    for week, (group_a, group_b) in enumerate(zip(groups["A"], groups["B"], strict=True), 1):
        if group_a["week"] != group_b["week"] or group_a["week"] != f"M{week:02}":
            raise ValueError(f"Calendar groups disagree at M{week:02}")
        windows.append([group[k] for group in (group_a, group_b) for k in ("start", "end")])
    if len(windows) != 44:
        raise ValueError("Expected 44 planning windows")
    return windows


def allocate(rows, windows, web):
    suggested = [web.get(str(week), [*dates, {"": []}])
                 for week, dates in enumerate(windows, 1)]
    if [entry[:4] for entry in suggested] != windows:
        raise ValueError("Web date windows disagree with the RPT calendar")
    if [n for entry in suggested for n in entry[4][""]] != list(rows):
        raise ValueError("Web and Telegram PdP sequences disagree")
    # Keep sessions in sequence and stay as close to the existing Web
    # distribution as the durations printed in the Telegram rows allow.
    candidates = {0: (0, ())}
    target_end = 0
    for week, entry in enumerate(suggested, 1):
        target_count = len(entry[4][""])
        target_end += target_count
        limit = (0 if week in CLOSURES else 120 if week == DEEPAVALI
                 else 180 if week in SHORT_WEEKS else 240)
        next_candidates = {}
        for start, (cost, counts) in candidates.items():
            minutes = 0
            for count in range(min(4, len(rows) - start) + 1):
                end = start + count
                if count:
                    minutes += rows[end][3]
                if minutes > limit:
                    break
                score = cost + abs(target_end - end) + 3 * abs(target_count - count)
                if end not in next_candidates or score < next_candidates[end][0]:
                    next_candidates[end] = (score, (*counts, count))
        candidates = next_candidates
    if len(rows) not in candidates:
        raise ValueError("The full PdP sequence does not fit the holiday-adjusted timetable")
    cursor = 1
    for week, (dates, count) in enumerate(zip(windows, candidates[len(rows)][1]), 1):
        identity = list(range(cursor, cursor + count))
        yield week, dates, identity
        cursor += count


def draw_grid(page, top, bottom, *, merged=False):
    page.draw_rect(fitz.Rect(COLUMNS[0], top, COLUMNS[-1], bottom), width=0.5)
    if not merged:
        for x in COLUMNS[1:-1]:
            page.draw_line((x, top), (x, bottom), width=0.5)


def week_heading(week, dates, ids, continuation=False):
    a1, a2, b1, b2 = [date.fromisoformat(value).strftime("%d/%m") for value in dates]
    detail = CLOSURES.get(week, "Ruang fleksibel" if not ids else "")
    suffix = ("  |  " + detail) if detail else ("  |  Sambungan" if continuation else "")
    return (f"M{week:02}  |  Kumpulan A {a1}-{a2}  |  Kumpulan B {b1}-{b2}"
            f"  |  {len(ids)} PdP" + suffix)


def render(source, destination, year, windows, web):
    with fitz.open(source) as doc:
        rows, content, (first_header, first_columns), (other_top, other_columns) = original_rows(doc, year)
        plan = list(allocate(rows, windows, web))
        width, height = doc[0].rect.br
        resources = doc.xref_get_key(doc[0].xref, "Resources")[1]
        if any(doc.xref_get_key(page.xref, "Resources")[1] != resources for page in doc):
            raise ValueError("Expected common embedded Amiri resources across the source PDF")
        original_pages = doc.page_count

        def new_page(first=False):
            page = doc.new_page(width=width, height=height)
            doc.xref_set_key(page.xref, "Resources", resources)
            # The new date headings share the same font resource across pages.
            page.insert_font(fontname="hebo")
            if first:
                top, preceding = first_header
                bottom, operations = first_columns
                write_operations(page, preceding, 0)
                page.draw_line((38.2, 52.55), (803.75, 52.55), width=0.6)
            else:
                top = 31.4
                bottom, operations = other_top, other_columns
            draw_grid(page, top, bottom)
            write_operations(page, operations, 0)
            return page, bottom

        page, y = new_page(first=True)
        for week, dates, ids in plan:
            need = rows[ids[0]][1] - rows[ids[0]][0] if ids else 0
            if y + 25 + need > BOTTOM:
                page, y = new_page()
            draw_grid(page, y, y + 25, merged=True)
            page.insert_text((40, y + 15), week_heading(week, dates, ids),
                             fontsize=9, fontname="hebo")
            y += 25
            for number in ids:
                top, bottom, operations, _ = rows[number]
                height_needed = bottom - top
                if y + height_needed > BOTTOM:
                    page, y = new_page()
                    draw_grid(page, y, y + 25, merged=True)
                    page.insert_text((40, y + 15), week_heading(week, dates, ids, True),
                                     fontsize=9, fontname="hebo")
                    y += 25
                draw_grid(page, y, y + height_needed)
                write_operations(page, operations, top - y)
                y += height_needed
        doc.delete_pages(0, original_pages - 1)
        doc.xref_set_key(doc.pdf_catalog(), "StructTreeRoot", "null")
        doc.xref_set_key(doc.pdf_catalog(), "MarkInfo", "null")
        doc.save(destination, garbage=4, deflate=True, no_new_id=True)
    return plan, rows, content


def verify_pdf(path, plan, rows, content, year):
    expected = {week: (dates, ids) for week, dates, ids in plan}
    printed = {}
    actual = defaultdict(list)
    week = None
    with fitz.open(path) as pdf:
        for page in pdf:
            bands = page_bands(page)
            spans = band_spans(page, bands)
            for i in range(2, len(bands)):
                values = [span["text"] for span in spans[i]]
                for value in values:
                    if match := WEEK.match(value):
                        week = int(match[1])
                        continuation = value.endswith("  |  Sambungan")
                        if continuation != (week in printed):
                            raise ValueError(f"Unexpected duplicate heading in {path} at M{week:02}")
                        printed[week] = value
                        if value != week_heading(week, *expected[week], continuation):
                            raise ValueError(f"Wrong date/count in {path} at M{week:02}")
                for number in lesson_numbers(spans[i]):
                    actual[week].append(number)
                    omit_time = year == 6 and number in RESTORE_HOUR
                    if (cell_text(spans[i], omit_time) != content[number]
                            or band_minutes(spans[i]) != rows[number][3]):
                        raise ValueError(f"Content or duration changed at PdP {number:03} in {path}")
    if (list(printed) != list(expected) or actual.keys() - expected.keys()
            or any(actual[n] != ids for n, (_, ids) in expected.items())):
        raise ValueError(f"Wrong weekly PdP sequence in {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("web_json", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("Choose a different output directory")
    web = json.loads(args.web_json.read_text(encoding="utf-8"))
    windows = calendar_windows()
    args.output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.output) as directory:
        tmp = Path(directory)
        for year in COUNTS:
            filename = FILE_TEMPLATE % year
            path = tmp / filename
            plan, rows, content = render(args.source / filename, path, year, windows, web[f"PI:{year}"])
            verify_pdf(path, plan, rows, content, year)
        for path in tmp.iterdir():
            path.replace(args.output / path.name)


if __name__ == "__main__":
    main()
