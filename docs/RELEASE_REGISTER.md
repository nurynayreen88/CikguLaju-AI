# CikguLaju AI — release register

**Satu tempat rujukan:** [Issue #496 — PUSAT RELEASE](https://github.com/nurynayreen88/CikguLaju-AI/issues/496).

Semua kerja pembaikan RPH, RPT, API Telegram, Web, kurikulum, Word/PDF, login dan kuota dari sesi atau chat berbeza hendaklah dirujuk pada Issue #496 terlebih dahulu. Issue itu ialah **senarai kerja & status semasa**, bukan fail ini yang mungkin ketinggalan.

## Aliran wajib

1. Catat isu, subjek/Tahun/PdP dan pautan PR sedia ada. **Sambung PR asal** jika skop sama; jangan menghasilkan patch baharu yang menggantikan kerja orang lain.
2. Bezakan status: `DRAF/HOLD` → `CI PASS` → `ACADEMIC APPROVED` → `MERGED main / merged production branch` → `DEPLOYED` → `LIVE VERIFIED`. Status ini tidak setara.
3. Semak sumber KPM/DSKP/RPT/SOW, SK, SP, Tajuk, Buku Teks/BA dan identiti PdP sebenar. Draf yang sekadar lulus format bukan kandungan READY.
4. Periksa branch destinasi, merge conflict, full diff, jenis fail dan checksum sebelum merge. Jangan cherry-pick PDF atau SQLite lama yang akan menimpa versi lebih baharu. **Khusus: #464 aset PI lama T3–T6 tidak boleh dipindah terus atas versi 56 PDF semasa; rujuk #489.**
5. Sebelum aktifkan kepada pengguna, uji Web dan Telegram sebenar: pilih Tahun/Subjek/Tajuk/PdP, jana Word/PDF, A4, Jawi, aktiviti guru/murid, akses berbayar dan 10 janaan percubaan. Kegagalan janaan tidak boleh mengurangkan kuota. Jangan ubah data pengguna, langganan, pembayaran atau DB asal ketika menyunting RPH.
6. Nyatakan sumber dan bukti CI, bukti audit akademik, URL PR, commit dan status deploy dalam Issue #496. Jika belum lengkap, kekalkan HOLD. Jangan umum LIVE semata-mata kerana merge.

## Titik semakan pertama — 10 November 2026

- **Sudah merged ke `main`:** #486 (BM), #493 (Maths private quality gate), #494 (MT6-079–084 HOLD). Status sebenarnya `LIVE VERIFIED` perlu disahkan berasingan.
- **Sudah merged ke cabang Web produksi:** #489 (RPT PDF note gate), #491 dan #492 (Maths Web quality/dependency hotfix). Cabang bukan bukti deploy.
- **Kekal HOLD:** #460, #464, #482, #487, #495, #443, #441, #322, #143, #277, #275, #449 dan lain-lain yang disenaraikan dalam Issue #496.
- Ini ialah gambar keadaan pada tarikh di atas; untuk kemas kini, rujuk Issue #496, keputusan PR terkini dan log deploy.

**Peraturan penerbitan:** bahan yang belum disahkan tidak boleh diberi label FINAL READY atau diterbitkan kepada pengguna hanya untuk mengejar kuantiti.
