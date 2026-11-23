"""Source-preserving, two-panel Jawi header for verified active PI native PDF.

Reuses the exact eight already-rendered Jawi metadata pairs; no source text
or images are altered. Rebuilds only their visual containers, retaining all
curriculum/activities/reflection flowables verbatim. Unsupported layouts
fail closed to the established one-table PI renderer.
"""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Spacer

HEADER_LABELS = (
    "مات ڤلاجرن", "تاهون / تيڠکتن", "تاريخ", "هاري",
    "ماس", "کلس", "بيلڠن موريد", "تاجوق",
)
IDENTITY_FILL = colors.HexColor("#F8EBCD")
TEACHER_FILL = colors.HexColor("#F5F7FA")


def _flow_text(value):
    return str(getattr(value, "text", "") or "").strip()


def _inner(rows, indexes, widths):
    table = Table([[rows[i][0], rows[i][1]] for i in indexes],
                  colWidths=[w * mm for w in widths], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return table


def reflow_verified_pi_header(state, story):
    if not isinstance(state, dict) or (
        str(state.get("task") or "").strip() != "rph"
        or str(state.get("subject") or "").strip() != "Pendidikan Islam"
    ):
        return story
    if not isinstance(story, list) or len(story) != 7:
        return story
    title, top_space, info, middle_space, activity, foot_space, footer = story
    if (not isinstance(info, Table) or not isinstance(activity, Table)
            or not isinstance(footer, Table)
            or not all(isinstance(s, Spacer) for s in (top_space, middle_space, foot_space))
            or _flow_text(title) != "رنچڠن ڤڠاجرن هارين"):
        return story
    rows = getattr(info, "_cellvalues", ())
    columns = getattr(info, "_colWidths", ())
    if (len(rows) != 17 or len(columns) != 2
            or abs(columns[0] - 124 * mm) > 2
            or abs(columns[1] - 48 * mm) > 2
            or any(not isinstance(row, (list, tuple)) or len(row) != 2 for row in rows)
            or any(_flow_text(row[1]) != expected
                   for row, expected in zip(rows[:8], HEADER_LABELS))):
        return story
    # ReportLab's native PI RTL Table wrapper has ALREADY reversed each
    # physical row to [Jawi value, Jawi label]. Do not reverse it again.
    # Match other RPH: wide lesson identity LEFT; narrow teacher fields RIGHT.
    wide = _inner(rows, (0, 1, 7), (82, 26))
    teacher = _inner(rows, (5, 2, 3, 4, 6), (36, 20))
    banner = Table([[wide, teacher]], colWidths=[112 * mm, 60 * mm],
                   hAlign="CENTER")
    banner.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#6D7C8B")),
        ("BACKGROUND", (0, 0), (0, 0), IDENTITY_FILL),
        ("BACKGROUND", (1, 0), (1, 0), TEACHER_FILL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    body = Table([list(row) for row in rows[8:]],
                 colWidths=[124 * mm, 48 * mm], hAlign="CENTER")
    body.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F3F1DF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return [title, top_space, banner, Spacer(1, 2 * mm),
            body, middle_space, activity, foot_space, footer]
