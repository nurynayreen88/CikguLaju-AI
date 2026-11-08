"""Read-only pre-release reconciliation of all Maths v60 lessons against native PdP.

Never imports or changes the database. Call ONLY with a staging audit source
that verifies Telegram Matematik's v25.99 canonical DB checksum first, then
sets CIKGULAJU_MATH_V2599_SOURCE_VERIFIED and exposes _sm2542_rows.
This audit-only proof marker is NOT a production feature flag and does NOT
replace textbook/activity-book academic approval or Web/Telegram E2E tests.
"""
from __future__ import annotations

from collections import defaultdict

from rph_standalone.matematik.v60_source_loader import get_lesson, verify_all
from web.matematik_v60_native_rows import is_enabled, parse_lesson


class NativeCoverageUnavailable(RuntimeError):
    """Cannot prove the mapping; caller must keep v60 unreleased."""


def _single_positive_number(value):
    if type(value) is int and 1 <= value <= 117:
        return value
    if type(value) is str and value.isdecimal() and str(int(value)) == value and 1 <= int(value) <= 117:
        return int(value)
    return None


def audit_native_mapping(runtime) -> dict:
    """Return evidence of coverage, never a claim of academic FINAL READY.

    Every source lesson must match exactly one native Telegram PdP key, native
    Lesson number and native SK/SP. Multi-SP, duplicate, missing and orphan
    entries are rejected rather than treated as verified source records.
    """
    if not is_enabled():
        raise NativeCoverageUnavailable("Matematik v60 staging flag is disabled")
    if not getattr(runtime, "CIKGULAJU_MATH_V2599_SOURCE_VERIFIED", False):
        raise NativeCoverageUnavailable("Native DB v26.00 is not confirmed active")
    reader = getattr(runtime, "_sm2542_rows", None)
    if not callable(reader):
        raise NativeCoverageUnavailable("Native PdP reader unavailable")
    if verify_all() != 585:
        raise NativeCoverageUnavailable("585 v60 source lessons failed integrity check")

    result = {"version": "v60", "source_lessons": 585, "matched": 0,
              "per_year": {}, "mapping_ready": False,
              "academic_signoff": False, "runtime_e2e_passed": False}

    for year in range(2, 7):
        expected = {
            n: parse_lesson(get_lesson(year, n), year, n)
            for n in range(1, 118)
        }
        try:
            rows = reader(f"Tahun {year}", "Matematik")
        except Exception as exc:
            raise NativeCoverageUnavailable(f"Cannot read Year {year} native PdP") from exc
        if not isinstance(rows, list) or len(rows) > 5000:
            raise NativeCoverageUnavailable(f"Invalid Year {year} native PdP source")
        groups = defaultdict(list)
        problems = []
        for row in rows:
            if not isinstance(row, dict):
                problems.append("non-dictionary native row")
                continue
            code = row.get("pdp_sequence_code")
            if not isinstance(code, str) or not code.strip() or len(code) > 100:
                problems.append("native row without a valid PdP key")
                continue
            groups[code].append(row)

        # Collect every raw PdP -> Lesson claim *before* validating SP.
        # Otherwise one invalid multi-SP group can be overlooked while a
        # different PdP with the same Lesson is mistakenly counted as matched.
        claimed_by = defaultdict(set)
        for code, group in groups.items():
            numbers = {_single_positive_number(r.get("source_sequence_no")) for r in group}
            if len(numbers) == 1 and None not in numbers:
                claimed_by[next(iter(numbers))].add(code)

        matched = set()
        for code, group in groups.items():
            numbers = {_single_positive_number(r.get("source_sequence_no")) for r in group}
            pairs = {(str(r.get("sk_code") or "").strip(),
                      str(r.get("sp_code") or "").strip()) for r in group}
            if len(numbers) != 1 or None in numbers:
                problems.append(f"{code}: missing or ambiguous Lesson number")
                continue
            number = next(iter(numbers))
            if len(claimed_by[number]) != 1:
                problems.append(f"{code}: duplicate Lesson {number} across native PdP keys")
                continue
            if len(pairs) != 1 or not all(next(iter(pairs))):
                problems.append(f"{code}: missing or multiple SK/SP values")
                continue
            sk, sp = next(iter(pairs))
            if (sk, sp) != (expected[number]["_sk_code"], expected[number]["_sp_code"]):
                problems.append(f"{code}: Year {year} Lesson {number} SK/SP differs from v60")
                continue
            matched.add(number)
        missing = [n for n in range(1, 118) if n not in matched]
        result["per_year"][str(year)] = {
            "source": 117, "native_rows": len(rows), "native_pdp": len(groups),
            "matched": len(matched), "unmatched": len(missing),
            "unmatched_lesson_numbers": missing,
            "conflicts": len(problems), "conflict_samples": problems[:20],
        }
        result["matched"] += len(matched)

    result["mapping_ready"] = (
        result["matched"] == 585
        and all(record["conflicts"] == 0 for record in result["per_year"].values())
    )
    return result
