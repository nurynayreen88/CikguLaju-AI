# Pendidikan Moral Tahun 2–6 — liputan 96 sesi / 96 jam (CikguLaju)

**Versi kerja berasaskan DSKP, bukan pengesahan penuh halaman aktiviti buku teks atau jadual setiap kelas.** Dikemas kini 4 November 2026.

## Bahan tersedia
- **210 RPH teras** (42 Tahun 2–6 setiap tahun) kekal dalam `rph_standalone/pendidikan_moral/yearN/lesson_001.md` dan seterusnya.
- **270 RPH pengukuhan** (54 setahun) diwujudkan dalam `rph_standalone/pendidikan_moral/pengukuhan/yearN/sesi_###.md`. Semuanya mempunyai rujukan kod/teks SP daripada crosswalk DSKP, objektif, langkah guru dan murid, 5+20+20+10+5 minit, BBM dan evidens PBD.
- Setiap tahun mempunyai **96 baris** dalam `yearN_96h_coverage_PLANNING.csv`: 42 TERAS + 54 PENGUKUHAN. Lima tahun = 480 sesi terancang.
- Sepuluh CSV RPT `yearN_sequence_96_2027_groupA_STAGING.csv` dan `...groupB_STAGING.csv`, setiap satu 96 sesi dengan sumber minggu **M01–M44** daripada tab `INDUK MINGGU RPT 2027 A B` dalam spreadsheet CikguLaju `1tf6-B6hmA4U6E0fCROcKpxh-B5uLUQOYBt6TZft_7_k`.
- Laluan muat turun dalam `complete_96_downloads.py` membina sepuluh RPT PDF A4 landskap Kumpulan A/B, lima PDF RPH pengukuhan (54 halaman/tahun), dan lima fail Word boleh sunting (54 RPH/tahun). Butang khusus diletakkan dalam menu RPT 2027 **berbayar sahaja**. Callback RPT 42 PdP lama masih boleh dipanggil daripada mesej lama tetapi tidak dipromosikan dalam menu.
- **Laluan 42 RPH teras melalui pemilih Telegram asal tidak diubah**. Pengukuhan 54 sesi tersedia sebagai pakej muat turun berasingan; pengukuhan tidak diselit ke pemilih PdP/RPH Hari Ini yang bergantung database 42-teras.

## Pengesahan teknikal
`scripts/check_moral_96h_planning.py` memeriksa setiap fail 480 sesi, padanan SP dan 960 baris jadual kumpulan A/B. `scripts/check_moral_96_downloads.py` memeriksa penjanaan PDF/Word untuk lima tahun, bilangan halaman PDF, menu muat turun dan kawalan akses melalui simulasi Telegram. `scripts/check_pm_80_beta.py` dan ujian database lama turut dikekalkan. Semua fail Moodle/Moral ini berada dalam kawalan versi; tiada mutasi terhadap DB pengguna, langganan atau subjek lain.

## Batasan — jangan tandakan FINAL READY 100%
1. Sumber halaman buku teks bagi sebahagian besar sesi masih **permulaan unit (VERIFIED_TOC_START_ONLY)**, bukan pemeriksaan visual setiap aktiviti untuk SP. Hanya subset aktiviti dalam `audits/pendidikan_moral_y2_y6_units02_03_visual_30pdp_20261104.json` telah dipadankan khusus (33 RPH teras).
2. Penambahan 54 sesi/tahun ialah **agihan kerja 60 minit** untuk mencapai sasaran perancangan 96 jam; **bukan** bilangan sesi rasmi atau keperluan jadual waktu KPM 2027. Minit sebenar mengikut sekolah.
3. RPT A/B menetapkan **julat minggu induk M01–M44**, bukan tarikh PdP individu; cuti negeri, cuti gantian, hari subjek, aktiviti rasmi dan jadual kelas mesti diambil daripada profil guru sebelum menetapkan tarikh sebenar.
4. Audit pedagogi manual, ketepatan halaman aktiviti semua RPH, paparan Word satu halaman A4 bagi setiap RPH, dan ujian sebenar penghantaran akaun Telegram masih diperlukan. Ujian CI menghantar fail melalui mock, bukan bot kepada akaun guru.
5. Fail `yearN_sequence_DRAF.csv` dan flag sumber `DRAF_SEMAK` asal dikekalkan untuk kompatibiliti, bukan ditimpa atau ditanda palsu READY. Audit lama `scripts/check_pendidikan_moral_release_readiness.py` ialah **pintu FINAL READY** berasingan dan masih mempunyai isu belum ditutup.

**Prinsip pelepasan:** Memastikan versi yang boleh digunakan sebagai cadangan CikguLaju tidak bermaksud semua sumber dan kalendar mendapat kelulusan rasmi.
