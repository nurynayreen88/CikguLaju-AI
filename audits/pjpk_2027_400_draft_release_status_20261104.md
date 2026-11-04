# PJPK 2027 — keputusan semakan selepas susunan PK Tahun 2–6
**Tarikh:** 4 Nov 2026  
**Status:** STAGING. **0/400 RPH baharu READY**; tiada gabungan ke main, DB atau deployment.

## Inventori semasa
| Tahun | PJ DRAF | PK asal tematik/editorial DRAF | PK PdP baharu bernombor DRAF | Jumlah |
|---|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 (KP2027 perlukan DK sebenar) |
| 2 | 41 (termasuk empat sisipan Akuatik) | 18 | 35 | 94 |
| 3 | 38 | 9 | 32 | 79 |
| 4 | 34 | 9 | 32 | 75 |
| 5 | 33 | 12 | 32 | 77 |
| 6 | 34 | 9 | 32 | 75 |
| **Jumlah** | **180** | **57** | **163** | **400** |

## RPH Pendidikan Jasmani
- **176** RPH PJ bernombor PdP ditulis semula dengan aktiviti lebih khusus, format lebih ringkas dan PBD; **belum diuji Word A4 atau Telegram**.
- **4** sisipan Akuatik Tahun 2 berasingan, belum lulus kemudahan dan keselamatan.
- Tahun 6 PdP 033: SP 5.2.2 yang bercanggah telah dikeluarkan daripada **draf RPH cadangan**, tetapi sumber RPT 2027 asal belum diselaraskan; kekal BLOK.
- **31** cadangan halaman buku teks Tahun 5–6 ditemui daripada RPT 2026; masih belum disahkan secara visual pada buku asal.

## Pendidikan Kesihatan (PK)
- **163** PdP **cadangan CikguLaju** baharu diberi nombor Lesson:
  * Tahun 2: **35 × 30 minit = 17.5 jam** (PEERS 26, Pemakanan 5, Pertolongan Cemas 4 PdP).
  * Tahun 3: **32 × 30 minit = 16 jam** (PEERS 26, Pemakanan 4, Pertolongan Cemas 2 PdP).
  * Tahun 4–6: setiap tahun **32 × 30 minit = 16 jam** (PEERS 24, Pemakanan 5, Pertolongan Cemas 3 PdP).
- SK **1.1 dan 1.2**, serta **2.1 hingga 9.1**, disemak kewujudannya dalam DSKP dan dimasukkan. Pemetaan ini ialah **susunan calon**, bukan jadual KPM 2027 yang diluluskan.
- Dua fail RPT CSV: `rpt_staging/pjpk/pendidikan_kesihatan_2027_year2_year3.csv` dan `rpt_staging/pjpk/pendidikan_kesihatan_2027_year4_year6.csv`.
- 57 fail tematik/editorial asal dipelihara untuk audit silang; **bukan 57 PdP tambahan** yang harus dimasukkan dalam RPT, kerana boleh bertindan dengan 163 Lesson baharu.

## Gerbang pelepasan belum lulus
1. Semak semuka setiap objektif, aktiviti, teks SP, buku teks dan pentaksiran; audit teks automatik tidak setara pengesahan pedagogi.
2. Susun 163 PdP PK mengikut **takwim induk 2027 Kumpulan A/B**, jadual masa guru dan cuti negeri. Tiada minggu/tarikh diandaikan sebagai fakta.
3. Uji Word sebenar **A4 satu halaman** pada enjin RPH Telegram dan Web staging, termasuk turutan & teks Jawi jika terpakai.
4. Uji import DB versi baharu, FK/integrity/orphan/duplicate, backup, serta laluan Telegram dan Web. Jangan ubah DB asal.
5. KP2027 Tahun 1 belum diluluskan tanpa DK khusus; jangan campur standard KSSR lama atau label Tahun 1 READY.

**Keputusan:** semua 400 fail kekal `DRAFT_NOT_APPROVED` dan `production_ready=false`.
