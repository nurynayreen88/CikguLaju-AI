"""Exact, source-referenced display labels for seven audited native KSSR RPH.

This adapter changes ONLY the printed SK/SP cells when the native verified
PdP yields a bare code. The official DSKP/DPK wording below is year-specific.
Unknown codes, unrelated years, specialty renderers and existing descriptive
text are never guessed or rewritten; the curriculum DB is never modified.
"""
from __future__ import annotations

import re

# DSKP KSSR Semakan 2017 (Matematik Tahun 3–6 / Sains Tahun 5–6);
# DPK Edisi 3 Matematik Tahun 2.
# Verification references:
# https://ecentral.my/wp-content/uploads/2024/09/DOKUMEN-PENJAJARAN_KSSR-MATEMATIK-TAHAP-1_EDISI-3-compressed.pdf
# https://www.tcer.my/wp-content/uploads/2021/01/KSSR-MATEMATIK-TAHUN-3-DIJAJARKAN-NEW.pdf
# https://asiemodel.net/wp-content/uploads/2022/08/DSKP-KSSR-SEMAKAN-2017-MATEMATIK-TAHUN-4.pdf
# https://fliphtml5.com/bjmui/mpbq/DSKP_KSSR_%28Semakan_2017%29_Matematik_Tahun_5_SK/44/
# https://www.eprema.com.my/SKDocs/DSKP/Tahun6/9.DSKP_KSSR_T6_Semakan_Matematik.pdf
# https://asiemodel.net/wp-content/uploads/2022/08/012_DSKP_KSSR_Semakan_2017_Sains_Thn5-print.pdf
# https://anyflip.com/qqfu/esbw/basic/51-94

_VERIFIED = {
    ("Matematik", 2): ("1.1", "Nilai nombor",
        "1.1.1(i)", "Membaca nombor yang diberi dalam perkataan"),
    ("Matematik", 3): ("1.1", "Nilai nombor",
        "1.1.1(ii)", "Menyebut sebarang nombor yang diberi dalam bentuk angka"),
    ("Matematik", 4): ("1.1", "Nilai nombor",
        "1.1.1(i)", "Membaca sebarang nombor yang diberi dalam perkataan"),
    ("Matematik", 5): ("1.1", "Nilai nombor",
        "1.1.1(i)", "Membaca sebarang nombor dalam perkataan"),
    ("Matematik", 6): ("1.1", "Nombor bulat hingga 10 000 000",
        "1.1.1", "Membaca, menyebut dan menulis sebarang nombor hingga 10 000 000"),
    ("Sains", 5): ("2.1", "Sistem Rangka Manusia",
        "2.1.1", "Memerihalkan fungsi rangka utama manusia"),
    ("Sains", 6): ("13.1", "Kebaikan dan Keburukan Teknologi",
        "13.1.1", "Menyatakan maksud teknologi dan kepentingannya"),
}
# Additional *same-lesson* SP clauses explicitly present in the grouped
# verified Math source. DPK/DSKP year-specific, not inferred from the title.
_EXTRA_SPS = {
    ("Matematik", 2): {
        "1.1.1(ii)": "Menyebut sebarang nombor yang diberi dalam bentuk angka",
    },
    ("Matematik", 3): {
        "1.1.1(iii)": "Memadan angka dengan namanya dalam perkataan",
    },
    ("Matematik", 4): {
        "1.1.1(ii)": "Menyebut sebarang nombor yang diberi dalam bentuk angka",
    },
    ("Matematik", 5): {
        "1.1.1(ii)": "Menyebut sebarang nombor dalam bentuk angka",
        "1.1.1(iii)": "Menulis nombor dalam angka dan perkataan",
    },
}

_MARKER = "_CIKGULAJU_SK_SP_VERIFIED_DESCRIPTIONS_20261124"



