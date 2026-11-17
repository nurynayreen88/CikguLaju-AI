# RPT dan RPH Sains SK Tahun 6 2027 sebelum UASA

Sumber ialah [RPT dan indeks Web](https://github.com/nurynayreen88/CikguLaju-AI/tree/57aa5be4c9c0cc8511a545ee88dfb4423df50cb9). Semua 89 PdP mengekalkan nombor, urutan, padanan SK/SP dan tempoh asal. PdP 085–089 dalam Unit 1 diajar dahulu. PdP 001–084 menyusul dalam Unit 2–13. Kesemua 96 kod SP meliputi [DSKP Sains Tahun 6 KSSR Semakan 2017, BPK September 2021](https://anyflip.com/qqfu/esbw/basic/51-94). Rujukan halaman bercetak dalam draf diambil daripada [Buku Teks Sains Tahun 6 SK edisi Bahasa Melayu, DBP 2021](https://anyflip.com/ukjk/xril/basic/), ISBN 978-983-49-3278-7.

## Agihan 64 jam

Agihan menggunakan 50 sesi 30 minit dan 39 sesi 60 minit dalam 35 minggu pengajaran. Had cadangan tiga sesi seminggu mengekalkan jumlah masa. M08, M13, M26 dan M36 mempunyai 150 minit. Tujuh minggu yang diberi had 90 minit digunakan untuk membantu perancangan slot sekolah. Guru menyesuaikan hari dan masa dengan jadual waktu serta cuti negeri.

PdP terakhir ialah 17–21 Oktober bagi Kumpulan A dan 18–22 Oktober bagi Kumpulan B, pada M38. Tiga belas PdP dari M39–44 dialihkan. M06 dan M19 tiada PdP baharu, M18 dikhaskan untuk pentaksiran dan M39–44 tersedia untuk ulang kaji, UASA dan aktiviti sekolah. M10 Kumpulan A bermula 15 Mac selepas cuti tambahan Aidilfitri. Sumber tarikh ialah [Kalendar Akademik KPM 2027](https://www.moe.gov.my/index.php/surat-siaran-kpm-bil1-tahun-2027-kalendar-akademik).

## Padanan RPH

- Lima RPH Unit 1 menggunakan sumber [Kemahiran Saintifik](../docs/SAINS_UNIT_AWAL_20261113.md). Baki 84 RPH menggunakan [bank aktiviti Sains Tahun 6 sedia ada](../web/sains_y6_84_activity_bank_draf_20261107.py). Setiap RPH mempunyai tugasan PBD individu serta tempoh untuk tindakan guru dan murid.
- PdP 021 menggunakan anak pokok yang disediakan lebih awal. PdP 036 memisahkan ujian geseran mengikut permukaan dan jisim. PdP 053 membandingkan dua kaedah untuk buah yang sama dengan rekod susulan bertarikh. PdP 077 dan 079 menggunakan bahan yang siap dipotong untuk amali 30 minit.
- PdP 013–014 menilai tafsiran foto dan data pemerhatian. Evidens pelaksanaan penyiasatan dan eksperimen bagi SP 3.1.3–3.1.4 memerlukan pengesahan guru. Halaman buku berfungsi sebagai rujukan topik dan amali, dengan kesesuaian tugasan masih dalam semakan guru.

## Eksport dan status

Jalankan `PYTHONDONTWRITEBYTECODE=1 python -m staging.sains.tahun6.eksport_2027 --output /tmp/Sains_SK_Tahun_6`. Eksport menghasilkan RPT Word serta 89 RPH Word dan PDF. RPT Word dan PDF semakan mempunyai 13 halaman A4 landskap. Ujian setempat membandingkan identiti serta minit semua rekod terhadap RPT sumber, menyemak 44 julat A/B dan mengesahkan setiap RPH satu halaman A4 dalam kedua-dua format.

Ujian integrasi lama memerlukan Flask dan keluaran binaan sejarah yang tiada dalam persekitaran ini. Semakan khusus 2027 dijalankan terus terhadap RPT sumber dan fail yang baru dieksport.

**HOLD semakan guru dan CI.** Fail ini sedia untuk semakan. Penerbitan dan muat turun melalui akaun guru di Web dan Telegram belum diuji.
