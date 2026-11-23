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
_MARKER = "_CIKGULAJU_SK_SP_VERIFIED_DESCRIPTIONS_20261124"


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
    if not choice:
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

    sk_code, sk_text, sp_code, sp_text = choice
    revisions = {}
    for name, source_code, description in (
        ("STANDARD KANDUNGAN", sk_code, sk_text),
        ("STANDARD PEMBELAJARAN", sp_code, sp_text),
    ):
        shown = rows.get(name)
        if isinstance(shown, str) and shown.strip() == source_code:
            revisions[name] = f"{source_code} {description}"
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
