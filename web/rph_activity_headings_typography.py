"""Non-destructive final-document typography for CikguLaju RPH activity headings.

The curriculum and SK/SP stay untouched.  The legacy Telegram Word generator
writes the complete 'Aktiviti Utama' cell as a plain run, while the PDF generator
previously bolded only en-dash headings.  This adapter styles headings in the
finished file / escaped PDF text, not by rewriting a lesson's content.
"""
from __future__ import annotations

import html
import os
import re
from pathlib import Path

# Keep this narrow: a heading must BEGIN its own line. Ordinary body mentions
# of an activity must never become bold.
HEADING = re.compile(
    r"^[ \t]*(?:(?:\d{1,2})[.)][ \t]*)?"
    r"(?:Aktiviti|Activity)[ \t]+[1-9]\d{0,2}"
    r"(?:[ \t]*\([ \t]*[1-9]\d{0,2}[ \t]*(?:minit|minutes?|mins?)[ \t]*\))?"
    r"(?:[ \t]*(?:[:：]|[–—-])[ \t]*.*)?[ \t]*$",
    flags=re.IGNORECASE,
)

# PI has a separate Jawi/RTL renderer and must never be reformatted by this
# Latin document helper.
SKIP_SUBJECTS = ("pendidikan islam", "bahasa arab", "islamic", "arabic")


def eligible_rph(state):
    if not isinstance(state, dict) or state.get("task") != "rph":
        return False
    subject = str(state.get("subject") or "").strip().casefold()
    return bool(subject) and not any(x in subject for x in SKIP_SUBJECTS)


_INSTRUCTION_PREFIX = re.compile(
    r"^([ \t]*(?:(?:\d{1,2})[.)][ \t]*)?"
    r"(?:Aktiviti|Activity)[ \t]+[1-9]\d{0,2}"
    r"(?:[ \t]*\([ \t]*[1-9]\d{0,2}[ \t]*(?:minit|minutes?|mins?)[ \t]*\))?"
    r"[ \t]*(?:[:：]|[–—-]))([ \t]*)(.+)$",
    re.IGNORECASE,
)
_TEACHER_OR_PUPIL = re.compile(
    r"^(?:guru|murid|teacher|pupil|pupils|student|students)\b", re.IGNORECASE,
)


def _inline_instruction(line):
    """Find existing numbered label plus an INSTRUCTION, not a short title.

    This creates a presentation-only line break after the heading label.
    The original characters remain in their original order, and undoing that
    new break restores the original source line byte-for-byte.
    """
    match = _INSTRUCTION_PREFIX.fullmatch(line)
    if not match:
        return None
    body = match.group(3)
    if not (
        _TEACHER_OR_PUPIL.match(body)
        or (body.endswith((".", "!", "?")) and len(body.split()) >= 5)
    ):
        return None
    return match.group(1), match.group(2) + body


def _segments(raw):
    # Keep every original text character. Only add a visual break to separate
    # "Aktiviti 1: Guru..." into bold heading and ordinary body instruction.
    for i, line in enumerate(raw.split("\n")):
        if i:
            yield "\n", False
        inline = _inline_instruction(line)
        if inline:
            yield inline[0], True
            yield "\n", False
            yield inline[1], False
        else:
            yield line, bool(HEADING.match(line))




