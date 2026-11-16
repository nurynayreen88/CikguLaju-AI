"""English SK Year 2–6 review plans shared by Web and Telegram RPH Hari Ini."""
from datetime import date, datetime, time, timedelta
from functools import lru_cache
import io
import json
import os
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from tools.build_english_paired_rph_2027 import INK, TEAL, make_sheet, paired_plan_index
from tools.build_english_rpt_2027_review import CALENDAR, PAIR_PLAN, schedule
from web.school_days_2027 import FRI_SAT, is_school_day


def enabled():
    return os.environ.get("CIKGULAJU_ENGLISH_2027_INTEGRATED_RPH_ENABLED") == "1"


@lru_cache(maxsize=1)
def _pair_numbers():
    return {
        (int(year), number): (first, first + 1)
        for year, starts in json.loads(PAIR_PLAN.read_text()).items()
        for first in starts
        for number in (first, first + 1)
    }


def pair_numbers(year, number):
    return _pair_numbers().get((year, number))


def teaching_date():
    return datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()


@lru_cache(maxsize=1)
def _calendar():
    return json.loads(CALENDAR.read_text())["minggu"]


@lru_cache(maxsize=5)
def _schedule(year):
    return {week: sessions for week, _, _, sessions in schedule(year)}


def teaching_week(year, state, target):
    if year not in range(2, 7) or target.year != 2027 or not is_school_day(state, target):
        return ()
    group = "A" if state in FRI_SAT else "B"
    for row in _calendar():
        start, end = map(date.fromisoformat, row[group])
        if start <= target <= end:
            return _schedule(year)[row["minggu"]]
    return ()


def one_hour(start, end):
    try:
        return datetime.combine(date.min, time.fromisoformat(end)) - datetime.combine(
            date.min, time.fromisoformat(start)) == timedelta(hours=1)
    except (TypeError, ValueError):
        return False


def pbd_context(year, number):
    lessons = paired_plan_index()[year, number][-1]
    standards = tuple(code for _, row, *_ in lessons
                      for code in (row["main_ls"], row["complementary_ls"]))
    return {
        "lesson": "Lesson " + " + ".join(f"{lesson[0]:03d}" for lesson in lessons),
        "sk": " / ".join(dict.fromkeys(code.rsplit(".", 1)[0] for code in standards)),
        "sp": " / ".join(dict.fromkeys(standards)),
        "criteria1": lessons[0][3],
        "criteria2": lessons[1][3],
    }


def filename(year, pair, fmt):
    a, b = pair
    suffix = "docx" if fmt == "word" else "pdf"
    return f"RPH_English_SK_2027_Y{year}_L{a:03d}-{b:03d}.{suffix}"


def _pdf_for_sheet(sheet, output):
    """Render the same editable plan without a LibreOffice dependency."""
    body = ParagraphStyle("RPH", fontName="Helvetica", fontSize=10, leading=13,
                          textColor=colors.HexColor("#" + INK), spaceAfter=6)
    band = ParagraphStyle("Band", parent=body, fontName="Helvetica-Bold",
                          textColor=colors.white, backColor=colors.HexColor("#" + TEAL),
                          spaceBefore=7, spaceAfter=8, borderPadding=5)
    footer = ParagraphStyle("Footer", parent=body, alignment=TA_RIGHT, fontSize=8)
    story = []
    for index, block in enumerate(sheet.iter_inner_content()):
        if hasattr(block, "rows"):
            story.append(Paragraph(escape("  ·  ".join(cell.text for cell in block.rows[0].cells)), band))
            continue
        style = body
        if index == 0:
            style = ParagraphStyle("Series", parent=body, textColor=colors.HexColor("#" + TEAL))
        elif index == 1:
            style = ParagraphStyle("Topic", parent=body, fontSize=24, leading=28)
        if block.text:
            text = "".join(
                ("<b>" + escape(run.text) + "</b>") if run.bold else escape(run.text)
                for run in block.runs
            ).replace("\n", "<br/>")
            story.append(Paragraph(text, style))
    story.extend((Spacer(1, 7), Paragraph("CikguLaju  /  English SK 2027", footer)))
    SimpleDocTemplate(output, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=17 * mm, bottomMargin=15 * mm,
                      title=sheet.core_properties.title).build(story)


def render(year, number, fmt, teacher):
    if fmt not in ("word", "pdf"):
        raise ValueError("Unknown RPH format")
    plan = paired_plan_index()[year, number]
    output = io.BytesIO()
    sheet = make_sheet(*plan, teacher=teacher)
    if fmt == "word":
        sheet.save(output)
    else:
        _pdf_for_sheet(sheet, output)
    return output.getvalue()


def plan_for_selection(year, number, unit):
    plan = paired_plan_index().get((year, number))
    if plan is None:
        return None
    topic = plan[-1][0][1]["topic"]
    if " ".join(topic.casefold().split()) != " ".join(unit.casefold().split()):
        return None
    return tuple(item[0] for item in plan[-1])
