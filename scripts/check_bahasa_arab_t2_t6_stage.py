#!/usr/bin/env python3
"""Read-only staging structural QA: 72 Bahasa Arab PdP drafts (60 Unit1 + 12 Year4 Unit2), 20 units, 15 banks.
NOT a pedagogical approval, RPT 2027 release, source page certification or production patch.
"""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = ROOT / "rph_standalone" / "bahasa_arab"
RPT = ROOT / "rpt_2027" / "bahasa_arab"
EXPECTED_SP = {2:["1.1.1","1.1.2","1.2.1","2.1.1","2.2.1","3.1.1","3.2.1","1.3.1","1.3.2","2.3.1","3.3.1","1.4.1"],3:["1.1.1","1.1.2","1.2.1","2.1.1","2.2.1","3.1.1","3.2.1","1.3.1","1.3.2","2.3.5","3.3.1","1.4.1"],4:["1.1.1","1.1.2","1.2.1","2.1.1","2.2.1","3.1.1","3.2.1","1.3.1","1.3.2","2.3.1","3.3.1","1.4.1"],5:["1.1.1","1.1.3","1.2.1","2.1.1","2.2.1","3.2.1","1.3.1","1.3.2","2.3.1","2.3.2","3.3.1","1.4.1"],6:["1.1.1","1.1.2","1.2.1","2.1.2","2.2.1","3.1.1","1.3.1","1.3.2","2.3.1","2.3.2","3.2.1","1.4.1"]}
UNIT_1 = {2:"هيا نتعارف",3:"تفضل إلى الفصل",4:"الشهور الميلادية",5:"في المطبخ",6:"حياتنا أجمل بالنظافة"}
MARKERS = ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Penutup", "BBM",
           "PBD", "Kriteria kejayaan", "Refleksi", "DRAF", "BELUM READY")
