# RPT 2027 — audit akhir teknikal 21 PDF (7 Nov 2026)

**Status: STAGING DRAF — tidak diterbitkan kepada pengguna.**
Branch/PR: `feat/rpt2027-sejarah-pjpk-unified-staging-20261107` / PR #441.

## Keputusan ujian terkini

- CI: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42274834653 — **LULUS**.
- Artifak: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42274834653/artifacts/13532197457
- 21 PDF / 489 halaman A4 landskap diperiksa. Halaman depan mempunyai hanya tajuk RPT/subjek/tahun, slot logo, nama sekolah, nama guru.
- Semua 1,233 PdP mempunyai pernyataan SK/SP daripada crosswalk sumber DSKP yang masih memerlukan semakan halaman/kelulusan guru.
- Kecacatan glif DSKP PUA `U+F0B7` (bullet) dan `U+F02D` (hyphen) dinormalkan pada peringkat paparan, sumber mentah tidak ditimpa; **0 aksara NULL** ditemui dalam PDF.
- **41 SP Pendidikan Kesihatan Tahun 2–6** dibersihkan daripada limpahan *Standard Prestasi Tahap 1* yang tersalin akibat pengestrakan jadual PDF. Teks asal dan bahagian yang dipisahkan disimpan di dalam `extraction_corrections` setiap fail sumber.

## Semakan tarikh minggu A/B mengikut satu induk

Sumber: Google Sheet `CIKGULAJU_RPT_2027_KALENDAR_CUTI_FINAL_VERIFIED`, tab `INDUK MINGGU RPT 2027 A B` (44 minggu berjadual setiap kumpulan), snapshot:
`rpt_2027/common/calendar_week_2027_a_b_snapshot_20261107_DRAF.json`.

Ujian kelas menjamin tarikh luar rujukan/tidak padan **tidak disenyapkan**.

| Keputusan | PdP | Pengendalian |
|---|---:|---|
| Sepadan terus dengan induk | 844 | Kekal tanpa perubahan |
| PSV T2–6: label minggu lama tidak sama dengan julat tarikh asal | 185 | Label **paparan sahaja** diselaraskan kepada minggu induk melalui padanan tepat Kumpulan A + B; nilai sumber `source_week` dikekalkan, tiada perubahan pada CSV atau tarikh |
| Sejarah T4–6: tarikh calon tetapi tiada label minggu sumber | 108 | **Belum diputuskan**; jangan andaikan minggu; padanan seterusnya diperlukan |
| RBT T4–6: tarikh dan minggu belum tersedia dalam CSV | 96 | Kekal kosong; perlu jadual PdP daripada sumber sah |

**Jumlah 1,233 PdP.** Selepas penyesuaian label PSV, 1,029 PdP memaparkan minggu dan tarikh yang konsisten dengan induk; 185 daripada jumlah itu masih rekod relabel staging yang perlu diluluskan dari segi kurikulum/agihan guru.

Pemeriksaan silang tambahan ke atas CSV Sejarah menunjukkan **35/36 tarikh setiap tahun** sepadan terus dengan julat minggu induk. PdP 009 bagi T4–6 mempunyai tarikh calon Kumpulan A **15–18 Mac 2027**, tetapi minggu M10 induk bermula **14 Mac**. Jangan tukar tarikh ini tanpa bukti cuti negeri/gantian; kemungkinan kelas sebenar bermula selepas hari pertama minggu.

## Pagar release yang masih terbuka

1. Pengesahan visual/isi kandungan pernyataan SK/SP dengan halaman DSKP bagi setiap tahun/subjek. Crosswalk hanyalah draf dan ada sumber ekstraksi kompleks, terutama PJPK/Pendidikan Kesihatan dan PSV.
2. Pelarasan sumber mingguan Sejarah dan agihan RBT tanpa rekaan tarikh. Aturan cuti negeri/gantian KPM/BKPP dan kemungkinan pindaan masih perlu signoff.
3. Padanan sebenar 21 RPT dengan RPH/DB yang sedang digunakan (bukan hanya struktur PDF). Pengesahan berasingan untuk subjek yang belum termasuk dalam 21 PDF.
4. Integrasi penjana ke profil pengguna Web/Telegram untuk mengisi logo sekolah, nama sekolah, nama guru adalah **belum dibuat**. Penjana staging hanya menyokong parameter pilihan.
5. **JANGAN MERGE atau DEPLOY** sehingga syarat di atas diluluskan. Tiada DB aktif, Web, Telegram, RPT pengajar atau fail asal ditimpa dalam kerja audit ini.

