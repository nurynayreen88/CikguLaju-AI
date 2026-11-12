"""Unit tests for internal developer-note leakage into RPT teacher documents."""
import tempfile
import unittest
from pathlib import Path

from scripts.audit_rpt2027_teacher_text_leaks_20261108 import (
    find_internal_notes, scan_paths,
)


class TeacherTextLeakAuditTests(unittest.TestCase):
    def test_original_pendidikan_islam_leak_is_detected(self):
        text = "Pemetaan buku teks belum disahkan; rujuk buku dan DSKP sebelum READY."
        rules = {item["rule"] for item in find_internal_notes(text)}
        self.assertIn("TEXTBOOK_MAPPING_REVIEW", rules)
        self.assertIn("DEVELOPER_INSTRUCTION", rules)
        self.assertIn("READY_INTERNAL", rules)

    def test_math_bm_psv_and_rbt_editor_messages_are_detected(self):
        examples = (
            "DRAF TERKAWAL / PRA-READY",
            "Pengesahan instrumen belum selesai.",
            "Buku Aktiviti belum disahkan.",
            "Semak tajuk penuh",
            "4, 7 (calon teks digital; belum sah)",
            "STATUS DRAF — halaman latihan dan cuti negeri belum lengkap",
            "Tiada janaan automatik sehingga pengesahan selesai.",
        )
        for sample in examples:
            with self.subTest(sample=sample):
                self.assertTrue(find_internal_notes(sample))

    def test_legitimate_pedagogical_language_does_not_trigger(self):
        clean = (
            "Murid membaca petikan dan menjawab tiga soalan. "
            "Guru membuat semakan bahan bertulis, merekod PBD dan "
            "menjalankan aktiviti berdasarkan Standard Pembelajaran 2.3.1. "
            "Buku Teks halaman 21."
        )
        self.assertEqual(find_internal_notes(clean), [])

    def test_unreadable_pdf_and_empty_folder_fail_closed(self):
        import contextlib
        import io
        from scripts.audit_rpt2027_teacher_text_leaks_20261108 import main
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            corrupt = folder / "rpt_corrupt.pdf"
            corrupt.write_bytes(b"%PDF-corrupt-not-real")
            # This is an error, not a clean document with zero findings.
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(corrupt)]), 1)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(folder / "missing")]), 1)

    def test_image_only_pdf_is_not_silently_marked_clean(self):
        # No text layer means the audit cannot read developer notes visible
        # inside a raster image. Such a PDF must require manual inspection.
        import fitz
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "rpt_2027_scanned.pdf"
            with fitz.open() as document:
                document.new_page(width=842, height=595)
                document.save(file)
            report = scan_paths([file], pdf_only=True)
            self.assertEqual(report["scanned_files"], 1)
            self.assertEqual(report["findings_count"], 0)
            self.assertEqual(len(report["read_errors"]), 1)
            self.assertIn("no extractable text", report["read_errors"][0]["error"])

    def test_blank_cover_and_readable_page_remain_auditable(self):
        # A blank cover alone is not a reason to block a document whose
        # remaining pages have an extractable and fully scanned text layer.
        import fitz
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "rpt_2027_mixed.pdf"
            with fitz.open() as document:
                document.new_page(width=842, height=595)
                page = document.new_page(width=842, height=595)
                page.insert_text((50, 50), "RANCANGAN PENGAJARAN TAHUNAN 2027")
                document.save(file)
            report = scan_paths([file], pdf_only=True)
            self.assertEqual(report["read_errors"], [])
            self.assertEqual(report["findings_count"], 0)

    def test_image_only_middle_body_page_requires_manual_review(self):
        # Cover and final pages may be searchable while a scanned table page
        # in between hides developer text inside a raster image.
        import contextlib
        import fitz
        import io
        from scripts.audit_rpt2027_teacher_text_leaks_20261108 import main
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "rpt_2027_mixed_source.pdf"
            with fitz.open() as raster_source:
                page = raster_source.new_page(width=842, height=595)
                page.insert_text((50, 70), "SEMAK TAJUK PENUH - DO NOT PUBLISH")
                png = page.get_pixmap().tobytes("png")
            with fitz.open() as document:
                cover = document.new_page(width=842, height=595)
                cover.insert_text((50, 60), "RANCANGAN PENGAJARAN TAHUNAN 2027")
                body = document.new_page(width=842, height=595)
                body.insert_image(body.rect, stream=png)
                last = document.new_page(width=842, height=595)
                last.insert_text((50, 60), "Murid membaca buku teks halaman 12")
                document.save(file)
            report = scan_paths([file], pdf_only=True)
            self.assertEqual(report["scanned_files"], 1)
            self.assertEqual(report["findings_count"], 0)
            self.assertEqual(len(report["read_errors"]), 1)
            self.assertIn("body pages have no extractable text: 2",
                          report["read_errors"][0]["error"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--pdf-only", str(file)]), 1)

    def test_readable_all_body_pages_pass_structure_gate(self):
        import fitz
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "rpt_2027_readable.pdf"
            with fitz.open() as document:
                for text in (
                    "RANCANGAN PENGAJARAN TAHUNAN 2027",
                    "Tema 1 PdP 001 Standard Pembelajaran 1.1.1",
                    "Tema 2 PdP 002 Standard Pembelajaran 1.2.1",
                ):
                    page = document.new_page(width=842, height=595)
                    page.insert_text((50, 60), text)
                document.save(file)
            report = scan_paths([file], pdf_only=True)
            self.assertEqual(report["read_errors"], [])
            self.assertEqual(report["findings_count"], 0)

    def test_teacher_projection_keeps_source_and_hides_review_notes(self):
        from rpt_2027.common.teacher_display_projection import (
            public_note, public_standard, public_topic
        )
        notes = (
            "Bahan: Kad nombor | PBD: Murid menyusun kad nombor. "
            "Pemetaan buku teks belum disahkan; rujuk buku dan DSKP sebelum READY.",
        )
        row = {
            "sk": "1.1",
            "sp": "1.1.1",
            "sk_display": "1.1 — Pernyataan penuh SK belum dipadankan",
            "sp_display": "1.1.1 — Pernyataan penuh SP belum dipadankan",
            "note": notes[0],
            "topic": "Menyusun kad nombor"
        }
        old = dict(row)
        self.assertEqual(public_standard(row, "sk"), "1.1")
        self.assertEqual(public_standard(row, "sp"), "1.1.1")
        printable = public_note(row)
        self.assertNotIn("belum disahkan", printable)
        self.assertNotIn("READY", printable)
        self.assertIn("Bahan: Kad nombor", printable)
        self.assertEqual(row, old)

        held = dict(row, source_held=True,
                    topic="KONFLIK SUMBER DIBETULKAN DALAM CADANGAN")
        self.assertEqual(public_note(held), "")
        self.assertEqual(public_topic(held), "")
        arabic = dict(row, source_sp_dskp_text_signoff=False)
        self.assertEqual(public_note(arabic), "")
        self.assertFalse(arabic["source_sp_dskp_text_signoff"])

    def test_music_pdf_editorial_leaks_trigger_pdf_release_guard(self):
        findings = (
            ("BT m/s: 10 (draf).", "MUSIC_DRAFT_BOOK_PAGE"),
            ("Simbol/skor tidak penuh dalam teks; rujuk rajah DSKP PDF hlm 33",
             "MUSIC_MISSING_NOTATION"),
            ("Pengukuhan pilihan, bukan projek rasmi; DRAF",
             "MUSIC_EDITOR_STATUS"),
            ("BT m/s:. | Audio: Tiada", "EMPTY_BOOK_PAGE"),
        )
        for source, expected in findings:
            with self.subTest(source=source):
                rules = {r["rule"] for r in find_internal_notes(source)}
                self.assertIn(expected, rules)
        self.assertFalse(find_internal_notes(
            "Standard Pembelajaran 3.3.1 Menulis draf dan menghasilkan "
            "penulisan imaginatif."
        ))

    def test_music_review_notes_not_printed_but_verified_fields_remain(self):
        from rpt_2027.common.teacher_display_projection import public_note
        examples = (
            ("BT m/s: 20-21 (draf). | Audio: 14–16. | "
             "Simbol/skor tidak penuh dalam teks; rujuk rajah DSKP PDF hlm 35",
             ("BT m/s: 20-21", "Audio: 14–16"),
             ("(draf)", "Simbol/skor tidak penuh", "rujuk rajah")),
            ("Pengukuhan pilihan, bukan projek rasmi; DRAF | "
             "Simbol/skor tidak penuh dalam teks; rujuk rajah DSKP PDF hlm 39",
             (), ("DRAF", "Simbol/skor tidak penuh", "rujuk rajah")),
        )
        for original, must_show, must_hide in examples:
            with self.subTest(original=original):
                row = {"note": original}
                rendered = public_note(row)
                self.assertEqual(row["note"], original)
                for text in must_show:
                    self.assertIn(text, rendered)
                for text in must_hide:
                    self.assertNotIn(text, rendered)

    def test_music_empty_book_page_never_prints_empty_reference(self):
        from scripts.build_rpt_2027_remaining_four_subjects_staging import (
            music_records, csv_rows, ROOT,
        )
        from rpt_2027.common.teacher_display_projection import public_note
        found_empty = False
        for year in range(2, 7):
            base = ROOT / "staging/pendidikan_muzik/rpt_rph_2027"
            raw = csv_rows(base / f"year{year}" /
                           f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv")
            rows = music_records(year)
            self.assertEqual(len(raw), len(rows))
            for original, row in zip(raw, rows):
                book = (original.get("BT m/s") or
                        original.get("RPT halaman BT (belum sah)") or
                        original.get("Buku Teks m/s") or "").strip()
                if book and book.lower() not in ("-", "—", "tiada", "n/a"):
                    continue
                found_empty = True
                self.assertNotIn("BT m/s:", row["note"])
                self.assertNotIn("BT m/s:", public_note(row))
        self.assertTrue(found_empty, "Expected original blank Music book source")

    def test_teacher_notes_hide_editor_status_but_preserve_valid_learning_refs(self):
        from rpt_2027.common.teacher_display_projection import public_note
        scenarios = (
            ("PdP 005 | DRAF PKJR — BAM Aktiviti 1 m/s 1; belum READY",
             ("BAM Aktiviti 1 m/s 1",), ("DRAF PKJR", "belum READY")),
            ("DRAF — BT1/BA1/DSKP disemak, belum READY; sesi susulan",
             (), ("DRAF", "READY")),
            ("BT m/s: 10 (draf). | Audio: 1–4.",
             ("BT m/s: 10", "Audio: 1–4"), ("(draf)",)),
            ("Masih DRAF. | Bahan: Mushaf al-Quran",
             ("Bahan: Mushaf al-Quran",), ("Masih DRAF",)),
            ("Masa: 60 minit. | Buku teks m/s: 5.2.1 (hlm. 2–2) — CALON BUKAN VISUAL."
             " | Jadual sebenar boleh disesuaikan oleh guru.",
             ("Masa: 60 minit", "Jadual sebenar"), ("CALON", "hlm. 2–2")),
            ("Murid menulis draf karangan dan menyemak semula.",
             ("menulis draf karangan",), ("Masih DRAF",)),
        )
        for original, must_keep, must_hide in scenarios:
            with self.subTest(original=original):
                row = {"note": original}
                rendered = public_note(row)
                self.assertEqual(row["note"], original)
                for value in must_keep:
                    self.assertIn(value, rendered)
                for value in must_hide:
                    self.assertNotIn(value, rendered)
                self.assertFalse(find_internal_notes(rendered))

    def test_actual_pi_y3_and_y6_curriculum_audit_notes_never_print(self):
        """The 3 source records retain provenance, but teacher PDF shows none."""
        from copy import deepcopy
        from scripts.build_rpt_2027_remaining_four_subjects_staging import pi_records
        from rpt_2027.common.teacher_display_projection import public_note
        for year, lesson in ((3, 6), (3, 50), (6, 87)):
            with self.subTest(year=year, lesson=lesson):
                record = pi_records(year)[lesson - 1]
                original = deepcopy(record)
                self.assertIn("SEMAKAN KURIKULUM", record["note"])
                teacher_note = public_note(record)
                for internal in (
                    "SEMAKAN KURIKULUM",
                    "SEMAKAN DSKP DIPERLUKAN",
                    "Pemetaan buku teks terdahulu",
                    "Masih DRAF",
                ):
                    self.assertNotIn(internal, teacher_note)
                self.assertIn("Bahan:", teacher_note)
                self.assertIn("Penilaian:", teacher_note)
                if year == 3:
                    self.assertIn("Mushaf al-Quran", teacher_note)
                else:
                    self.assertIn("Bahan sumber guru", teacher_note)
                self.assertFalse(find_internal_notes(teacher_note))
                self.assertEqual(record, original)

    def test_pdf_render_gate_detects_internal_footer_and_clauses(self):
        from rpt_2027.common.teacher_display_projection import public_note
        row = {
            "note": ("Tarikh A/B ialah cadangan; semak negeri, cuti dan jadual guru. "
                     "Aktiviti guru: Mengendalikan eksperimen ringkas.")
        }
        self.assertNotIn("semak negeri", public_note(row).lower())
        self.assertIn("Aktiviti guru", public_note(row))

    def test_bm_y2_y3_all_source_hold_notes_are_withheld_not_mutated(self):
        from scripts.build_rpt_2027_remaining_four_subjects_staging import bm_records
        from rpt_2027.common.teacher_display_projection import public_note
        expected = {2: 2, 3: 7, 4: 0, 5: 0, 6: 0}
        for year, count in expected.items():
            with self.subTest(year=year):
                rows = bm_records(year)
                held = [row for row in rows if row.get("source_held")]
                self.assertEqual(len(held), count)
                for row in held:
                    original_note = row["note"]
                    self.assertIn("HOLD", original_note)
                    self.assertEqual(public_note(row), "")
                    self.assertEqual(row["note"], original_note)
                self.assertTrue(all(not row.get("source_held")
                                    for row in rows[:3]))
        leaked = ("PdP 034 BT1 m/s 32 BA m/s 38 "
                  "HOLD padanan SP berganda, semak semula sumber.")
        self.assertIn("HELD_BM_SP_CROSSWALK",
                      {r["rule"] for r in find_internal_notes(leaked)})

    def test_bm_y2_held_pdp_130_131_do_not_leak_ready_instruction(self):
        from rpt_2027.common.teacher_display_projection import public_note
        records = (
            "HOLD: BT2 m/s 39 Pengayaan A mengedit penggunaan kata dan B "
            "membina ayat penyata; SP dan pentaksiran perlu disemak sebelum READY",
            "HOLD: BT2 m/s 41 pengukuhan bacaan kefahaman; SP dalam sumber "
            "mungkin tidak tepat, perlu semakan DSKP/BT sebelum READY",
        )
        for note in records:
            with self.subTest(note=note):
                self.assertEqual(public_note({"note": note}), "")
                self.assertIn("HOLD", note)  # Original evidence is untouched.

    def test_pjpk_provenance_removed_but_book_and_assessment_remain(self):
        from rpt_2027.common.teacher_display_projection import public_note
        note = ("Sumber: PJ456_2027_RPT. Buku teks m/s 2–3. "
                "Rujukan: Rujuk DSKP | Masa: 30 minit. "
                "Aktiviti (sumber): Murid melakukan imbangan. "
                "PBD (draf): Guru menilai imbangan.")
        rendered = public_note({"note": note})
        self.assertNotIn("PJ456_2027_RPT", rendered)
        self.assertNotIn("Rujuk DSKP", rendered)
        self.assertIn("Buku teks m/s 2–3", rendered)
        self.assertIn("Masa: 30 minit", rendered)
        self.assertIn("Aktiviti: Murid melakukan imbangan", rendered)
        self.assertIn("PBD: Guru menilai imbangan", rendered)
        self.assertEqual(len(find_internal_notes(rendered)), 0)
        self.assertTrue(find_internal_notes(note))

    def test_official_menulis_draf_standard_remains_complete(self):
        from rpt_2027.common.teacher_display_projection import (
            public_note, public_standard
        )
        original = "3.3.1 — Menulis draf dan menghasilkan penulisan imaginatif."
        row = {"sk": "3.3", "sp": "3.3.1",
               "sp_display": original, "note": "Murid menulis draf karangan pendek."}
        self.assertEqual(public_standard(row, "sp"), original)
        self.assertIn("menulis draf", public_note(row))
        self.assertEqual(find_internal_notes(original), [])

    def test_english_sow_source_provenance_is_not_a_teacher_note(self):
        from rpt_2027.common.teacher_display_projection import public_note
        raw = ("SB p.58 | Main/Complementary codes from source SOW, "
               "not a new DSKP choice.")
        shown = public_note({"note": raw})
        self.assertEqual(shown, "SB p.58")
        self.assertTrue(find_internal_notes(raw))
        self.assertFalse(find_internal_notes(shown))

    def test_pi_mushaf_reference_survives_without_developer_instruction(self):
        from rpt_2027.common.teacher_display_projection import public_note
        original = ("Bahan: Mushaf al-Quran | Mushaf al-Quran (tasmi'/khatam) "
                    "mengikut ayat dalam RPT; tidak mereka halaman buku teks.")
        shown = public_note({"note": original})
        self.assertIn("Mushaf al-Quran (tasmi'/khatam) mengikut ayat dalam RPT", shown)
        self.assertNotIn("tidak mereka", shown)
        self.assertFalse(find_internal_notes(shown))
        self.assertTrue(find_internal_notes(original))

    def test_sains_internal_crosswalk_id_is_preserved_but_not_printed(self):
        from rpt_2027.common.teacher_display_projection import public_lesson_identity
        row = {"id": "001", "display_id": "SCI-Y4-PDP-001", "note": "DRAF LEGACY"}
        initial = dict(row)
        self.assertEqual(public_lesson_identity("sains", row), "PdP 001")
        self.assertEqual(row, initial)
        self.assertTrue(find_internal_notes(row["display_id"]))
        self.assertFalse(find_internal_notes(public_lesson_identity("sains", row)))
        self.assertEqual(public_lesson_identity("english", 
                         {"id": "001", "display_id": "Lesson 001"}), "Lesson 001")

    def test_bm_crosswalk_and_editorial_references_are_internal_only(self):
        from rpt_2027.common.teacher_display_projection import public_note, public_topic
        row = {"topic": "Ceria Pagi BM2-P001",
               "note": ("PdP 001 · Ceria Pagi BM2-P001 BT1 m/s 2–3 "
                        "| Semak judul aktiviti penuh | PBD: Pemerhatian lisan")}
        old = dict(row)
        self.assertEqual(public_topic(row), "Ceria Pagi")
        shown = public_note(row)
        self.assertNotIn("BM2-P001", shown)
        self.assertNotIn("Semak judul", shown)
        self.assertIn("BT1 m/s 2–3", shown)
        self.assertIn("PBD: Pemerhatian lisan", shown)
        self.assertTrue(find_internal_notes(row["note"]))
        self.assertFalse(find_internal_notes(shown))
        self.assertEqual(row, old)
        self.assertEqual(public_note({"note": "BA1 18–20 berdasarkan BT (BA asal belum disemak)"}), "")
        self.assertEqual(public_note({"note": "Sumber berbeza; jangan dakwa kedua-duanya setara"}), "")
        note = public_note({"note": "BA sahaja dalam RPT sumber (tiada BT khusus); BA m/s 4-5"})
        self.assertIn("BA sahaja", note)
        self.assertIn("BA m/s 4-5", note)
        self.assertFalse(find_internal_notes(note))

    def test_optional_pi_tasmi_has_no_fabricated_official_sk_sp(self):
        from rpt_2027.common.teacher_display_projection import public_standard
        row = {"sk": "PROGRAM TASMI PILIHAN GURU — BUKAN KOD SK RASMI",
               "sp": "BACAAN TASMI / PBD — TIADA KOD SP RASMI DALAM RPT SUMBER"}
        self.assertEqual(public_standard(row,"sk"),"Aktiviti pilihan guru (tiada SK rasmi)")
        self.assertEqual(public_standard(row,"sp"),"Aktiviti pilihan guru (tiada SP rasmi)")
        self.assertTrue(find_internal_notes(row["sk"]))
        self.assertTrue(find_internal_notes(row["sp"]))
        self.assertFalse(find_internal_notes(public_standard(row,"sk")))
        self.assertFalse(find_internal_notes(public_standard(row,"sp")))

    def test_scan_teacher_output_separately_from_source_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "rpt.html").write_text(
                "<html><p>Semak tajuk penuh</p></html>", encoding="utf-8"
            )
            (root / "source.csv").write_text(
                "nota\nPemetaan buku teks belum disahkan\n", encoding="utf-8"
            )
            teacher = scan_paths([root], teacher_output_only=True)
            self.assertEqual(teacher["scanned_files"], 1)
            self.assertEqual(teacher["files_with_findings"], 1)
            self.assertFalse(teacher["read_errors"])
            full = scan_paths([root])
            self.assertEqual(full["scanned_files"], 2)
            self.assertEqual(full["files_with_findings"], 2)
            self.assertFalse(full["academic_signoff"])


if __name__ == "__main__":
    unittest.main()
