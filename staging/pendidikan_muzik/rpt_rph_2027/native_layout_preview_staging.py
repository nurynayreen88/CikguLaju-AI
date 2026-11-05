"""Staging-only RPH Muzik -> Telegram-native layout preview.

Never imported by app.py, web routes or Telegram. No writer, side effects,
entitlement changes, audio or public availability. Output is NOT FINAL READY.
The real native renderer must still be tested with verified source parity.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOLD_HEADING = re.compile(r"^\\s*\\*\\*([^*\\n]+)\\*\\*\\s*(.*)$")
CODES = re.compile(r"^[1-5]\\.[1-9]\\.\\d+$")
ACTIVITY_HEADER = ["Fasa / Masa", "Aktiviti Pengajaran & Pembelajaran", "Catatan"]


def _sections(text):
    """Keep a section's complete text, including continuation lines."""
    found = []
    current = None
    for line in text.splitlines():
        match = BOLD_HEADING.match(line)
        if match:
            label, inline = match.groups()
            label = label.strip().rstrip(":").strip()
            current = {"label": label, "parts": [inline.lstrip(":").strip()]}
            found.append(current)
        elif current is not None:
            current["parts"].append(line.strip())
    return [
        (s["label"], "\\n".join(s["parts"]).strip())
        for s in found
    ]


def _lookup(items, pattern):
    matches = [(key, value) for key, value in items if re.search(pattern, key, re.I)]
    if len(matches) != 1:
        raise ValueError(f"Missing/ambiguous Music RPH section {pattern}: {len(matches)}")
    name, value = matches[0]
    if not value or value.strip("— _\\n") == "":
        raise ValueError(f"Empty Music RPH section: {name}")
    return name, value


def build_staging_preview(root, year, pdp):
    """Return validated preview layout without touching production or writing files."""
    if type(year) is not int or year not in range(2, 7):
        raise ValueError("Year 2–6 only; Year 1 is KP2027")
    if type(pdp) is not int or pdp not in range(1, 36):
        raise ValueError("PdP must be 1–35")
    base = Path(root).resolve()
    if not (base / "year%d" % year).is_dir():
        raise ValueError("Missing year directory")
    directory = base / f"year{year}"
    manifest = json.loads((directory / "pdp_manifest.json").read_text(encoding="utf-8"))
    row = manifest["pdps"][pdp - 1]
    if row["pdp"] != pdp or row["pdp_id"] != f"MZ-Y{year}-{pdp:02d}":
        raise ValueError("Staging source identity mismatch")
    sp = row["sp"]
    if not isinstance(sp, list) or not sp or not all(isinstance(v, str) and CODES.fullmatch(v) for v in sp):
        raise ValueError("Untrusted SP list")
    path = directory / f"rph_pdp_{pdp:02d}.md"
    if path.is_symlink() or not path.resolve().is_relative_to(base):
        raise ValueError("Untrusted source path")
    raw = path.read_text(encoding="utf-8")
    items = _sections(raw)
    labels = {
        "objective": _lookup(items, r"^objektif(?:\\s|$)"),
        "induction": _lookup(items, r"^set\\s+induksi\\b"),
        "act1": _lookup(items, r"^aktiviti\\s*1\\b"),
        "act2": _lookup(items, r"^aktiviti\\s*2\\b"),
        "assessment": _lookup(items, r"^pengukuhan\\b"),
        "closure": _lookup(items, r"^penutup\\b"),
        "materials": _lookup(items, r"^bahan\\b"),
    }
    criterion = [(k, v) for k, v in items if re.search(r"^kriteria\\s+kejayaan", k, re.I)]
    if len(criterion) > 1:
        raise ValueError("Duplicated success criteria")
    criteria = criterion[0][1] if criterion else "—"
    notes = "Aktiviti 1 — " + labels["act1"][0] + "\\n" + labels["act1"][1] + \
            "\\n\\nAktiviti 2 — " + labels["act2"][0] + "\\n" + labels["act2"][1] + \
            "\\n\\nPengukuhan dan Penilaian — " + labels["assessment"][0] + "\\n" + labels["assessment"][1]
    standards = []
    for code in sp:
        parent = code.rsplit(".", 1)[0]
        if parent not in standards:
            standards.append(parent)
    ref = [v for k, v in items if re.search(r"^(?:refleksi|catatan.*pemulihan)", k, re.I)]
    reflection = ref[0] if ref else "____________"
    metadata = [
        ("Nama Guru", ""), ("Nama Sekolah", ""), ("Tarikh", ""), ("Hari", ""),
        ("Masa", ""), ("Kelas", ""), ("Bilangan Murid", ""), ("Tahun", str(year)),
        ("Subjek", "Pendidikan Muzik"), ("Tajuk", row["unit"]),
        ("PdP", str(pdp)), ("Standard Kandungan", "; ".join(standards)),
        ("Standard Pembelajaran", "; ".join(sp)),
        ("OBJEKTIF PEMBELAJARAN", labels["objective"][1]),
        ("KRITERIA KEJAYAAN", criteria or "—"), ("PENGETAHUAN SEDIA ADA", "—"),
        ("BAHAN BANTU MENGAJAR", labels["materials"][1]),
        ("EMK / NILAI", "—"), ("KBAT / PAK21", "—"),
        ("PENTAKSIRAN", labels["assessment"][1]),
    ]
    layout = {
        "style": "telegram-native-rph-v1",
        "header": [{"label": k, "value": v} for k, v in metadata],
        "activity_header": ACTIVITY_HEADER,
        "phases": [
            {"label": "Set Induksi (4 minit)", "activity": labels["induction"][1], "notes": ""},
            {"label": "Aktiviti Utama dan Pengukuhan (24 minit)", "activity": notes, "notes": ""},
            {"label": "Penutup (2 minit)", "activity": labels["closure"][1], "notes": ""},
        ],
        "footer": [
            {"label": "Pemulihan / Pengayaan", "value": reflection or "____________"},
            {"label": "Refleksi", "value": "____________"},
        ],
    }
    # This asserts only pedagogical phase fidelity, NOT full document conversion.
    for name in ("act1", "act2", "assessment"):
        if labels[name][1] not in layout["phases"][1]["activity"]:
            raise ValueError(f"Lost {name}")
    warnings = ["NOT_PUBLISHED", "NO_REAL_WORD_PDF_RENDER", "NO_CROSS_PLATFORM_PARITY"]
    if not criterion:
        warnings.append("NO_EXPLICIT_SUCCESS_CRITERIA")
    if not row.get("source_book_text_crosscheck", False):
        warnings.append("TEXTBOOK_NOT_FULLY_CROSSCHECKED_OR_NONOFFICIAL")
    return {
        "subject": "MUZIK", "year": year, "pdp": pdp,
        "source_pdp_id": row["pdp_id"], "layout": layout,
        "phase_text": {key: value for key, (_, value) in labels.items()},
        "warnings": warnings, "approved_for_live": False,
    }
