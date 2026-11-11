# CikguLaju Pendidikan Islam — V6 pratonton staging sahaja

**Belum LIVE / belum FINAL READY.** Pakej ini mengandungi kod pembaca bahan QA, bukan fail pengganti Telegram produksi. Semua laluan gagal secara selamat tanpa tetapan staging yang jelas.

## Data yang digunakan

Letakkan kedua-dua arkib berikut pada pelayan staging dengan akses fail **persendirian**, bukan URL awam:

- `CIKGULAJU_PI_2027_T2_T6_RPH_RPT_TASMI_V5_INTEGRASI_STAGING_20261105.zip` (696 RPH Word, 5 RPT Word, 5 RPT PDF, 8 panduan tasmi' cadangan).
- `CIKGULAJU_PI_2027_RPH_696_PDF_PRATONTON_V5_STAGING_20261105.zip` (696 PDF draf satu halaman A4).

Pakej ini hanya membaca ZIP. Tiada import `app.py`, tiada sambungan database, tiada perubahan kredit, bayaran, pendaftaran atau akaun, dan tiada callback Telegram.

## Cara menguji sendiri pada pelayan staging

Salin `bundle_reader.py`, `preview_reader.py`, dan `staging_gateway.py` ke `curriculum_staging/pendidikan_islam_v5/`, kemudian tetapkan environment (gunakan **token rawak panjang yang berasingan** dan jangan masukkan ke GitHub):

```
PI_V5_STAGING_GATEWAY=1
PI_V5_STAGING_TOKEN=<secret rawak sekurang-kurangnya 24 aksara>
PI_V5_ARCHIVE=<path fail ZIP V5 pada staging>
PI_V5_PREVIEW_ARCHIVE=<path ZIP PDF pratonton pada staging>
```

Dengan Python WSGI dan `gunicorn` dipasang, jalankan secara terasing:

```
gunicorn --bind 127.0.0.1:8008 curriculum_staging.pendidikan_islam_v5.staging_gateway:application
```

Contoh laluan selepas autentikasi `Authorization: Bearer <token>`: `/api/pi/lessons?year=2`, `/api/pi/lesson?year=2&lesson=1`, `/api/pi/preview?year=2&lesson=1`, `/api/pi/word?year=2&lesson=1`, `/api/pi/tasmi?year=2&lesson=35`, `/api/pi/rpt?year=2&format=pdf`. **Tiada CORS dan tiada token dalam URL.** Integrasi browser/Telegram memerlukan jambatan autentikasi rasmi yang belum dilakukan.

## Bukti QA

- 25/25 ujian Python lulus dengan **kedua-dua ZIP asal** dipasang pada pembolehubah persekitaran; termasuk ralat checksum, bahan tiada, akses tanpa token, pembacaan RPH/PDF/RPT, bilangan 696 dan enam RPH ditahan.
- PDF pratonton 696/696 mempunyai label draf/staging dan **bukan untuk pengguna biasa**.
- Enam Lesson ditahan: `T2-L035`, `T6-L006`, `T6-L014`, `T6-L018`, `T6-L060`, `T6-L117`.
- Panduan tasmi' V4 adalah bahan sokongan **cadangan CikguLaju** dan bukan perubahan SK/SP rasmi.
- Ujian automatik GitHub di PR #311 menjalankan fixture sintetik; fail sebenar bersifat persendirian dan tidak ada dalam workflow CI.

## Syarat sebelum penerbitan

1. Pengesahan kandungan 696 RPH dan semua enam Lesson ditahan oleh pemilik kurikulum/panitia; keputusan 8 pelan bacaan cadangan.
2. Penyediaan cara penghantaran ZIP yang selamat pada pelayan staging, bukan sambungan terus kepada Library ChatGPT.
3. Integrasi pemilihan Tahun → Subjek → Unit/Tajuk → Lesson kepada **identiti Lesson yang sah**, bukan menganggap ID baris DB sama dengan nombor Lesson.
4. Pengesahan akses pengguna berbayar, satu klik pratonton → muat turun, serta ujian Telegram/Web staging dengan akaun sebenar.
5. Semua ujian regresi lulus, kemudian barulah pertimbangkan PR bukan draf / penerbitan.

**Jangan merge ke `main`, jangan deploy ke Render produksi, jangan anggap kandungan READY semata-mata kerana ujian fail lulus.**