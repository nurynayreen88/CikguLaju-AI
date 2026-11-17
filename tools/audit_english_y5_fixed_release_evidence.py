"""Join isolated source and layout checks for the 151 fixed SOW Year 5 lessons."""

from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

from tools.audit_english_2_6_release_status_20261104 import OFFICIAL_INDEX, _check
from tools.audit_english_y5_sow_printed_page_citations_20261105 import INDEX as PAGES_INDEX
from tools.audit_english_y5_sow_printed_page_citations_20261105 import run as check_citations
from tools.verify_english_800_native_pdf_contract_20261104 import OUTPUT as NATIVE_OUTPUT
from tools.verify_english_y4_y5_draft_a4 import OUT as WORD_OUTPUT
from web.english_y5_standalone_runtime import CHOICE_LESSONS, LESSON_ROOT, approved_for_telegram

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "english_y5_fixed_release_evidence"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    official = read_json(OFFICIAL_INDEX)["lessons"]
    pages = read_json(PAGES_INDEX)["printed_pages_by_lesson_1_to_160"]
    book_audio = read_json(
        ROOT / "audits/english_y5_all_87_sow_audio_refs_to_drive_file_ids_20261105.json"
    )
    audio_lessons = {
        item["lesson"]: "; ".join(
            f"{track['cd']}-{track['track']:02d}" for track in item["tracks"]
        ) for item in book_audio["lesson_audio_candidates"]
    }
    book_sample = read_json(
        ROOT / "audits/english_y5_l029_l030_original_sow_tb_sb_wb_audio_sources_20261105.json"
    )
    book_review_hashes = {
        (row["lesson"], row["source_sha256"]):
        "audits/english_y5_l029_l030_original_sow_tb_sb_wb_audio_sources_20261105.json"
        for row in book_sample["word_a4_ci_evidence"]["lessons"]
    } if book_sample["gates"]["printed_book_activity_verified"] else {}
    book_review = read_json(ROOT / "audits/english_y5_standalone_printed_book_review_20261117.json")
    book_review_hashes.update({
        (row["lesson"], row["source_sha256"]): book_review["evidence"]
        for row in book_review["lessons"]
    })
    citations = check_citations()
    missing_citations = set(citations["lessons_without_explicit_printed_page"])
    wrong_citations = {item["lesson"] for item in citations["mismatches"]}
    word = {r["lesson"]: r for r in read_json(WORD_OUTPUT / "year5/report.json")["lessons"]}
    native = {
        r["lesson"]: r for r in read_json(NATIVE_OUTPUT / "year5/native_pdf_report.json")["results"]
    }
    fixed = sorted(set(range(1, 161)) - CHOICE_LESSONS)
    if set(word) != set(fixed) or not set(fixed).issubset(native):
        raise ValueError("The Word and PDF reports must cover all 151 fixed Year 5 Lessons")

    rows = []
    for n in fixed:
        source = official[f"5/{n}"]
        match = _check(5, n, source)
        word_doc, pdf_doc = word[n], native[n]
        track_labels = audio_lessons.get(n, "")
        source_hash = sha256((LESSON_ROOT / f"lesson_{n:03d}.md").read_bytes()).hexdigest()
        book_evidence = book_review_hashes.get((n, source_hash), "")
        rows.append({
            "lesson": n,
            "topic": source["topic"],
            "sp_utama": source["main_ls"],
            "sp_pelengkap": source["complementary_ls"],
            "sow_muka_surat_bercetak": pages[n - 1],
            "petikan_halaman_dalam_rph": (
                "tidak sepadan" if n in wrong_citations
                else "tiada dalam sumber RPH" if n in missing_citations
                else "sepadan"
            ),
            "padanan_sp_dan_medan_rph": "lulus" if not match["failures"] else "gagal",
            "word_a4_satu_halaman": word_doc["pages"] == 1 and word_doc["a4"],
            "pdf_native_a4_satu_halaman": pdf_doc.get("pages") == 1 and bool(pdf_doc.get("a4")),
            "trek_bernombor_dalam_sow": track_labels,
            "status_audio": "semak kandungan dan tugas" if track_labels else "semak keperluan dalam rancangan",
            "status_buku": (
                "bukti semakan buku tersedia bagi sumber ini" if book_evidence
                else "semak bukti aktiviti bagi versi satu Lesson"
            ),
            "bukti_semakan_buku": book_evidence,
            "sumber_sha256": source_hash,
            "kelulusan_penerbitan_direkod": approved_for_telegram(n),
        })
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "English_SK_Year_5_semakan_151_lesson.csv").open(
            "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter()
    for row in rows:
        counts["lesson"] += 1
        counts["source_mapping"] += row["padanan_sp_dan_medan_rph"] == "lulus"
        counts["word_a4"] += row["word_a4_satu_halaman"]
        counts["native_pdf_a4"] += row["pdf_native_a4_satu_halaman"]
        counts["numbered_audio_lessons"] += bool(row["trek_bernombor_dalam_sow"])
        counts["book_review_with_source_hash"] += bool(row["bukti_semakan_buku"])
        counts["release_approvals"] += row["kelulusan_penerbitan_direkod"]
    print("YEAR5_FIXED_RELEASE_EVIDENCE", json.dumps(dict(counts), sort_keys=True))
    notes = (
        "Semakan English SK Year 5 2027\n\n"
        "CSV memautkan setiap Lesson kepada SP SOW dan pengenalan kandungan sumber. "
        "RPH Word dan salinan PDF semakan boleh dibuka mengikut nombor Lesson. "
        "Kiraan PDF native datang daripada ujian setempat penjana ReportLab.\n\n"
        "Kandungan buku, audio yang digunakan dan muat turun akaun guru diperiksa secara berasingan. "
        "Salinan audit ini tidak memberikan kelulusan penerbitan.\n"
    )
    (OUT / "BACA_DULU.txt").write_text(notes, encoding="utf-8")
    if counts["source_mapping"] != len(fixed):
        raise SystemExit("Year 5 source mapping has unresolved Lesson rows")


if __name__ == "__main__":
    main()
