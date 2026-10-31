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
