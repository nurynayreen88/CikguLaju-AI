# Matematik 2027 v29 — pemulihan SP/Fokus berasaskan DSKP (5 Nov 2026)

**CALON STAGING SAHAJA. BUKAN FINAL READY. JANGAN MERGE / DEPLOY.**

Salinan baharu Word/PDF Tahun 2–6 dijana daripada dokumen v28 Google Drive. Fail asal v28, GitHub `main`, database, telegram/web, langganan dan Render tidak diubah. Sumber ayat SP penuh ialah PDF DSKP Matematik bagi tahun masing-masing; tiada SP direka.

| Tahun | Sel SP dipulihkan | Fokus PdP dipulihkan | Lesson elipsis masih ada | Halaman PDF staging |
|---|---:|---:|---:|---:|
| 2 | 0 | 0 | 0 | 21 |
| 3 | 5 | 30 | 0 | 31 |
| 4 | 6 | 0 | 45 | 35 |
| 5 | 10 | 40 | 0 | 35 |
| 6 | 23 | 31 | 0 | 35 |
| **Jumlah** | **44** | **101** | **45** | — |

Tahun 4 masih ada **61 tanda elipsis aktiviti** dalam **45 Lesson**, serta **68 Lesson** mempunyai catatan `PdP perlu dilengkapkan/disahkan`. Kandungan ini tidak dipotong/dipadam secara automatik; perlu dibandingkan dengan 83 RPH sumber v15 dan Buku Teks/Buku Aktiviti sebelum siap.

## Ujian PDF calon

- Lima DOCX berjaya dirender sebagai lima PDF A4 landscape tanpa halaman kosong.
- Setiap PDF masih mempunyai ID Lesson **001–117** dan minggu **01–44** secara lengkap.
- Pemeriksaan kotak teks tidak menemui teks di luar sempadan fizikal halaman.
- Pakej ZIP salinan calon bersama laporan JSON dan SHA-256 disediakan sebagai **lampiran perbualan ChatGPT**, bukan aset yang diaktifkan dalam aplikasi. **Jangan tukar fail PDF `main` tanpa lulus release gates.**

## Gate terbuka

1. Lengkapkan 45 Lesson Tahun 4 dan 68 nota belum siap daripada bukti RPH sumber, bukan mengada-adakan aktiviti.
2. Sahkan halaman BT/BA dan kesesuaian pedagogi **setiap** Lesson/RPH; kod SP wujud bukan kelulusan akademik.
3. Buktikan 585/585 pemetaan Lesson→RPH yang tepat, Word/PDF RPH 1 halaman A4, dan PBD yang benar-benar boleh digunakan.
4. Uji kalendar negeri/cuti 2027, kawalan akses, muat turun Telegram, pengasingan pengguna, serta regresi subjek lain pada staging.
5. Selepas semua ujian lulus, semak diff terhadap `main` semasa, dan buat backup sebelum merge secara terhad.

Rujukan: [Audit main v28](./matematik_585_lesson_main_pdf_release_gate_20261105.md), [Sumber Word v28 Drive](https://drive.google.com/drive/folders/1GtPmahAZTo5nKaCdWf4g3CcEirUqZpkN), [Buku Teks Tahun 4](https://drive.google.com/file/d/14YFkZnDxLQA_OpFMpI_eJQCTjUfQRDtZ/view).
