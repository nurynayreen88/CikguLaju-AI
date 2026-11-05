# PSV Tahun 2–6 — Calon penerbitan SELAMAT (bukan LIVE)

**5 November 2026 | Keputusan: STAGING QA / RELEASE BLOCKED**

## Bukti kerja terbaharu

- Calon penerbitan yang bersih: [PR #267](https://github.com/nurynayreen88/CikguLaju-AI/pull/267) pada `staging/psv-y2-y6-publish-candidate-20261105`, dibina daripada `main` semasa. PR masih **DRAF**, `merged=false`, dan semakan banding perbezaan tidak mendapati perubahan dalam `app.py`, database, Supabase, referral, bayaran atau subjek lain.
- 210/210 RPH tersusun: Tahun 2 hingga Tahun 6, masing-masing 42 PdP; source Markdown, RPT 2027 dan peta crosswalk sumber ada.
- DSKP asal Tahun 2–6 disemak daripada PDF Google Drive. Semua kod SP yang digunakan wujud dalam DSKP. **Kewujudan kod tidak membuktikan makna SP/teknik**: sebab itu regresi `test_forty_unit_dskp_technique_and_production_semantics` menyemak 40 unit dan 152 RPH bukan pameran, juga semakan kod projek bercetak untuk Tahun 2–4.
- SP Tahun 6 `3.1.1` mewajibkan penghasilan **folio**: PdP 034 (wau bulan) dan PdP 039 (beg batik) kini mengandungi folio lima bahagian, hasil gambar dan apresiasi; RPT Tahun 6 turut diselaraskan.
- 12 header SP projek Tahun 2–4 telah dibersihkan daripada nota dalaman, tetapi **kod `3.3.x` bercetak di bawah SK `5.1` masih dikekalkan**; tiada kod rasmi palsu.
- RPH Tahun 4 ukiran sabun dan Tahun 5 teknik tekat telah diperbetulkan secara substantif; kumpulan Tahun 6 wau/beg juga sudah ditambah baik. Backup lengkap kekal pada staging PR #196 serta sejarah GitHub.
- Alat audit `rph_standalone/psv/preview_a4.py` disertakan. Bukti pada staging terdahulu:
  - [Ujian RPH PDF pratonton — 210/210 satu A4, 21/21 unittest](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41873591285)
  - [Ujian RPH Word LibreOffice — 210/210 satu A4](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41874076050)
- Untuk pemeriksaan integrasi native, `web/psv_2027_rph_release_bridge.py` hanya tersedia sebagai **adapter tidak dipasang**. Ia memproses SK/SP, objektif, kriteria, 5 langkah dan BBM ke struktur RPH asli, mengekalkan tarikh/kelas/refleksi. `tests/test_psv_runtime_bridge_candidate.py` menyediakan ujian 210 PdP, pemilihan salah subjek/tahun/SP, dan fail korup.

## Kawalan penerbitan — wajib

**Fail `rpt_2027/psv/psv_release_approval.json` belum wujud dan TIDAK boleh direka atau ditandakan lulus tanpa bukti.** Adapter hanya boleh menyampaikan RPH kepada pengguna jika kesemua perkara berikut benar:
1. Bendera eksplisit `CIKGULAJU_PSV_RPH_RELEASE_ENABLED=1`;
2. Fail kelulusan mengandungi `approved=true`, `rph_count=210`, `years=[2,3,4,5,6]`, `source_review=INDIVIDUAL_TEXTBOOK_DSKP_PASSED` dan `runtime_staging=PASSED`;
3. Setiap RPH dan RPT yang dipilih masing-masing mempunyai status `READY`.

**Pada masa laporan ini disediakan: semua RPH masih DRAF SEMAK dan approval file tiada.** Bot produksi, DB, pengguna, bayaran, dan menu tidak diubah. Tiada arahan merge atau deploy.

## Gerbang tertangguh untuk FINAL READY

1. Dapatkan **ujian CI untuk commit terkini PR #267** yang berjaya; workflow yang ditambah harus menguji 210 source, 40 unit semantik, 210 Word/PDF A4, dan adapter fail-closed. Keputusan hijau workflow versi lama bukan pengganti.
2. Laksanakan audit manusia/visual **isi semua 210 aktiviti dan halaman Buku Teks**, khususnya penafsiran SP yang tidak hanya dipastikan melalui kehadiran kod, keselamatan kraf, dan kemunasabahan aktiviti PdP.
3. Lakukan **ujian integrasi sebenar dalam Telegram staging** selepas wiring yang terkawal (navigasi Unit → PdP, kelas, tarikh, Word/PDF, akses, kuota, pengguna serentak) tanpa menyentuh produksi.
4. Sahkan hasil Word/PDF satu A4 bagi penjana native staging (bukan setakat alat preview) dan semakan visual rawak per tahun.
5. Selepas bukti kelulusan lengkap, lakukan port/review terpilih kepada `main` terkini; jangan gabung PR #196 yang lama. RPT sekolah 2027 untuk tarikh negeri/cuti gantian masih memerlukan gerbang penerbitan berasingan.

## Keputusan tegas

**Boleh diuji dalam staging, belum FINAL READY untuk penerbitan pengguna.** Jangan menganggap kiraan 210/210 atau A4 210/210 sebagai kelulusan pedagogi 210/210. PR #267 dikekalkan DRAF.