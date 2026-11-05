# Matematik Tahun 2–6 — v38: 34 pasangan sesi Tahun 4 (5 November 2026)

## Keputusan
**585/585 RPH lulus QA dokumen; Tahun 4 34/34 pasangan berjaya dipisahkan dari segi aktiviti/pentaksiran.** Namun **FINAL READY AKADEMIK = FALSE** dan **TELEGRAM LIVE = BELUM DIBUKTIKAN**.

## Punca isu dan pembetulan berjejak
Pemetaan Tahun 4 `117 Lesson` kepada `83 ID RPH sumber` menghasilkan **34 ID sumber yang digunakan oleh dua Lesson** (68 fail individu). Dalam v37:
- Kesemua 34 Lesson pertama mempunyai **Aktiviti 2** yang menyebut "empat latihan berbeza berkaitan..." tanpa memberikan soalan atau langkah khusus.
- Pentaksiran kedua-dua Lesson bagi setiap pasangan mempunyai set yang sama, walaupun sesi sambungan memerlukan penilaian pengaplikasian yang berbeza.

Dalam v38:
- **34 Aktiviti 2 sesi asas** diganti dengan latihan jelas, bahan matematik, tindakan murid dan kaedah semakan mengikut SP.
- **34 pentaksiran sesi kedua** diganti dengan item individu atau rubrik berbeza, supaya tidak mengulang bulat-bulat PBD sesi pertama.
- Tiga ayat objektif yang tidak gramatis diperbetulkan, iaitu Tahun 4 **Lesson 022, 023, 024**. Dua yang pertama tergolong dalam 68 pembetulan di atas; Lesson 024 adalah tambahan. Jumlah fail RPH Tahun 4 yang berubah = **69**, tidak 71.
- Sebanyak **516 RPH lain dan 1548 fail individu Word, PDF serta Markdown** adalah **byte-for-byte sama** seperti v37. Semua Tahun 2, 3, 5 dan 6 kekal.

## Pengesahan QA setempat
- Setiap Tahun mempunyai **117/117 DOCX, PDF, Markdown**; jumlah **585 setiap format**.
- Semua **585 PDF individu** ialah **satu halaman A4**; fail PDF gabungan Tahun 2–6 mengandungi **117 halaman setiap tahun**.
- 34/34 pasangan: PBD Lesson kedua tidak sama dengan PBD Lesson pertama; Aktiviti 2 Lesson pertama bukan lagi teks "empat latihan berbeza" generik.
- `zip.testzip()` = PASS; tiada fail yang tersalah Tahun/Lesson; PDF individu mempunyai fail yang unik.
- Semakan visual sampel Tahun 4 termasuk Lesson 011, 023 dan 100; teks berada dalam halaman.
- Adapter staging versi v38 diuji secara setempat dengan **10/10 unittest PASS** (termasuk membaca 585 PDF, SHA-256, akses berbayar, callback lama, gagal hantar, fail closed dan flag staging).
- Pakej ZIP `CIKGULAJU_MATEMATIK_v38_585_RPH_SPLIT_SESSIONS_STAGING.zip` saiz **47,999,353 bytes**, SHA-256 **29097e08da6b79ba1f3395defe03fbb0e02554bf58bcc794aeacc30a335558ad**.
- Matriks CSV 585 Lesson dan CSV khusus 34 pasangan disediakan sebagai lampiran dalam sesi ChatGPT. Matriks tidak menaik taraf sebarang baris kepada `FINAL_READY`.

## Syarat akademik dan runtime yang belum lulus
1. Aktiviti/PBD bagi **585/585** RPH masih memerlukan pengesahan individu terhadap kandungan Buku Teks dan Buku Aktiviti, bukan semakan kewujudan kod SP sahaja.
2. 34 sesi tambahan Tahun 4 kini **berbeza secara pedagogi**, namun belum ada kelulusan berdasarkan naskhah lengkap 83 RPH asal v15 dan pemeriksaan aktiviti halaman Buku Teks/Buku Aktiviti bagi setiap pasangan.
3. Tarikh/masa RPT 2027 mengikut cuti umum dan negeri serta jadual guru belum diluluskan secara individu.
4. Telegram sebenar belum diuji menerima RPH v38 dengan DB dan laluan runtime produksi (hanya mock tempatan); regresi subjek lain dan backup/version DB mesti lulus sebelum release.
5. GitHub `main` dan Render Telegram production **tidak diubah**. Modul pratonton tersedia pada [cabang staging berasingan](https://github.com/nurynayreen88/CikguLaju-AI/tree/staging/matematik-v38-rph-preview-20261105) dan hanya boleh diaktifkan secara eksplisit pada staging. ZIP RPH belum dimasukkan ke GitHub public.

## Ketetapan
**Status: STAGING — READY TEKNIKAL, BUKAN FINAL READY AKADEMIK.** Jangan ubah status dalam menu guru, jangan merge `main`, jangan timpa DB atau RPH versi lama tanpa bukti individu dan ujian sebenar.

Pautan audit terdahulu: [v37](./matematik_v37_teacher_view_gate_20261105.md), [v35](./matematik_v35_585_rph_source_safe_qa_20261105.md).
