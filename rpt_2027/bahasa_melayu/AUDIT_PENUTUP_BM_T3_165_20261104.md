# AUDIT PENUTUP STRUKTUR — BM Tahun 3 RPT/RPH 2027 (4 November 2026)

**Status akademik: DRAF / HOLD — tiada READY.**

## 1. Kelengkapan fail yang disahkan secara langsung dalam GitHub staging
- **165/165** fail `rph_standalone/bahasa_melayu/year3/lesson_001.md` hingga `lesson_165.md` tersedia, ID unik, tiada nombor tertinggal.
- **165/165** rekod RPT Tahun 3 tersedia dalam format Markdown dan HTML, setiap satu ID unik.
- Audit metadata Markdown–HTML RPT menggunakan pembacaan kedua-dua fail: **0 perbezaan dalam medan yang diperiksa**.
- Penambahan sesi ini: 85 fail RPH baharu Lesson 081–165, enam pembetulan berpandukan Buku Teks Jilid 2/BA2/DSKP; tiada perubahan kepada tahun atau subjek lain.
- Tahun 3 merangkumi **24 Unit, 44 slot minggu** pada RPT gabungan A+B; penempatan minggu bukan pengesahan tarikh PdP negeri.

## 2. Taburan status
| Kumpulan Lesson | DRAF | HOLD | READY |
|---|---:|---:|---:|
| 001–080 (audit sebelumnya) | 45 | 35 | 0 |
| 081–120 (batch baharu) | 17 | 23 | 0 |
| 121–165 (batch baharu + 6 dibetulkan) | 29 | 16 | 0 |
| **JUMLAH** | **91** | **74** | **0** |

Kiraan status ialah gabungan audit asal dan fail baharu yang ditulis dalam sesi ini; bukan keputusan semakan pedagogi penuh untuk 165 sesi.

## 3. Sumber dan pembetulan yang telah disahkan
- DSKP BM Tahun 3, Buku Aktiviti Jilid 1 dan 2 (DBP) dibaca untuk memandu aktiviti.
- Buku Teks Jilid 2 disemak secara terus bagi enam pembetulan: Lesson **127, 130, 131, 133, 146, 165**. Rujuk `AUDIT_PEMBETULAN_BT_BA_DSKP_T3_20261104.md`.
- Sumber 2026 masih asas susunan Lesson; apabila bertentangan dengan BT/DSKP, sumber primer dipentingkan dan jejak perubahan dilaporkan.
- Konflik lain: 089, 076–080, ulangan/PKJR dan Lesson bertajuk terpotong kekal HOLD sehingga ada keputusan sumber.

## 4. Pintu untuk READY yang masih ditutup
1. Semakan akademik semua 165 SK/SP dan tajuk, halaman BT/BA termasuk dua jilid dan 74 rekod HOLD.
2. Keputusan khusus bagi Lesson berulang serta pengayaan dan modul PKJR.
3. Semakan Agihan 44 minggu terhadap kalendar negeri 2027, cuti umum/cuti gantian dan slot jadual guru.
4. Cetakan satu muka surat A4 untuk setiap RPH dan RPT Word landscape; pemeriksaan visual PDF/Word belum dibuat.
5. QA/CI melalui runtime serta integrasi database Telegram/Web dan kelulusan guru. Skrip QA struktur disediakan pada `tools/qa_bm_year3_structure_20261104.py`, **tetapi belum dijalankan**.
6. Penerbitan ke produksi tidak diizinkan sebelum semua pintu lulus.

## Kawalan versi
Semua perubahan dibuat pada `staging/bm-rpt-2027-20261103`. `main`, data kurikulum aktif, Telegram, Web dan pengguna **tidak diubah**.

## Sumber
- Buku Teks BM SK Tahun 3 Jilid 2 DBP 2018: https://fliphtml5.com/hkvtu/gpia/Bahasa_Melayu_Tahun_3_SK_Jilid_2/
- Buku Aktiviti Tahun 3 Jilid 1: https://drive.google.com/file/d/1WoaWY-FgDVhJTZjQI16T3Ol6jFvmlGOg/view
- Buku Aktiviti Tahun 3 Jilid 2: https://drive.google.com/file/d/1ln3x1r0kXSXIBJObUIG1iUaas0jGFkt0/view
- DSKP BM Tahun 3: https://drive.google.com/file/d/1q-Mdq8kIZGui7-IccvSGJx1dfMjIOAQN/view
