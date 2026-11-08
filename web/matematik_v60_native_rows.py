"""Opt-in RPH Matematik v60 rows for the *existing* Telegram Word/PDF engine.

Staging-only: never consults or alters RPT, curriculum DB, users or quotas.
A lesson must match the selected native PdP sequence and the exact SK/SP;
if the match fails while enabled, fail CLOSED rather than silently send v25 text.
The authoritative content is the SHA-verified 585-Markdown v60 snapshot in main.
"""
from __future__ import annotations

import os
import re
from typing import Mapping

_ALLOWED_YEARS = range(2, 7)
_FIELDS = (
    "Tajuk", "SK", "SP", "Objektif", "Set induksi (5 minit)",
    "Aktiviti 1 — Penerokaan/Model (20 minit)",
    "Aktiviti 2 — Aplikasi/Latihan (20 minit)",
    "Penutup (5 minit)", "BBM", "Rujukan", "Refleksi guru",
)
_PBD_FIELDS = (
    "Aktiviti 3 — Buku Aktiviti/PBD (10 minit)",
    "Pengukuhan dan pentaksiran (10 minit)",
)
_METADATA = re.compile(r"(?m)^\*\*([^*\n]+):\*\*\s*([^\n]+?)\s*$")
_SPCODE = re.compile(r"^(\d+\.\d+\.\d+)\s+—\s+(.+)$")
_SKCODE = re.compile(r"^(\d+\.\d+)\s+(.+)$")
_TITLE = re.compile(r"^# RPH Matematik Tahun ([2-6]) — Lesson (\d{3})$")


class MathematicsRPHUnavailable(RuntimeError):
    """Verified RPH cannot be selected; never fall back to a different plan."""


def is_enabled(environ=None) -> bool:
    env = os.environ if environ is None else environ
    return (env.get("CIKGULAJU_ENV") == "staging"
            and env.get("CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED") == "1")


def _math_year(state: Mapping) -> int | None:
    if not isinstance(state, Mapping) or state.get("task") not in ("rph", "quick_material"):
        return None
    name = re.sub(r"[^a-z]", "", str(state.get("subject") or "").lower())
    if name not in ("matematik", "mathematics", "math"):
        return None
    year = str(state.get("year") or state.get("year_label") or "").strip().lower()
    found = re.fullmatch(r"(?:tahun\s*)?([2-6])", year)
    return int(found.group(1)) if found else None


def _positive_int(value) -> int | None:
    if type(value) is int:
        return value if 1 <= value <= 117 else None
    if type(value) is str and re.fullmatch(r"(?:[1-9]|[1-9]\d|1(?:0\d|1[0-7]))", value.strip()):
        return int(value.strip())
    return None


def _lesson_identity(state: Mapping) -> int:
    # These are the native Telegram sequence attributes, never a guessed
    # week number or RPT row index. An opaque PdP selection is mandatory.
    code = state.get("pdp_sequence_code")
    if not isinstance(code, str) or not code.strip() or len(code) > 100:
        raise MathematicsRPHUnavailable("Native PdP sequence identity missing")
    first = _positive_int(state.get("source_sequence_no"))
    if first is None:
        raise MathematicsRPHUnavailable("Exact native lesson number unavailable")
    other = _positive_int(state.get("pdp_no"))
    if other is not None and other != first:
        raise MathematicsRPHUnavailable("Conflicting PdP numbering")
    return first


def parse_lesson(raw: str, year: int, lesson: int) -> dict:
    """Parse one exact source Markdown without inferring any exercise or SP."""
    if type(year) is not int or year not in _ALLOWED_YEARS or type(lesson) is not int or not 1 <= lesson <= 117:
        raise MathematicsRPHUnavailable("Invalid Matematik RPH identity")
    if not isinstance(raw, str) or len(raw) < 450 or len(raw) > 20000:
        raise MathematicsRPHUnavailable("Incomplete Matematik source")
    first = raw.splitlines()[0]
    header = _TITLE.fullmatch(first)
    if not header or int(header.group(1)) != year or int(header.group(2)) != lesson:
        raise MathematicsRPHUnavailable("RPH heading/lesson mismatch")
    pairs = list(_METADATA.findall(raw))
    fields = {}
    for key, value in pairs:
        if key in fields:
            raise MathematicsRPHUnavailable("Duplicate RPH field")
        fields[key] = value.strip()
    if any(not fields.get(k) for k in _FIELDS):
        raise MathematicsRPHUnavailable("RPH sections incomplete")
    if sum(bool(fields.get(k)) for k in _PBD_FIELDS) != 1:
        raise MathematicsRPHUnavailable("RPH must have exactly one PBD section")
    if not _SPCODE.fullmatch(fields["SP"]) or not _SKCODE.fullmatch(fields["SK"]):
        raise MathematicsRPHUnavailable("Invalid source SK/SP")
    sp = _SPCODE.fullmatch(fields["SP"]).group(1)
    sk = _SKCODE.fullmatch(fields["SK"]).group(1)
    if not sp.startswith(sk + "."):
        raise MathematicsRPHUnavailable("Source SK/SP incompatible")
    fields["_sk_code"] = sk
    fields["_sp_code"] = sp
    fields["_pbd"] = next(fields[k] for k in _PBD_FIELDS if k in fields)
    fields["_pbd_title"] = next(k for k in _PBD_FIELDS if k in fields)
    return fields


