"""Staging-only RPH Muzik -> Telegram-native layout preview.

Never imported by app.py, web routes or Telegram. No writer, side effects,
entitlement changes, audio or public availability. Output is NOT FINAL READY.
The real native renderer must still be tested with verified source parity.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOLD_HEADING = re.compile(r"^\s*\*\*([^*\n]+)\*\*\s*(.*)$")
CODES = re.compile(r"^[1-5]\.[1-9]\.\d+$")
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
        (s["label"], "\n".join(s["parts"]).strip().replace("**", ""))
        for s in found
    ]


def _lookup(items, pattern):
    matches = [(key, value) for key, value in items if re.search(pattern, key, re.I)]
    if len(matches) != 1:
        raise ValueError(f"Missing/ambiguous Music RPH section {pattern}: {len(matches)}")
    name, value = matches[0]
    if not value or value.strip("— _\n") == "":
        raise ValueError(f"Empty Music RPH section: {name}")
    return name, value


def build_staging_preview(root, year, pdp):
    """Return validated preview layout without touching production or writing files."""
    if type(year) is not int or year not in range(2, 7):
        raise ValueError("Year 2–6 only; Year 1 is KP2027")
    if type(pdp) is not int or pdp not in range(1, 36):
        raise ValueError("PdP must be 1–35")
    base = Path(root).resolve()
    if not (base / f"year{year}").is_dir():
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
        "objective": _lookup(items, r"^objektif(?:\s|$)"),
        "induction": _lookup(items, r"^set\s+induksi\b"),
        "act1": _lookup(items, r"^aktiviti\s*1\b"),
        "act2": _lookup(items, r"^aktiviti\s*2\b"),
        "assessment": _lookup(items, r"^pengukuhan\b"),
        "closure": _lookup(items, r"^penutup\b"),
        "materials": _lookup(items, r"^bahan\b"),
    }
    criterion = [(k, v) for k, v in items if re.search(r"^kriteria\s+kejayaan", k, re.I)]
    if len(criterion) > 1:
        raise ValueError("Duplicated success criteria")
    # Draft sidecar is editorial scaffolding only, never an official DSKP gate.
    draft_overlay = json.loads((base / "SUCCESS_CRITERIA_DRAFT_20261106.json").read_text(encoding="utf-8"))
    drafted = draft_overlay.get(row["pdp_id"]) if not criterion else None
    if drafted and (drafted.get("approval") != "DRAF_EDITORIAL_BELUM_DISAHKAN"
                    or drafted.get("year") != year or drafted.get("pdp") != pdp):
        raise ValueError("Untrusted success criterion overlay")
    # Fail closed if the auditable SP crosswalk is not the same as this manifest.
    # An SP number appearing in DSKP text does NOT imply pedagogical approval.
    dskp_matrix = json.loads((base / "DSKP_SP_CODE_PRESENCE_175_20261106.json").read_text(encoding="utf-8"))
    ix = (year - 2) * 35 + pdp - 1
    if len(dskp_matrix["records"]) != 175 or ix < 0:
        raise ValueError("Untrusted Muzik DSKP crosswalk size")
    crosswalk = dskp_matrix["records"][ix]
    if (crosswalk["pdp_id"] != row["pdp_id"] or crosswalk["manifest_sp"] != sp
            or crosswalk["year"] != year or crosswalk["pdp"] != pdp
            or crosswalk.get("official_approval") is not False):
        raise ValueError("Untrusted Muzik DSKP source crosswalk")
    print_code_conflict = bool(crosswalk["sp_not_found_in_source"])
    source_numbering_unresolved = bool(row.get("dskp_sp_heading_numbering_conflict"))
    if source_numbering_unresolved and row.get("dskp_crosswalk_approved") is not False:
        raise ValueError("Unapproved SK/SP source numbering discrepancy")
    if print_code_conflict and (not row.get("dskp_source_printed_sp")
                                or row.get("dskp_crosswalk_approved") is not False):
        raise ValueError("Missing unapproved Year4 source-code conflict annotation")
    candidate_days_zero = row.get("rpt2027_day_audit", {}).get("status") == "ZERO_CALON_PDP_IN_ALL_16_STATES"
    if candidate_days_zero and not row["rpt2027_day_audit"].get("automatic_shift_or_skip_forbidden", False):
        raise ValueError("Music zero-day RPT slot cannot be auto-shifted")
    criteria = criterion[0][1] if criterion else drafted["criterion"] if drafted else "—"
    # Each source heading already includes its activity number/phase name.
    # Avoid "Aktiviti 1 - Aktiviti 1" and "Pengukuhan - Pengukuhan".
    notes = labels["act1"][0] + "\n" + labels["act1"][1] + \
            "\n\n" + labels["act2"][0] + "\n" + labels["act2"][1] + \
            "\n\n" + labels["assessment"][0] + "\n" + labels["assessment"][1]
    # The standalone 2019 Music Year 4 DSKP prints SK 3.1 with SP 3.2.x,
    # and SK 4.1 with SP 4.2.1. Deriving SK from the SP prefix is WRONG.
    # Keep this explicit source anomaly instead of silently normalizing SP.
    standards = []
    for code in sp:
        parent = code.rsplit(".", 1)[0]
        if year == 4 and parent == "3.2":
            parent = "3.1"
        elif year == 4 and code == "4.2.1":
            parent = "4.1"
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
    if print_code_conflict:
        warnings.extend(["SP_CODE_NOT_FOUND_IN_YEAR_DSKP", "DSKP_CROSSWALK_NOT_APPROVED"])
    if source_numbering_unresolved:
        warnings.extend(["DSKP_SK_SP_NUMBERING_DISCREPANCY", "DSKP_CROSSWALK_NOT_APPROVED"])
    if candidate_days_zero:
        warnings.extend(["RPT_ZERO_CANDIDATE_SCHOOL_DAYS", "PDP_ANJAL_DO_NOT_AUTO_SHIFT"])
    if not criterion:
        warnings.append("NO_EXPLICIT_SUCCESS_CRITERIA")
        if drafted:
            warnings.append("EDITORIAL_DRAFT_CRITERION_OVERLAY_NOT_APPROVED")
    if not row.get("source_book_text_crosscheck", False):
        warnings.append("TEXTBOOK_NOT_FULLY_CROSSCHECKED_OR_NONOFFICIAL")
    return {
        "subject": "MUZIK", "year": year, "pdp": pdp,
        "source_pdp_id": row["pdp_id"], "layout": layout,
        "phase_text": {key: value for key, (_, value) in labels.items()},
        "warnings": warnings, "approved_for_live": False,
        "source_sp_code_conflict": print_code_conflict,
        "source_sp_numbering_discrepancy": source_numbering_unresolved,
        "rpt_week_zero_candidate_days": candidate_days_zero,
    }
