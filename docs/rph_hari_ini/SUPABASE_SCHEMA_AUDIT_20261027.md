# Audit Supabase Sebenar — RPH Hari Ini
Tarikh: 2026-10-27
Project: CikguLaju (Supabase project ref soxakntcanbycjoygrcx)
Kaedah: metadata read-only (`list_projects`, `list_tables`, query `pg_policies`). Tiada data peribadi guru diambil, tiada DDL/DML.

## Dapatan yang disahkan
- `public.teacher_profiles`: 11 baris (anggaran metadata), RLS enabled, PK `telegram_user_id bigint`; `state_name text`, `class_profiles jsonb`, `school_name text`. Kelas/jadual disimpan dalam JSON profil; **belum ada stable class_id berasingan** dalam skema yang disemak.
- `public.rph_progress`: 0 baris (metadata), RLS enabled, PK `id bigint`; `telegram_user_id text`, `class_name text`, `subject text`, `sequence_no int`, `sequence_kind text`, `year_label text`, `last_success_at timestamptz`. Tiada `school_year` atau `confirmed_taught_at`.
- `public.rph_generation_history`: 0 baris (metadata), RLS enabled, PK `id bigint`, `telegram_user_id text`, `class_name text`, `subject text`, `sequence_no int`, `year_label text`, `status text`, `generated_at timestamptz`.
- `pg_policies` untuk tiga jadual tersebut: **tiada polisi RLS** dipulangkan. Ini berkemungkinan bermaksud akses Data API oleh anon/authenticated ditolak; perlu sahkan hak `service_role` dan deployment sebelum mengaktifkan fungsi baharu.
- Kod `app.py` menggunakan `rph_progress` sebagai checkpoint selepas janaan berjaya, bukan bukti PdP diajar.
- Skema `rph_taught_progress` dan `rph_taught_events` **belum wujud**. Tiada migrasi dijalankan.

## Risiko dan syarat keselamatan
1. Jangan ubah `rph_progress` menjadi taught progress; asingkan rekod baharu.
2. Jangan gunakan `year_label` sebagai tahun persekolahan: Tahun 4 != 2027.
3. Kekalkan `telegram_user_id` sebagai pemilik, tetapi tetapkan stable class identity dengan kaedah non-destructive (class_profiles kini berasaskan JSON).
4. Atomic confirm mesti menggunakan satu transaksi Postgres/RPC berizin server sahaja, dengan unique event key (tarikh sesi sebenar) dan compare-and-swap.
5. Audit RLS/grants dan akses bot sebelum sebarang deployment. Jangan cipta SECURITY DEFINER dalam public secara terbuka.
6. Semak cuti rasmi KPM 2027 sebelum enjin cadangan diaktifkan.
7. Ujian transaksi perlu dilakukan dalam persekitaran ujian, bukan mengubah data guru produksi.

## Status
**Schema discovery completed. Implementation NOT done.** `main`, live bot, and Supabase production records remain unchanged.
