"""Owner-requested 2027 weekly RPT *proposal*, not a class timetable.

Years 2-6 start PdP in Week 01; Year 1 remains its separate transition
programme. Never mutate the original curriculum records or assign a specific
day/period. Preserve source identity, standards, topic and row order.

This is staging-only until academic and timetable verification is complete.
"""
from __future__ import annotations

from copy import deepcopy
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.format_2026_layout_preview import validate_rows

PLAN_STATUS = "OWNER_REQUESTED_WEEKLY_PROPOSAL_NOT_ACADEMIC_SIGNOFF"
# Week 06 may have CNY closures; Week 44 reserved for closing activities.
# Candidate plan uses central A/B week windows, not an actual class timetable.
CANDIDATE_WEEKS = tuple(f"M{i:02d}" for i in range(1, 44) if i != 6)


def _calendar():
    cal = load_calendar_weeks()
    if (cal["A"]["M01"] != ("2027-01-04", "2027-01-07")
            or cal["B"]["M01"] != ("2027-01-04", "2027-01-08")):
        raise ValueError("KPM 2027 Week 1 calendar no longer matches source")
    if any(w not in cal["A"] or w not in cal["B"] for w in CANDIDATE_WEEKS):
        raise ValueError("Proposed calendar weeks absent from central snapshot")
    return cal


def _set_week(row, week, calendar):
    a, b = calendar["A"][week], calendar["B"][week]
    row.update(
        week=week, a_start=a[0], a_end=a[1],
        b_start=b[0], b_end=b[1], week_allocation=PLAN_STATUS,
        class_date_confirmed=False, academic_week_signoff=False,
    )


def move_first_sessions_to_m01(source_rows, *, subject, year, sessions):
    """Move only the first sessions from M02; do not shift remaining weeks.

    Existing M02 keeps at least one PdP. All source records are deep-copied.
    """
    if subject not in ("bahasa_melayu", "pendidikan_islam"):
        raise ValueError("Week 01 source-gap redistribution only for BM/PI")
    if type(year) is not int or not 2 <= year <= 6:
        raise ValueError("Year 1 transition is excluded")
    if type(sessions) is not int or sessions <= 0:
        raise ValueError("A positive first-week PdP allocation is required")
    if not source_rows or source_rows[0].get("week") != "M02":
        raise ValueError("Source Week 02 position changed; refuse guessing")
    source_m02 = 0
    for row in source_rows:
        if row.get("week") == "M02":
            source_m02 += 1
        else:
            break
    if source_m02 <= sessions or any(
        r.get("source_held") for r in source_rows[:sessions]
    ):
        raise ValueError("No safe sourced sessions to redistribute from M02")
    cal = _calendar()
    rows = deepcopy(source_rows)
    for row in rows[:sessions]:
        row.setdefault("source_week", "M02")
        row["week_original_before_owner_plan"] = "M02"
        _set_week(row, "M01", cal)
    validate_rows(subject, year, rows)
    if [r["id"] for r in rows] != [r["id"] for r in source_rows]:
        raise ValueError("Curriculum PdP order changed")
    return rows


def allocate_arabic_weeks(source_rows, *, year):
    """1 PdP in shortened M01; 1–2 per later instructional week.

    Current source has 58/60 ordered PdP with no timetable. Distribute evenly
    over 42 candidate teaching weeks, without claiming weekday or class time.
    """
    if type(year) is not int or not 2 <= year <= 6:
        raise ValueError("Arabic Year 1 transition is excluded")
    if len(source_rows) not in (58, 60) or any(
        row.get("week") or row.get("a_start") or row.get("b_start")
        for row in source_rows
    ):
        raise ValueError("Arabic source timetable is no longer unallocated")
    calendar = _calendar()
    n = len(source_rows)
    # First week one session; spread remaining extra sessions across later
    # 41 week windows with no more than two sessions in any week.
    later = len(CANDIDATE_WEEKS) - 1
    extra = n - len(CANDIDATE_WEEKS)
    if extra < 0 or extra > later:
        raise ValueError("Arabic PdP count exceeds supported weekly capacity")
    quotas = [1] + [
        1 + ((i * extra) // later - ((i - 1) * extra) // later)
        for i in range(1, later + 1)
    ]
    if len(quotas) != len(CANDIDATE_WEEKS) or sum(quotas) != n:
        raise ValueError("Arabic plan incomplete")
    labels = [week for week, count in zip(CANDIDATE_WEEKS, quotas)
              for _ in range(count)]
    rows = deepcopy(source_rows)
    for row, label in zip(rows, labels):
        row["week_original_before_owner_plan"] = ""
        _set_week(row, label, calendar)
        row["note"] = (row["note"].replace(
            "Tarikh A/B belum diperuntukkan. DRAF.",
            "Jadual kelas/masa PdP perlu disesuaikan oleh guru.")
            + " Agihan minggu mengikut turutan PdP; bukan hari kelas yang ditetapkan.")
    validate_rows("bahasa_arab", year, rows)
    return rows


def allocate_rbt_weeks(source_rows, *, year):
    """One project/skill PdP per selected week across the school year.

    Keep 32 distinct PdP and space them across M01..M43, avoiding the
    interrupted M06. Do not overwrite teacher-entered weekly schedules.
    """
    if year not in (4, 5, 6) or type(year) is not int:
        raise ValueError("RBT only Year 4–6")
    if len(source_rows) != 32 or any(
        row.get("week") or row.get("a_start") or row.get("b_start")
        for row in source_rows
    ):
        raise ValueError("RBT source already has a week/teacher allocation")
    calendar = _calendar()
    n = len(source_rows)
    indices = [i * (len(CANDIDATE_WEEKS) - 1) // (n - 1)
               for i in range(n)]
    if len(set(indices)) != n:
        raise ValueError("RBT proposed weekly slots overlapped")
    rows = deepcopy(source_rows)
    for row, i in zip(rows, indices):
        label = CANDIDATE_WEEKS[i]
        row["week_original_before_owner_plan"] = ""
        _set_week(row, label, calendar)
        row["note"] = (row["note"].replace(
            "Tarikh A/B belum dinyatakan dalam sumber; tidak diandaikan.",
            "Jadual sebenar boleh disesuaikan oleh guru.")
            + " Agihan minggu projek mengikut urutan PdP.")
    validate_rows("rbt", year, rows)
    return rows
