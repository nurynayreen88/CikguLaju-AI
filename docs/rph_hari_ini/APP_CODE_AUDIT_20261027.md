# Audit Kod Sebenar — RPH Hari Ini (27 Oktober 2026)

**Sumber:** `app.py` blob SHA `fde446fd0f721a7eaba8cfa1461a8beb8265dd06` pada branch staging. Kandungan berjaya dibaca melalui GitHub blob walaupun fetch_file bagi fail besar mengembalikan kandungan kosong.

## Fungsi sebenar yang ditemui
- `_teacher_profile(cid)` membaca `teacher_profiles` di **Supabase** menggunakan `telegram_user_id`; medan `state_name` dan `class_profiles` wujud dalam kod.
- `_profile_group(state_name)` menentukan Kumpulan A/B menggunakan `GROUP_A_STATES`.
- `_profile_class_records(cid)` ialah sumber kelas dan jadual yang dipaut pada profil; `_timetable_entries(cid)` mengembangkan jadual setiap kelas, menambah `class_name`, `students`, `_ci`, `_ei`.
- `_today_rows_v25272(cid)` menggunakan UTC+08:00 dan menapis jadual berdasarkan nama hari sahaja. **Tiada semakan cuti/takwim** pada fungsi ini.
- `_today_rph_menu_v25272(cid)` menyenaraikan sesi hari ini. Teks sedia ada menyebut kemajuan bergerak selepas RPH berjaya dijana; **ini bercanggah dengan polisi pengesahan PdP selesai** dan mesti diperbetulkan dengan kawalan sebenar.
- `_today_batch_status_v25273(cid)` membaca `_rph_progress_v25273(cid,class_name,subject)`; `_today_batch_menu_v25273(cid)` memaparkan checkpoint dan boleh menawarkan jana semua jika semuanya ada.
- Kod mempunyai pengendalian `todayrph272` dan `todaybatch273_*` dalam callback berlapis. Jangan menggantikan callback tanpa menjejak wrapper terakhir.

## Jurang yang kini terbukti
1. **Sistem stor bercampur**: profil guru dalam Supabase, kurikulum tempatan SQLite; jangan anggap semua data guru disimpan dalam SQLite.
2. `_today_rows_v25272` hanya menapis hari mingguan; perlu kalendar sekolah, cuti negeri dan tarikh sesi yang disahkan sebelum auto-suggest.
3. Perlu audit lanjut pelaksanaan `_rph_progress_v25273` dan callback jana untuk mengesahkan sama ada kemajuan berubah ketika janaan atau pengesahan.
4. Identiti kemajuan perlu merangkumi tahun persekolahan; padanan `class_name` dan `subject` perlu dinormalkan/diikat kepada identiti yang stabil.
5. Slot berturutan perlu pengelompokan sesi yang eksplisit, bukan dianggap dua PdP secara automatik.

## Tindakan integrasi seterusnya
- Audit kod penuh `_rph_progress_v25273`, penulis checkpoint dan semua callback berkaitan.
- Dapatkan skema sebenar Supabase dan DB SQLite menggunakan akses baca sahaja; jangan ubah rekod lama.
- Bina adapter **read-only** ke fungsi sedia ada dahulu, disertakan ujian dua kelas/dua subjek, tahun persekolahan, cuti dan slot berganda.
- Hanya selepas itu rancang transaksi pengesahan berasingan dan ujian end-to-end di staging.

**Status:** Audit kod sumber sebenar, bukan integrasi bot. Tiada merge/deploy atau migrasi DB.
