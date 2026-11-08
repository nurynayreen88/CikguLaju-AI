"""Cross-field tajwid 'mad' type guard across PI Year2-6 (editor HOLD).

Only tests records with exactly one named mad form in the source SP and
ensures its stated objective, induction, activities and PBD do not silently
switch to another named form. A lesson teaching multiple mad forms (review)
is intentionally excluded from this single-target guard. It is NOT an
expert tajwid/ayah-source approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from pi_quality_audit import COUNT, ROOT

# Exact lexical names used in existing SK/SP, Jawi/Arabic script.
KINDS = (
    "صلة قصيرة", "صلة طويلة", "بدل", "عوض", "تمكين",
    "طبيعي", "أصلي", "اصيل", "فرعي", "واجب متصل",
    "جائز منفصل", "عارض للسكون", "لازم", "لين",
)
FIELDS = ("objektif","set_induksi","aktiviti_utama","pentaksiran")
REPAIRED = {"T5-L041","T5-L045","T5-L049"}


def kinds(text):
    return {kind for kind in KINDS if ("مد "+kind) in text}


def audit(root=ROOT):
    root=Path(root)
    rows=[]
    mismatches=[]
    indexed={}
    for year, expected in COUNT.items():
        doc=json.loads((root/f"year{year}.json").read_text(encoding="utf-8"))
        assert doc["year"]==year and doc["ready"] is False
        assert len(doc["records"])==expected
        for row in doc["records"]:
            indexed[row["id"]]=row
            if row["withheld"]:
                assert "fields" not in row
                continue
            assert row["verified_ready"] is False
            fields=row["fields"]
            target=kinds(fields["sp"])
            if len(target)!=1:
                continue
            target=next(iter(target))
            wrong={field:sorted(kinds(fields[field])-{target}) for field in FIELDS}
            wrong={field:v for field,v in wrong.items() if v}
            if wrong:
                mismatches.append({"id":row["id"],"sp_target":target,
                                   "wrong_field_hukum":wrong})
            rows.append({"id":row["id"],"year":year,"sp_target":target,
                         "conflicting_other_mad_count":sum(len(v) for v in wrong.values()),
                         "publication":"HOLD","expert_tajwid_approved":False})
    assert not mismatches,("Source tajwid hukum differs between SP and RPH",mismatches)
    assert len(rows)==30,("Unexpected coverage: investigate source updates",len(rows))
    assert {r["id"] for r in rows}>=REPAIRED
    edits=[]
    for ident in sorted(REPAIRED):
        row=indexed[ident]
        is49=ident=="T5-L049"
        meta=row["staging_y5_tajwid_l049_source_alignment"] if is49 else row["staging_y5_tajwid_mad_iwad_source_alignment"]
        original=meta["original_fields"]
        revised=meta["revised_fields"]
        assert meta["revision"]==(
            "pi-y5-l049-mad-iwad-crossfield-20261108" if is49
            else "pi-y5-l041-l045-mad-iwad-copyedit-20261108")
        assert meta["source_sp_hukum" if is49 else "source_sp_target_hukum"]=="مد عوض"
        assert meta["publication"]=="HOLD" and meta["teacher_ready"] is False
        assert meta["academic_expert_approved"] is False
        assert meta["jawi_orthography_approved"] is False
        assert row["fields"]["sp"].count("مد عوض")>=1
        assert set(original)==set(revised)
        assert all(original[k]!=revised[k] and row["fields"][k]==revised[k]
                   for k in revised)
        assert "مد بدل" in ("\n".join(original.values()))
        assert "مد بدل" not in ("\n".join(revised.values()))
        assert "مد ب عوض" in ("\n".join(original.values()))
        assert "مد ب عوض" not in ("\n".join(revised.values()))
        edits.append({"id":ident,"changed_fields":sorted(revised),
                      "source_sp_unmodified":True,
                      "original_field_text_preserved":True,
                      "expert_approved":False})
    assert [len(x["changed_fields"]) for x in edits]==[2,2,3]
    assert len(indexed)==sum(COUNT.values())==696
    return {
        "scope":"PI Year2-6 single-mad SP lexical cross-field guard only",
        "source_catalog_total":696,
        "single_named_mad_source_lessons_checked":len(rows),
        "conflicting_mad_labels_remaining":len(mismatches),
        "source_corrected_year5_lessons":len(edits),
        "source_corrected_fields":sum(len(x["changed_fields"]) for x in edits),
        "source_rpt_modified":False,
        "expert_tajwid_approvals":0,"teacher_ready":0,
        "release":"NO_GO",
        "rows":rows,"source_corrections":edits,
    }


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=audit()
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("rows","source_corrections")},
                     ensure_ascii=False,indent=2))