## Bukti

- `scripts/audit_rpt_2027_calendar_master_staging.py` menghasilkan
  `staging/rpt_2027_seragam_2026/audit_calendar_week_alignment.json` dalam artifak CI.
- `tests/test_rpt_2027_calendar_master_staging.py` menyemak 44 minggu A/B, kes PSV yang perlu relabel, serta kes tanpa sumber.
- `tests/test_rpt_2027_second_batch_preview.py` menyemak 41 pembetulan SP PK dan semua kod sumber.
- `.github/workflows/rpt-2027-format-2026-staging-qa.yml` menguji 21 PDF, imej muka depan, jadual, teks bermasalah, limpahan blok, dan memuat naik bukti.


## Sambungan pengesahan khusus Sejarah (7 November 2026, versi terkini)

**CI terkini LULUS:** https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42278126563
Artifak pratonton 21 PDF / 490 halaman + 42 PNG + JSON audit:
https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42278126563/artifacts/13534790761

### Rujukan buku teks PdP Sejarah, bukan sekadar halaman unit

Ledger sedia ada `audits/sejarah_y4_y6_primary_textbook_page_evidence_20261106.json` mempunyai **108/108** padanan halaman teks digital buku teks. Tiga PDF Sejarah kini memaparkan **m/s khusus bagi setiap PdP** dengan nota: *padanan teks digital DRAF; gambar/latihan belum disahkan*. Rujukan unit lama dan status sumber seperti `BELUM_DISAHKAN` dikekalkan dalam rekod `source_unit_page_note`, bukan ditimpa. Setiap pernyataan SK/SP dan urutan PdP kekal asal. Bukti buku tidak dianggap kelulusan pedagogi/aktiviti.

### Padanan minggu Sejarah + cuti KPM 14 Mac

- **105/108 Sejarah** mempunyai julat calon A/B yang sama tepat dengan satu minggu induk. Identiti PdP tetap; hanya label Mxx **(cadangan)** ditambah pada paparan.
- **3/108** = Tahun 4, 5, 6 **PdP 009**: minggu induk M10 bermula **14 Mac 2027** bagi A, manakala tarikh sumber calon bermula **15 Mac 2027**. Semakan 16-negeri indeks menunjukkan **14 Mac ialah cuti tambahan KPM Hari Raya Puasa bagi ketiga-tiga negeri Kumpulan A**: Kedah (indeks baris 74), Kelantan (439), Terengganu (804). Oleh itu, tarikh 15–18 Mac dikekalkan. Bukti dibekukan secara baca-sahaja dalam `rpt_2027/common/sejarah_group_a_2027_03_14_holiday_index_evidence_DRAF.json`.
- Tahun 4–6 menerima label `M10 (cadangan; cuti A)` untuk PdP 009. Status kalender `GROUP_A_FIRST_DAY_KPM_HOLIDAY_INDEXED` **tidak** bermaksud guru/sekolah telah meluluskan jadual sesi.
- Tiada tarikh atau halaman buku teks asal ditokok tambah dalam CSV. Fail sumber RPT dan RPH tidak diubah.

### Jumlah audit 1,233 PdP selepas pemurnian

| Kategori | PdP |
|---|---:|
| Minggu dan tarikh asal terus padan induk | 844 |
| PSV relabel paparan sahaja | 185 |
| Sejarah padan tarikh calon kepada minggu induk | 105 |
| Sejarah padan minggu dengan pengecualian cuti tambahan KPM A | 3 |
| RBT Tahun 4–6 tiada jadual minggu/tarikh sumber | 96 |
| **Jumlah** | **1,233** |

**1,137 PdP mempunyai label minggu selaras dengan sumber yang wujud.** Ini tidak sama dengan kelulusan jadual guru, cuti negeri terperinci, ketepatan kurikulum atau FINAL READY. RBT 32 PdP/tahun belum boleh diberi minggu A/B tetap tanpa penjadualan sebenar sekolah; jangan isikan secara anggaran.

### Keputusan ujian PDF

21/21 PDF dan **490 halaman** diperiksa selepas perubahan Sejarah. Muka depan hanya tajuk, kotak logo sekolah, nama sekolah dan nama guru. Semakan halaman: 0 blok teks melampaui sempadan, 0 aksara NUL, 21 PDF landskap sah. Laporan JSON membezakan kategori minggu termasuk bukti cuti M10. **Release gate kekal BLOCKED**, terutama kelulusan aktiviti/halaman buku dan integrasi RPT bersama profil Web/Telegram.


