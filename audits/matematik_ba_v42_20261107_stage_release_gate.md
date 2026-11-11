# Matematik v42 — arkib asal v41 ditemui, 234 RPH Buku Aktiviti disediakan (STAGING)

Tarikh audit: 7 November 2026. **Pelepasan: HOLD / DRAF, jangan merge atau deploy.**

## Lokasi fail sebenar
- Arkib asal v41 telah dipulihkan dari **ChatGPT Library**, bukan dari Drive/GitHub.
- Nama: `CIKGULAJU_MATEMATIK_v41_585_RPH_KANDUNGAN_DSKP_STAGING.zip`
- SHA-256 asal **disahkan**: `58e9f50701e26f318829f4730b38b20ae8eb4dbffb0e8b44987c315eab36bc89`
- Kit integrasi v41 `CIKGULAJU_MATEMATIK_v41_STAGING_INTEGRATION_KIT.zip` turut dipulihkan.
- v41 mengandungi **585 DOCX**, **585 PDF individu**, **585 Markdown**, lima PDF gabungan dan audit JSON/CSV. v41 asal tidak diubah.

## Output baharu
- **v42**: `CIKGULAJU_MATEMATIK_v42_585_RPH_BA_T2_T3_DRAF_STAGING.zip`
- Disimpan di Library: `/CikguLaju/Matematik_2027_STAGING/CIKGULAJU_MATEMATIK_v42_585_RPH_BA_T2_T3_DRAF_STAGING.zip`
- SHA-256 v42: `1a55a2c2f557f6394824f97b4f8f718313d12190636977d28dc2ecc4d3983601`
- **234 RPH Tahun 2–3** diubah secara terhad pada Word, Markdown dan PDF: `Aktiviti 3 — Buku Aktiviti/PBD • 10 min`, bahan dan rujukan topik + halaman bercetak Buku Aktiviti. Tempoh total **60 minit** dipelihara. Tidak mereka nombor latihan.
- **351 RPH Tahun 4–6** tidak diubah; 1,053 fail DOCX/MD/PDF individu disahkan byte-identical dengan v41. Bagi Tahun 4–6, gunakan BT/PBD tanpa rujukan BA palsu.
- Kedua-dua PDF gabungan Tahun 2 dan 3 dijana semula untuk sepadan dengan versi Word/PDF individu.
- Semua **585 PDF individu** masih satu halaman A4 mengikut audit v41 + v42. **234 PDF yang dikemas kini** diuji satu-satu: satu halaman A4, teks 'Aktiviti 3' + Buku Aktiviti dan tiada blok teks melepasi sempadan.
- ZIP penuh diuji CRC `testzip()==None`; bilangan fail akhir: 585 DOCX, 585 Markdown, 590 PDF (585 individu + 5 gabungan). Semakan visual sampel Word Tahun 2 dan Tahun 3 selesai tanpa clipping.

## Sumber Buku Aktiviti
- BA SK Tahun 2: 164 halaman PDF, offset +6 ke nombor halaman bercetak; SHA `1fac0d7984e9c8c725036dd3888d91df2a5138e9d776fed6574791e610a8f318`.
- BA SK Tahun 3: 158 halaman PDF, offset +3; SHA `43de2cbf17e63ef62433ee89274bdd593d48c65df166765a2e59f3194d579878`.
- 190 entri kandungan BA telah dipadankan kepada 234 calon lesson mengikut SP dan topik; 72 rujukan lama Tahun 2 v27 pernah sepadan dengan julat TOC; 9 sampel latihan diperiksa secara visual.
- **PENTING:** Rujukan topik+halaman yang dijumpai dalam TOC belum membuktikan kesemua butiran latihan dan pemilihan item individu sesuai dengan semua SP. Arahan dalam RPH ialah *guru memilih latihan yang menepati SP*. Ini draf yang boleh diuji, bukan pensijilan akademik.
- Sumber BA asal kekal dalam Drive pemilik, tidak dimasukkan ke GitHub.

## Gate penerbitan
- `0/585` mendapat **signoff akademik individu** dalam kerja v42 ini; tiada tuntutan palsu READY.
- Kesesuaian setiap soalan/aktiviti BA dengan SP, objektif dan PBD Tahun 2–3 mesti disahkan seorang demi seorang untuk kelulusan akademik.
- Tahun 4–6 perlu semakan Buku Teks individu dan pecahan 83→117 Tahun 4 sebelum FINAL READY.
- Staging API Telegram/Web + DB kanonik, takwim 2027 negeri dan ujian regresi belum dilaksanakan; **tidak diimport ke production**.
- PR ini kekal **draft staging**. Tiada perubahan pada `main`, Render production, database pengguna, kuota atau pembayaran.

Sila rujuk `audits/matematik_ba_v42_234_candidate_manifest_20261107.csv` serta artifak v42 di Library.
