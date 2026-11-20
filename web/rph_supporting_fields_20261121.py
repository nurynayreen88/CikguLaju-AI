"""Add compact, source-anchored teaching supports to the established RPH layout.

The four approved subject families use the existing three-table renderer:
Matematik SK, Sains SK, DLP Science/Mathematics, and PPKI.  The original
curriculum, teacher/pupil activities, SK/SP, PBD and reflection remain intact.
No official curriculum standard or activity from a textbook is invented.
"""

import re


def _family(heading):
    if not isinstance(heading, (tuple, list)) or len(heading) < 3:
        return None
    subject = str(heading[1]).casefold()
    if "ppki" in subject:
        return "ppki"
    if "dlp" in subject and ("science" in subject or "mathematics" in subject):
        return "dlp"
    if "sains" in subject and "dlp" not in subject:
        return "sains"
    if "matematik" in subject and "dlp" not in subject:
        return "matematik"
    return None


def _field(rows, *labels):
    targets = {label.casefold() for label in labels}
    for label, value in rows:
        if str(label).casefold() in targets and str(value).strip():
            return str(value).strip()
    return ""


def _brief(text, limit=92):
    # Use a real phrase from the current lesson, not a made-up page reference.
    compact = " ".join(str(text or "").split())
    first = re.split(r"(?<=[.!?])\s+", compact, maxsplit=1)[0]
    if len(first) <= limit:
        return first
    return first[:limit].rsplit(" ", 1)[0].rstrip(" ,.;") + "…"


def _lesson_pupil_action(activities):
    if not isinstance(activities, (tuple, list)):
        return ""
    selected = [
        str(row[2]).strip() for row in activities[1:]
        if len(row) == 3 and str(row[2]).strip()
        and not any(tag in str(row[0]).casefold() for tag in ("penutup", "closure"))
    ]
    return selected[-1] if selected else ""


def _emk_from_context(topic, objective, family, *, english=False):
    source = f"{topic} {objective}".casefold()
    groups = (
        (("bersih", "kebersihan", "hygiene", "kesihatan", "health", "makanan"), 
         ("Kesihatan dan kebersihan", "Health and hygiene")),
        (("alam sekitar", "kitar semula", "environment", "recycle", "pencemaran"),
         ("Kelestarian alam sekitar", "Environmental sustainability")),
        (("keselamatan", "safety", "bahaya", "safe"),
         ("Keselamatan dan tanggungjawab", "Safety and responsibility")),
        (("ukur", "mengukur", "measure", "jisim", "data", "rekod", "record", "jadual", "table"),
         ("Ketelitian merekod maklumat", "Accuracy when recording information")),
    )
    for keywords, labels in groups:
        if any(word in source for word in keywords):
            return labels[int(english)]
    if family == "ppki":
        return "Nilai murni: berdikari mengikut tahap keupayaan murid"
    if family in ("sains", "dlp"):
        return "Nilai murni: sikap ingin tahu dan menggunakan bukti" if not english else "Values: curiosity and evidence-based thinking"
    return "Nilai murni: ketelitian dan bertanggungjawab" if not english else "Values: accuracy and responsibility"


def _pak21_from_actions(activities, *, english=False, family=None):
    actions = " ".join(str(value) for row in activities[1:] if len(row) == 3
                       for value in row[1:]).casefold()
    if any(word in actions for word in ("kumpulan", "group", "pasangan", "pair", "rakan", "partner")):
        return "Kolaborasi dan komunikasi" if not english else "Collaboration and communication"
    if any(word in actions for word in ("banding", "compare", "sebab", "reason", "bukti", "evidence", "infer")):
        return "Pemikiran kritis dan komunikasi" if not english else "Critical thinking and communication"
    if family == "ppki" or any(word in actions for word in ("kad", "gambar", "isyarat", "picture", "gesture")):
        return "Komunikasi multimodal melalui respons dan bahan visual" if not english else "Multimodal communication using visual responses"
    return "Komunikasi melalui pembentangan atau respons murid" if not english else "Communication through pupil responses"


