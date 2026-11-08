"""Read-only crosswalk candidates; NEVER silently map or release a Math RPH.

The Telegram v25.99 canonical PdP count is not the 117-per-year proposal in
v60. Matching on SP alone, a week or a position cannot approve an RPH.
The crosswalk classifies candidates and ambiguity for human source review.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from rph_standalone.matematik.v60_source_loader import get_lesson
from web.matematik_v60_native_rows import parse_lesson


def make_candidates(year: int, native_rows: list[dict]) -> dict:
    if type(year) is not int or year not in range(2, 7):
        raise ValueError("Only Maths Year 2-6 supported")
    if not isinstance(native_rows, list) or any(not isinstance(r, dict) for r in native_rows):
        raise ValueError("Expected a full list of native Telegram PdP source records")
    sources = defaultdict(list)
    for no in range(1, 118):
        r = parse_lesson(get_lesson(year, no), year, no)
        sources[(r["_sk_code"], r["_sp_code"])].append({
            "lesson": no, "topic": r["Tajuk"], "sp": r["SP"],
        })

    groups = defaultdict(list)
    for row in native_rows:
        key = str(row.get("pdp_sequence_code") or "").strip()
        if not key:
            raise ValueError("Real native PdP source has a missing code")
        groups[key].append(row)

    seen_numbers = defaultdict(set)
    for code, items in groups.items():
        for item in items:
            no = str(item.get("source_sequence_no") or "").strip()
            if no.isdecimal() and int(no) > 0:
                seen_numbers[int(no)].add(code)

    results = []
    for code, items in groups.items():
        numbers = {str(r.get("source_sequence_no") or "").strip() for r in items}
        pairs = {(str(r.get("sk_code") or "").strip(),
                  str(r.get("sp_code") or "").strip()) for r in items}
        unit = str(items[0].get("unit_title") or "").strip()
        native_title = str(items[0].get("pdp_title") or "").strip()
        info = {"pdp_code": code,
                "source_sequence_numbers": sorted(numbers),
                "native_title": native_title,
                "native_unit": unit,
                "sksp": [{"sk": a, "sp": b} for a, b in sorted(pairs)],
                "candidate_v60_lessons": [],
                "status": "NEEDS_MANUAL_MAPPING",
                "approved": False,
                "reason": ""}
        if len(numbers) != 1 or not next(iter(numbers)).isdigit():
            info.update(status="BLOCKED_MISSING_OR_MIXED_NATIVE_NUMBER",
                        reason="Cannot resolve exact native Lesson number")
        elif len(seen_numbers.get(int(next(iter(numbers))), set())) > 1:
            info.update(status="BLOCKED_DUPLICATE_NATIVE_NUMBER",
                        reason="Several PdP keys claim the same native number")
        elif len(pairs) != 1 or not all(next(iter(pairs))):
            info.update(status="BLOCKED_MULTI_SP",
                        reason="One native PdP has multiple or missing SK/SP")
        else:
            pair = next(iter(pairs))
            candidates = sources.get(pair, [])
            info["candidate_v60_lessons"] = candidates
            if not candidates:
                info.update(status="UNMAPPED_NO_EXACT_SKSP",
                            reason="No v60 Lesson has this exact SK/SP")
            elif len(candidates) > 1:
                info.update(status="AMBIGUOUS_DUPLICATE_SKSP",
                            reason="More than one v60 Lesson has the same SK/SP")
            else:
                proposed = candidates[0]["lesson"]
                native_number = int(next(iter(numbers)))
                info.update(
                    status=("EXACT_NUMBER_AND_SKSP_CANDIDATE"
                            if proposed == native_number
                            else "UNIQUE_SKSP_DIFFERENT_NUMBER_CANDIDATE"),
                    reason=("Still requires academic title/activity/textbook evidence "
                            "before anyone approves publication"),
                )
        results.append(info)

    counts = Counter(item["status"] for item in results)
    return {"year": year, "native_pdp_count": len(groups),
            "v60_source_count": 117,
            "status_counts": dict(sorted(counts.items())),
            "approved_count": 0, "academic_signoff": False,
            "candidates": results}


def make_all_candidates(rows_by_year: dict[int, list[dict]]) -> dict:
    all_reports = {str(year): make_candidates(year, rows_by_year[year])
                   for year in range(2, 7)}
    total = Counter()
    for r in all_reports.values():
        total.update(r["status_counts"])
    return {"source": "read-only v25.99 native PdP versus v60 SK/SP",
            "status": "ACADEMIC_HOLD",
            "actual_pdp_total": sum(v["native_pdp_count"] for v in all_reports.values()),
            "v60_lessons": 585,
            "approved_count": 0,
            "status_counts": dict(sorted(total.items())),
            "by_year": all_reports}
