# Pendidikan Muzik — Release Gate Word/PDF Telegram–Web (6 November 2026)

**Status:** DRAF / TIDAK UNTUK LIVE. Ini **audit integrasi**, bukan penyelesaian runtime atau bukti fail Word/PDF berjaya dijana.

## Bukti konfigurasi semasa

1. `web/native_rph_telegram_api.py` mempunyai peta `SUBJECTS` untuk ENGLISH, BM, MATH, SCIENCE, PI, MORAL, PJPK dan PSV; **MUZIK belum disenaraikan**. `build_native_input()` menolak subjek yang tidak tersenarai.
2. `web/rph_shared_source_identity.py` menggunakan `source_paths()` untuk membina digest fail RPH/mapping bagi subjek tertentu. **MUZIK belum mempunyai laluan sumber**, maka ia belum boleh lulus mekanisme padanan identiti Word/PDF Web–Telegram.
3. RPH Muzik kini berada dalam **staging/pendidikan_muzik/rpt_rph_2027/year{2..6}/rph_pdp_{01..35}.md** dan manifest tahunan. Tiada bukti bahawa parser layout Telegram sedia ada boleh membaca format Markdown ini secara terus.
4. Runtime sepunya memerlukan struktur `telegram-native-rph-v1`, header metadata, 3 fasa dan 2 medan footer, sementara setiap RPH Muzik mempunyai set induksi, dua aktiviti, pengukuhan dan penutup. Adapter ujian perlu mengekalkan **semua kandungan aktiviti, SK/SP, tarikh, masa, kelas, penilaian dan refleksi** dalam jadual native (bukan membuang fasa).
5. **Tiada fail Word/PDF Muzik yang telah dirender dan diperiksa satu halaman A4**. Kejayaan CI audit manifest bukan bukti cetakan atau kesamaan Telegram–Web.

## Urutan kerja sebelum mempertimbangkan FINAL READY

- **Kurikulum:** keputusan semakan berautoriti bagi konflik SP Tahun4 (PdP21,24 dan SK 4.1 / SP 4.2.1), skop not kreatif B/A/G berbanding G/A/B/C’, dan status 8 PdP pengukuhan cadangan. Jangan menyamakan semakan teks buku dengan kelulusan.
- **Takwim:** 175 padanan slot minggu ke indeks induk lulus, tetapi padanan hari sebenar perlu menggunakan indeks 16 negeri, cuti perayaan, gantian, jadual guru dan penanda minggu tanpa PdP. Jangan alihkan Lesson/PdP kerana minggu 0 hari kelas.
- **Sumber immutable:** apabila kurikulum lulus, tentukan satu set fail yang sama (RPH, manifest, RPT/mapping yang disahkan) dan digest sumber yang digunakan Telegram serta Web; **jangan fallback senyap** ke kandungan lain.
- **Adapter format:** sediakan pembentuk layout `telegram-native-rph-v1` bagi Muzik menggunakan generator sebenar (bukan penjana Word kedua yang menghasilkan format berlainan).
- **Ujian fail:** jana **175 DOCX dan 175 PDF** dalam ruang ujian terkawal, buka/parse kedua-duanya untuk jadual SK/SP, objektif, fasa, bahan, masa/kelas dan bilangan halaman A4. **Bukti satu halaman setiap RPH belum ada**.
- **Pengesahan suara/audio:** nombor Audio buku tidak membuktikan fail/lesen/track sah. Jangan mengaktifkan button fail audio sebelum bukti padanan lengkap.
- **Kawalan operasi:** tambah laluan MUZIK ke Web/Telegram hanya setelah ujian staging lulus, tanpa menjejaskan quota percuma, pembayaran, akaun, referral atau DB pengguna. Uji penjanaan sama pada dua platform dan aktifkan hanya release yang diluluskan.

**Laluan sumber:** `web/native_rph_telegram_api.py`; `web/rph_shared_source_identity.py`; `tests/test_pendidikan_muzik_rpt_rph_2027_staging.py`; `year4/AUDIT_SK_SP_DSKP_BUKU_20261106.md`; `KALENDAR_2027_WEEK_SLOT_AUDIT_20261106.md`.

**Keputusan teknikal:** **BLOCKED — NOT FINAL READY**. Dokumen ini tidak membuat perubahan kepada `web/`, `app.py`, sumber runtime atau produksi.


## Staging source-digest prototype (6 Nov 2026)
Kawalan asal `web/rph_shared_source_identity.py` masih belum mengenali MUZIK. Modul `music_source_identity_staging.py` mengira fingerprint SHA-256 lima fail sumber untuk 175 PdP serta fail closed pada symlink/hilang/mutasi; tidak didaftarkan sebagai sumber runtime. Rujuk `MUSIC_SOURCE_IDENTITY_STAGE_AUDIT_20261106.md`. Fingerprint **bukan** kelulusan kurikulum atau penerbitan.
