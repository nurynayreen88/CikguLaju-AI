"""Keep scheduling annotations out of the displayed activity steps."""

import re


_MINUTES = (
    r"\d{1,3}(?:[ \t]*[-–—][ \t]*\d{1,3})?[ \t]*"
    r"(?:minit|minutes?|mins?|دقيقة|دقائق|مينيت|مينت)"
)
_DURATION_LINE = re.compile(rf"[ \t]*(?:\({_MINUTES}\)|{_MINUTES})[ \t]*:?[ \t]*", re.I)
_DURATION_GROUP = rf"[ \t]*\([ \t]*{_MINUTES}[ \t]*\)"
_ACTIVITY_HEADING = re.compile(
    r"^[ \t]*(?:\d+[.)][ \t]*)?"
    r"(?:(?:Aktiviti|Activity|Langkah|Step|اکتيۏيتي)[ \t]+\d+\b|"
    r"Reinforcement[ \t]*/[ \t]*PBD\b|Assessment[ \t]*/[ \t]*PBD\b|"
    r"Pengukuhan[ \t]*/[ \t]*(?:PBD|Pentaksiran)\b|"
    r"(?:Set Induksi|Set Induction|Main Activities|Aktiviti Utama|Penutup|Closure|"
    r"Pengukuhan|Pemulihan|Pengayaan|Reinforcement|Remedial|Enrichment|PBD)\b)",
    re.I,
)
_TITLE_DURATION = re.compile(rf"{_DURATION_GROUP}(?=[ \t]*:?[ \t]*$)", re.I)
_LEADING_DURATION = re.compile(rf"{_DURATION_GROUP}(?=[ \t]*(?:[:–—-]|$))", re.I)
_INLINE_INSTRUCTIONS = re.compile(r"[:.!?][ \t]+\S")


def phase_heading(text):
    """Remove a duration from a field already known to hold a phase heading."""
    return _TITLE_DURATION.sub("", text)


def activity_without_schedule(text):
    """Strip durations from phase metadata while preserving lesson sentences."""
    display = []
    before_body = True
    for line in text.split("\n"):
        if before_body and _DURATION_LINE.fullmatch(line):
            continue
        heading = _ACTIVITY_HEADING.match(line)
        if heading:
            # A duration immediately after the label is a schedule annotation.
            # A duration inside the teacher's or pupils' instructions is content.
            suffix = line[heading.end():]
            annotation = _LEADING_DURATION.match(suffix)
            if annotation:
                suffix = suffix[annotation.end():]
            before_body = not _INLINE_INSTRUCTIONS.search(suffix)
            if before_body:
                suffix = phase_heading(suffix)
            line = line[:heading.end()] + suffix
        elif line.strip():
            before_body = False
        display.append(line)
    return "\n".join(display)
