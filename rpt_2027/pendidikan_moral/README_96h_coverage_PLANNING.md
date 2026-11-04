# Pendidikan Moral Tahun 2–6 — perancangan liputan 96 jam (STAGING)

**Status: PELAN SAHAJA, BUKAN RPH/RPT FINAL READY.** 4 November 2026.

## Angka yang boleh diaudit
- Setiap tahun: 42 PdP teras sedia ada × 60 minit = 42 jam.
- Jurang terhadap **sasaran perancangan** 96 jam: **54 jam/tahun**.
- 14 unit/tahun: unit 1 dan 14 mendapat tiga cadangan pengukuhan; 12 unit lain mendapat empat cadangan. Jumlah 54 pengukuhan.
- Setiap fail `yearN_96h_coverage_PLANNING.csv` mengandungi 96 slot, mengikut turutan unit, dengan **42 pautan RPH teras** dan **54 slot tambahan yang BELUM mempunyai RPH**.
- Lima tahun: 210 RPH teras tersedia; 270 sesi pengukuhan masih memerlukan RPH, sumber aktiviti, rubrik PBD, Word/PDF dan QA.

## Keterbatasan dan prinsip
- Sesi perancangan 60 minit ialah andaian kerja untuk membandingkan jam tahunan, **bukan** jadual waktu atau bilangan PdP rasmi KPM. Jumlah waktu sebenar dan pembahagian PdP 2027 perlu disahkan.
- Masa, minggu dan tarikh Kumpulan A/B sengaja tidak diisi; jangan mengagihkan tarikh tanpa jadual sekolah dan takwim/cuti negeri yang disahkan.
- Kod SP dan fokus pengukuhan diambil daripada lima fail DSKP crosswalk sedia ada. Indeks buku hanya halaman mula unit `VERIFIED_TOC_START_ONLY`; **tiada dakwaan halaman aktiviti tepat bagi 270 slot baharu**.
- Pelan ini **tidak digunakan oleh Telegram/web/penjana RPH**, bukan pengganti lima CSV RPT 42 PdP yang sudah live, dan tidak mengubah database pengguna, kuota, pembayaran atau subjek lain.
- Jangan menandakan `PERLU_RPH_DAN_SEMAKAN_BUKU` sebagai READY. Langkah seterusnya ialah menyediakan RPH sumber-sepadan secara batch, audit format satu halaman A4, kemas kini jadual 2027 dan uji penghantaran sebenar.

## Rujukan peruntukan
- Sasaran perancangan 96 jam/tahun diambil daripada semakan terdahulu dalam `scripts/check_pendidikan_moral_release_readiness.py`, yang merujuk jawapan Parlimen 30 Julai 2025. Keserasian takwim/kurikulum 2027 masih perlu diperiksa sebelum pelancaran penuh.
