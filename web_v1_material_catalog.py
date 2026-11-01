"""Fail-closed material manifest for Web V1.

Only explicitly verified, entitled downloadable files may be shown.
No URLs are inferred from subject names, RPT records or lesson numbers.
"""
from urllib.parse import urlsplit

ALLOWED_KINDS = frozenset({"rph", "textbook", "workbook", "audio", "teacherbook", "rpt", "support"})
ALLOWED_FORMATS = frozenset({"pdf", "docx", "mp3", "zip"})
SUBJECT_ENGLISH = frozenset({"ENGLISH"})
BILINGUAL_SUBJECTS = frozenset({"MATH", "SCIENCE"})


def material_label(kind, subject_code, language="bm"):
    if kind not in ALLOWED_KINDS:
        raise ValueError("unsupported material kind")
    english = subject_code in SUBJECT_ENGLISH or (subject_code in BILINGUAL_SUBJECTS and language == "en")
    labels = {
        "rph": ("RPH", "Lesson Plan"),
        "textbook": ("Buku Teks", "Student's Book / Textbook"),
        "workbook": ("Buku Aktiviti", "Workbook / Activity Book"),
        "audio": ("Audio", "Lesson Audio"),
        "teacherbook": ("Buku Panduan Guru", "Teacher's Book"),
        "rpt": ("RPT", "Scheme of Work"),
        "support": ("Bahan Sokongan", "Supporting Materials"),
    }
    return labels[kind][1 if english else 0]


def visible_materials(records, *, subject_code, entitled_ids):
    """Render metadata only; caller must separately authorize actual downloads.

    Records come from a trusted, verified file registry, not user input.
    HTTPS file endpoints are restricted to same-origin relative paths, preventing
    untrusted external links and javascript: URLs.
    """
    if not isinstance(records, (list, tuple)):
        raise ValueError("invalid material registry")
    entitled = set(entitled_ids)
    visible = []
    seen = set()
    for item in records:
        if not isinstance(item, dict):
            continue
        ident = item.get("id")
        kind = item.get("kind")
        fmt = item.get("format")
        path = item.get("download_path")
        if (not isinstance(ident, str) or ident in seen or ident not in entitled
                or kind not in ALLOWED_KINDS or fmt not in ALLOWED_FORMATS
                or item.get("verified") is not True
                or not isinstance(path, str) or not path.startswith("/api/materials/download/")
                or urlsplit(path).scheme or urlsplit(path).netloc
                or "?" in path or "#" in path or "\\" in path):
            continue
        language = item.get("language", "bm")
        if language not in ("bm", "en"):
            continue
        seen.add(ident)
        visible.append({
            "id": ident, "kind": kind, "label": material_label(kind, subject_code, language),
            "format": fmt.upper(), "language": language, "download_path": path,
        })
    return visible