def bold_activity_headings_in_docx(path):
    """Style only previously unstyled, single-run activity cells.

    Existing headings already bold in a richer standalone template are left
    untouched.  No labels, values, text, tables, page dimensions or SK/SP are
    edited.  Returns the number of heading lines updated.
    """
    from docx import Document

    target = Path(path)
    doc = Document(str(target))
    updated = 0
    for table in doc.tables:
        for row in table.rows:
            # Only the activity column of 3-column phase tables, never
            # identifiers, teacher details or heading cells.
            if len(row.cells) != 3:
                continue
            cell = row.cells[1]
            for paragraph in cell.paragraphs:
                raw = paragraph.text
                if not any(HEADING.match(line) for line in raw.split("\n")):
                    continue
                # The native renderer creates one plain run for this phase.
                # Preserve custom rich formatting from all other adapters.
                if len(paragraph.runs) != 1:
                    continue
                original = paragraph.runs[0]
                if original.bold is True:
                    continue
                original.text = ""
                for segment, bold in _segments(raw):
                    if not segment:
                        continue
                    run = paragraph.add_run(segment)
                    if bold:
                        run.bold = True
                        updated += 1
                paragraph._p.remove(original._r)
                if paragraph.text != raw and paragraph.text.replace("\n", "") != raw.replace("\n", ""):
                    raise ValueError("RPH activity styling changed the content")
    if updated:
        # Save atomically; never leave a half-written RPH if ZIP saving fails.
        temp = target.with_name(target.name + ".typography.tmp")
        try:
            doc.save(str(temp))
            os.replace(str(temp), str(target))
        finally:
            if temp.exists():
                temp.unlink()
    return updated


def bold_pdf_heading_markup(raw_text, legacy_markup):
    """Add bold to activity headings the legacy PDF regex missed (e.g. ':').

    Preserve the PI-specific escaped/Jawi renderer and every already-bold line.
    """
    raw = str(raw_text or "")
    lines = raw.splitlines()
    old_parts = legacy_markup.split("<br/>")
    if len(lines) != len(old_parts):
        return legacy_markup
    result = []
    for line, existing in zip(lines, old_parts):
        inline = _inline_instruction(line)
        if inline:
            plain = html.escape(line)
            # Only rebuild safe literal source markup, never modify markup
            # containing unrelated formatting, links or curriculum metadata.
            if existing in (plain, "<b>" + plain + "</b>"):
                result.append(
                    "<b>" + html.escape(inline[0]) + "</b><br/>"
                    + html.escape(inline[1])
                )
            else:
                result.append(existing)
        elif HEADING.match(line) and not existing.lstrip().startswith("<b>"):
            result.append("<b>" + html.escape(line) + "</b>")
        else:
            result.append(existing)
    return "<br/>".join(result)


def install(runtime):
    """Patch actual Telegram output boundaries once, without altering app.py."""
    if getattr(runtime, "_CIKGULAJU_RPH_HEADING_BOLD_20261106", False):
        return False
    previous_word = runtime.create_word_file
    previous_pdf_markup = runtime._rph_activity_heading_markup_v25184
    previous_document_rows = getattr(runtime, "_rph_document_rows", None)

    def document_rows_with_pi_standards(state, rows):
        rows = previous_document_rows(state, rows)
        if (runtime._pi_primary_v25210(state)
                and state.get("year") in ("Tahun 2", "Tahun 3", "Tahun 4", "Tahun 5", "Tahun 6")):
            from web.pi_navigation import pi_rph_document_rows

            return pi_rph_document_rows(state, rows)
        return rows

    def word_with_consistent_activity_headings(state, source_text, chat_id):
        path = previous_word(state, source_text, chat_id)
        if eligible_rph(state) and isinstance(path, (str, Path)):
            bold_activity_headings_in_docx(path)
        return path

    def pdf_with_consistent_activity_headings(text):
        old = previous_pdf_markup(text)
        # Preserve Jawi renderer exactly; the existing PI-specific context is
        # managed by the native generator, not mutated by this patch.
        if getattr(runtime, "_CIKGULAJU_PI_RENDER_CONTEXT_V2593", False):
            return old
        return bold_pdf_heading_markup(text, old)

    runtime.create_word_file = word_with_consistent_activity_headings
    runtime._rph_activity_heading_markup_v25184 = pdf_with_consistent_activity_headings
    if callable(previous_document_rows):
        runtime._rph_document_rows = document_rows_with_pi_standards
    runtime._CIKGULAJU_RPH_HEADING_BOLD_20261106 = True
    return True
