# Matematik v46 — ralat sudut DSKP disahkan dan dibetulkan (7 November 2026)

**TECHNICAL QA PASS / FINAL READY ACADEMIC = NO. Staging sahaja.**

## Ralat kandungan disahkan pada sumber primer
- DSKP Matematik Tahun 6 (2021), PDF physical page **72**, SP **8.1.1** menunjukkan **45°, 90°, 180°**; teks PDF yang diekstrak menukarkan superskrip ⁰ kepada angka 0 lalu menghasilkan `450, 900 dan 1800`.
- Arkib v45 Tahun 6 **Lesson 108 dan 109** mengandungi ungkapan salah itu pada baris **SP** serta **Objektif**, walaupun langkah aktiviti dan pentaksiran sudah menggunakan sudut yang betul.
- Betulkan kedua-duanya menjadi `45°, 90° dan 180°` pada fail Markdown, Word dan PDF. **Hanya dua lesson tersebut berubah**; semua lesson lain dikekalkan.
- PDF gabungan Tahun 6 dijana semula. Visual kedua-dua halaman A4 disemak, tanpa teks terpotong.

## Arkib v46 yang dijana
- Nama: `CIKGULAJU_MATEMATIK_v46_585_RPH_SP_SUDUT_DSKP_STAGING.zip`.
- SHA-256: `f95078a1cfec1e29e0cae5436bbb01c158f41234d9d6581c17c24924d53124fa`.
- Saiz: **48,944,891 bait**.
- Sumber v45 SHA-256: `9c6ed89ba1fa892b01da8e2fdc5fd7364369891c4996d930a65b6759f96e70e4`.
- 585 Word + 585 PDF individu + 585 Markdown + 5 PDF gabungan. ZIP CRC `testzip()==None`.
- **585/585** PDF A4 satu halaman, fasa PdP dan SP terpapar, tajuk aktiviti Word bold; Buku Aktiviti Tahun 2–3 kekal 234 RPH, Tahun 4–6 tidak ditambah BA palsu.
- Unit test **21/21 PASS** dalam harness terasing yang menggunakan arkib v46 sebenar: semua 585 PDF dapat dibaca, Word/PDF ikut lesson, akses admin dan pelanggan disahkan, pengguna tanpa bayaran ditolak, callback lama tidak diubah, hash rosak ditolak, kegagalan penghantaran tidak dilapor berjaya, tiada operasi DB/kuota.

## Ujian pemeriksaan SP lain
- Semakan automatik membandingkan frasa awalan SP dalam 585 RPH dengan DSKP 2016–2021. Sebahagian skor rendah berpunca daripada **lebih satu SP dalam satu lesson**, atau lajur catatan PDF yang dicantumkan sewaktu ekstraksi.
- Kandidat Tahun 4 Lesson 001, 002, 005, 022, 054, 074, 081–082 disemak pada teks DSKP; tiada bukti ralat kod SP untuk dibetulkan. **Jangan auto-ubah apabila skor rendah semata-mata.**
- PDF DSKP Tahun 6 page 72 dibaca secara visual untuk memastikan ralat superskrip bukan ralat sebenar dokumen.

## Fail audit GitHub
- `audits/matematik_v46_release_gate_20261107.json`
- `audits/matematik_v46_2_degree_symbol_fixes_20261107.csv`
- `rph_standalone/matematik/staging_preview_v46.py`
- `tests/test_matematik_ba_v46_preview_20261107.py`
- `tests/test_matematik_ba_v46_degrees_20261107.py`

## Baki pelepasan
- Signoff latihan khusus BA/BT dengan SP dan PBD untuk semua 585 lesson belum siap; **0/585** diluluskan secara formal, walaupun sampel latihan Tahun 2/3 pernah diperiksa.
- Pengesahan akademik 34 pasangan sesi Tahun 4 belum siap.
- Pemetaan kalendar negeri/Kumpulan A-B 2027 dan penjajaran RPT belum lulus.
- **Ujian E2E perkhidmatan Telegram/Web staging sebenar belum dijalankan.** Semua ujian v46 merupakan harness terasing/mock sahaja.
- ChatGPT Library sudah penuh; jangan padam atau menimpa versi pengguna tanpa persetujuan. ZIP disediakan melalui perbualan.

**PR #444 kekal draft dan tidak dimerge. Tiada import DB, perubahan akaun, kuota, pembayaran atau deployment Render production.**
