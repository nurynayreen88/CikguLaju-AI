"""Fail-closed release gate for existing English standalone Markdown files.

This does not infer approval from file presence or RPT verification.
A file explicitly marked NOT READY FOR RELEASE must never be downloadable.
"""
from pathlib import Path
import re

from english_standalone_adapter import load_english_rph


def load_release_ready_english(year: int, lesson_no: int) -> str:
    if type(year) is not int or type(lesson_no) is not int:
        raise ValueError("Invalid year or lesson number")
    content = load_english_rph(year, lesson_no)
    if content is None:
        raise LookupError("Standalone English lesson unavailable")
    status = re.findall(r"(?im)^\*\*QA status:\*\*\s*(.+)$", content)
    if len(status) != 1:
        raise LookupError("Lesson has no unambiguous release approval")
    value = status[0].strip()
    if value != "READY FOR RELEASE":
        raise LookupError("Standalone English lesson not approved for release")
    return content
