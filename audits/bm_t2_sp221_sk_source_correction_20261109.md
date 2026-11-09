# Bahasa Melayu Tahun 2 — SP 2.2.1 / SK source correction (2026-11-09)

## Punca
Dalam DB master Telegram v26.00, satu baris `verified_pdp_sequence` bagi:
- Tahun 2 / unit **Hidup Berjiran** / tajuk **Majlis Pengikat Kemesraan**
- `sk_code=2.1`, `sp_code=2.2.1`, status `SOURCE_VERIFIED`

Padanan SK/SP ini bercanggah. Jadual `curriculum_standards` dalam master yang **sama** menyimpan rekod sah, BM Tahun 2: `SK 2.2` / `SP 2.2.1`, dengan kedua-dua teks standard tersedia.

## Bukti luar
DSKP KSSR (Semakan 2017), Bahasa Melayu Sekolah Kebangsaan Tahun 2, halaman cetak **31** (halaman PDF **43**), bahagian 2.0 Kemahiran Membaca. SP 2.2.1 menyenaraikan kosa kata, isi tersurat, isi tersirat, idea utama, idea sampingan, idea keseluruhan.

Sumber PDF: https://bukuteksdigital.my/wp-content/uploads/2020/06/DSKP-KSSR-SEMAKAN-2017-BAHASA-MELAYU-TAHUN-2.pdf#page=43

Surat Siaran KPM Bil.1/2025 membenarkan Dokumen Penjajaran Edisi 3 sebagai pilihan bersama DSKP Semakan 2017 untuk Tahap 1:
https://www.moe.gov.my/surat-siaran-kpm-bil-1-tahun-2025-pelaksanaan-dokumen-penjajaran-kurikulum-standard-sekolah-rendah-semakan-2017

## Tindakan staging
`web/telegram_native_bm_sequence_rph_bridge.py` mengandungi pembetulan **read-only** hanya untuk identiti PdP tersebut: apabila sumber urutan masih menyatakan `2.1/2.2.1`, semak jadual `curriculum_standards` BM T2 untuk rekod tunggal `2.2/2.2.1` berstatus `verified=1` dan lengkap teks SP. Jika bukti tiada atau bercanggah, **FAIL CLOSED**.

Master DB `v26.00` asal, baris `verified_pdp_sequence`, RPH lain, aliran Telegram dan pengguna tidak ditimpa.

## Batasan
- Pembaikan ini untuk runtime Web BM yang meminta penjana Telegram. Ia **tidak** menulis pembetulan ke database Telegram.
- Tahun 1 2027 tertakluk kepada DK KP2027 tersendiri; bukan ditukar kepada KSSR Semakan 2017 secara automatik.
- PR masih DRAF; perlu CI dan semakan pelepasan sebelum gabung/deploy.
