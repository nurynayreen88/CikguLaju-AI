"""Isolated document renderer for CikguLaju web staging.

This module does not import app.py, access Telegram, query the database,
debit credits, or decide whether an RPH is approved. The caller must validate
an approved standalone RPH and authorization before invoking it.

NOTE: This is a staging renderer, NOT yet the extracted production layout.
"""
from dataclasses import dataclass
from io import BytesIO
from typing import Literal


@dataclass(frozen=True)
class ApprovedRPH:
    lesson_id: int
    title: str
    content: str
    approval_reference: str


def render_approved_rph(
    rph: ApprovedRPH, format: Literal["docx", "pdf"]
) -> tuple[bytes, str]:
    """Return document bytes and MIME type, with no side effects.

    Approval reference must be supplied by a trusted server-side lookup,
    never copied from browser input. This guard is not proof of approval.
    """
    if type(rph.lesson_id) is not int or rph.lesson_id <= 0:
        raise ValueError("Invalid lesson ID")
    if not isinstance(rph.approval_reference, str) or not rph.approval_reference.strip():
        raise ValueError("Missing server-side approval reference")
    if not isinstance(rph.title, str) or not isinstance(rph.content, str) or not rph.title.strip() or not rph.content.strip():
        raise ValueError("Empty RPH")
    if format == "docx":
        from docx import Document

        document = Document()
        document.add_heading(rph.title, level=1)
        for paragraph in rph.content.splitlines():
            if paragraph.strip():
                document.add_paragraph(paragraph.strip())
        output = BytesIO()
        document.save(output)
        return output.getvalue(), (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    if format == "pdf":
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from xml.sax.saxutils import escape

        output = BytesIO()
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(output)
        story = [Paragraph(escape(rph.title), styles["Heading1"]), Spacer(1, 8)]
        for paragraph in rph.content.splitlines():
            if paragraph.strip():
                story.append(Paragraph(escape(paragraph), styles["Normal"]))
        doc.build(story)
        return output.getvalue(), "application/pdf"
    raise ValueError("Unsupported format")
