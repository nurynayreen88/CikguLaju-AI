"""Ten high-frequency hand-drafted Jawi closing CANDIDATES for editor review.

This is NOT machine transliteration, expert approval, or teacher-facing content.
The original Rumi source is the key and remains unchanged in year*.json.
Reject drift rather than silently applying a candidate to changed text.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path

from pi_closing_jawi_review_queue import ROOT, build

# Human-drafted starting points only. Spellings, diacritics, punctuation and
# pedagogical suitability all require a qualified Jawi/Pendidikan Islam reviewer.
CANDIDATES = {
    "Murid memperdengarkan bacaan ayat yang ditetapkan dalam objektif; guru membetulkan sebutan dan merekod pencapaian tasmi'.":
        "موريد ممڤردڠركن باچاءن ايات يڠ دتتڤكن دالم اوبجيكتيف؛ ݢورو ممبتولكن سبوتن دان مريكود ڤنچاڤاين تسميع.",
    "Murid membaca dan menulis satu ayat atau teks pendek Jawi; guru menyemak ketepatan ejaan dan susunan ayat.":
        "موريد ممباچ دان منوليس ساتو ايات اتاو تيكس ڤينديق جاوي؛ ݢورو مڽمق كتيڤتن ايجاءن دان سوسونن ايات.",
    "Murid mengenal pasti satu hukum tajwid, memberikan contoh daripada mushaf dan membacanya dengan betul; guru menyemak ketepatan hukum serta bacaan.":
        "موريد مڠنل ڤستي ساتو حكوم تجويد، ممبري چونتوه درڤد مصحف دان ممباچڽ دڠن بتول؛ ݢورو مڽمق كتيڤتن حكوم سرتا باچاءن.",
    "Murid menulis satu contoh Jawi selaras objektif; guru menyemak bentuk dan ejaannya.":
        "موريد منوليس ساتو چونتوه جاوي سلارس اوبجيكتيف؛ ݢورو مڽمق بنتوق دان ايجاءنڽ.",
    "Murid menceritakan satu teladan daripada peristiwa sirah yang dikaji; guru menghubungkan pengajaran dengan kehidupan.":
        "موريد منچريتاكن ساتو تلادن درڤد ڤريستيوا سيره يڠ دكاجي؛ ݢورو مڠهوبوڠكن ڤڠاجرن دڠن كهيدوڤن.",
    "Murid memperdengarkan satu potongan hafazan surah yang ditetapkan; guru menyemak kelancaran dan tajwid.":
        "موريد ممڤردڠركن ساتو ڤوتوڠن حفازن سوره يڠ دتتڤكن؛ ݢورو مڽمق كلنچرن دان تجويد.",
    "Murid merumuskan pengajaran surah serta memberikan satu contoh amalan dalam kehidupan; guru menilai kefahaman dan kaitan jawapan dengan tuntutan ayat.":
        "موريد مروموسكن ڤڠاجرن سوره سرتا ممبري ساتو چونتوه عملن دالم كهيدوڤن؛ ݢورو منيلاي كفهمن دان كاءيتن جواڤن دڠن تونتوتن ايات.",
    "Murid memperdengarkan satu bacaan solat yang ditetapkan atau menunjukkan cara melaksanakannya; guru memberi maklum balas.":
        "موريد ممڤردڠركن ساتو باچاءن صلاة يڠ دتتڤكن اتاو منونجوقكن چارا ملاكساناكنڽ؛ ݢورو ممبري معلوم بالاس.",
    "Murid menyatakan satu amalan adab daripada tajuk dan cara mengamalkannya; guru membuat rumusan.":
        "موريد مڽاتاكن ساتو عملن ادب درڤد تاجوق دان چارا مڠعملكنڽ؛ ݢورو ممبوات روموسن.",
    "Murid membaca dan membina dua perkataan Jawi mengikut bilangan suku kata yang dipelajari; guru membetulkan ejaan.":
        "موريد ممباچ دان ممبينا دوا ڤركاتاءن جاوي مڠيكوت بيلڠن سوكو كات يڠ دڤلاجري؛ ݢورو ممبتولكن ايجاءن.",
}

CSV_FIELDS = (
    "group_id", "lesson_count", "lesson_ids", "original_closing_rumi",
    "candidate_jawi_text", "original_text_sha256",
    "jawi_reviewer", "content_reviewer", "jawi_spelling_verified",
    "source_sp_verified", "word_pdf_verified", "approved",
    "can_publish", "release",
)


def generate(root=ROOT):
    queue = build(root)
    groups = queue["groups"]
    found = {x["original_closing_rumi"] for x in groups}
    assert len(CANDIDATES) == 10 and set(CANDIDATES).issubset(found)
    top10 = groups[:10]
    assert set(CANDIDATES) == {x["original_closing_rumi"] for x in top10}, (
        "Closing frequency distribution has changed; review candidates again"
    )
    records = []
    for group in top10:
        candidate = CANDIDATES[group["original_closing_rumi"]]
        assert candidate and not re.search(r"[A-Za-z]", candidate), (
            "Candidate still contains Rumi letters"
        )
        assert group["original_text_sha256"] and len(group["original_text_sha256"]) == 64
        records.append({
            "group_id": group["group_id"],
            "lesson_count": group["lesson_count"],
            "lesson_ids": group["lesson_ids"],
            "original_closing_rumi": group["original_closing_rumi"],
            "candidate_jawi_text": candidate,
            "original_text_sha256": group["original_text_sha256"],
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
    assert covered == 581
    assert sum(x["lesson_count"] for x in groups[10:]) == 109
    return {
        "purpose": "High-frequency Jawi candidates ONLY, no source changes",
        "all_draft_closings": 690,
        "unique_source_closings": 78,
        "candidate_groups": 10,
        "candidate_covered_lesson_occurrences": covered,
        "remaining_without_candidate": 690 - covered,
        "approved": 0,
        "can_publish": False,
        "academic_quality_percent": None,
        "release": "NO_GO",
        "records": records,
    }


def write(json_file, csv_file, root=ROOT):
    value = generate(root)
    Path(json_file).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    with Path(csv_file).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(value["records"])
    print(json.dumps({k: v for k, v in value.items() if k != "records"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--json", required=True)
    a.add_argument("--csv", required=True)
    args = a.parse_args()
    write(args.json, args.csv)