def _kbat_from_context(activities, *, english=False):
    text = " ".join(str(value) for row in activities[1:] if len(row) == 3
                    for value in row[1:]).casefold()
    if any(word in text for word in ("sebab", "justify", "reason", "inferens", "inference", "why")):
        return "Memberi sebab berdasarkan hasil aktiviti" if not english else "Justify an answer using lesson evidence"
    if any(word in text for word in ("banding", "compare", "bezakan", "difference", "perbezaan")):
        return "Membandingkan hasil atau pilihan" if not english else "Compare results or alternatives"
    return "Mengaplikasikan kemahiran dalam situasi baharu" if not english else "Apply the skill to a new situation"


def supplement_details(heading, details, activities, footer):
    """Append two compact rows to details; preserve all footer rows and order.

    RPH has three tables. The assessment, existing PPKI support and reflection
    remain in their original final table, including every index and label.
    """
    family = _family(heading)
    if family is None:
        return details
    if not isinstance(details, (list, tuple)) or not isinstance(footer, (list, tuple)) or not all(
        isinstance(row, (list, tuple)) and len(row) == 2 for row in (*details, *footer)
    ):
        return details
    present = " ".join(str(label).casefold() for label, _ in (*details, *footer))
    # Existing subject-supplied supports take precedence over inferred displays.
    if "emk" in present and "pak21" in present and "pemulihan" in present and "pengayaan" in present:
        return details
    english = str(heading[0]).strip() == "Daily Lesson Plan"
    topic = _brief(heading[2], limit=62)
    objective = _field(details, "Objektif", "Objektif Pembelajaran", "Learning objective", "Learning objectives")
    materials = _field(details, "Bahan", "Bahan Bantu Mengajar", "Materials")
    existing_support = _field(footer, "Sokongan", "Pemulihan", "Remedial")
    pupil_action = _brief(_lesson_pupil_action(activities), limit=70)
    emk = _emk_from_context(topic, objective, family, english=english)
    pak21 = _pak21_from_actions(activities, english=english, family=family)
    if pupil_action:
        pak21 += "; " + pupil_action
    kbat = _kbat_from_context(activities, english=english)
    if english:
        remediation = (existing_support or
                       f"Repeat the task on {topic} with teacher prompts and { _brief(materials, 38) or 'available materials' }.")
        extension = f"Use {topic} in a new example and explain the choice or result."
        lines_one = (("Cross-curricular elements", emk), ("21st-century learning", pak21),
                     ("Higher-order thinking", kbat))
        lines_two = (("Remedial", remediation), ("Enrichment", extension))
        label_one, label_two = "CCE / 21st-century learning / HOTS", "Remedial / Enrichment"
    else:
        if existing_support:
            remediation = f"Ulang tugasan {topic} dengan berpandukan sokongan yang dinyatakan dalam bahagian akhir RPH."
        else:
            aid = _brief(materials, 48)
            remediation = (
                f"Bimbing semula tugasan berkaitan {topic}" +
                (f" menggunakan {aid}." if aid else " secara berperingkat.")
            )
        if family == "ppki":
            extension = f"Murid yang menguasai kemahiran memilih atau menunjukkan tindakan dalam situasi baharu berkaitan {topic}."
        elif family == "sains":
            extension = f"Bandingkan satu contoh baharu tentang {topic} dan nyatakan sebab berdasarkan pemerhatian."
        else:
            extension = f"Bina satu contoh baharu berkaitan {topic} dan terangkan cara atau jawapan."
        lines_one = (("EMK", emk), ("PAK21", pak21), ("KBAT", kbat))
        lines_two = (("Pemulihan", remediation), ("Pengayaan", extension))
        label_one, label_two = "EMK / PAK21 / KBAT", "Pemulihan / Pengayaan"
    addition = []
    if not all(label.casefold() in present for label, _ in lines_one):
        addition.append((label_one, "\n".join(
            f"{name}: {value}" for name, value in lines_one
            if name.casefold() not in present
        )))
    if not all(label.casefold() in present for label, _ in lines_two):
        addition.append((label_two, "\n".join(
            f"{name}: {value}" for name, value in lines_two
            if name.casefold() not in present
        )))
    return list(details) + addition
