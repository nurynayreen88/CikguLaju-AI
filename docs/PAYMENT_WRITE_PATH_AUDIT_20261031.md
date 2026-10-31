# Audit laluan pembayaran dan ketahanan data — 31 Oktober 2026

Skop: pemeriksaan statik `app.py` pada branch `staging/supabase-persistence-audit-20261031`. **Bukan pengesahan operasi live.**

## Penemuan disahkan melalui kod

1. `_activate_access(...)` memanggil Supabase RPC `cikgulaju_activate_subscription` dengan ID Telegram, rujukan bayaran, amaun dan tempoh. Ini laluan langganan yang bertujuan kekal merentas redeploy. Atomicity sebenar perlu disahkan pada definisi RPC di database.
2. `_mark_payment_request(...)` hanya mengemas kini SQLite `payment_requests`. Rekod permintaan dan status semakan lama berisiko hilang selepas storan Render sementara diganti.
3. `_admin_list(kind='pending')` masih membaca SQLite `payment_requests`; `active` dan `inactive` juga membaca `user_access` SQLite. Hanya laluan `payments` yang telah dipintas kepada pembaca Supabase dalam PR ini. **Jangan anggap seluruh panel admin sudah persistent.**
4. `_new_donation_receipt(...)` menulis SQLite dahulu dan cuba merekod audit dalam Supabase `credit_ledger`. Kegagalan Supabase hanya dicetak sebagai amaran dan fungsi masih memulangkan ID resit SQLite. Ini bukan jaminan penyimpanan audit kekal.
5. `_sb_request` melemparkan `CreditStoreUnavailable` bagi ralat HTTP/rangkaian; pembaca sejarah bayaran admin sengaja tidak fallback ke SQLite supaya kegagalan tidak tersalah dipaparkan sebagai tiada rekod.
6. `_ensure_user_credit` masih membaca baki SQLite untuk migrasi awal apabila pengguna belum wujud dalam `cikgulaju_users`. Risiko bootstrap perlu diuji bagi keadaan database sementara hilang.

## Urutan pembaikan selamat (belum dilaksanakan)

- Periksa skema dan RLS jadual Supabase untuk permintaan bayaran, bukti bayaran dan audit kelulusan. Tentukan kunci idempotensi dan akses admin.
- Sediakan migrasi **additive**, tidak memadam atau menulis ganti rekod sedia ada. Uji backup, constraint dan polisi sebelum aplikasi menggunakannya.
- Dual-read atau backfill sejarah SQLite lama secara terkawal dengan ID rujukan unik; jangan anggap semua sejarah telah dimigrasi.
- Tukar pending/approval dan resit kepada Supabase sebagai sumber kebenaran, dan hanya akui kejayaan selepas transaksi persistent disahkan.
- Uji semua laluan admin dan reboot/redeploy menggunakan data ujian tanpa menjejaskan pengguna sebenar.

## Release gate

PR #71 kekal Draft: CI GitHub masih gagal, log job tidak tersedia melalui connector; belum ada ujian integrasi Supabase sebenar atau ujian redeploy. **Jangan merge ke main** sebelum semua gate disahkan.

## Pemeriksaan kod terperinci — fungsi permintaan bayaran

- `_new_payment_request(chat_id, message_id, amount)` membuat `INSERT` ke SQLite `payment_requests` dan mengembalikan `lastrowid` tempatan. ID ini tidak boleh dianggap sama dengan ID identity jadual `pioneer_payment_requests` di Supabase.
- `_latest_pending_payment(chat_id)` membaca hanya SQLite; selepas kehilangan fail SQLite, permintaan Supabase sedia ada tidak dapat ditemui melalui fungsi ini.
- `_set_payment_note(request_id, note)` menyimpan nota hanya dalam SQLite. Jadual Supabase `pioneer_payment_requests` yang telah diperiksa tidak mempunyai lajur `notes`; jangan menulisnya ke lajur lain secara tersirat.
- `_payment_request(request_id)` dan `_mark_payment_request(request_id, status, ...)` menggunakan ID SQLite. Migrasi terus kepada ID Supabase tanpa pemetaan eksplisit boleh mengemas kini rekod orang lain.
- `_admin_list(kind='pending')` masih bergantung pada SQLite; menukar paparan sejarah sahaja tidak mengubah aliran kelulusan.

### Gate migrasi wajib

1. Tambah pemetaan ID legacy yang unik dan boleh diaudit; jangan padankan rekod berdasarkan ID integer sahaja.
2. Reka penyimpanan nota dan bukti yang serasi dengan skema sebenar; jangan simpan kandungan resit sensitif dalam log.
3. Pastikan operasi kelulusan idempotent dan disahkan dalam satu transaksi server-side; kegagalan Supabase mesti menghentikan pengakuan kejayaan.
4. Lakukan ujian penjanaan permintaan, kelulusan, penolakan, retry dan redeploy sebelum menukar laluan produksi.
