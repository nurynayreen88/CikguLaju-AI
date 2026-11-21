"""Conservative native ReportLab PDF RPH header layout, non-destructive.

Reuses the eight existing Paragraph pairs for subject, year, topic, class,
date, day, time and pupil count. Leaves all remaining curriculum table rows,
teaching phases, assessment, differentiation, reflection and PDF links intact.
Speciality renderers (Sains, DLP, PPKI, Islamic Jawi, Arabic RTL) stay as-is.
Unexpected source layouts fail closed to the existing PDF story.
"""
from __future__ import annotations

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


def premium_pdf_story(state, story):
    """Return reflowed PDF story preserving each original Paragraph object.

    This is a native pre-render ReportLab layout change: no rasterization,
    hidden text, redaction, retyping of source curriculum, or PDF overlays.
    """
    fill = color_for_state(state)
    subject = _normal(state.get("subject")) if isinstance(state, dict) else ""
    if (not fill or any(marker in subject for marker in SPECIAL)
            or not isinstance(story, list) or len(story) < 7):
        return story
    title = story[0]
    original_info = story[2]
    if not isinstance(title, Paragraph) or not isinstance(original_info, Table):
        return story
    if not isinstance(story[1], Spacer) or not isinstance(story[3], Spacer):
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
    return [header, Spacer(1, 3 * mm), details, *story[3:]]