def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def check() -> None:
    m = json.loads((SUBJECT / "source_manifest_20261105.json").read_text(encoding="utf-8"))
    assert m["release_status"] == "DRAF_STAGING_SAHAJA"
    assert m["total_final_ready_rph"] == 0
    assert all(m[key] is False for key in ("production_db_touched", "telegram_live_touched", "web_live_touched"))
    assert sorted(m["years"]) == ["2","3","4","5","6"]
    units = read_csv(RPT / "unit_sequence_DRAF_20261105.csv")
    assert len(units) == 20
    assert Counter(int(row["tahun"]) for row in units) == Counter({y:4 for y in range(2,7)})
    assert all(row["status"] == "DRAF_SEMAK" and row["pdp_ready"] == "FALSE" for row in units)
    assert next(x["tajuk_arab"] for x in units if x["tahun"] == "3" and x["unit"] == "4") == "الوقت كالذهب"
    assert m["years"]["3"]["unit_4_theme_tag"] == "الزمان"
    assert m["years"]["3"]["unit_4_corrected"] == "الوقت كالذهب"
    assert next(x["tajuk_arab"] for x in units if x["tahun"] == "5" and x["unit"] == "3") == "هيا نشترك في الأنشطة اللاصفية"
    assert m["years"]["5"]["unit_3_title_corrected"] == "هيا نشترك في الأنشطة اللاصفية"
    y5bank = (ROOT / "materials" / "bahasa_arab" / "year5" / "unit_03_activity_bank_DRAF.md").read_text(encoding="utf-8")
    assert "**Unit:** هيا نشترك في الأنشطة اللاصفية" in y5bank
    assert "فرقة الكشافة" in y5bank
    assert {(int(x["tahun"]),int(x["unit"])) for x in units} == {(y,n) for y in range(2,7) for n in range(1,5)}
    assert m["primary_crosswalk_file"] == "rpt_2027/bahasa_arab/pdp_001_012_DRAF.csv"
    rows = read_csv(RPT / "pdp_001_012_DRAF.csv")
    assert len(rows) == 60
    assert Counter(int(x["tahun"]) for x in rows) == Counter({y:12 for y in range(2,7)})
    assert all(x["status"] == "DRAF_SEMAK" and x["ready"] == "FALSE" and x["halaman_buku_disahkan"] == "FALSE" for x in rows)
    mapping = {(int(x["tahun"]),int(x["pdp"])):x for x in rows}
    assert len(mapping) == 60
    for y in range(2,7):
        s = m["years"][str(y)]
        assert s["provisional_rph_count"] == 12
        assert s["textbook"]["source_page_verified"] is False
        for n in range(1,13):
            p = SUBJECT / f"year{y}" / f"lesson_{n:03d}.md"
            text = p.read_text(encoding="utf-8")
            row = mapping[(y,n)]
            assert row["unit"] == "1"
            assert row["sp"] == EXPECTED_SP[y][n-1]
            assert all(marker in text for marker in MARKERS), p
            assert f"PdP {n:03d}" in text and f"Bahasa Arab Tahun {y}" in text
            assert row["sp"] in text and UNIT_1[y] in text
            assert s["rpt_2026"] in text
            assert len(text) > 1000, p
    banks = 0
    for y in range(2,7):
        for u in range(2,5):
            p = ROOT / "materials" / "bahasa_arab" / f"year{y}" / f"unit_{u:02d}_activity_bank_DRAF.md"
            text = p.read_text(encoding="utf-8")
            assert f"Bahasa Arab Tahun {y}" in text and "Bukti PBD" in text
            assert all(m in text for m in ("DRAF_SEMAK", "BELUM READY", "https://anyflip.com/"))
            banks += 1
    assert banks == m["additional_unit_activity_bank_count"] == 15
    y6_evidence = json.loads((ROOT / "audits" / "bahasa_arab_y6_textbook_page_evidence_20261105.json").read_text(encoding="utf-8"))
    assert y6_evidence["year"] == 6 and y6_evidence["individual_rph_approval"] is False
    assert y6_evidence["all_unit_pages_verified_at_toc_level"] is True
    assert len(y6_evidence["book"]["toc"]) == 4
    assert [(u["printed_page_start"], u["printed_page_end"]) for u in y6_evidence["book"]["toc"]] == [(1,30),(31,60),(61,90),(91,120)]
    assert m["years"]["6"]["textbook"]["source_page_verified"] is False
    assert all(x["ready"] is False for x in y6_evidence["lesson_candidates"])
    assert len(y6_evidence["lesson_candidates"]) == 12
    assert y6_evidence["conflicts"] == []
    assert len(y6_evidence["resolved_discussions"]) == 1
    assert y6_evidence["resolved_discussions"][0]["lesson"] == "year6/lesson_004"
    assert y6_evidence["resolved_discussions"][0]["old_sp"] == "2.1.1"
    assert y6_evidence["resolved_discussions"][0]["new_sp"] == "2.1.2"
    assert y6_evidence["lesson_candidates"][3]["sp_in_draft"] == "2.1.2"
    assert mapping[(6,4)]["sp"] == "2.1.2"
    assert "2.1 / 2.1.2" in (SUBJECT / "year6" / "lesson_004.md").read_text(encoding="utf-8")
    for idx, row in enumerate(y6_evidence["book"]["toc"], start=1):
        found = next(r for r in units if r["tahun"]=="6" and r["unit"]==str(idx))
        assert found["halaman_mula_buku"] == str(row["printed_page_start"])
        assert found["halaman_akhir_buku"] == str(row["printed_page_end"])
        assert found["status"] == "DRAF_SEMAK" and found["pdp_ready"] == "FALSE"
    bibliography = json.loads((ROOT / "audits" / "bahasa_arab_buku_teks_bibliography_20261105.json").read_text(encoding="utf-8"))
    assert len(bibliography["items"]) == 5
    assert bibliography["individual_rph_verified"] == 0
    assert bibliography["no_new_textbook_pdf_uploaded"] is True
    assert m["bibliography_file"] == "audits/bahasa_arab_buku_teks_bibliography_20261105.json"
    for year, isbn in ((2,"978-983-49-1589-6"), (3,"978-983-49-2033-3"), (4,"978-983-49-2480-5"), (5,"978-983-49-2838-4"), (6,"978-983-49-3300-5")):
        item = next(x for x in bibliography["items"] if x["year"] == year)
        assert item["isbn"] == isbn
        assert m["years"][str(year)]["textbook"]["bibliographic_verification"]["isbn"] == isbn
        assert m["years"][str(year)]["textbook"]["source_page_verified"] is False
    y3_expected = [("تفضل إلى الفصل","1","28"),("ملابسي الجميلة","29","58"),("الألوان حولنا","59","86"),("الوقت كالذهب","87","117")]
    for idx, (title,start,end) in enumerate(y3_expected,1):
        found = next(row for row in units if row["tahun"] == "3" and row["unit"] == str(idx))
        assert (found["tajuk_arab"],found["halaman_mula_buku"],found["halaman_akhir_buku"]) == (title,start,end)
        assert found["pdp_ready"] == "FALSE" and found["status"] == "DRAF_SEMAK"
    bank3 = (ROOT / "materials" / "bahasa_arab" / "year3" / "unit_04_activity_bank_DRAF.md").read_text(encoding="utf-8")
    assert "**Unit:** الوقت كالذهب" in bank3
    assert "**Tema DSKP:** الزمان" in bank3
    assert next(x["activity_book_isbn"] for x in bibliography["items"] if x["year"] == 2) == "978-983-49-1590-2"
    y4 = json.loads((ROOT / "audits" / "bahasa_arab_y4_textbook_pdp001_006_evidence_20261106.json").read_text(encoding="utf-8"))
    assert y4["year"] == 4 and y4["final_ready"] == 0
    assert len(y4["page_level_findings"]) == 6
    assert y4["no_published_textbook_copied"] is True
    assert [r["printed_page"] for r in y4["page_level_findings"]] == ["2","2","4–5","3","7","3"]
    assert [r["sp"] for r in y4["page_level_findings"]] == EXPECTED_SP[4][:6]
    for idx in range(1,7):
        file = SUBJECT / "year4" / f"lesson_{idx:03d}.md"
        content = file.read_text(encoding="utf-8")
        assert "**Bukti padanan buku teks yang dikenal pasti:**" in content
        assert "BELUM READY" in content
    assert m["years"]["4"]["first_six_source_evidence"] == "audits/bahasa_arab_y4_textbook_pdp001_006_evidence_20261106.json"
    y5_source = json.loads((ROOT / "audits" / "bahasa_arab_y5_pdp001_012_source_audit_20261106.json").read_text(encoding="utf-8"))
    assert y5_source["year"] == 5 and y5_source["all_rph_final_ready"] == 0
    assert y5_source["pdp_source_reviewed"] == 12 and len(y5_source["pdp"]) == 12
    assert y5_source["flagged_lessons"] == []
    assert [v["lesson"] for v in y5_source["remediated_conflicts"]] == ["002","004","012"]
    assert y5_source["release_blocked"] is True
    assert [x["draft_sp"] for x in y5_source["pdp"]] == EXPECTED_SP[5]
    assert all(x["ready"] is False and x["manual_approval"] is False for x in y5_source["pdp"])
    assert y5_source["pdp"][1]["evidence_status"] == "MATCH_BOOK_PAGE_SP_AFTER_CORRECTION"
    assert y5_source["pdp"][1]["draft_sp"] == "1.1.3"
    assert "1.1.3" in y5_source["pdp"][1]["book_printed_codes"]
    assert y5_source["pdp"][3]["evidence_status"] == "BOOK_CODE_AND_EXERCISE_ALIGNED_WITH_TEACHER_EXTENSION"
    assert y5_source["pdp"][11]["evidence_status"] == "MATCH_BOOK_PAGE_SP_AFTER_CONTENT_CORRECTION"
    assert m["years"]["5"]["source_evidence_pdp001_012"] == "audits/bahasa_arab_y5_pdp001_012_source_audit_20261106.json"
    assert m["years"]["5"]["source_audit_unresolved"] == y5_source["flagged_lessons"]
    assert m["years"]["5"]["textbook"]["source_page_verified"] is False
    for i, record in enumerate(y5_source["pdp"],1):
        rph = (SUBJECT / "year5" / f"lesson_{i:03d}.md").read_text(encoding="utf-8")
        assert "**Audit buku teks (6 Nov 2026):**" in rph
        assert "BELUM READY" in rph and record["draft_sp"] in rph
        assert f"**{record['source_printed_pages']}**" in rph
        assert record["evidence_status"] in rph
    y4rest = json.loads((ROOT / "audits" / "bahasa_arab_y4_pdp007_012_source_audit_20261106.json").read_text(encoding="utf-8"))
    assert y4rest["final_ready"] == 0 and len(y4rest["pdp"]) == 6
    assert [x["lesson"] for x in y4rest["pdp"]] == [f"{i:03d}" for i in range(7,13)]
    assert [x["sp"] for x in y4rest["pdp"]] == EXPECTED_SP[4][6:12]
    assert y4rest["flagged_lessons"] == []
    assert y4rest["remediated_conflicts"][0]["lesson"] == "012"
    assert y4rest["pdp"][5]["evidence_status"] == "MATCH_BOOK_PAGE_SP_AFTER_CONTENT_CORRECTION"
    assert all(x["ready"] is False and x["manual_approval"] is False for x in y4rest["pdp"])
    assert m["years"]["4"]["source_evidence_pdp007_012"] == "audits/bahasa_arab_y4_pdp007_012_source_audit_20261106.json"
    assert m["years"]["4"]["source_reviewed_drafts_total"] == 12
    for i, x in enumerate(y4rest["pdp"], 7):
        src = (SUBJECT / "year4" / f"lesson_{i:03d}.md").read_text(encoding="utf-8")
        assert "**Audit buku teks (6 Nov 2026):**" in src
        assert f"**{x['page']}**" in src
        assert "BELUM READY" in src and x["evidence_status"] in src
    y3_source = json.loads((ROOT / "audits" / "bahasa_arab_y3_pdp001_012_source_audit_20261106.json").read_text(encoding="utf-8"))
    assert y3_source["year"] == 3 and y3_source["unit"] == 1
    assert y3_source["reviewed_count"] == 12 and y3_source["final_ready_count"] == 0
    assert y3_source["product_release_approved"] is False
    assert [x["pdp"] for x in y3_source["items"]] == [f"{i:03d}" for i in range(1,13)]
    assert [x["sp"] for x in y3_source["items"]] == EXPECTED_SP[3]
    assert all(x["source_reviewed"] and x["manual_approval"] is False and x["ready"] is False for x in y3_source["items"])
    assert m["years"]["3"]["source_evidence_pdp001_012"] == "audits/bahasa_arab_y3_pdp001_012_source_audit_20261106.json"
    assert m["years"]["3"]["textbook"]["source_page_verified"] is False
    for i, item in enumerate(y3_source["items"], start=1):
        src = (SUBJECT / "year3" / f"lesson_{i:03d}.md").read_text(encoding="utf-8")
        assert "**Audit sumber BT Tahun 3 (6 Nov 2026):**" in src
        assert f"**{item['page_textbook']}**" in src
        assert "BELUM READY" in src
    readiness = json.loads((ROOT / "audits" / "bahasa_arab_release_readiness_20261106.json").read_text(encoding="utf-8"))
    assert readiness["release_state"] == "DRAF_STAGING_RELEASE_BLOCKED"
    assert readiness["completed"]["source_page_draft_reviewed"] == 72
    assert readiness["completed"]["draft_rph"] == 72
    assert sum(y["source_page_reviewed_rph"] for y in readiness["years"]) == 72
    assert all(y["unwritten_units"] == ([3,4] if y["year"] == 4 else [2,3,4]) for y in readiness["years"])
    assert readiness["total_ready_rph"] == 0 and readiness["release_authorized"] is False
    assert all(readiness[k] is False for k in ("production_db_touched","telegram_live_touched","web_live_touched"))
    assert any(x["id"] == "full_pdp_coverage" and x["status"] == "BLOCKED" for x in readiness["release_checks"])
    assert any(x["id"] == "word_pdf_programmatic_a4" and x["status"] == "PASS_TECHNICAL_ONLY" for x in readiness["release_checks"])
    y6review = json.loads((ROOT / "audits" / "bahasa_arab_y6_pdp001_012_text_source_audit_20261106.json").read_text(encoding="utf-8"))
    assert y6review["year"] == 6 and y6review["unit"] == 1
    assert y6review["source_text_reviewed_count"] == 12 and y6review["final_ready_count"] == 0
    assert len(y6review["pdp"]) == 12
    assert [x["sp"] for x in y6review["pdp"]] == EXPECTED_SP[6]
    assert all(x["textbook_sp_found_for_topic"] and x["manual_approval"] is False and x["ready"] is False for x in y6review["pdp"])
    assert m["years"]["6"]["source_evidence_pdp001_012"] == "audits/bahasa_arab_y6_pdp001_012_text_source_audit_20261106.json"
    assert m["years"]["6"]["source_text_reviewed_drafts"] == 12
    assert m["years"]["6"]["textbook"]["source_page_verified"] is False
    for i, row in enumerate(y6review["pdp"], 1):
        s = (SUBJECT / "year6" / f"lesson_{i:03d}.md").read_text(encoding="utf-8")
        assert "**Semakan teks BT Tahun 6 (6 Nov 2026):**" in s
        assert f"**{row['printed_page_text_source']}**" in s
        assert "BELUM READY" in s
    assert readiness["completed"]["source_page_draft_reviewed"] == 72
    assert sum(y["source_page_reviewed_rph"] for y in readiness["years"]) == 72
    y2_source = json.loads((ROOT / "audits" / "bahasa_arab_y2_pdp001_012_text_source_audit_20261106.json").read_text(encoding="utf-8"))
    assert y2_source["year"] == 2 and y2_source["unit"] == 1
    assert y2_source["source_page_reviewed_draft_count"] == 12
    assert len(y2_source["items"]) == 12 and y2_source["final_ready"] == 0
    assert [x["sp"] for x in y2_source["items"]] == EXPECTED_SP[2]
    assert y2_source["ambiguous_book_sp_pdp"] == ["002","004","010","011"]
    assert all(x["teacher_approval"] is False and x["ready"] is False for x in y2_source["items"])
    assert y2_source["release_authorized"] is False
    assert m["years"]["2"]["source_evidence_pdp001_012"] == "audits/bahasa_arab_y2_pdp001_012_text_source_audit_20261106.json"
    assert m["years"]["2"]["source_text_reviewed_drafts"] == 12
    assert m["years"]["2"]["textbook"]["source_page_verified"] is False
    assert readiness["completed"]["year2_sp_book_ocr_ambiguous"] == 4
    for i, record in enumerate(y2_source["items"], start=1):
        text = (SUBJECT / "year2" / f"lesson_{i:03d}.md").read_text(encoding="utf-8")
        assert "**Semakan Buku Teks asal Tahun 2 (6 Nov 2026):**" in text
        assert f"**{record['book_printed_page_text']}**" in text
        assert record["evidence_status"] in text and "BELUM READY" in text
    more_rows = read_csv(RPT / "year4_unit2_pdp013_024_DRAF.csv")
    assert len(more_rows) == 12
    assert [(row["tahun"], row["pdp"], row["unit"]) for row in more_rows] == [("4", f"{n:03d}", "2") for n in range(13,25)]
    expected_more_sp = ["1.1.1","1.1.2","2.1.1","3.1.1","1.2.1","1.2.2","1.2.4","2.2.1","3.2.1","1.3.4","2.3.2","3.4.1"]
    assert [row["sp"] for row in more_rows] == expected_more_sp
    assert all(row["status"] == "DRAF_SEMAK" and row["ready"] == "FALSE" and row["kelulusan_individu"] == "FALSE" for row in more_rows)
    more_evidence = json.loads((ROOT / "audits" / "bahasa_arab_y4_unit2_pdp013_024_text_source_audit_20261106.json").read_text(encoding="utf-8"))
    assert more_evidence["candidate_rph_count"] == 12 and more_evidence["unit_completed"] is False
    assert more_evidence["release_authorized"] is False and more_evidence["final_ready"] == 0
    assert [item["sp"] for item in more_evidence["items"]] == expected_more_sp
    assert [item["printed_page"] for item in more_evidence["items"]] == [row["halaman_buku_teks_dicadang"] for row in more_rows]
    assert all(item["manual_approval"] is False and item["ready"] is False for item in more_evidence["items"])
    assert m["years"]["4"]["unit2_candidate_rph_count"] == 12
    assert m["years"]["4"]["unit2_release_approved"] is False
    assert m["total_provisional_rph_count"] == 72
    assert readiness["completed"]["year4_unit2_candidate_rph"] == 12
    assert readiness["completed"]["verified_a4_render_for_new_12"] is False
    for n, item in zip(range(13,25),more_evidence["items"]):
        page = SUBJECT / "year4" / f"lesson_{n:03d}.md"
        text = page.read_text(encoding="utf-8")
        assert len(text) > 1450 and all(marker in text for marker in MARKERS), page
        assert item["sp"] in text and "من في المدرسة؟" in text
        assert "PdP" in text and "BELUM READY" in text and "DRAF_SEMAK" in text
        assert f"**{item['printed_page']}**" in text
    assert len(list(SUBJECT.glob("year*/lesson_*.md"))) == 72
    print("PASSED: 20 unit indexes, 60 Unit1 + 12 Unit2 crosswalks, 72 RPH draft files, 15 banks.")
    print("RELEASE BLOCKED: 0 READY; full-year curriculum/book-page approval, RPT 2027 and runtime parity missing; A4 preview CI passed.")

if __name__ == "__main__":
    check()