## Sambungan: bukti langsung buku teks RBT Tahun 4 dan pembetulan tajuk (7 Nov 2026)

- **RBT Tahun 4**: PDF asal 104 halaman dimuat daripada Drive pengguna; SHA-256 `8964ad3f0789ae825041294b5327ddc6bd6a40af3f8e5c835543157ffc1f9780`. Pengesahan teks pada halaman bercetak: **57/57 kod SP** dan **61/61 pasangan kod–halaman** lulus. Semakan gambar hanya sampel 9 halaman (4, 7, 9, 11, 34, 45, 68, 86, 97); status **0/32 kelulusan aktiviti visual** kekal.
- **Padanan RPH–RPT–buku Tahun 4**: ujian silang `tests/test_rpt_2027_rbt_t4_book_page_evidence.py` memastikan **32/32 RPH** merujuk kepada halaman bercetak sama seperti ledger dan CSV; status asal `belum sah` tidak diubah.
- **RBT T4–6: 12/96 tajuk PdP 99 aksara terpotong** telah digantikan pada **paparan PDF staging sahaja** menggunakan teks penuh SP DSKP. Identiti: Tahun 4 (003, 017, 019, 021, 028, 030), Tahun 5 (005, 010, 014, 029), Tahun 6 (018, 022). Tajuk asal CSV/RPH disimpan dalam `source_topic`; fail RPH asal tidak ditimpa. Lihat `audits/rbt_2027_truncated_12_pdp_titles_staging_20261107.md`.
- Audit lain RBT T4–6: **16/16 SK + 114/114 SP** pernyataan penuh padan kod dan teks DSKP asal (selepas penormalan sengkang PDF); semakan visual/aktiviti belum ditandatangani.
- CI 21 asal + 3 simulasi RBT **LULUS**: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42316669184
  Artifak 24 PDF + 48 PNG + audit kalendar: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42316669184/artifacts/13551206896
- Pemeriksaan PDF Tahun 4, 5 dan 6 mengesahkan perkataan tajuk panjang seperti "Penyelenggaraan peralatan", "kategori produk", "menggunakan peralatan yang sesuai" dan "akan dibina" kini muncul penuh.

**Pagar pelepasan tidak berubah:** Tahun 5–6 belum mendapat pengesahan PDF buku teks asal setara T4, semua 96 agihan RBT menunggu jadual sekolah sebenar, kelulusan visual/aktiviti/safety guru belum selesai, pengisian profil Web/Telegram belum diaktifkan. PR kekal DRAF; tidak dibenarkan mengubah produksi.

## Audit silang RBT Tahun 5–6 (7 November 2026)

- CI [#42317847385](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42317847385) **LULUS**, **26 ujian**, menghasilkan 21 RPT asas + 3 simulasi RBT serta laporan audit tambahan. Artifak [#13550699081](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42317847385/artifacts/13550699081).
- `scripts/audit_rbt_y5_y6_64_pdp_page_consistency_staging.py` memastikan **64/64 PdP** Tahun 5–6 mempunyai pasangan kod SP, julat halaman calon, identiti, unit, turutan dan nota RPT yang sama antara **RPH, RPT, ledger buku dan manifest kelulusan**. Rujukan SP sumber: 34 Tahun 5, 23 Tahun 6.
- PDF sumber dalam talian membolehkan **semakan sampel**: T5 SP 4.3.1 (4–6), 4.3.2 (7–9), 6.4.6 (60), 7.1.6 (77–80); T6 SP 5.2.1 (2), 5.2.5 (11–20). Ini **bukan** semakan individu lengkap untuk semua 64 PdP. T6 halaman 51–76 masih perlu dibaca dan disahkan dengan lebih menyeluruh.
- Audit JSON pengguna diterbitkan dalam artifak di `staging/rpt_2027_seragam_2026/audit_rbt_y5_y6_64_pdp_page_consistency.json`. Status `STAGING_INTERNAL_CONSISTENCY_ONLY`, `independent_book_page_checks_completed: 0` untuk audit menyeluruh, `teacher_approvals: 0`, `release_ready_count: 0`.
- Rekod lengkap `audits/rbt_y5_y6_64_pdp_book_mapping_and_sample_source_review_20261107.md`.

**Pagar release:** status utama **BLOCKED** selagi tiada bukti semakan visual setiap PdP, aktiviti buku, keselamatan amali dan agihan tarikh sekolah. Semua data asal, Telegram, Web dan produksi kekal tidak diubah.
