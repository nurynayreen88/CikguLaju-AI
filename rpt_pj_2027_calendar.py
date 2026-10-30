"""Non-destructive RPT PJ 2027 catalogue and calendar resolver.

Data must be exported from the approved Google Sheet tab
'INDEKS PDP 2027 DIKIRA'. No Google API credentials are required at runtime.
This module does not alter the bot database or grant access to RPT.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

SHEET_ID = "1tf6-B6hmA4U6E0fCROcKpxh-B5uLUQOYBt6TZft_7_k"
SHEET_TAB = "INDEKS PDP 2027 DIKIRA"
GROUP_A = frozenset({"KEDAH", "KELANTAN", "TERENGGANU"})
REQUIRED = {"Tarikh", "Negeri", "Kumpulan", "Status PdP Dikira"}
YEAR_COUNTS = {4: 34, 5: 33, 6: 34}


class CalendarDataError(ValueError):
    pass


def read_calendar_csv(path: str | Path, *, strict: bool = True):
    """Read exported Sheet CSV, reject duplicates and wrong state/day counts.

    Returns {(NEGERI, 'YYYY-MM-DD'): record}. Strict mode expects 5,840
    daily records (16 states x 365 dates). Never treats a missing date as PdP.
    """
    records = {}
    states = defaultdict(set)
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED.issubset(reader.fieldnames or ()):
            raise CalendarDataError("Missing required calendar columns")
        for row in reader:
            state = (row["Negeri"] or "").strip().upper()
            raw_date = (row["Tarikh"] or "").strip()
            try:
                day = date.fromisoformat(raw_date)
            except ValueError as exc:
                raise CalendarDataError(f"Invalid date: {raw_date}") from exc
            if day.year != 2027 or not state:
                raise CalendarDataError(f"Unexpected calendar entry: {state}/{raw_date}")
            group = (row["Kumpulan"] or "").strip().upper()
            expected = "A" if state in GROUP_A else "B"
            if group not in {expected, "KUMPULAN " + expected}:
                raise CalendarDataError(f"Wrong group for {state}: {group}")
            key = (state, raw_date)
            if key in records:
                raise CalendarDataError(f"Duplicate calendar date: {key}")
            records[key] = row
            states[state].add(raw_date)
    if strict and (len(states) != 16 or len(records) != 5840 or
                   any(len(days) != 365 for days in states.values())):
        raise CalendarDataError("Incomplete 2027 calendar: expected 16 x 365 days")
    return records


def school_days(records, state: str, start: str, end: str):
    """Return explicitly flagged candidate PdP dates within inclusive bounds."""
    state = state.strip().upper()
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise ValueError("Start must not exceed end")
    found = []
    day = date.fromisoformat(start)
    last = date.fromisoformat(end)
    from datetime import timedelta
    while day <= last:
        key = (state, day.isoformat())
        if key not in records:
            raise CalendarDataError(f"Missing calendar record: {key}")
        status = (records[key].get("Status PdP Dikira") or "").strip().upper()
        if status.startswith("CALON PDP"):
            found.append(day.isoformat())
        day += timedelta(days=1)
    return found


def can_download_rpt(*, is_developer=False, subscription_active=False,
                     rakan_pembangun_active=False):
    """Caller must obtain these flags from existing trusted access checks."""
    return bool(is_developer or subscription_active or rakan_pembangun_active)


def validate_pdp_counts(rows):
    """Validate 34/33/34 lesson slots per state without changing records."""
    counts = defaultdict(set)
    for row in rows:
        state = str(row["Negeri"]).strip().upper()
        year = int(row["Tahun"])
        lesson = int(row["PdP"])
        if year not in YEAR_COUNTS or lesson < 1:
            raise CalendarDataError("Invalid year/PdP")
        if lesson in counts[(state, year)]:
            raise CalendarDataError(f"Duplicate PdP: {state}/{year}/{lesson}")
        counts[(state, year)].add(lesson)
    for (state, year), values in counts.items():
        if values != set(range(1, YEAR_COUNTS[year] + 1)):
            raise CalendarDataError(f"Incomplete PdP sequence: {state}/{year}")
    return len(counts)
