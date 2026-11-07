# Pendidikan Islam 2027 — 690 RPH DRAF untuk semakan

**Bukan FINAL READY. Bukan RPH rasmi yang diperakui.**

Asal: 696 DOCX dalam pakej V5 yang telah diaudit sebelum ini. Salinan sumber tahun berasingan mengandungi 690 draf yang boleh dibaca, bersama 6 rekod *held* tanpa kandungan untuk diedarkan. Tidak ada perubahan pada DB pengguna, kuota atau bayaran.

## Kandungan

| Tahun | Rekod | Draf pratonton | Ditahan |
|---|---:|---:|---:|
| 2 | 112 | 111 | 1 |
| 3 | 147 | 147 | 0 |
| 4 | 151 | 151 | 0 |
| 5 | 143 | 143 | 0 |
| 6 | 143 | 138 | 5 |
| **Jumlah** | **696** | **690** | **6** |

Ditahan: Tahun 2 Lesson 035; Tahun 6 Lesson 006, 014, 018, 060, 117.

Teks setiap draf berasal daripada RPH Word V5, dengan cap integriti asal dikekalkan. Nota footer `STATUS` dan **187 rekod halaman buku teks lama yang belum diperakui** dikeluarkan daripada salinan bacaan, bukan diubah dalam sumber asal. Kandungan SK/SP, objektif, aktiviti, PBD dan teks Jawi tidak dibetulkan secara automatik. Semua aktiviti dan padanan sumber masih memerlukan semakan guru.

`pi_review_catalog.py` ialah pembaca data dan pemetaan draf untuk pengujian **sahaja**. Ia tidak didaftarkan ke bot Telegram atau Web, tidak menyentuh database dan tidak memintas hak langganan/kuota. Fungsi `preview_rows` tidak dipasang automatik. Sesiapa yang ingin memasang sumber ini pada runtime mesti menggunakan pintu akses sedia ada dan menguji Word/PDF secara berasingan.

Jangan menandakan mana-mana rekod sebagai READY tanpa bukti pengesahan individu. Jangan membuka enam rekod *held*. Penyelesaian lapan pengecualian tasmi' ialah panduan pilihan guru, bukan kod SP baharu.

## Kemas kini staging 7 Nov 2026 — PR #443 (belum diluluskan)

Catatan sejarah di atas menerangkan **katalog asal**. Pada cabang `staging/rph80-pendidikan-islam-second-20261107`, 560 draf ditambah langkah PdP/PBD (masih belum disahkan pakar) dan aktiviti lain dinomborkan; **tiada** rekod yang bertukar status READY. Bilangan draf kekal 690, rekod ditahan kekal 6. Pembetulan staging tidak membuktikan teks/halaman buku asal atau pengesahan 80%.

Audit Buku Aktiviti:
- **174** calon latihan BA daripada 258 draf Tahun 2–3; **84** fokus kepada pentaksiran lisan/bacaan/hafazan/tasmi' tanpa paksaan BA.
- Fail kerja editor tetap: [PI_BA_REVIEW_REGISTER_174_STAGING.csv](./PI_BA_REVIEW_REGISTER_174_STAGING.csv) — mengandungi kod KPM **BA102001/BA103001**, 42 petunjuk halaman PdPR dengan URL, serta ruangan untuk pengesahan langsung. **Semua halaman bercetak dan arahan latihan asal masih belum disahkan.**
- Laporan lengkap: [STAGING_QUALITY_REPORT_20261107.md](./STAGING_QUALITY_REPORT_20261107.md).
- CI menghasilkan 11 artefak sementara dan menyemak kewujudan setiap fail (termasuk CSV); fail asal/latihan buku berhak cipta tidak dimuat naik semula.

**Dilarang menerbitkan petunjuk halaman sekunder sebagai halaman BA yang telah disahkan.** PR #443 ialah DRAFT/HOLD; ia bukan perubahan live Telegram/Web, bukan pengesahan Word/PDF satu halaman dan bukan pemberian akses muat turun buku.


### Draf editor berasingan, bukan Web/Telegram LIVE

Bagi 690 RPH Tahun 2–6, alat `pi_editor_material_projection.py` memisahkan **523 catatan audit / sumber lama** daripada senarai Bahan dalam paparan editor; semua nota asal disimpan secara utuh di medan editor berserta hash rujukan. Katalog dan RPH asal **tidak ditimpa**. Artefak `pi_editor_material_preview_690.json` ialah pratonton terasing, bukan pembekal bahan READY. Ujian automatik menyemak semua 690 draf dan 6 rekod ditahan.

Status Buku Aktiviti Tahun 2–3 masih **174 calon / 0 halaman disahkan pada buku asal**. Jangan isi halaman RPH berdasarkan OCR rosak, perkongsian video atau modul PdPR sahaja. Ini bukan pengesahan 80% kualiti akademik.
