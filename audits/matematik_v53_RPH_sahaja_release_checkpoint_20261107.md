# Matematik v53 — audit RPH sahaja, tiada kerja RPT

**7 November 2026 • DRAF STAGING • QA ARKIB LULUS / BELUM FINAL READY AKADEMIK**

## Perkara yang diperbaiki
- **32 RPH Matematik Tahun 2–6** disunting pada **47 bahagian**:
  - 13 set induksi untuk geometri Tahun 2 (L106–L110) dan Tahun 3 (L100–L107), menggantikan alat `jangka sudut` yang tidak relevan dengan model kubus, prisma, poligon dan paksi simetri.
  - 13 aktiviti Buku Aktiviti/PBD pada RPH tersebut menggunakan tugasan yang sepadan dengan kandungan buku sebenar yang diperiksa **secara visual** (Buku Aktiviti Tahun 2 hlm. bercetak 139–141, 143–144; Tahun 3 hlm. bercetak 129–136). Contohnya: T3 L106–107 halaman 136 mempunyai masalah kubus yang mempunyai 8 bucu dan 12 tepi sama panjang, bola bukan prisma dan pentagon sekata yang mempunyai 5 paksi simetri.
  - 21 Aktiviti 2 diperbaiki dengan menggantikan arahan templat `membina satu soalan setara dengan nombor berbeza dalam had SP` yang kurang sesuai bagi topik bukan pengiraan (unit, ukuran, prisma, kewangan, insurans/takaful dan geometri) dengan tugasan khusus yang berdasarkan Aktiviti 1/2 serta SP sedia ada.
- **553 RPH selebihnya tidak berubah** berbanding v52 dalam Word, Markdown atau PDF. Tiada perubahan kod SP, tajuk, nombor lesson atau masa mengajar.
- Semua suntingan before/after berada di `audits/matematik_v53_47_pembetulan_RPH_sahaja_20261107.csv`.

## QA sebenar pada arkib
- Input: `CIKGULAJU_MATEMATIK_v52_585_RPH_NISBAH_PECAHAN_SP_STAGING.zip`, SHA256 `646ec1516189275509382d92cc7228912f7a805b41229d5912f5f1a9ea58f847`.
- Output: `CIKGULAJU_MATEMATIK_v53_585_RPH_BA_GEOMETRI_AKTIVITI_STAGING.zip`, **49,393,550 bait**, SHA256 `518e4a56f8a88ee3fdf9d0adf33e02140fb21442b20c836bb8a02c2148ad09fe`.
- 585 Word + 585 Markdown + 585 PDF A4 1 halaman, serta lima PDF gabungan, masing-masing 117 halaman. ZIP CRC lulus; tiada nama fail berulang.
- **32×3 fail** individu berubah sepadan audit dan **553×3 fail** individu lain kekal byte-identical.
- Semua 47 teks baharu disahkan berada dalam Markdown yang dikirim. QA awal mendapati builder Markdown kehilangan sebahagian suntingan apabila satu RPH mempunyai banyak perubahan; **dibaiki sebelum arkib v53 akhir**, dibina semula dan QA lulus.
- Semua 32 DOCX di-render kepada PDF menggunakan LibreOffice, disemak satu halaman A4 dan teks tidak keluar sempadan. Paparan contoh Tahun 2 L106, Tahun 3 L106, L107 dan Tahun 6 L054 diperiksa secara visual.
- PDF gabungan bagi Tahun 2, 3, 5 dan 6 dijana semula daripada PDF individu terkini. Tahun 4 diguna semula tanpa perubahan.
- ZIP mengandungi **tiada PDF RPT atau fail RPT**. Tidak ada semakan atau pengubahsuaian RPT di Google Drive atau GitHub perbualan RPT lain dalam pusingan ini.

## Batas bukti
- Tugas BA halaman terpilih telah dipadankan secara visual bagi 13 lesson geometri; **bukan kelulusan akademik semua item BA/BT** dan bukan signoff rasmi. Rujukan BA terperinci asal pada 234 lesson Tahun 2–3 dikekalkan.
- Audit masih belum memeriksa semua latihan bagi 585 RPH, termasuk 34 pasangan Tahun 4 pada item buku teks. `formal_academic_signoff=NO`.
- Telegram/Web staging real E2E tidak dilakukan. Kawalan kuota/akses perlu ujian pada runtime sebenar sebelum terbit.
- `final_ready=false`, `production_modified=false` dan `rpt_changed=false`.
- **Tidak merge PR, tidak deploy Render, tidak ubah DB, data guru, langganan, bayaran, kuota atau RPT**.

PR #444 ialah draf staging untuk **RPH sahaja**. Arkib besar hanya tersedia melalui perbualan; CSV kecil disimpan dalam Library staging dan GitHub audit.
