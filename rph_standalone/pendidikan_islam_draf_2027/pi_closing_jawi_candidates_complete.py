"""ALL 78 distinct Rumi closings have Jawi editorial CANDIDATES; no approval.

This is a *draft review pack* only. Existing RPH original Rumi remains untouched.
Content specialists MUST check language, Jawi spelling, theology, pedagogy,
SP/DSKP and real Word/PDF rendering before any candidate can replace text.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path

from pi_closing_jawi_review_queue import ROOT, build
from pi_closing_jawi_candidates_batch2 import generate as generate_23
from pi_closing_jawi_candidates import CSV_FIELDS

# For the remaining 55 single-use closings, use exact source Lesson identity
# as editor lookup; an assertion below rejects mismatched source/usage.
REMAINING = {
    "T4-L051": "موريد ملافظكن بهاݢين اذان اتاو اقامة يڠ دڤلاجري دان ممبريكن جوابنڽ؛ ݢورو ممبتولكن لفظ.",
    "T2-L023": "موريد ممباچ دوا چونتوه كليمه يڠ مڠندوڠي مد اصلي؛ ݢورو مڽمق حكوم دان قدر ڤنجڠ باچاءن.",
    "T3-L075": "موريد ممباچ سمولا ڤتيقن حديث كاسيه سايڠ دان مڽاتاكن ترجمهڽ؛ ݢورو مڽمق باچاءن دان مقصود.",
    "T3-L011": "موريد ممبري چونتوه تيندقن يڠ ممبوقتيكن كأيمانن كڤد الله العليم دان الحكيم؛ ݢورو ممبتولكن چونتوه يڠ كورڠ تڤت.",
    "T3-L083": "موريد ممبري ساتو چونتوه ادب ترهادڤ اورڠ لبيه مودا اتاو لبيه توا؛ ݢورو منيلاي چونتوه دان مڠاءيتكنڽ دڠن عملن هارين.",
    "T6-L142": "موريد ممبريكن ساتو چونتوه ادب منجاݢ هرتا بندا اتاو كمودهن عوام؛ ݢورو منيلاي چونتوه دان ممبريكن معلوم بالاس.",
    "T6-L011": "موريد ممبريكن ساتو چونتوه باݢي جنيس حكوم دالم اسلام يڠ تله دڤلاجري؛ ݢورو مڽمق ڤڠكلسن.",
    "T4-L107": "موريد ممبيذاكن روكون دان سنت ڤواسا رمضان مڠݢوناكن چونتوه؛ ݢورو مڽمق ڤڠكلسن.",
    "T5-L099": "موريد ممبينچڠكن چونتوه دان كسن شيريك سچارا ريڠكس؛ ݢورو منيلاي الاسن يڠ دسامڤايكن.",
    "T3-L079": "موريد ممڤردڠركن باچاءن حديث سرتا منرڠكن مقصود مڠاسيهي يڠ مودا دان مڠحرمتي يڠ توا؛ ݢورو ممبري معلوم بالاس.",
    "T2-L080": "موريد ممڤردڠركن دوا چونتوه باچاءن نون اتاو ميم برسبدو؛ ݢورو مڽمق دڠوڠ دان حكوم تجويد.",
    "T4-L055": "موريد ممڤردڠركن ساتو بهاݢين اذان اتاو اقامة دالم اکتيويتي برڤاسڠن؛ ݢورو منيلاي لفظ دان جوابن.",
    "T3-L103": "موريد مناماكن كتاب الله يڠ دڤلاجري سرتا ممباچ سمولا دليل كأيمانن كڤد كتاب؛ ݢورو ممبريكن ڤمبتولن.",
    "T5-L134": "موريد منرڠكن چونتوه ڤربواتن سيحير دان كسنڽ سچارا ليسن؛ ݢورو منيلاي كتيڤتن ايسي سرتا الاسن.",
    "T5-L043": "موريد منرڠكن مقصود هاري اخيرت دان ممباچ سمولا دليل بركاءيتن؛ ݢورو ممبري ڤمبتولن.",
    "T4-L095": "موريد منرڠكن مقصود كفور بسرطا ساتو چونتوه يڠ دبينچڠكن؛ ݢورو ممبتولكن فهمن يڠ كورڠ تڤت.",
    "T3-L003": "موريد منرڠكن مقصود نام الله العليم دان الحكيم سچارا ليسن؛ ݢورو مڽمق جوابن دان ممبري معلوم بالاس برداسركن اوبجيكتيف.",
    "T4-L134": "موريد منرڠكن مقصود نفاق دان ساتو چونتوه يڠ دڤلاجري؛ ݢورو مڠسهكن جوابن ملالوءي سوال جواب.",
    "T5-L095": "موريد منرڠكن مقصود شيريك دان ساتو چونتوه يڠ دڤلاجري؛ ݢورو ممبتولكن ساله فهم برداسركن ايسي ڤدڤ.",
    "T6-L134": "موريد منرڠكن ڤركارا يڠ بوليه مڽببكن ردة برداسركن ڤمبلاجرن؛ ݢورو ممبتولكن ككليروان.",
    "T5-L019": "موريد منرڠكن ڤركارا يڠ ممبطلكن تيمم سرتا ساتو كڤنتيڠنڽ؛ ݢورو مڽمق چونتوه يڠ دبريكن.",
    "T6-L007": "موريد منرڠكن ساتو كڤنتيڠن برايمان كڤد الله الهادي دان العدل؛ ݢورو منيلاي هوراين.",
    "T4-L007": "موريد منرڠكن ساتو كڤنتيڠن برايمان كڤد نام الله العظيم دان الحميد؛ ݢورو منيلاي هوراين ريڠكس.",
    "T5-L007": "موريد منرڠكن ساتو كڤنتيڠن برايمان كڤد نام الله الملك دان الحسيب؛ ݢورو منيلاي ملالوءي سوال جواب.",
    "T4-L019": "موريد منرڠكن ساتو كڤنتيڠن برسوچي دان ممبنديڠكن چارا مڽوچيكن نجيس؛ ݢورو مڠسهكن جوابن.",
    "T6-L099": "موريد منرڠكن ساتو كسن عملن خرافات دان چارا منجاءوهينڽ؛ ݢورو منيلاي چادڠن موريد.",
    "T4-L099": "موريد منرڠكن ساتو كسن كفور دان ممبري الاسن ترهادڤ سيتواسي يڠ دبينچڠكن؛ ݢورو منيلاي حجه.",
    "T6-L087": "موريد منرڠكن ساتو ڤونچا دان ساتو كسن رسواه؛ ݢورو منيلاي كفهمن ملالوءي سوال جواب.",
    "T3-L015": "موريد مڠكلسكن چونتوه حدث دان مڽاتاكن حكوم برسوچي؛ ݢورو منيلاي ڤڠكلسن ملالوءي سوال جواب ريڠكس.",
    "T4-L011": "موريد مڠكلسكن چونتوه نجيس مڠيكوت جنيسڽ دان مڽبوت چارا مڽوچيكنڽ؛ ݢورو مڽمق كتيڤتن.",
    "T6-L015": "موريد مڠكلسكن ڤربواتن كڤد واجب، سنت، مكروه، حرام اتاو هاروس؛ ݢورو ممبتولكن ڤڠكلسن.",
    "T4-L138": "موريد منيلاي ساتو سيتواسي بركاءيتن چيري اورڠ برايمان اتاو منافق؛ ݢورو منليتي الاسن دان ممبتولكنڽ.",
    "T5-L015": "موريد منونجوقكن سمولا ساتو لڠكه تيمم يڠ تله دڤلاجري؛ ݢورو منيلاي عملي برداسركن سناراي سمق.",
    "T6-L019": "موريد مڽاتاكن چونتوه عملن برداسركن حكوم يڠ دڤلاجري دان كڤنتيڠنڽ؛ ݢورو مڽمق جوابن.",
    "T3-L099": "موريد مڽاتاكن مقصود برايمان كڤد كتاب الله دان ممباچ سمولا دليل يڠ دڤلاجري؛ ݢورو مڽمق جوابن.",
    "T5-L130": "موريد مڽاتاكن مقصود دان حكوم سيحير سرتا ساتو چونتوه يڠ دبينچڠكن؛ ݢورو مڽمق جوابن.",
    "T6-L095": "موريد مڽاتاكن مقصود خرافات سرتا ساتو چونتوه يڠ دڤلاجري؛ ݢورو ممبتولكن ساله فهم.",
    "T4-L003": "موريد مڽاتاكن مقصود نام الله العظيم دان الحميد، كمودين ݢورو مڽمق جوابن برداسركن اوبجيكتيف.",
    "T5-L003": "موريد مڽاتاكن مقصود نام الله الملك دان الحسيب سرتا حكومڽ؛ ݢورو مڽمق جوابن ليسن.",
    "T6-L003": "موريد مڽاتاكن مقصود نام الله الهادي دان العدل سرتا حكومڽ؛ ݢورو مڽمق جوابن.",
    "T4-L103": "موريد مڽاتاكن مقصود ڤواسا رمضان دان حكومڽ؛ ݢورو مڽمق جوابن برسام كلس.",
    "T6-L043": "موريد مڽاتاكن مقصود قضاء دان قدر سرتا ممباچ دليل بركاءيتن؛ ݢورو ممبتولكن جوابن.",
    "T6-L130": "موريد مڽاتاكن مقصود ردة دان حكوم يڠ تله دڤلاجري؛ ݢورو مڽمق جوابن سچارا برهمه.",
    "T4-L043": "موريد مڽاتاكن ڤربيذاءن نبي دان رسول سرتا ممباچ دليل يڠ دڤلاجري؛ ݢورو ممبتولكن جوابن.",
    "T4-L111": "موريد مڽاتاكن ڤركارا يڠ ممبطلكن ڤواسا سرتا ساتو كڤنتيڠنڽ؛ ݢورو مڽمق جوابن.",
    "T3-L007": "موريد مڽاتاكن ساتو كسن برايمان كڤد الله العليم دان الحكيم؛ ݢورو منيلاي كتيڤتن هوراين ملالوءي سوال جواب.",
    "T5-L011": "موريد مڽبوت مقصود تيمم دان سبب يڠ مڠهاروسكنڽ؛ ݢورو ممبتولكن جوابن برداسركن ايسي ڤلاجرن.",
    "T4-L047": "موريد مڽبوت ڤرانن رسول سرتا ساتو كڤنتيڠن برايمان كڤد رسول؛ ݢورو مڽمق ملالوءي سوال جواب.",
    "T3-L107": "موريد مڽنارايكن كسن برايمان كڤد كتاب الله سرتا ساتو تيندقن بركاءيتن؛ ݢورو منيلاي دڠن سوال جواب.",
    "T6-L138": "موريد مڽنارايكن كسن ردة دان لڠكه منجاݢ عقيدة؛ ݢورو مڽمق كسسواين جوابن.",
    "T5-L047": "موريد مڽنارايكن نام لاءين هاري اخيرت سرتا ساتو كڤنتيڠن برايمان كڤداڽ؛ ݢورو مڽمق جوابن برتوليس.",
    "T6-L047": "موريد مڽنارايكن ساتو كڤنتيڠن برايمان كڤد قضاء دان قدر سرتا ساتو تيندقن بركاءيتن؛ ݢورو مڽمق.",
    "T3-L019": "موريد مڽنارايكن ساتو سبب حدث بسر دان ساتو لارڠن كتيك برحدث بسر؛ ݢورو مڽمق كتيڤتن جوابن.",
    "T4-L015": "موريد مڽوسون سمولا لڠكه مڽوچيكن جنيس نجيس يڠ دڤلاجري؛ ݢورو مڽمق اوروتن ملالوءي كاد لڠكه.",
    "T3-L023": "موريد مروموسكن چارا برسوچي درڤد حدث بسر دان ساتو كڤنتيڠن مندي واجب؛ ݢورو ممبتولكن توروتن اتاو فاكـتا.",
}


def generate(root=ROOT):
    queue = build(root)
    initial = generate_23(root)
    assert queue["lesson_count"] == 690 and queue["unique_closings"] == 78
    assert initial["candidate_groups"] == 23 and initial["candidate_covered_lesson_occurrences"] == 635
    remaining = queue["groups"][23:]
    assert len(remaining) == 55 and len(REMAINING) == 55
    assert set(REMAINING) == {x["lesson_ids"] for x in remaining}, (
        "One-use Rumi source identities changed; do not silently remap"
    )
    records = list(initial["records"])
    for group in remaining:
        candidate = REMAINING[group["lesson_ids"]]
        assert group["lesson_count"] == 1 and candidate.strip()
        assert not re.search(r"[A-Za-z]", candidate), (
            "Rumi letters present in proposed Jawi for " + group["lesson_ids"]
        )
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
    assert len(records) == 78
    assert len({x["group_id"] for x in records}) == 78
    assert sum(x["lesson_count"] for x in records) == 690
    assert all(x["can_publish"] is False and x["approved"] is False for x in records)
    return {
        "purpose": "Complete Jawi candidate drafts only; no academic certification or runtime switch",
        "all_draft_closings": 690,
        "unique_source_closings": 78,
        "candidate_groups": 78,
        "candidate_covered_lesson_occurrences": 690,
        "remaining_without_candidate": 0,
        "approved": 0,
        "jawi_spelling_verified": 0,
        "can_publish": False,
        "academic_quality_percent": None,
        "release": "NO_GO",
        "records": records,
    }


def write(json_file, csv_file, root=ROOT):
    value = generate(root)
    Path(json_file).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n",
                               encoding="utf-8")
    with Path(csv_file).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(value["records"])
    print(json.dumps({k: v for k, v in value.items() if k != "records"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--csv", required=True)
    args=p.parse_args()
    write(args.json, args.csv)
