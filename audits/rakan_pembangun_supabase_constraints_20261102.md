# Audit indeks dan keputusan keselamatan Rakan Pembangun — 2026-11-02

## Dapatan read-only Supabase CikguLaju
- `public.pioneer_entitlements` mempunyai PRIMARY KEY (`telegram_user_id`).
- `payment_reference` mempunyai UNIQUE btree index.
- CHECK `entitlement = 'PIONEER_LIFETIME'`.
- 2 rekod, 2 aktif, 0 dibatalkan, 0 rujukan kosong.
- Fungsi `approve_pioneer_early_bird` menggunakan advisory transaction lock, menolak pengguna yang sudah mempunyai entitlement, dan memeriksa kuota 500.
- Fungsi ini tidak mengesahkan resit TNG secara langsung.
- Telegram approval menjana rujukan UUID dalaman; ini tidak membuktikan keunikan transaksi bank.

## Keputusan
**Jangan buang atau ubah UNIQUE constraint sedia ada.**
Penyelesaian mestilah mengekalkan entitlement lama dan menambah bukti transaksi sebenar secara berasingan.

## Syarat sebelum merge
1. Semak bukti transaksi TNG secara bebas dan dapatkan ID transaksi yang benar-benar unik bagi merchant.
2. Gunakan identiti transaksi bank sebagai kunci deduplikasi, bukan UUID pengaktifan.
3. Claim transaksi dan grant entitlement dalam satu operasi atomik; kegagalan mesti rollback kedua-duanya.
4. Jangan menandakan permohonan SQLite approved jika transaksi database gagal.
5. Uji dua akaun berkongsi resit, approval serentak, retry, dan kegagalan di tengah transaksi.
6. Jangan mengubah rekod sedia ada atau deploy produksi tanpa kelulusan.
