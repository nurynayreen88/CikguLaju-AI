"""Read-only full 342-PdP Sains release gate.

Structural source checks are automated; textbook page/academic and runtime approval
is NEVER inferred from passing CI. No writes to user databases or production.
"""
from __future__ import annotations
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from tools.render_sains_rpt_2027_ab_review_20261106 import ROOT, OUT, EXPECTED
from web.sains_y3_rph_activity_preview_20261106 import source_ledgers

AUDIT_DIR=ROOT/"build/sains_2027_342_pdp_release_audit"
YEARS={2,3,4,5,6}
ISSUE_COLUMNS=[
    "tahun","pdp_code","pdp_number","unit","sk","sp","tajuk",
    "sumber_dskp_sp","rph_word_pdf","rujukan_buku_teks",
    "status_tarikh_rpt","uji_telegram_web","kelulusan_akademik",
    "isu","keputusan"
]

def analyze():
    inv=json.loads((ROOT/"audits/sains_dskp_t2_t5_sp_token_inventory_20261106.json").read_text(encoding="utf-8"))
    y6=json.loads((ROOT/"audits/sains_dskp_t6_sp_token_inventory_20261106.json").read_text(encoding="utf-8"))
    assert set(inv["years"])=={"2","3","4","5"} and len(set(y6["sp_tokens"]))==96
    y3,fixes=source_ledgers()
    assert len(y3)==45 and len(fixes)==12
    ledger=[]
    counts={}
    for year,expected in sorted(EXPECTED.items()):
        path=OUT/f"SAINS_TAHUN_{year}_SOURCE_DRAF.csv"
        with path.open(encoding="utf-8-sig",newline="") as f:
            source=list(csv.DictReader(f))
        if len(source)!=expected:
            raise ValueError(f"Year {year} expected {expected} actual {len(source)}")
        codes=set(inv["years"][str(year)]["sp_tokens"]) if year!=6 else set(y6["sp_tokens"])
        seen=set(); nums=set(); annual=[]
        for row in source:
            code=row["Kod sumber"]
            num=int(row["PdP asal"])
            expected_code=f"SCI-Y{year}-PDP-{num:03d}"
            if code!=expected_code or code in seen or num in nums:
                raise ValueError(f"Duplicate or inconsistent source PdP {year} {code}")
            seen.add(code);nums.add(num)
            sk=row["SK"].strip(); sp=row["SP"].strip()
            if not sk or not sp or not row["Unit"].strip() or not row["Fokus PdP (draf QA)"].strip():
                raise ValueError(f"Missing academic source identity {code}")
            for token in (x.strip() for x in sp.split(",")):
                if token not in codes:
                    raise ValueError(f"SP {token} not in verified-text token inventory for {code}")
                if token.rsplit(".",1)[0]!=sk:
                    raise ValueError(f"SP/SK prefix differs for {code}: {sk} / {token}")
            issues=[]
            if year!=3:
                issues.append("RPH_STANDALONE_UNVERIFIED")
            else:
                if code not in y3:raise ValueError(f"Year3 RPH draft missing {code}")
                issues.append("RPH_YEAR3_DRAFT_ACADEMIC_QA_PENDING")
                if "DSKP_TITLE_CANDIDATE" in row["Catatan QA"]:
                    issues.append("DSKP_TITLE_FIX_AWAITING_REVIEW")
            if year in (4,6):
                issues.append("TEXTBOOK_ACCESS_VISUAL_QA_BLOCKED")
            else:
                issues.append("TEXTBOOK_PAGE_VISUAL_QA_PENDING")
            if year==6:
                issues.append("DSKP_YEAR6_PUBLIC_MIRROR_NOT_OWNER_ORIGINAL")
            if year in (2,3):
                issues.append("DSKP_EDISI3_OPTION_NOT_ALIGNED")
            issues.extend(("RPT_PDP_DATE_UNSCHEDULED",
                           "TELEGRAM_WEB_E2E_DOWNLOAD_UNVERIFIED",
                           "TEACHER_ACADEMIC_APPROVAL_MISSING"))
            output={
                "tahun":year,
                "pdp_code":code,
                "pdp_number":num,
                "unit":row["Unit"],
                "sk":sk,
                "sp":sp,
                "tajuk":row["Fokus PdP (draf QA)"],
                "sumber_dskp_sp":"LEXICAL_TOKEN_MATCH_ONLY",
                "rph_word_pdf":"DRAF_YEAR3_ONLY" if year==3 else "NOT_VERIFIED",
                "rujukan_buku_teks":"BLOCKED_ACCESS" if year in (4,6) else "NEEDS_PAGE_VISUAL_QA",
                "status_tarikh_rpt":"BELUM_DIJADUAL",
                "uji_telegram_web":"NOT_TESTED",
                "kelulusan_akademik":"PENDING",
                "isu":";".join(issues),
                "keputusan":"HOLD",
            }
            annual.append(output);ledger.append(output)
        if nums!=set(range(1,expected+1)):
            raise ValueError(f"Gap in Year{year} source sequence")
        counts[str(year)]={
            "jumlah_pdp":expected,
            "unik_pdp":len(seen),
            "rph_draf_tersedia":expected if year==3 else 0,
            "rph_standalone_belum_disahkan":0 if year==3 else expected,
            "final_ready":0,
            "isu":dict(Counter(i for row in annual for i in row["isu"].split(";"))),
        }
    if len(ledger)!=342 or sum(x["rph_standalone_belum_disahkan"] for x in counts.values())!=297:
        raise ValueError("Unexpected audit total or missing RPH count")
    return ledger,{
        "status":"AUDIT_STRUCTURAL_CI_PASS_NOT_RELEASE",
        "decision":"HOLD",
        "checked_pdp":len(ledger),
        "standalone_rph_year3_draft":45,
        "standalone_rph_remaining_unverified":297,
        "academically_approved":0,
        "year1_kp2027":"EXCLUDED_ALAM_DAN_MANUSIA",
        "source":"v25.82 staging source, DSKP code inventories, draft RPT source CSV",
        "years":counts,
        "release_requirements":[
            "Visual and textual textbook pages checked individually against approved year-specific edition",
            "Standalone RPH Year2/4/5/6 actually generated and audited individually",
            "Year3 45 RPH and 23 boundary cases receive content/teacher approval",
            "Year6 original exact-edition DSKP validated",
            "State holidays and local timetable resolved before PdP-specific calendar dates",
            "Telegram-Web same source and user download smoke tests pass",
            "Backup, rollback and owner approval precede any production integration"
        ],
        "non_destructive":True,
    }

def main():
    rows,summary=analyze()
    AUDIT_DIR.mkdir(parents=True,exist_ok=True)
    with (AUDIT_DIR/"SAINS_342_PDP_RELEASE_GATE_DRAF.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=ISSUE_COLUMNS)
        w.writeheader();w.writerows(rows)
    (AUDIT_DIR/"SUMMARY_HOLD.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_FULL_RELEASE_AUDIT: 342/342 source identities checked, "
          "Year3 draft=45, 297 Year2/4/5/6 RPH unverified, "
          "FINAL_READY=0, decision=HOLD; no database writes")
if __name__=="__main__":main()
