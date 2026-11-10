"""Year4/5 2027 Sains annual RPT from complete original 2017 DSKP source SP.

Replace the truncated v25.82 79/83-row *preview* with all 91/95 official
standards in a separate, explicitly staged 88/116-PdP plan. The number of
teaching sessions is an OWNER target, not a claim that KPM prescribed a
one-SP/one-PdP timetable or verified the linked legacy RPH. Original PDFs and
the Web's live 56 PDF set remain untouched pending curriculum signoff.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows
from rpt_2027.common.week1_owner_plan_20261110 import CANDIDATE_WEEKS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rpt_2027/sains/kssr2017_y4_y5_186_official_sp_source_extraction_20261107_DRAF.json"
OUT = ROOT / "staging/rpt_2027_seragam_2026/sains_kssr2017_88_116_full_dskp_source_candidate"
SOURCE_COUNTS = {4: 91, 5: 95}
PDP_TARGETS = {4: 88, 5: 116}
PLAN_STATUS = "ALL_OFFICIAL_SOURCE_SP_COVERED_NOT_RPH_ACADEMIC_SIGNOFF"


def _source(year: int):
    if type(year) is not int or year not in SOURCE_COUNTS:
        raise ValueError("Only Sains Years 4-5 KSSR2017 source supported")
    obj = json.loads(SOURCE.read_text("utf-8"))
    if (obj.get("total_official_sp") != 186 or
        obj.get("academic_release_ready") is not False or
        obj.get("ready_for_web_telegram") is not False):
        raise ValueError("Source 186-SP release gate or count changed")
    info = obj.get("source", {})
    if (info[str(year)]["official_sp_count"] != SOURCE_COUNTS[year] or
        info[str(year)]["rpt_pdp_mapping_approved"] is not False):
        raise ValueError("DSKP source status unexpected")
    rows = [deepcopy(r) for r in obj["rows"] if r["year"] == year]
    if len(rows) != SOURCE_COUNTS[year]:
        raise ValueError("Incomplete Year-specific original DSKP SK/SP index")
    seen = set()
    for row in rows:
        code = row.get("sp_code", "")
        sk = row.get("sk_code", "")
        text = row.get("sp_text_source_extract_UNVERIFIED", "")
        if not code.startswith(sk + ".") or code in seen or len(text.strip()) < 15:
            raise ValueError(f"Duplicate/bad DSKP SP row: {year}/{code}")
        if row.get("visual_signoff") is not False:
            raise ValueError("Source visual approval changed unexpectedly")
        if not isinstance(row.get("original_pdf_page"), int):
            raise ValueError("Missing independently cited original PDF page")
        seen.add(code)
    return rows


def _groups_y4(rows):
    """Pair exactly three related adjacent SPs without dropping a standard."""
    index_candidates = [
        i for i in range(len(rows) - 1)
        if rows[i]["sk_code"] == rows[i + 1]["sk_code"]
        and rows[i]["sk_code"] != "1.1"
    ]
    targets = (len(rows)//4, len(rows)//2, 3*len(rows)//4)
    chosen = []
    for aim in targets:
        options = [i for i in index_candidates if
                   all(abs(i - j) > 1 for j in chosen)]
        if not options:
            raise ValueError("No safe adjacent within-SK DSKP SP grouping")
        chosen.append(min(options, key=lambda i: (abs(i-aim), i)))
    merged = set(chosen)
    output = []
    i = 0
    while i < len(rows):
        if i in merged:
            output.append([rows[i], rows[i+1]])
            i += 2
        else:
            output.append([rows[i]])
            i += 1
    if len(output) != PDP_TARGETS[4]:
        raise ValueError("Year4 source 91 SP -> 88 PdP plan incomplete")
    return output


def _groups_y5(rows):
    """21 additional sourced-SP practice/PBD sessions, no fabricated standards."""
    extra = PDP_TARGETS[5] - len(rows)
    if extra != 21:
        raise ValueError("Year5 source target changed")
    repeated_indices = {
        (i * (len(rows)-1)) // (extra-1)
        for i in range(extra)
    }
    if len(repeated_indices) != extra:
        raise ValueError("Year5 PBD repetition positions collided")
    output = []
    for i, record in enumerate(rows):
        output.append([record])
        if i in repeated_indices:
            output.append([record])
    if len(output) != PDP_TARGETS[5]:
        raise ValueError("Year5 source 95 SP -> 116 PdP plan incomplete")
    return output


def _week_labels(n: int):
    if n < 2 * len(CANDIDATE_WEEKS):
        raise ValueError("Annual PdP below two per instructional week")
    later = len(CANDIDATE_WEEKS) - 1
    extra = n - 2*len(CANDIDATE_WEEKS)
    if not 0 <= extra <= later:
        raise ValueError("Annual PdP exceeds 3/week scheduling proposal")
    quotas = [2] + [
        2 + ((i*extra)//later - ((i-1)*extra)//later)
        for i in range(1, later+1)
    ]
    if sum(quotas)!=n or any(not 2<=c<=3 for c in quotas):
        raise ValueError("Scheduling quotas invalid")
    return [w for w,c in zip(CANDIDATE_WEEKS, quotas) for _ in range(c)]


def annual_source_plan(year: int):
    original = _source(year)
    grouped = _groups_y4(original) if year==4 else _groups_y5(original)
    weeks = _week_labels(len(grouped))
    master = load_calendar_weeks()
    output=[]
    prior_code = None
    observed=[]
    for n,(group,week) in enumerate(zip(grouped,weeks),1):
        major = int(group[0]["sk_code"].split(".")[0])
        if any(int(item["sk_code"].split(".")[0])!=major for item in group):
            raise ValueError("Do not combine SP across textbook units")
        if week not in master["A"] or week not in master["B"]:
            raise ValueError("Week outside verified A/B calendar snapshot")
        sks=list(dict.fromkeys(g["sk_code"] for g in group))
        if len(sks)!=1:
            raise ValueError("Combined SP must have the same sourced SK")
        codes=[g["sp_code"] for g in group]
        observed.extend(codes)
        special = bool(prior_code == codes[0])
        prior_code = codes[0]
        names={g["sk_title_source"] for g in group}
        if len(names)!=1:
            raise ValueError("Source SK titles differ within combined lesson")
        title=next(iter(names))
        a=master["A"][week];b=master["B"][week]
        # Show the actual SP learning focus, not the same unit heading in
        # every single PdP. The full original statement remains in SP.
        focus = group[0]["sp_text_source_extract_UNVERIFIED"].strip()
        if not focus:
            raise ValueError("Missing original DSKP SP teaching focus")
        topic = ("Pengukuhan / PBD: " if special else "") + focus[:115]
        note=("PBD: kumpulkan evidens melalui pemerhatian, respons murid "
              "dan hasil tugasan berdasarkan SP " + " / ".join(codes) + ".")
        row=dict(id=f"{n:03d}",
                 week=week,a_start=a[0],a_end=a[1],
                 b_start=b[0],b_end=b[1],
                 unit=f"Unit {major}: {title}",
                 topic=topic,
                 sk=sks[0],sp=" / ".join(codes),
                 sk_display=sks[0]+" — "+title,
                 sp_display="\n".join(
                     x["sp_code"]+" — "+x["sp_text_source_extract_UNVERIFIED"]
                     for x in group),
                 note=note,
                 source_original_pdf_pages=[g["original_pdf_page"] for g in group],
                 source_official_sp_codes=codes,
                 curriculum_source="KSSR2017_ORIGINAL_PDF_186_SP_INDEX",
                 academic_release_approved=False,
                 teacher_approved=False,
                 original_sp_text_visual_signoff=False,
                 rph_2027_crosswalk_verified=False,
                 week_allocation=PLAN_STATUS,
                 class_day_time_confirmed=False)
        output.append(row)
    if len(output)!=PDP_TARGETS[year]:
        raise ValueError("Wrong owner-target RPT annual PdP count")
    counts=Counter(observed)
    expected={x["sp_code"] for x in original}
    if set(counts)!=expected or any(c!=1 for c in counts.values()) and year==4:
        raise ValueError("Sourced original SP lost or illegally duplicated")
    if year==5 and sum(c-1 for c in counts.values())!=21:
        raise ValueError("Year5 extra practice sessions were not source grounded")
    if output[0]["week"]!="M01" or int(output[0]["unit"].split(":")[0][5:])!=1:
        raise ValueError("Missing official Unit1 at Week01")
    validate_rows("sains",year,output)
    return output


def build_all(destination=OUT):
    out=Path(destination)
    result=[]
    for year in (4,5):
        rows=annual_source_plan(year)
        path=out/f"CIKGULAJU_RPT_SAINS_TAHUN_{year}_2027_{len(rows)}_PDP_KSSR2017_PENUH_SOURCES_STAGING.pdf"
        build_preview("sains",year,rows,path,max_span_rows=2)
        result.append((year,len(rows),path))
    return result


if __name__=="__main__":
    for y,n,path in build_all():
        print("SOURCE_GROUNDED_SAINS",y,n,path,"academic_final=false",flush=True)
