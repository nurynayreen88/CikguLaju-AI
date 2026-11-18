# RPT dan RPH Sains SK Tahun 6 2027 sebelum UASA

Sumber ialah [RPT dan indeks Web](https://github.com/nurynayreen88/CikguLaju-AI/tree/57aa5be4c9c0cc8511a545ee88dfb4423df50cb9). Semua 89 PdP mengekalkan nombor, urutan, padanan SK/SP dan tempoh asal. Tajuk PdP 012–015 dalam Unit 3 diperbetulkan mengikut SP 3.1.2–3.1.5. PdP 085–089 dalam Unit 1 diajar dahulu. PdP 001–084 menyusul dalam Unit 2–13. Kesemua 96 kod SP meliputi [DSKP Sains Tahun 6 KSSR Semakan 2017, BPK September 2021](https://anyflip.com/qqfu/esbw/basic/51-94). Rujukan halaman bercetak dalam draf diambil daripada [Buku Teks Sains Tahun 6 SK edisi Bahasa Melayu, DBP 2021](https://anyflip.com/ukjk/xril/basic/), ISBN 978-983-49-3278-7.

## Agihan 64 jam

Agihan menggunakan 50 sesi 30 minit dan 39 sesi 60 minit dalam 35 minggu pengajaran. Had cadangan tiga sesi seminggu mengekalkan jumlah masa. M08, M13, M26 dan M36 mempunyai 150 minit. Tujuh minggu yang diberi had 90 minit digunakan untuk membantu perancangan slot sekolah. Guru menyesuaikan hari dan masa dengan jadual waktu serta cuti negeri.

PdP terakhir ialah 17–21 Oktober bagi Kumpulan A dan 18–22 Oktober bagi Kumpulan B, pada M38. Tiga belas PdP dari M39–44 dialihkan. M06 dan M19 tiada PdP baharu, M18 dikhaskan untuk pentaksiran dan M39–44 tersedia untuk ulang kaji, UASA dan aktiviti sekolah. M10 Kumpulan A bermula 15 Mac selepas cuti tambahan Aidilfitri. Sumber tarikh ialah [Kalendar Akademik KPM 2027](https://www.moe.gov.my/index.php/surat-siaran-kpm-bil1-tahun-2027-kalendar-akademik).

## Padanan RPH

- Lima RPH Unit 1 menggunakan sumber [Kemahiran Saintifik](../docs/SAINS_UNIT_AWAL_20261113.md). Baki 84 RPH menggunakan [bank aktiviti Sains Tahun 6 sedia ada](../web/sains_y6_84_activity_bank_draf_20261107.py). Setiap RPH mempunyai tugasan PBD individu serta tempoh untuk tindakan guru dan murid.
- PdP 021 menggunakan anak pokok yang disediakan lebih awal. PdP 036 memisahkan ujian geseran mengikut permukaan dan jisim. PdP 053 membandingkan dua kaedah untuk buah yang sama dengan rekod susulan bertarikh. PdP 077 dan 079 menggunakan bahan yang siap dipotong untuk amali 30 minit.
- PdP 013 mengukur perubahan lilitan belon dalam penyiasatan yis pembakar berpandukan Aktiviti 1, m/s 36–37. Murid melengkapkan pemerhatian pergerakan dan pertumbuhan dengan rakaman serta foto bertarikh mengikut fokus m/s 37–39.
- PdP 014 menggunakan faktor nutrien pada m/s 43. Murid memulakan eksperimen yis pembakar dengan gula sebagai pemboleh ubah dan merekod kiraan sel awal. PdP 016 melengkapkan bacaan susulan serta laporan individu. Kiraan sel pada grid yang sama saiz digunakan sebagai evidens pertumbuhan. Guru menyemak selang masa bacaan dan kemudahan mikroskop ketika menyemak draf.

## Eksport dan status

Jalankan `PYTHONDONTWRITEBYTECODE=1 python -m staging.sains.tahun6.eksport_2027 --output /tmp/Sains_SK_Tahun_6`. Eksport menghasilkan RPT Word serta 89 RPH Word dan PDF. RPT Word dan PDF semakan mempunyai 13 halaman A4 landskap. Ujian setempat membandingkan identiti serta minit semua rekod terhadap RPT sumber, menyemak 44 julat A/B dan mengesahkan setiap RPH satu halaman A4 dalam kedua-dua format.

Dua set ujian setempat untuk takwim Sains dan bank Sains Tahun 6 lulus 16/16 selepas keluaran rujukan dibina semula. Semakan khusus Unit 3 mengesahkan tajuk, padanan SP, amali PdP 013–014 dan penyambungan bacaan ke PdP 016 pada fail yang baru dieksport.

**HOLD semakan guru dan CI.** Fail ini sedia untuk semakan. Penerbitan dan muat turun melalui akaun guru di Web dan Telegram belum diuji.
