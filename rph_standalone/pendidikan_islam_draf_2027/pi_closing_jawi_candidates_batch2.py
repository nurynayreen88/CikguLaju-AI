"""Additional 13 high-frequency Jawi closing CANDIDATES, editor only.

Combines the ten earlier proposals with 13 new manually prepared proposals.
These are NOT approved transliterations, do NOT alter source JSON, and MUST NOT
be connected to Telegram, Web, or the production document generator.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path
from pi_closing_jawi_review_queue import ROOT, build
from pi_closing_jawi_candidates import CANDIDATES, CSV_FIELDS

ADDITIONAL = {
    "Murid menyatakan satu contoh kasih kepada Rasulullah dan tindakan yang boleh diamalkan setiap hari.":
        "موريد مڽاتاكن ساتو چونتوه كاسيه كڤد رسول الله دان تيندقن يڠ بوليه دعملكن ستياڤ هاري.",
    "Murid menyampaikan satu pengajaran hadis yang dipelajari dan menerangkan amalan yang sesuai; guru mengesahkan kefahaman.":
        "موريد مڽمڤايكن ساتو ڤڠاجرن حديث يڠ دڤلاجري دان منرڠكن عملن يڠ سسواي؛ ݢورو مڠسهكن كفهمن.",
    "Murid membezakan satu contoh syarat wajib dengan syarat sah solat; guru menilai kefahaman lisan.":
        "موريد ممبيذاكن ساتو چونتوه شرط واجب دڠن شرط صح صلاة؛ ݢورو منيلاي كفهمن ليسن.",
    "Murid membina satu rangkai kata Jawi daripada perkataan yang dipelajari; guru menyemak padanan serta tulisan.":
        "موريد ممبينا ساتو رڠكاي كات جاوي درڤد ڤركاتاءن يڠ دڤلاجري؛ ݢورو مڽمق ڤادنن سرتا توليسن.",
    "Murid menyebut satu sifat Allah yang dipelajari dan menerangkan maksud atau kesan beriman dengannya; guru mengesahkan jawapan.":
        "موريد مڽبوت ساتو صيفت الله يڠ دڤلاجري دان منرڠكن مقصود اتاو كسن برايمان دڠنڽ؛ ݢورو مڠسهكن جواڤن.",
    "Murid menerangkan satu cara atau syarat beristinjak yang betul; guru membetulkan salah faham melalui soal jawab.":
        "موريد منرڠكن ساتو چارا اتاو شرط براستنجاء يڠ بتول؛ ݢورو ممبتولكن ساله فهم ملالوءي سوال جواب.",
    "Murid menyebut maksud satu nama Allah yang dipelajari dan contoh pengamalannya; guru membimbing rumusan.":
        "موريد مڽبوت مقصود ساتو نام الله يڠ دڤلاجري دان چونتوه ڤڠعملنڽ؛ ݢورو ممبيمبيڠ روموسن.",
    "Murid menyatakan satu fakta tentang malaikat dan kesan keimanan terhadap amalan; guru mengesahkan evidens lisan.":
        "موريد مڽاتاكن ساتو فاکتا تنتڠ ملائكة دان كسن كأيمانن ترهادڤ عملن؛ ݢورو مڠسهكن بوكتي ليسن.",
    "Murid menerangkan satu adab berdoa dan mengamalkannya secara tertib; guru membuat pemerhatian.":
        "موريد منرڠكن ساتو ادب بردعاء دان مڠعملكنڽ سچارا ترتيب؛ ݢورو ممبوات ڤمرهاتين.",
    "Murid menyebut dua adab makan atau minum dan memperagakan satu amalan; guru memberi maklum balas.":
        "موريد مڽبوت دوا ادب ماكن اتاو مينوم دان ممڤراݢاكن ساتو عملن؛ ݢورو ممبري معلوم بالاس.",
    "Murid menyatakan satu teladan amanah Rasulullah dan cara mengamalkannya di sekolah; guru merumus pengajaran.":
        "موريد مڽاتاكن ساتو تلادن امانه رسول الله دان چارا مڠعملكنڽ د سكوله؛ ݢورو مروموس ڤڠاجرن.",
    "Murid menyatakan satu adab bersahabat dan mempraktikkannya melalui contoh situasi; guru merumus.":
        "موريد مڽاتاكن ساتو ادب برصحابت دان ممڤراكتيككنڽ ملالوءي چونتوه سيتواسي؛ ݢورو مروموس.",
    "Murid menyatakan satu contoh teladan Rasulullah dalam persahabatan dan mengaitkannya dengan situasi kelas.":
        "موريد مڽاتاكن ساتو چونتوه تلادن رسول الله دالم ڤرصحابتن دان مڠاءيتكنڽ دڠن سيتواسي كلس.",
}


def generate(root=ROOT):
    queue = build(root)
    groups = queue["groups"]
    assert queue["unique_closings"] == 78 and queue["lesson_count"] == 690
    assert len(CANDIDATES) == 10 and len(ADDITIONAL) == 13
    combined = dict(CANDIDATES)
    assert not set(ADDITIONAL).intersection(CANDIDATES)
    combined.update(ADDITIONAL)
    targets = groups[:23]
    assert set(combined) == {x["original_closing_rumi"] for x in targets}, (
        "Source closure text or frequency changed; editor must regenerate proposals"
    )
    records = []
    for row in targets:
        candidate = combined[row["original_closing_rumi"]]
        assert candidate.strip() and not re.search("[A-Za-z]", candidate), (
            "Some proposed Jawi text contains Roman letters"
        )
        records.append({
            "group_id": row["group_id"],
            "lesson_count": row["lesson_count"],
            "lesson_ids": row["lesson_ids"],
            "original_closing_rumi": row["original_closing_rumi"],
            "candidate_jawi_text": candidate,
            "original_text_sha256": row["original_text_sha256"],
            "jawi_reviewer": None,
            "content_reviewer": None,
            "jawi_spelling_verified": False,
            "source_sp_verified": False,
            "word_pdf_verified": False,
            "approved": False,
            "can_publish": False,
            "release": "NO_GO",
        })
    covered = sum(x["lesson_count"] for x in records)
    assert covered == 635 and 690-covered == 55
    return {
        "purpose": "23 hand-drafted Jawi proposals for review only; source Rumi untouched",
        "all_draft_closings": 690,
        "unique_source_closings": 78,
        "candidate_groups": len(records),
        "candidate_covered_lesson_occurrences": covered,
        "remaining_without_candidate": 690-covered,
        "approved": 0,
        "jawi_spelling_verified": 0,
        "can_publish": False,
        "academic_quality_percent": None,
        "release": "NO_GO",
        "records": records,
    }


def write(json_file, csv_file, root=ROOT):
    result = generate(root)
    Path(json_file).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                               encoding="utf-8")
    with Path(csv_file).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(result["records"])
    print(json.dumps({k: v for k, v in result.items() if k != "records"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--csv", required=True)
    args=p.parse_args()
    write(args.json, args.csv)
