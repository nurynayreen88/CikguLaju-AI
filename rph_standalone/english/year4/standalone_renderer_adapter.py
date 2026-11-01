"""Non-destructive adapter: standalone English Year 4 Markdown -> RPH renderer fields.

This module has no database, Telegram or network side effects.
Call adapt_year4_standalone(markdown) before create_word_file/create_pdf_file.
The existing lesson Markdown is not modified.
"""
import re

SECTIONS = {
    "Set induction": "SET INDUCTION",
    "Closure": "CLOSURE",
    "Assessment and differentiation": "ASSESSMENT",
}
ACTIVITY = re.compile(r"^Activity\s+\d+\b", re.I)


def adapt_year4_standalone(markdown: str) -> str:
    """Return colon-headed text accepted by the existing English RPH parser."""
    blocks = {}
    current = None
    for line in markdown.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip()
            blocks[current] = []
        elif current:
            blocks[current].append(line)
    def body(prefix):
        return "\n".join(next((lines for heading, lines in blocks.items() if heading.lower().startswith(prefix.lower())), [])).strip()
    activities = []
    for heading in blocks:
        if ACTIVITY.match(heading) or re.match(r"^(?:reinforcement|pbd)\b", heading, re.I):
            activities.append(f"{heading}\n{body(heading)}")
    # The active English renderer expects these exact standard field names.
    # Do not infer content standards from learning-standard codes.
    title = re.search(r"^\*\*Topic:\*\*\s*(.+)$", markdown, re.M)
    main_sp = re.search(r"^\*\*Main SP:\*\*\s*(.+)$", markdown, re.M)
    comp_sp = re.search(r"^\*\*Complementary SP:\*\*\s*(.+)$", markdown, re.M)
    refs = re.search(r"^\*\*References:\*\*\s*(.+)$", markdown, re.M)
    if not main_sp:
        main_sp = re.search(r"^\*\*Main SK/SP:\*\*\s*(.+)$", markdown, re.M)
    if not comp_sp:
        comp_sp = re.search(r"^\*\*Complementary SK/SP:\*\*\s*(.+)$", markdown, re.M)
    if not title:
        title = re.search(r"^\*\*(?:Unit/Topic|Unit):\*\*\s*(.+)$", markdown, re.M)
    if not refs:
        refs = re.search(r"^\*\*Materials:\*\*\s*(.+)$", markdown, re.M)
    audio = re.search(r"^\*\*Audio:\*\*\s*(.+)$", markdown, re.M)
    materials = refs.group(1).strip() if refs else ""
    if audio and audio.group(1).strip():
        audio_note = audio.group(1).strip()
        if audio_note.lower() not in materials.lower():
            materials = (materials + "\nAudio: " + audio_note).strip()
    objectives = re.search(r"^\*\*Learning objectives?:\*\*\s*(.+)$", markdown, re.M | re.I)
    success = re.search(r"^\*\*Success (?:evidence|criteria):\*\*\s*(.+)$", markdown, re.M | re.I)
    fields = [
        ("TOPIC", title.group(1) if title else ""),
        ("MAIN LEARNING STANDARD", main_sp.group(1).strip() if main_sp else ""),
        ("COMPLEMENTARY LEARNING STANDARD", comp_sp.group(1).strip() if comp_sp else ""),
        # Backward-compatible field for the existing base parser. Keep both
        # learning standards labelled; do not invent content standards.
        ("LEARNING STANDARD", "\n".join(filter(None, [
            "Main: " + main_sp.group(1).strip() if main_sp else "",
            "Complementary: " + comp_sp.group(1).strip() if comp_sp else "",
        ]))),
        ("STANDARD PEMBELAJARAN", "\n".join(filter(None, [
            "Main: " + main_sp.group(1).strip() if main_sp else "",
            "Complementary: " + comp_sp.group(1).strip() if comp_sp else "",
        ]))),
        ("LEARNING OBJECTIVES", objectives.group(1).strip() if objectives else ""),
        ("SUCCESS CRITERIA", success.group(1).strip() if success else ""),
        ("TEACHING AND LEARNING MATERIALS", materials),
        ("SET INDUCTION", body("Set induction")),
        ("MAIN ACTIVITIES", "\n\n".join(activities)),
        ("CLOSURE", body("Closure")),
        ("ASSESSMENT", body("Assessment and differentiation") or body("Differentiation and assessment") or body("PBD and differentiation")),
    ]
    return "\n".join(f"{key}:\n{value}" for key, value in fields if value)
