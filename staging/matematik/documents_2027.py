"""Shared Years 4 to 6 SK Mathematics source for 2027 RPT and RPH delivery."""

from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from dlp_year2_rph import _pdf, _word
from staging.matematik.eksport_rpt_dpk import export_table
from staging.matematik.eksport_slot_30_tahap2 import load, short_document
from staging.matematik.eksport_tahap2 import complete_rpt_details, full_schedule, hour_document, load_hour
from web.rph_teacher_reflection import clean_reflection


YEARS = (4, 5, 6)
RENDERERS = {"word": _word, "pdf": _pdf}


@dataclass(frozen=True)
class Lesson:
    year: int
    number: int
    unit: int
    unit_title: str
    title: str
    sk: str
    standards: tuple[str, ...]
    pages: str
    minutes: int
    parts: tuple

    @property
    def code(self):
        return f"SK27-MATH-Y{self.year}-L{self.number:03d}"


@lru_cache(maxsize=len(YEARS))
def _build_year(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unsupported SK Mathematics 2027 year")
    schedule = full_schedule(year)
    hour = load_hour(year, schedule)
    short, _, sources = load(year)
    short_by_number = {plan.lesson: plan for plan in short}
    details = complete_rpt_details(year, short, hour, sources)
    lessons = []
    for number, (week, minutes) in schedule.items():
        unit, unit_title, title, sk, standards, _, _, pages, _ = details[number]
        source = sources[number - 1]
        if minutes == 30:
            parts = short_document(year, short_by_number[number], week, source)
        else:
            parts = hour_document(year, number, week, source, hour[number])
        lessons.append(Lesson(year, number, unit, unit_title, title, sk.split()[0],
                              tuple(standards.split(", ")), pages, minutes, parts))
    return tuple(lessons), details


def lessons_for_year(year):
    return _build_year(year)[0]


def export_rpt(year, path):
    path = Path(path)
    _, details = _build_year(year)
    export_table(path, year, details, kssr_dskp=True, edition='Kumpulan A dan B')
    return path


def render_download(plan, fmt, teacher):
    renderer = RENDERERS[fmt]
    heading, fields, activities, reflection = plan.parts
    class_line = " · ".join(
        f"{label} {teacher.get(key) or '______'}"
        for key, label in (("class", "Kelas"), ("date", "Tarikh"), ("time", "Masa"),
                           ("students", "Murid"))
    )
    notes = clean_reflection(teacher.get("reflection") or "")
    fields = [(label, class_line if label == "Maklumat kelas" else value)
              for label, value in fields]
    reflection = [(label, notes if label == "Refleksi" and notes else value)
                  for label, value in reflection]
    stream = BytesIO()
    renderer(stream, heading, fields, activities, reflection)
    return stream.getvalue()


class Downloads:
    def __init__(self, year):
        self._units = {}
        for lesson in lessons_for_year(year):
            unit = f"{lesson.unit:02d}"
            title, members = self._units.setdefault(unit, (lesson.unit_title, {}))
            members[lesson.code] = lesson

    def download_catalogue(self):
        return [{
            "id": unit, "title": title,
            "lessons": [{"id": lesson.code, "title": lesson.title,
                         "label": f"Lesson {lesson.number:03d} · {lesson.minutes} minit"}
                        for lesson in members.values()],
        } for unit, (title, members) in self._units.items()]

    def resolve_download(self, unit, code):
        title, members = self._units[unit]
        return title, members[code]

    render_download = staticmethod(render_download)
