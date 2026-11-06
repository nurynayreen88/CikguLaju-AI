# RPT Muzik 2027 — Audit hari calon PdP mengikut 16 negeri (6 November 2026)

**Sumber read-only:** [CIKGULAJU_RPT_2027_KALENDAR_CUTI_FINAL_VERIFIED, tab INDEKS PDP 2027 DIKIRA](https://docs.google.com/spreadsheets/d/1tf6-B6hmA4U6E0fCROcKpxh-B5uLUQOYBt6TZft_7_k/edit). Sumber mengandungi 5,840 rekod tarikh negeri sepanjang 2027, 16 negeri/WP × 365 hari. Indeks sumber dibekukan pada 28 Okt 2026 mengikut tab STATUS RELEASE 2027; masih tertakluk warta/KPM kemudian.

**Kaedah pengiraan:** Bagi setiap negeri, gunakan Kumpulan A/B yang direkodkan. Padankan 35 slot berangka M01–M35 daripada snapshot induk GitHub kepada tarikh di jadual harian negeri. Hitung sebagai **hari calon PdP**, hanya rekod yang `Status PdP Dikira` bermula dengan `CALON PDP`. Label sumber `CALON PDP - CUTI GANTIAN BELUM AUDIT` menuntut semakan masa hadapan; angka positif **bukan jaminan sesi sebenar**. Kelas boleh tiada subjek Muzik pada hari sekolah.

**Keputusan:** 560 kombinasi negeri×slot diperiksa (16×35). **32 kombinasi berkandungan 0 hari calon PdP**, semuanya slot **M06 dan M19 bagi setiap satu daripada 16 negeri**; 528 kombinasi lain mempunyai lebih daripada satu hari calon PdP; tiada kombinasi tepat satu hari.

| Slot | Tarikh Kumpulan A | Tarikh Kumpulan B | Calon hari PdP dalam indeks | Tindakan |
|---|---|---|---|---|
| M06 / **PdP06 semua Tahun 2–6** | 7–11 Februari 2027 | 8–12 Februari 2027 | **0 di semua 16 negeri** | **PDP_ANJAL**, guru/jadual negeri pilih tarikh sebenar sebelum menjana |
| M19 / **PdP19 semua Tahun 2–6** | 16–20 Mei 2027 | 17–21 Mei 2027 | **0 di semua 16 negeri** | **PDP_ANJAL**, guru/jadual negeri pilih tarikh sebenar sebelum menjana |

Ini ialah **10 PdP unik (2 setiap tahun)** yang perlu diberi amaran kerana penggunaan minggu asal tidak sesuai. **Jangan** membuang, menomborkan semula, atau memindahkan PdP ke minggu lain secara automatik; identiti setiap PdP dikekalkan dan pengesahan tarikh mesti dibuat mengikut hari/jadual guru. Rujuk `KALENDAR_2027_HARI_PDP_16_NEGERI_AUDIT.json` untuk hitungan setiap negeri/slot.

**Bukan FINAL READY:** Kesahihan cuti negeri, pengumuman tambahan dan cuti gantian masa hadapan boleh berubah. Kira semula apabila sumber berubah. Tiada perubahan pada kalendar Drive, data pengguna atau runtime Telegram/Web.
