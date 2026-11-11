# Matematik v45 — audit Buku Aktiviti, 7 November 2026

**STATUS: STAGING QA TECHNICAL PASS / FINAL READY ACADEMIC = NO.**

## Artifak
- Arkib: `CIKGULAJU_MATEMATIK_v45_585_RPH_BA_SP_HALAMAN_STAGING.zip` (~49.14 MB).
- SHA-256: `9c6ed89ba1fa892b01da8e2fdc5fd7364369891c4996d930a65b6759f96e70e4`.
- Asal v44 SHA-256 `6ff8ff3a83abd09a35fac23f94cb8980f928d0fc52bc37d5896abe4c2f1328e4`.
- 585 Word, 585 PDF individu satu halaman A4, 585 Markdown dan 5 PDF gabungan.
- ZIP CRC lulus. PDF gabungan Tahun 2 dan 3 dijana semula; Tahun 4–6 asal dikekalkan.

## Semakan bukti Buku Aktiviti
- **44 halaman** sebenar Buku Aktiviti Matematik Tahun 2 dan 3 diperiksa secara visual pada kotak footer yang menyenaraikan kod SP (Tahun 2:19 halaman; Tahun 3:25).
- **18** kelompok topik yang mempunyai lebih daripada satu kod SP dibandingkan dengan halaman latihan tersebut; melibatkan **62** RPH calon.
- **48 rujukan** diperincikan ke halaman yang menyebut kod SP sepadan: Tahun 2 = 29, Tahun 3 = 19.
- **14** lagi mempunyai padanan visual tetapi rujukan julat topik sedia ada masih sesuai dan tidak diubah.
- 48 RPH berubah pada Word, Markdown dan PDF: `144` kandungan individu berubah; **537** RPH lain kekal identik. Teks aktiviti/objektif tidak diubah bagi 48 ini, hanya nombor halaman BA. Semua 585 Word/PDF disemak struktur sekali lagi.
- Contoh Tahun 2: SP 4.2.1 dirujuk BA hlm. 105, SP 4.2.2 hlm. 106, SP 4.3.1 hlm. 107, SP 4.3.2 hlm. 108.
- **Kod SP pada footer bukan bukti semua item latihan pada halaman sesuai.** Arahan supaya guru memilih item mengikut SP kekal; **0 kelulusan latihan individu** dicatat.

## Audit lain dikekalkan
- Tahun 4: 83 RPH sumber menjadi 117 lesson. 34 pasangan pengembangan mempunyai SP yang sama, tetapi Aktiviti 1, Aktiviti 2 dan pentaksiran masing-masing berbeza secara teks. Ini audit struktur/pembezaan, belum signoff akademik.
- 351 RPH Tahun 4–6 mempunyai rujukan **lokasi SP dalam PDF Buku Teks**, tetapi latihan belum disahkan satu-satu. Tiada halaman BA palsu diperkenalkan untuk Tahun 4–6.
- Daripada 360 persamaan yang dikesan dalam korpus, 336 disahkan secara automatik dan 24 disemak dalam konteks penuh, tiada ralat matematik disahkan dalam sampel tersebut.

## Fail bukti di cabang staging
- `audits/matematik_v45_44_sp_footer_visual_20261107.csv`
- `audits/matematik_v45_48_ba_page_refinements_20261107.csv`
- `audits/matematik_v45_release_gate_20261107.json`
- `tests/test_matematik_ba_v45_footer_20261107.py`
- `rph_standalone/matematik/staging_preview_v45.py` — SHA terkunci dan opt-in staging sahaja.

## Halangan FINAL READY
1. Semakan akademik individu terhadap latihan terpilih, keperluan PBD dan ketepatan SP/objektif bagi keseluruhan 585 lesson.
2. Pengesahan akademik semua 34 sesi pecahan Tahun 4 terhadap buku asal, bukan sekadar pembezaan teks.
3. Ujian takwim sekolah/cuti negeri 2027 dan padanan RPT/lesson.
4. Ujian Telegram dan Web **staging sebenar** terhadap DB kanonik dan arkib v45. Ujian setempat/mock tidak sama dengan ujian live.
5. Storan ChatGPT Library masih penuh; jangan padam/overwrite versi lama tanpa kebenaran.

**Tidak merge, deploy, menukar DB, kuota atau pembayaran pengguna.** PR kekal draf.
