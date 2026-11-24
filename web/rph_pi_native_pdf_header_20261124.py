"""Source-preserving, two-panel Jawi header for verified active PI native PDF.

Reuses the exact eight already-rendered Jawi metadata pairs; no source text
or images are altered. Rebuilds only their visual containers, retaining all
curriculum/activities/reflection flowables verbatim. Unsupported layouts
fail closed to the established one-table PI renderer.
"""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, Table, TableStyle, Spacer
from reportlab.lib.utils import ImageReader
from PIL import Image

HEADER_LABELS = (
    "مات ڤلاجرن", "تاهون / تيڠکتن", "تاريخ", "هاري",
    "ماس", "کلس", "بيلڠن موريد", "تاجوق",
)
# ONE subject palette for all visible PI/Jawi label panels.
# The native activity and reflection tables already use #ECE4F6.
PI_FILL = colors.HexColor("#ECE4F6")
IDENTITY_FILL = PI_FILL
TEACHER_FILL = PI_FILL


class CenteredJawiTitle(Flowable):
    """Centre the EXISTING title glyph image instead of placing it at the right.

    Native Jawi paragraphs are drawn into transparent PNGs by the existing
    trusted text shaper, which always anchors them to the right. Cropping
    only transparent horizontal margins and centering that already-shaped
    artwork preserves every character, font, line and original lesson text.
    This class is used exclusively for the verified PI PDF title.
    """

    def __init__(self, title):
        super().__init__()
        self.original = title
        self.width = 0
        self.height = 0

    def wrap(self, available_width, available_height):
        self.width = available_width
        _, self.height = self.original.wrap(available_width, available_height)
        return self.width, self.height

    def draw(self):
        reader = getattr(self.original, "_img", None)
        source = getattr(reader, "_image", None)
        if not isinstance(source, Image.Image) or source.mode != "RGBA":
            # Safe fallback: never drop a title if a font renderer differs.
            self.original.drawOn(self.canv, 0, 0)
            return
        bbox = source.getchannel("A").getbbox()
        if not bbox:
            self.original.drawOn(self.canv, 0, 0)
            return
        # Preserve vertical image extent and the original rasterized glyphs.
        left, _, right, _ = bbox
        width = self.width * (right - left) / source.width
        crop = source.crop((left, 0, right, source.height))
        self.canv.drawImage(
            ImageReader(crop), (self.width - width) / 2, 0,
            width=width, height=self.height, mask="auto",
            preserveAspectRatio=True,
        )


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
    # Never alter independent PI-like PPKI/DLP/SJKC/SJKT renderers.
    for key in ("curriculum", "curriculum_version", "stream",
                "programme", "program", "school_type"):
        if any(tag in str(state.get(key) or "").casefold()
               for tag in ("ppki", "dlp", "sjkc", "sjkt", "kp2027")):
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
    # PI RTL master: wide subject/year/topic RIGHT; narrow teacher details LEFT.
    # Remove exactly the two redundant display labels. Keep the original
    # year and topic. Use the already trusted bold Jawi label shaper for
    # the subject value, not a Latin font or a PDF overlay.
    from copy import copy
    from reportlab.platypus import Paragraph
    subject_text = _flow_text(rows[0][0])
    year_text = _flow_text(rows[1][0])
    if subject_text == "ڤنديديقن اسلام" and year_text.startswith("تاهون "):
        label = rows[0][1]
        if isinstance(label, Paragraph):
            subject = Paragraph("<b>"+subject_text+"</b>", label.style)
        else:
            subject = copy(label)
            subject.text = subject_text
            if hasattr(subject, "_img"):
                subject._img = None
        wide = Table([[subject, ""], [rows[1][0], ""],
                      [rows[7][0], rows[7][1]]],
                     colWidths=[82*mm,26*mm], hAlign="CENTER")
        wide.setStyle(TableStyle([
            ("SPAN",(0,0),(1,0)),("SPAN",(0,1),(1,1)),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),1),
            ("RIGHTPADDING",(0,0),(-1,-1),1),
            ("TOPPADDING",(0,0),(-1,-1),1),
            ("BOTTOMPADDING",(0,0),(-1,-1),1),
        ]))
    else:
        wide = _inner(rows, (0, 1, 7), (82, 26))
    teacher = _inner(rows, (5, 2, 3, 4, 6), (36, 20))
    banner = Table([[teacher, wide]], colWidths=[60 * mm, 112 * mm],
                   hAlign="CENTER")
    banner.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#6D7C8B")),
        ("BACKGROUND", (0, 0), (0, 0), TEACHER_FILL),
        ("BACKGROUND", (1, 0), (1, 0), IDENTITY_FILL),
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
        ("BACKGROUND", (1, 0), (1, -1), PI_FILL),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return [CenteredJawiTitle(title), top_space, banner, Spacer(1, 2 * mm),
            body, middle_space, activity, foot_space, footer]