def _source_lesson(year: int, number: int) -> str:
    from rph_standalone.matematik.v60_source_loader import get_lesson
    return get_lesson(year, number)  # Source pack SHA-verified, all 585 lessons.


def _selected_standard(state: Mapping) -> tuple[str, str]:
    selected = state.get("selected_sp_codes")
    code = str(state.get("sp_code") or "").strip()
    # Multiple official SPs in a selected PdP cannot be replaced by a
    # single-SP RPH v60 without a separately approved composite plan.
    if selected is not None:
        if not isinstance(selected, (list, tuple)) or len(selected) != 1:
            raise MathematicsRPHUnavailable("Multi-SP PdP requires separate verification")
        found = str(selected[0]).strip()
        if not found or (code and code != found):
            raise MathematicsRPHUnavailable("Selected SP inconsistency")
        code = found
    sk = str(state.get("sk_code") or "").strip()
    if not code or not sk:
        raise MathematicsRPHUnavailable("Verified Telegram SP/SK missing")
    return sk, code


def verify_state(state: Mapping) -> tuple[int, int, dict] | None:
    """Returns verified source or None for other subjects and Year 1.

    Raises on any mismatch once opt-in is enabled, so the request cannot
    quietly revert to an older document for Mathematics Years 2–6.
    """
    if not is_enabled():
        return None
    year = _math_year(state)
    if year is None:
        return None
    if not state.get("quick_material_flow"):
        # Native sequence Web/Telegram flows set this trusted server-side flag.
        raise MathematicsRPHUnavailable("Unverified RPH generation route")
    number = _lesson_identity(state)
    sk, sp = _selected_standard(state)
    try:
        source = parse_lesson(_source_lesson(year, number), year, number)
    except MathematicsRPHUnavailable:
        raise
    except Exception as exc:
        raise MathematicsRPHUnavailable("Matematik v60 content integrity check failed") from exc
    if (source["_sp_code"], source["_sk_code"]) != (sp, sk):
        raise MathematicsRPHUnavailable("Native PdP and v60 SK/SP mismatch")
    return year, number, source



def resolve_native_state(runtime, state: Mapping) -> Mapping:
    """Resolve omitted Lesson number from the exact selected Telegram PdP.

    Telegram's quick-material callback sometimes stores only a PdP code;
    its source_sequence_no must be retrieved from the verified native reader,
    never inferred from a dropdown index, week or topic.
    """
    if not is_enabled() or _math_year(state) is None:
        return state
    if state.get("source_sequence_no") is not None:
        return state
    if not state.get("quick_material_flow"):
        raise MathematicsRPHUnavailable("Unverified Mathematics quick flow")
    code = state.get("pdp_sequence_code")
    if not isinstance(code, str) or not code.strip() or len(code) > 100:
        raise MathematicsRPHUnavailable("Exact Telegram PdP key not selected")
    reader = getattr(runtime, "_sm2542_rows", None)
    if not callable(reader):
        raise MathematicsRPHUnavailable("Native PdP source reader unavailable")
    year = _math_year(state)
    try:
        all_rows = reader(f"Tahun {year}", "Matematik")
    except Exception as exc:
        raise MathematicsRPHUnavailable("Unable to resolve Telegram PdP") from exc
    if not isinstance(all_rows, list) or len(all_rows) > 5000:
        raise MathematicsRPHUnavailable("Invalid Telegram PdP records")
    rows = [r for r in all_rows if isinstance(r, dict)
            and str(r.get("pdp_sequence_code") or "").strip() == code]
    if not rows:
        raise MathematicsRPHUnavailable("Selected PdP missing in source")
    nums = {_positive_int(r.get("source_sequence_no")) for r in rows}
    if len(nums) != 1 or None in nums:
        raise MathematicsRPHUnavailable("Native PdP has ambiguous Lesson identity")
    pairs = {(str(r.get("sk_code") or "").strip(),
              str(r.get("sp_code") or "").strip()) for r in rows}
    if len(pairs) != 1:
        raise MathematicsRPHUnavailable("Native PdP needs composite/verified SK/SP")
    sk, sp = next(iter(pairs))
    if not sk or not sp:
        raise MathematicsRPHUnavailable("Native PdP SK/SP missing")
    if state.get("sp_code") and str(state["sp_code"]).strip() != sp:
        raise MathematicsRPHUnavailable("Telegram selected a different SP")
    if state.get("sk_code") and str(state["sk_code"]).strip() != sk:
        raise MathematicsRPHUnavailable("Telegram selected a different SK")
    current = state.get("grouped_sp_codes") or state.get("selected_sp_codes")
    if current is not None and (not isinstance(current, (tuple, list))
                                or {str(x).strip() for x in current} != {sp}):
        raise MathematicsRPHUnavailable("Grouped SP mapping differs from PdP")
    resolved = dict(state)
    number = nums.pop()
    resolved.update(task="rph", source_sequence_no=number, pdp_no=number,
                    sk_code=sk, sp_code=sp, selected_sp_codes=[sp])
    return resolved


