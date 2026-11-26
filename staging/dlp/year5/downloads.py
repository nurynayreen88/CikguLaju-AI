"""Exact catalogue and download adapters for the two approved Year 5 sets."""

from functools import cached_property
from io import BytesIO

from dlp_year2_rph import _pdf, _word
from staging.dlp.year5 import render_mathematics, render_science


class Year5Downloads:
    def __init__(self, source, prefix):
        self.source = source
        self.prefix = prefix

    @cached_property
    def units(self):
        _, plans = self.source.load_plans()
        units = {}
        for plan in plans:
            unit_id = f"{int(plan['unit'].split()[1]):02d}"
            unit = units.setdefault(unit_id, {"id": unit_id, "title": plan["unit"], "lessons": {}})
            unit["lessons"][self.prefix + plan["id"]] = plan
        return units

    def catalogue_minutes(self,plan):
        if self.source is render_science:
            from staging.dlp.science_y45_session_delivery import extend
            return extend(plan,5)["minutes"]
        return plan["minutes"]

    def download_catalogue(self):
        return [
            {"id": unit["id"], "title": unit["title"], "lessons": [
                {"id": key, "title": plan["title"], "label": plan["label"],
                 "book_reference": plan["reference"], "minutes": self.catalogue_minutes(plan)}
                for key, plan in unit["lessons"].items()
            ]}
            for unit in self.units.values()
        ]

    def resolve_download(self, unit_id, lesson_id):
        unit = self.units.get(unit_id)
        if unit is None or lesson_id not in unit["lessons"]:
            return None
        return unit, {**unit["lessons"][lesson_id], "id": lesson_id}

    def render_download(self, plan, fmt, teacher):
        if self.source is render_science:
            from staging.dlp.science_y45_session_delivery import for_teacher
            plan=for_teacher(plan,5,teacher)
        buffer = BytesIO()
        self.source.render_plan(buffer, plan, {"word": _word, "pdf": _pdf}[fmt], teacher=teacher)
        return buffer.getvalue()


MATHEMATICS = Year5Downloads(render_mathematics, "DLP-MATH-Y5-")
SCIENCE = Year5Downloads(render_science, "DLP-SCI-Y5-")
