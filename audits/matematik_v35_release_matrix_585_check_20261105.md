# Release Matrix v35 — Matematik 2027 Tahun 2–6

**Kedudukan pada 5 Nov 2026: 585/585 lulus QA teknikal; ACADEMIC FINAL READY = FALSE; Telegram LIVE = NOT VERIFIED.** Jangan mengubah app/DB/akses produksi hanya kerana ujian teknikal lulus.

## Bukti matriks individu
- Fail CSV pengguna: `CIKGULAJU_MATEMATIK_V35_585_RPH_RELEASE_MATRIX_20261105.csv` (333,580 bytes)
- SHA-256 CSV: `f638ea79962c0e0adf4bb72ae8f2bfddf86bfb92615bfdfefb320c6125a689ad`
- Setiap 585 baris merekod Tahun, Lesson, Minggu, Tajuk, SK/SP, ID RPH sumber Tahun 4, bukti lokasi kod SP dalam PDF Buku Teks, SHA-256 Word & PDF unik, tiga subujian pengesahan kandungan, takwim, Telegram dan gate FINAL.
- Semua **585 Word, PDF dan Markdown wujud dalam ZIP**; semua **585 PDF A4 portrait satu halaman**; **585 SHA-256 PDF individu berbeza**. Setiap satu mempunyai bukti lokasi kod SP dalam Buku Teks, **tidak bermakna kesepadanan aktiviti kepada Buku Teks/Buku Aktiviti lulus**.
- Tahun 4: **83 ID sumber RPH yang berbeza** dirujuk oleh 117 Lesson; 34 Lesson ialah pecahan tambahan. Sebanyak 68 baris tergolong dalam pasangan Lesson yang menggunakan ID sumber sama; setiap pasangan wajib disemak sebelum kelulusan individu.
- Matrik ditandakan `QA_Akademik_Individu=BELUM LULUS`, `Ujian_Telegram_LIVE=BELUM DILAKUKAN`, `FINAL_READY=TIDAK` kerana tiada bukti lulus.

## Integriti pakej sumber
- `CIKGULAJU_MATEMATIK_v35_585_RPH_STAGING_QA.zip`
- SHA-256 ZIP: `f81236c1c8ba9137d92bf184892b908b38b6dc7dbcf4f5fa0c42655eff45ce1a`
- Mock staging preview test **9/9 PASS** dalam persekitaran tempatan. Test ini tidak menghantar fail ke Telegram API sebenar.
- Modul staging yang dipasang ke cabang berasingan: [staging/matematik-v35-rph-preview-20261105](https://github.com/nurynayreen88/CikguLaju-AI/tree/staging/matematik-v35-rph-preview-20261105). Modul tidak diimport oleh app production dan memerlukan `CIKGULAJU_MATH_RPH_V35_STAGING_PREVIEW=1`. Arkib ZIP itu **tidak** dimuat naik ke GitHub awam.

## Release gates belum ditutup
1. Guru/QA perlu menyemak setiap aktiviti, pengiraan dan PBD 585/585 terhadap halaman Buku Teks dan Buku Aktiviti berkaitan; tiada halaman yang boleh diandaikan.
2. Luluskan 83→117 Tahun 4, terutama 34 sesi pecahan, dan pastikan tiada RPH generik merentas SP.
3. Uji jadual 2027 negeri, cuti sekolah dan cuti ganti serta sesi guru.
4. Uji staging dengan DB versi kanonik dan Telegram *sebenar*, kawalan akses, kuota dan regresi semua subjek.
5. Rebase against the latest `main`, audit diff, backup DB pengguna/versi, barulah merge.

**Keputusan tidak boleh berubah kepada FINAL READY sebelum gates ini ditutup.**