def adapt_rows(state: Mapping, rows: dict) -> dict:
    if not isinstance(rows, dict):
        raise MathematicsRPHUnavailable("Word/PDF row layout not available")
    verified = verify_state(state)
    if verified is None:
        return rows
    year, number, source = verified
    result = dict(rows)
    result["MATA PELAJARAN"] = "Matematik"
    result["TAHUN/TINGKATAN"] = f"Tahun {year}"
    result["TAJUK"] = source["Tajuk"]
    result["STANDARD KANDUNGAN"] = source["SK"]
    result["STANDARD PEMBELAJARAN"] = source["SP"]
    result["OBJEKTIF PEMBELAJARAN"] = source["Objektif"]
    result["KRITERIA KEJAYAAN"] = source["Objektif"]
    result["SET INDUKSI"] = "5 minit\n" + source["Set induksi (5 minit)"]
    result["AKTIVITI UTAMA"] = "\n\n".join((
        "Aktiviti 1 — Penerokaan/Model (20 minit)\n" + source["Aktiviti 1 — Penerokaan/Model (20 minit)"],
        "Aktiviti 2 — Aplikasi/Latihan (20 minit)\n" + source["Aktiviti 2 — Aplikasi/Latihan (20 minit)"],
        source["_pbd_title"] + "\n" + source["_pbd"],
    ))
    result["PENTAKSIRAN"] = source["_pbd"]
    result["PENUTUP"] = "5 minit\n" + source["Penutup (5 minit)"]
    result["BAHAN BANTU MENGAJAR"] = source["BBM"] + "\nRujukan: " + source["Rujukan"]
    # Use teacher-provided reflection when available, not the source blank.
    if not str(result.get("REFLEKSI") or "").strip():
        result["REFLEKSI"] = source["Refleksi guru"]
    # Preserve trusted class/date/time/pupil values as entered by teacher.
    for key in ("KELAS", "TARIKH", "MASA", "HARI", "BILANGAN MURID"):
        if key in rows and result.get(key) != rows[key]:
            raise MathematicsRPHUnavailable("Teacher metadata cannot be overwritten")
    return result


def install(runtime) -> bool:
    """Wrap final existing native Word/PDF row renderer; never patch quotas."""
    if not is_enabled():
        return False
    if getattr(runtime, "CIKGULAJU_MATH_V60_NATIVE_ROWS_ACTIVE", False):
        return True
    previous = getattr(runtime, "_rph_rows", None)
    if not callable(previous):
        return False

    def render(state, *args, **kwargs):
        if _math_year(state) is None:
            return previous(state, *args, **kwargs)
        # Perform integrity/identity check *before* invoking old renderer.
        resolved_state = resolve_native_state(runtime, state)
        verified = verify_state(resolved_state)
        if verified is None:
            return previous(state, *args, **kwargs)
        # Pass the verified native identity to the original renderer too.
        # Telegram quick-material callbacks may omit source_sequence_no;
        # giving the unresolved state to the renderer risks generating an
        # unrelated legacy document before v60 replaces its rows.
        rows = previous(resolved_state, *args, **kwargs)
        return adapt_rows(resolved_state, rows)

    runtime._rph_rows = render
    runtime.CIKGULAJU_MATH_V60_NATIVE_ROWS_ACTIVE = True
    return True
