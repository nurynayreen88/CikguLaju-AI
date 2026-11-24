"""Compare the actual v26 source to the published SK RPT numbers, read-only.
Never activate an older 696 archive or treat counts as academic equivalence.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path
import sqlite3
from tools.bm_native_v26_navigation_audit import database
from web_v1_dropdown_catalog import _bm_verified_structured_rows
from web.pi_navigation import pi_navigation_unit, is_pi_recitation_session, GENERIC_RPT_ACTIVITIES

# Counts from production mapping fbbf9e122461663f3c3e67df482ee081d8aa9329.
EXPECTED = {"PI": [112, 147, 151, 143, 143], "BM": [164, 165, 165, 166, 165]}

def numbers(rows, field):
    return {int(r[field]) for r in rows if str(r.get(field) or "").isdigit()
            and int(r[field]) > 0}

def main():
    tmp, path = database()
    report = {"status": "QA_ONLY_NOT_ACADEMIC_APPROVAL", "years": {}}
    try:
        with sqlite3.connect(path.resolve().as_uri()+"?mode=ro", uri=True) as con:
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA query_only=ON")
            assert con.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            report["pi_verified_all_years"] = con.execute(
                "SELECT count(*) FROM rpt_entries WHERE subject='Pendidikan Islam' AND verified=1"
            ).fetchone()[0]
            for year in range(2, 7):
                target = f"Tahun {year}"
                pi = [dict(r) for r in con.execute("""
                    SELECT * FROM rpt_entries WHERE subject='Pendidikan Islam'
                    AND year_label=? AND verified=1
                    AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                    ORDER BY sequence_no,id""", (target,))]
                usable, excluded = [], Counter()
                for row in pi:
                    seq = row.get("sequence_no")
                    unit = pi_navigation_unit(row)
                    activity = str(row.get("activity_note") or "").strip()
                    if not unit or len(activity) < 30 or activity.casefold() in GENERIC_RPT_ACTIVITIES:
                        excluded["navigation_or_activity"] += 1
                        continue
                    detail = con.execute("""
                        SELECT * FROM pi_pdp_details_v2591
                        WHERE year_label=? AND pdp_no=? AND verified=1 LIMIT 1
                        """, (target, seq)).fetchone()
                    if detail is None:
                        excluded["missing_verified_jawi_detail"] += 1
                        continue
                    standards = [dict(s) for s in con.execute("""
                        SELECT standard_type,standard_code,standard_text
                        FROM rpt_entry_standards WHERE rpt_entry_id=? AND verified=1
                        """, (row["id"],))]
                    kinds = {s["standard_type"] for s in standards
                             if str(s.get("standard_code") or "").strip()}
                    combined = dict(row)
                    combined.update(dict(detail))
                    if not {"SK","SP"} <= kinds and (standards or not is_pi_recitation_session(combined)):
                        excluded["missing_verified_standard"] += 1
                        continue
                    usable.append(row)
                bm = _bm_verified_structured_rows(path, year)
                groups = defaultdict(list)
                for row in bm:
                    groups[tuple(row[k] for k in ("theme","unit_code","unit_title","topic"))].append(row)
                seq_groups = defaultdict(int)
                unnumbered = ambiguous = 0
                for members in groups.values():
                    seqs = numbers(members, "source_sequence_no")
                    if not seqs: unnumbered += 1
                    elif len(seqs) != 1: ambiguous += 1
                    else: seq_groups[next(iter(seqs))] += 1
                for code, actual, extra in (
                    ("PI", Counter(int(r["sequence_no"]) for r in usable
                                   if str(r.get("sequence_no") or "").isdigit()),
                     {"verified_rows":len(pi),"usable_rows":len(usable),"excluded":dict(excluded)}),
                    ("BM", seq_groups, {"verified_rows":len(bm),"native_groups":len(groups),
                       "unnumbered_groups":unnumbered,"ambiguous_groups":ambiguous}),
                ):
                    expected = set(range(1, EXPECTED[code][year-2]+1))
                    result = {"published_count":len(expected), "distinct_native_numbers":len(actual),
                              "missing_numbers":sorted(expected-set(actual)),
                              "extra_numbers":sorted(set(actual)-expected),
                              "ambiguous_numbers":sorted(n for n,c in actual.items() if c>1), **extra}
                    report["years"][f"{code}:{year}"] = result
                    print(code, year, json.dumps(result, ensure_ascii=False), flush=True)
        out = Path("qa/rpt-native-parity")
        out.mkdir(parents=True, exist_ok=True)
        (out/"report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf8")
    finally:
        tmp.cleanup()

if __name__ == "__main__":
    main()
