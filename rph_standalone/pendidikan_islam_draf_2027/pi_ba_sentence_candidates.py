"""Produce 174 conditional, source-aware one-sentence editorial proposals.

Never write proposals into the 690 RPH without book-page/exercise verification.
All Jawi is provisional and requires orthography plus subject-matter review.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import json

from pi_ba_match_queue import match_queue, NEEDS_PAGE

TOPIC = {
    "TULIS_JAWI": (
        "لاتيه منوليس جاوي", "menulis Jawi"
    ),
    "BINA_JAWI": (
        "لاتيه ممبينا ڤركاتاءن اتاو ايات جاوي", "membina perkataan/ayat Jawi"
    ),
    "BACA_JAWI": (
        "لاتيه ممباچ دان مڠنل ڤستي ڤركاتاءن جاوي", "membaca/mengenal pasti Jawi"
    ),
    "TAJWID": (
        "لاتيه مڠنل ڤستي حكوم تجويد يڠ دڽاتاكن دالم SP",
        "mengenal pasti hukum tajwid dalam SP"
    ),
    "KEFAHAMAN": (
        "لاتيه كفهمن اية، معني دان ڤڠاجرن سورة دالم SP",
        "kefahaman ayat, makna dan pengajaran surah dalam SP"
    ),
    "AKIDAH": (
        "لاتيه ڤادانن مقصود دان كسن كأيمانن بركاءيتن تاجوق SP",
        "akidah: maksud dan kesan iman yang ditetapkan SP"
    ),
    "IBADAH": (
        "لاتيه منييلاي شرط دان تاتاچارا عباده بركاءيتن SP",
        "ibadah: syarat, hukum atau tertib amalan dalam SP"
    ),
    "SIRAH": (
        "لاتيه مڽوسون ڤريستيوا دان اعتبار سيره دالم SP",
        "sirah: susunan peristiwa serta iktibar dalam SP"
    ),
    "ADAB": (
        "لاتيه مميليه عملن برادب دالم سيتواسي هارين مڠيكوت SP",
        "adab: mengaplikasi tindakan dalam situasi yang dipelajari"
    ),
    "HADIS": (
        "لاتيه مڠهورايكن تونتوتن حديث يڠ دتتڤكن دالم SP",
        "hadis: pengajaran hadis dalam SP tanpa mereka matan"
    )
}


def sentence_candidates(root=None):
    base=match_queue(root=root)
    rows=[]
    for r in base["rows"]:
        if r["disposition"] != NEEDS_PAGE:
            continue
        focus=r["learning_focus"]
        jw,rumi=TOPIC[focus]
        year=r["year"]
        # Notes deliberately avoid any printed page or claimed exercise ID.
        conditional=(
            f"جك لاتيه يڠ سسواي دڠن SP تله دسمق دالم بوکو اکتيۏيتي "
            f"ڤنديديقن اسلام تاهون {year}، موريد ملڠکڤکن {jw}؛ "
            "ݢورو مڽمق جاواڤن موريد اونتوق ڤنتكسيرن."
        )
        rows.append({
            "lesson_id": r["id"],
            "year": year,
            "sp_original": r["sp_original"],
            "learning_focus": focus,
            "reviewer_hint": r["suggested_exercise_to_check"],
            "candidate_jawi_one_sentence": conditional,
            "candidate_rumi_topic": rumi,
            "not_teacher_facing": True,
            "book_printed_page": None,
            "book_exercise_id": None,
            "book_exercise_verified": False,
            "sp_and_exercise_alignment_verified": False,
            "jawi_checked_by_expert": False,
            "a4_render_checked": False,
            "injected_into_rph": False,
            "release": "HOLD",
        })
    count=Counter(x["learning_focus"] for x in rows)
    assert len(rows) == 174 and len({x["lesson_id"] for x in rows})==174
    assert sum(x["learning_focus"].endswith("_JAWI") for x in rows)==73
    assert all(x["injected_into_rph"] is False and x["book_printed_page"] is None for x in rows)
    return {
        "subject": "Pendidikan Islam",
        "proposal_count": len(rows),
        "jawi_priority_count": 73,
        "by_skill": dict(sorted(count.items())),
        "verified_page_count": 0,
        "ready_rph_count": 0,
        "status": "STAGING_EDITOR_ONLY",
        "rows":rows,
    }


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args=p.parse_args()
    a=sentence_candidates()
    Path(args.output).write_text(json.dumps(a,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in a.items() if k!="rows"},ensure_ascii=False,indent=2))
