"""Multi-subject PPKI RPH adapter, isolated until curriculum approval.

Existing Pengurusan Kehidupan catalog and download routes are unchanged.
Never pass an unaudited lesson to the production renderer.
"""
from datetime import date


def render_approved_lesson(catalog, lesson, extension, teacher):
    """Require per-record approval and full source-backed standard text."""
    if catalog.get("status") != "READY" or lesson.get("status") != "READY":
        raise ValueError("PPKI lesson has not passed curriculum approval")
    if str(lesson.get("source_note") or "").startswith("KONFLIK"):
        raise ValueError("Unresolved source conflict")
    if catalog.get("year") not in (2, 3, 4, 5, 6):
        raise ValueError("Invalid PPKI year")
    if not str(catalog.get("subject_id", "")).endswith("_PPKI"):
        raise ValueError("Invalid PPKI subject")
    if extension not in ("docx", "word", "pdf"):
        raise ValueError("Invalid RPH format")
    if not any(candidate is lesson for candidate in catalog["lessons"]):
        raise ValueError("Lesson does not belong to catalog")
    sk_codes = list(dict.fromkeys(lesson.get("sk") or [
        ".".join(code.split(".")[:2]) for code in lesson["sp"]
    ]))
    sp_codes = lesson["sp"]
    if not isinstance(sp_codes, list) or not sp_codes or not sk_codes:
        raise ValueError("Missing SK/SP")
    def standard_lines(codes, mapping):
        lines = []
        for code in codes:
            description = mapping.get(code)
            if not isinstance(description, str) or not description.strip() or description.strip() == code:
                raise ValueError(f"Missing verified description: {code}")
            lines.append(f"{code} {description.strip()}")
        return "\n".join(lines)
    sk = standard_lines(sk_codes, catalog["content_standards"])
    sp = standard_lines(sp_codes, catalog["learning_standards"])
    if lesson["success_criterion"] != lesson["reflection_criterion"]:
        raise ValueError("Reflection criterion mismatch")
    unit_label = catalog.get("units", {}).get(str(lesson["unit"]))
    if not unit_label:
        raise ValueError("Missing verified unit label")
    display_date = date.fromisoformat(teacher["date"]).strftime("%d/%m/%Y") if teacher.get("date") else ""
    english = catalog["subject_id"] == "BAHASA_INGGERIS_PPKI"
    heading = ("Daily Lesson Plan" if english else "Rancangan Pengajaran Harian",
               f"PPKI · {catalog['subject']} · {'Year' if english else 'Tahun'} {catalog['year']}",
               lesson["title"])
    details = [
        ("Unit", unit_label),
        ("Date" if english else "Tarikh", display_date),
        ("Time" if english else "Masa", teacher.get("time", "")),
        ("Class" if english else "Kelas", teacher.get("class", "")),
        ("Number of Pupils" if english else "Bilangan Murid", teacher.get("students", "")),
        ("Content Standard" if english else "Standard Kandungan", sk),
        ("Learning Standard" if english else "Standard Pembelajaran", sp),
        ("Learning Objectives" if english else "Objektif Pembelajaran", lesson["objective"]),
        ("Success Criteria" if english else "Kriteria Kejayaan", lesson["success_criterion"]),
        ("Teaching and Learning Materials" if english else "Bahan Bantu Mengajar", lesson["materials"]),
        ("Reference" if english else "Rujukan", f"{'Textbook' if english else 'Buku Teks'} {lesson['textbook_page']}"),
    ]
    if lesson.get("activity_book_ref"):
        details.append(("Activity Book" if english else "Buku Aktiviti", lesson["activity_book_ref"]))
    activities = [
        ("Phase" if english else "Fasa", "Teacher" if english else "Guru", "Pupils" if english else "Murid"),
        ("Set Induction" if english else "Set Induksi", lesson["induction"], ""),
        ("Activity 1" if english else "Aktiviti 1", lesson["guided"], ""),
        ("Activity 2" if english else "Aktiviti 2", "", lesson["practice"]),
        ("Closure" if english else "Penutup", lesson["closure"], ""),
    ]
    reflection = teacher.get("reflection") or (
        ("____ / ____ pupils met the criterion: " if english else "____ / ____ murid mencapai kriteria: ")
        + lesson["reflection_criterion"]
    )
    footer = [
        ("Support" if english else "Sokongan", lesson["support"]),
        ("Assessment" if english else "Pentaksiran Bilik Darjah", lesson["assessment"]),
        ("Reflection" if english else "Refleksi", reflection),
    ]
    from web.rph_unified_engine import render_structured_rph
    return render_structured_rph(source="ppki", fmt=extension, heading=heading,
                                 details=details, activities=activities, footer=footer,
                                 compact=True, label_fill="EEE6F7")
