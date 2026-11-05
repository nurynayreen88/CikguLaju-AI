"""One canonical four-step selection flow for every CikguLaju subject.

Subject-specific SK/SP, skills, textbook pages and audio remain backend
metadata; users do not navigate different menus for BM vs English.
"""
from dataclasses import dataclass

STEPS = ("year", "subject", "unit", "lesson")


@dataclass(frozen=True)
class SubjectFlow:
    year: int
    subject: str = ""
    unit: str = ""
    lesson: str = ""


def normalize_flow(*, year, subject="", unit="", lesson=""):
    if type(year) is not int or year not in range(1, 7):
        raise ValueError("invalid year")
    fields = (subject, unit, lesson)
    if any(not isinstance(x, str) or len(x) > 300 for x in fields):
        raise ValueError("invalid selection")
    if unit and not subject:
        raise ValueError("subject required before unit")
    if lesson and not unit:
        raise ValueError("unit required before lesson")
    return SubjectFlow(year, subject.strip(), unit.strip(), lesson.strip())


def reset_after_change(flow, changed_step):
    """Clear downstream values for any subject, without special BM branches."""
    if changed_step not in STEPS:
        raise ValueError("unknown step")
    values = dict(year=flow.year, subject=flow.subject, unit=flow.unit, lesson=flow.lesson)
    for step in STEPS[STEPS.index(changed_step) + 1:]:
        values[step] = ""
    return normalize_flow(**values)
