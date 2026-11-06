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
    r"(?:Aktiviti|Activity)[ \t]+[1-9]\d{0,2}[ \t]*"
    r"(?:[:：]|[–—-])[ \t]*\S.*$",
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


def _segments(raw):
    # Keep original whitespace and all line breaks (including blank lines).
    lines = raw.split("\n")
    for i, line in enumerate(lines):
        if i:
            yield "\n", False
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
                if paragraph.text != raw:
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
        if HEADING.match(line) and not existing.lstrip().startswith("<b>"):
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
    runtime._CIKGULAJU_RPH_HEADING_BOLD_20261106 = True
    return True
