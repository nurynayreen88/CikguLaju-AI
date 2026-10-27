# Audit Kemajuan RPH — Punca Sebenar dan Reka Bentuk Pembetulan
Tarikh: 2026-10-27
Sumber: app.py blob fde446fd0f721a7eaba8cfa1461a8beb8265dd06
Status: STAGING / audit sahaja, tiada migrasi

## Bukti dalam kod
1. `_rph_progress_v25273` dan `_save_rph_progress_v25273` menyimpan checkpoint dalam `teacher_profiles.class_profiles[*].rph_progress` (fallback).
2. `_get_rph_progress_v25274` membaca Supabase `rph_progress` dan fallback ke profil.
3. `_upsert_rph_progress_v25274` menyimpan `sequence_no`, `sequence_kind`, `year_label`, `unit_name`, `topic_name`; `on_conflict` hanya `telegram_user_id,class_name,subject`.
4. `_record_successful_rph_v25274` merekod sejarah 'success' kemudian mengemas kini `rph_progress` **sebaik janaan berjaya**, bukan selepas PdP disahkan selesai.
5. `_manual_or_quick_success_v25275` memanggil recorder tersebut.
6. `_today_batch_status_v25273` dialias kepada `_today_batch_status_v25274`, yang membaca rekod janaan untuk memaparkan checkpoint.
7. `todaybatch273_run` masih guard/no-op dalam v25.273: tiada resolver automatik dijalankan pada callback itu.

## Keputusan reka bentuk wajib
**Jangan mengubah maksud atau memadam rekod `rph_progress` lama.** Kekalkan sebagai *last generated RPH* untuk keserasian sejarah. Tambah konsep *last confirmed taught lesson* yang berasingan, dengan identiti `teacher_id,school_year,class_id,subject_id` dan bukti `session_instance_id` yang mengandungi tarikh sebenar. Jangan menggunakan `year_label` (Tahun 2/3/4) sebagai pengganti `school_year` (2027).

Cadangan skema baharu perlu diluluskan selepas audit skema Supabase sebenar:
- `rph_taught_progress`: stable teacher/class/subject IDs + `school_year`, `last_confirmed_sequence`, `version`, timestamps; unique key per tahun persekolahan.
- `rph_taught_events`: idempotency key untuk sesi bertarikh, lesson sequence, teacher, class, subject, school year, confirmation timestamp; unique immutable event key.
- RPC/Postgres transaction untuk lock dan compare-and-swap; **jangan** gunakan dua panggilan REST biasa yang boleh menyebabkan separuh transaksi.
- Cadangan lesson: hanya daripada progress PdP disahkan + verified RPT/SOW + verified school calendar; jika tiada pengesahan, tunjuk pilihan setup/manual, bukan menaikkan sequence.
- Pengekalan data: tiada drop/reset/overwrite jadual sedia ada; migrasi additive selepas backup dan ujian staging.
- Jika terdapat kelas bernama sama pada sekolah/tahun berlainan, gunakan ID stabil; jangan andaikan `class_name` unik secara global.

## Ujian wajib
- Jana RPH dua kali tidak mengubah taught progress.
- Sahkan PdP sekali → maju satu lesson; pengesahan semula → idempotent.
- PdP kelas A tidak menjejaskan kelas B; subjek A tidak menjejaskan subjek B.
- Peralihan tahun persekolahan tidak memindahkan kemajuan lama.
- Slot berganda satu sesi tidak maju dua kali.
- Transaksi gagal tidak mengubah progress atau event.
- Cuti negeri / kalendar tidak disahkan → tiada auto-advance.
- Historical generation records remain intact.

## Sekatan
Jangan deploy atau merge; audit DB Supabase sebenar, polisi RLS dan jadual semasa sebelum sebarang SQL. 