def _source_labels(state, prefix):
    """Read exact verified descriptions carried by the selected native bridge.

    Conflicting text, absent text and non-matching codes stay unresolved.
    Do not use topics, objectives or another year's curriculum as a fallback.
    """
    candidates = {}
    pairs = state.get("_rph_verified_display_standard_pairs")
    if not isinstance(pairs, list):
        return {}
    for pair in pairs:
        if not isinstance(pair, dict):
            continue
        code = str(pair.get(prefix + "_code") or "").strip()
        label = str(pair.get(prefix + "_text") or "").strip()
        if not re.fullmatch(r"\d+(?:\.\d+)+(?:\([ivxlcdm]+\))?", code, re.I):
            continue
        if label.startswith(code + " "):
            label = label[len(code):].strip()
        # Reject missing/ambiguous compound labels and raw code-only values.
        if not label or ";" in label or not any(ch.isalpha() for ch in label):
            continue
        if re.fullmatch(r"[\d.()\sivxlcdm]+", label, re.I):
            continue
        candidates.setdefault(code, set()).add(label)
    return {code: next(iter(values)) for code, values in candidates.items()
            if len(values) == 1}


def _expand_source_cells(state, rows):
    revisions = {}
    for prefix, field in (("sk", "STANDARD KANDUNGAN"),
                          ("sp", "STANDARD PEMBELAJARAN")):
        value = rows.get(field)
        if not isinstance(value, str):
            continue
        labels = _source_labels(state, prefix)
        clauses = [piece.strip() for piece in value.split(";")]
        if clauses and all(piece in labels for piece in clauses):
            revisions[field] = "; ".join(f"{code} {labels[code]}" for code in clauses)
    return {**rows, **revisions} if revisions else rows


def display_verified_standards(state, rows):
    """Preserve source text; expand only exact, audited code-only cells."""
    if not isinstance(state, dict) or not isinstance(rows, dict):
        return rows
    if str(state.get("task") or "").strip().casefold() != "rph":
        return rows
    year = re.fullmatch(r"Tahun ([2-6])", str(state.get("year") or ""))
    if not year:
        return rows
    subject = str(state.get("subject") or "").strip()
    year_no = int(year[1])
    choice = _VERIFIED.get((subject, year_no))
    if subject not in ("Matematik", "Sains"):
        return rows
    for key in ("curriculum", "curriculum_version", "stream",
                "programme", "program", "school_type"):
        if any(bad in str(state.get(key) or "").casefold()
               for bad in ("dlp", "ppki", "sjkc", "sjkt", "kp2027")):
            return rows
    code = str(state.get("pdp_sequence_code") or "")
    prefix = f"MT{year_no}" if subject == "Matematik" else f"SCI-Y{year_no}"
    if not re.fullmatch(re.escape(prefix) + r"-PDP-\d{3}", code):
        return rows

    rows = _expand_source_cells(state, rows)
    if not choice:
        return rows

    sk_code, sk_text, sp_code, sp_text = choice
    revisions = {}
    shown_sk = rows.get("STANDARD KANDUNGAN")
    if isinstance(shown_sk, str) and shown_sk.strip() == sk_code:
        revisions["STANDARD KANDUNGAN"] = f"{sk_code} {sk_text}"
    shown_sp = rows.get("STANDARD PEMBELAJARAN")
    if isinstance(shown_sp, str):
        # Source may combine 2 or 3 *individually coded* SP with semicolons.
        # Expand ONLY when every one has an exact verified year-specific label.
        # This is atomic: a single unknown clause means preserve the original.
        sp_map = {sp_code: sp_text, **_EXTRA_SPS.get((subject, year_no), {})}
        clauses = [piece.strip() for piece in shown_sp.split(";")]
        if clauses and all(piece in sp_map for piece in clauses):
            revisions["STANDARD PEMBELAJARAN"] = "; ".join(
                f"{piece} {sp_map[piece]}" for piece in clauses
            )
    if not revisions:
        return rows
    return {**rows, **revisions}


def install(runtime):
    if getattr(runtime, _MARKER, False):
        return False
    previous = getattr(runtime, "_rph_rows", None)
    if not callable(previous):
        return False

    def with_verified_descriptions(state, *args, **kwargs):
        rows = previous(state, *args, **kwargs)
        return display_verified_standards(state, rows)

    runtime._rph_rows = with_verified_descriptions
    setattr(runtime, _MARKER, True)
    return True
