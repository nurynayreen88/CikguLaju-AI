# Matematik v48 — pembetulan akademik mata wang dan audit 34 pasangan Tahun 4

**Tarikh:** 7 November 2026  
**STATUS:** `TECHNICAL_QA_PASS`, `ACADEMIC_FINAL_READY=NO`, `STAGING_ONLY`.

## Sumber yang disahkan
- DSKP Matematik **Tahun 3 SP 4.6.2** (PDF sumber halaman fizikal 61): nilai **RM1** dinyatakan dengan nilai mata wang **semasa** negara lain.
- DSKP Matematik **Tahun 4 SP 3.5.2** (PDF sumber halaman fizikal 57): nilai **RM1** setara dengan mata wang **semasa** negara lain; catatan DSKP menghadkan jadual setara **RM1 sahaja**.
- DSKP Matematik **Tahun 4 SP 3.5.1**: mengenal mata wang negara utama dunia; tidak mensyaratkan kadar tukaran untuk aktiviti pengenalan.
- Sumber kadar rasmi bertarikh: Bank Negara Malaysia `https://www.bnm.gov.my/latest-rates`; jadual nilai setara RM1 perlu diambil **pada tarikh PdP sebenar**, bukan diandaikan atau dipasang kadar 2026 untuk 2027.
- Buku Teks Tahun 4: bab `Mata Wang Utama Dunia dan Nilainya` bermula pada halaman **126** menurut kandungan versi KSSR Matematik Tahun 4 SK yang dipaparkan di `https://anyflip.com/qtnbu/cqbc/basic`.
- Buku Aktiviti Tahun 3 (salinan pemilik): `Nilai Mata Wang` hlm. **86** (topik/halaman; item individu tidak semuanya disahkan).

## Empat RPH yang telah dibaiki
- `T3-L060` — hentikan penggunaan mata wang X dan latihan RM2/RM5 sebagai aktiviti utama. Murid kini membaca jadual kadar **RM1** bagi mata wang ASEAN dan mencatat tarikh sumber.
- `T4-L055` — set induksi/BBM ditukar kepada kad negara serta mata wang sebenar; tidak lagi memakai kadar X rekaan dalam tajuk **pengenalan**.
- `T4-L056` dan `T4-L057` — tukar jadual kadar X/Y/Z `SIMULASI` dan nombor contoh tidak terkini kepada jadual BNM bertarikh, kod **JPY, SGD, USD, GBP** dan pernyataan setara **RM1 sahaja**.
- Kesemua **21 medan RPH** yang disunting dalam empat lesson ada sejarah sebelum/selepas dalam `audits/matematik_v48_4_matawang_semakan_dskp_20261107.csv`.
- Fail **Word, Markdown, PDF** bagi empat lesson telah dijana semula. PDF gabungan Tahun 3 dan Tahun 4 turut dijana semula. **581 lesson lain kekal byte-identical** pada fail individu. Tiada angka kadar semasa statik dalam RPH.

## Arkib
- `CIKGULAJU_MATEMATIK_v48_585_RPH_MATA_WANG_SEMASA_DSKP_STAGING.zip`
- Saiz **48,770,526 bait**; SHA-256 `a19841be74474f819496f694faebcd75e617864bfac9c48c4b3e841ec0393b4b`.
- Sumber v47 SHA-256 `08890923150fa71002f5dd6d762ce880f2552987cda3d5c00095e689b8e7b762`.
- **585 DOCX + 585 Markdown + 585 PDF individu**, 5 PDF gabungan; CRC ZIP lulus.
- **585/585 PDF A4 satu halaman**. Empat Word/PDF baharu diperiksa sempadan teks; sampel visual T3-L060 dan T4-L056 telah disemak.
- Pembaikan set induksi **46 RPH** pada v47 dan rujukan BA **234 RPH T2/T3** kekal dalam arkib v48.

## Audit 34 pasangan Tahun 4
- Kod SP bagi **34/34 pasangan pengembangan** ditemui dalam DSKP Tahun 4 beserta halaman sumber.
- Setiap pasangan masih mempunyai **Aktiviti 1, Aktiviti 2 dan pentaksiran yang berbeza** (semakan teks).
- **Satu ketidakpadanan kandungan jelas SP 3.5.2** dikenal pasti dan dibaiki pada T4-L056/057.
- Bukti `audits/matematik_v48_34_pasangan_T4_DSKP_20261107.csv`.
- Perhatian: penemuan lokasi SP dalam DSKP dan pembezaan aktiviti **bukan** kelulusan akademik pada aras latihan Buku Teks. Storan fail BT Tahun 4 asal dalam Drive melebihi had muat turun **256MB** connector (306MB); semakan buku penuh perlu sumber boleh diakses/diterbitkan mengikut halaman atau pratonton teks.

## Gate pelepasan
- `TECHNICAL_QA=PASS`, `SOURCE_DSKP_MATCH_LOCATED=34/34`, `CURRENCY_SOURCE_CORRECTION=4 RPH`, `STATIC_EXCHANGE_RATE=false`.
- `ACADEMIC_EXERCISE_SIGNOFF=0/585`; semakan individu latihan BA/BT, PBD, 34 pasangan Tahun 4 dan perbezaan nilai tahun 2027 **belum siap**.
- `TELEGRAM_WEB_REAL_STAGING_E2E=NOT_RUN`; `2027_CALENDAR=NOT_CONFIRMED`; `FINAL_READY=false`.
- Tiada PR merge, tiada deployment Render production, tiada perubahan DB, kuota, profil atau pembayaran.
- ZIP hanya diartifakkan dalam perbualan kerana Library storan penuh; laporan CSV kecil disimpan di Library dan GitHub staging.

PR: https://github.com/nurynayreen88/CikguLaju-AI/pull/444
