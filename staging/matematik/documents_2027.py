"""Shared SK Mathematics source for 2027 RPT and RPH delivery."""

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
DPK_YEARS = (2, 3)
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
    dpk: bool = False

    @property
    def code(self):
        edition = "DPK3-" if self.dpk else ""
        return f"SK27-{edition}MATH-Y{self.year}-L{self.number:03d}"


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


@lru_cache(maxsize=len(DPK_YEARS))
def _build_dpk_year(year):
    if type(year) is not int or year not in DPK_YEARS:
        raise ValueError("Unsupported SK Mathematics DPK Edisi 3 year")
    if year == 2:
        from staging.matematik.tahun2 import eksport_rpt as rpt, eksport_tahun2 as rph

        chapters, schedule = rph.load()
        details = rpt.lessons_by_id(chapters)
        documents = []
        for unit, info, records in chapters:
            for record in records:
                number = record["lesson"] if unit == 1 else record[0]
                documents.append((number, rph.document(unit, info, record, schedule[number])))
    else:
        from staging.matematik.tahun3 import eksport_rpt as rpt, eksport_tahun3 as rph

        records, schedule = rph.load()
        details = rpt.lessons_by_id(records)
        documents = ((record[0], rph.document(record, schedule[record[0]])) for record in records)
    lessons = []
    for number, parts in documents:
        unit, name, title, _, sp_text, _, volume, pages, _ = details[number]
        standards = tuple(sp_text.split(", "))
        lessons.append(Lesson(year, number, unit, name, title, standards[0].rsplit(".", 1)[0],
                              standards, f"Jilid {volume}, hlm. {pages}",
                              schedule[number][1], parts, dpk=True))
    return tuple(lessons), details


def lessons_for_year(year, *, dpk=False):
    return (_build_dpk_year(year) if dpk else _build_year(year))[0]


def export_rpt(year, path, *, dpk=False):
    path = Path(path)
    if dpk:
        _, details = _build_dpk_year(year)
        export_table(path, year, details, edition="Pilihan guru",
                     review_note="42 sesi 30 minit dan 75 sesi 60 minit sepadan dengan set RPH.",
                     profile_cover=True)
    else:
        _, details = _build_year(year)
        export_table(path, year, details, kssr_dskp=True, edition='Kumpulan A dan B')
    return path


def render_download(plan, fmt, teacher):
    renderer = RENDERERS[fmt]
    heading, fields, activities, reflection = plan.parts
    notes = clean_reflection(teacher.get("reflection") or "")
    reflection = [(label, notes if label == "Refleksi" and notes else value)
                  for label, value in reflection]
    stream = BytesIO()
    renderer(stream, heading, fields, activities, reflection,
             compact=plan.dpk and plan.year == 2 and plan.number == 17,
             mathematics=True, teacher=teacher)
    return stream.getvalue()


class Downloads:
    def __init__(self, year, *, dpk=False):
        self._units = {}
        for lesson in lessons_for_year(year, dpk=dpk):
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
