"""Downloads for the audited Science DLP Year 3 RPH."""

from dlp_year2_rph import render, resolve, year3_science_catalog

SUBJECT = "SCIENCE_DLP"


def download_catalogue():
    return [
        {"id": unit["id"], "title": unit["title"], "lessons": [
            {"id": lesson["id"], "title": lesson["title"], "label": lesson["numbered_label"],
             "book_reference": lesson["references"], "minutes": lesson["minutes"]}
            for lesson in unit["lessons"]
        ]}
        for unit in year3_science_catalog()
    ]


def resolve_download(unit_id, lesson_id):
    return resolve(3, SUBJECT, unit_id, lesson_id)


def render_download(lesson, fmt, teacher):
    return render(SUBJECT, {"title": lesson["unit_title"]}, lesson, fmt, teacher)
