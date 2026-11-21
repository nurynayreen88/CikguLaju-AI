"""Conservative native ReportLab PDF RPH header layout, non-destructive.

Reuses the eight existing Paragraph pairs for subject, year, topic, class,
date, day, time and pupil count. Leaves all remaining curriculum table rows,
teaching phases, assessment, differentiation, reflection and PDF links intact.
Speciality renderers (Sains, DLP, PPKI, Islamic Jawi, Arabic RTL) stay as-is.
Unexpected source layouts fail closed to the existing PDF story.
"""
from __future__ import annotations

import html
import re

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from web.rph_reference_style_20261121 import color_for_state

EXPECTED_BM = (
    "Mata Pelajaran", "Tahun/Tingkatan", "Tarikh", "Hari", "Masa",
    "Kelas", "Bilangan Murid", "Tajuk",
)
EXPECTED_EN = (
    "Subject", "Year / Form", "Date", "Day", "Time", "Class",
    "Number of Pupils", "Topic",
)
SPECIAL = ("pendidikan islam", "bahasa arab", "sains", "science", "ppki", "dlp")


def _normal(value):
    return " ".join(str(value or "").casefold().split())


def _table_style(*, fill=None, border=False):
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if border:
        commands.insert(0, ("GRID", (0, 0), (-1, -1), 0.45, colors.black))
    if fill:
        commands.append(("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#" + fill)))
    return TableStyle(commands)


def _inner_identity_table(rows, indices, widths):
    table = Table([[rows[i][0], rows[i][1]] for i in indices],
                  colWidths=[x * mm for x in widths], hAlign="LEFT")
    table.setStyle(_table_style())
    return table


_ACTIVITY_TITLE = re.compile(
    r"^(?:Aktiviti|Activity)\s+[1-9]\d?"
    r"(?:\s*[.:)–—-]\s*\S.{0,109})?$",
    re.IGNORECASE,
)


def _bold_pdf_separate_activity_titles(table):
    """Apply bold only to source-authored title lines, never to instructions.

    Existing <br/> boundaries and curriculum text remain identical; odd
    ReportLab markup stays untouched rather than risking broken PDF output.
    """
    for row in getattr(table, "_cellvalues", ()):
        if (len(row) != 3
                or not isinstance(row[0], Paragraph)
                or not isinstance(row[1], Paragraph)):
            continue
        if _normal(row[0].getPlainText()) not in ("aktiviti utama", "main activities"):
            continue
        source = row[1]
        markup = source.text
        if not isinstance(markup, str) or "<br" not in markup.casefold():
            continue
        pieces = re.split(r"(<br\s*/?>)", markup, flags=re.IGNORECASE)
        found = False
        for i in range(0, len(pieces), 2):
            line = pieces[i]
            if i >= len(pieces) - 1 or "<" in line or ">" in line:
                continue
            if _ACTIVITY_TITLE.fullmatch(html.unescape(line).strip()):
                pieces[i] = "<b>" + line + "</b>"
                found = True
        if found:
            try:
                styled = Paragraph("".join(pieces), source.style)
                if styled.getPlainText() == source.getPlainText():
                    row[1] = styled
            except (ValueError, TypeError):
                # Fail closed to original content if ReportLab parsing differs.
                continue


def premium_pdf_story(state, story):
    """Return reflowed PDF story preserving each original Paragraph object.

    This is a native pre-render ReportLab layout change: no rasterization,
    hidden text, redaction, retyping of source curriculum, or PDF overlays.
    """
    if not isinstance(state, dict):
        return story
    fill = color_for_state(state)
    subject = _normal(state.get("subject"))
    # A legacy native RPH has precisely the title, three tables and three
    # spacers. Additional flowables signal a different lesson format.
    if (not fill or any(marker in subject for marker in SPECIAL)
            or not isinstance(story, list) or len(story) != 7):
        return story
    title = story[0]
    original_info = story[2]
    expected_title = ("DAILY LESSON PLAN" if subject in
                      ("english", "bahasa inggeris")
                      else "RANCANGAN PENGAJARAN HARIAN")
    if (not isinstance(title, Paragraph)
            or not isinstance(original_info, Table)
            or title.getPlainText().strip() != expected_title):
        return story
    if not all(isinstance(story[index], Spacer) for index in (1, 3, 5)):
        return story
    # All native outer grids must already be the approved 172 mm layout.
    # Never mix a premium 172 mm banner with a specialty width or phase grid.
    for table, sizes in (
        (story[2], (48, 124)), (story[4], (32, 112, 28)),
        (story[6], (48, 124)),
    ):
        if (not isinstance(table, Table)
                or len(table._colWidths) != len(sizes)
                or any(abs(width - mm * expected) > 2
                       for width, expected in zip(table._colWidths, sizes))):
            return story
    rows = getattr(original_info, "_cellvalues", ())
    if len(rows) < 12 or any(len(row) != 2 for row in rows):
        return story
    expected = EXPECTED_EN if subject in ("english", "bahasa inggeris") else EXPECTED_BM
    if not all(isinstance(row[0], Paragraph) and isinstance(row[1], Paragraph)
               and _normal(row[0].getPlainText()) == _normal(label)
               for row, label in zip(rows[:8], expected)):
        return story
    # Very long topic / teacher metadata retain the original printable flow.
    if any(len(row[1].getPlainText()) > 260 for row in rows[:8]):
        return story
    if any(abs(x - desired * mm) > 2
           for x, desired in zip(original_info._colWidths, (48, 124))):
        return story

    identity = _inner_identity_table(rows, (0, 1, 7), (34, 73))
    teacher = _inner_identity_table(rows, (5, 2, 3, 4, 6), (23, 33))
    # Restore owner-approved initial sample: the lesson identity occupies
    # the wide LEFT panel and the teacher fields the small RIGHT panel.
    # RTL specialty renderers are independent and require their own QA.
    header = Table([[[title, identity], teacher]],
                   colWidths=[112 * mm, 60 * mm], hAlign="CENTER")
    header.setStyle(_table_style(fill=fill, border=True))

    # Keep untouched curriculum paragraph objects and their source order.
    details = Table(rows[8:], colWidths=[48 * mm, 124 * mm], hAlign="CENTER")
    details.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    _bold_pdf_separate_activity_titles(story[4])
    return [header, Spacer(1, 3 * mm), details, *story[3:]]
