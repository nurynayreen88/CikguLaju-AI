# PSV Tahun 2–6 — Semakan susulan RPT/RPH (4 November 2026)

**Status: DRAF SEMAK, staging sahaja.** Dokumen ini mengemas kini dapatan urutan sumber selepas laporan `audits/psv_rpt2026_crosscheck_sources_20261104.md`. Laporan terdahulu ialah pemerhatian sebelum susunan RPT terkini disemak semula; jangan tafsirkan jurangnya sebagai masih aktif tanpa menyemak commit terkini.

## 1. Padanan urutan unit RPT 2026 → RPT 2027

Crosswalk `crosswalk_2026_tahun{2..6}_VERIFIED_SOURCE.csv` mengandungi 10 unit bagi setiap tahun. Semakan semula urutan 42 PdP setiap tahun pada branch ini:

| Tahun | Unit sepadan mengikut urutan RPT 2026 | Nota |
|---|---:|---|
| 2 | 10/10 | Hanya variasi huruf besar pada 'Burung Kenek-kenek' dan 'Uli-uli Tembikar' |
| 3 | 10/10 | Unit 3 Aneka Capan dan Unit 4 Serangga Comel berada pada kedudukan yang betul |
| 4 | 10/10 | Tanda soal pada 'Helo, Helo Apa Khabar?' sahaja berlainan daripada crosswalk |
| 5 | 10/10 | Bermula Si Putih Menawan, diikuti Sayangilah Habitat Kita |
| 6 | 10/10 | Unit 1 Gambaran Minda hingga Unit 10 Beg Batik Rekaanku; slot Projek Seni Visual tidak dianggap unit buku teks |

Ini **audit turutan 50 unit berdasarkan crosswalk tersimpan**, bukan pensijilan bahawa setiap butiran SK/SP atau setiap halaman buku telah diluluskan.

## 2. Pembetulan konkrit RPT Tahun 5

Sebelum pembetulan, **42/42 entri `Objektif` RPT CSV** menggunakan rumusan singkat seperti 'mengenal dua unsur seni' dan 'menghasilkan karya dengan selamat'. RPH masing-masing sudah mempunyai objektif dan evidens PBD lebih khusus.

Saya selaraskan **42/42 objektif dan `Evidens PBD` dalam RPT CSV** menggunakan seksyen 'Objektif dan kriteria kejayaan' setiap `lesson_001.md` hingga `lesson_042.md`. Nombor PdP, unit, SK, SP, sumber, status dan pautan RPH **tidak diubah**.

Backup asal: `rpt_2027/psv/backups/RPT_PSV_Tahun_5_2027_DRAF_before_objectives_20261104.csv`.

RPT HTML Tahun 5 sengaja tidak diubah kerana versi cetakan ringkas memaparkan **Sesi, PdP, Unit, Fokus, SP dan halaman BT sahaja**, tidak memaparkan kolum Objektif atau Evidens PBD.

Ujian regresi ditambah: `tests/test_psv_rpt_rph_source_order.py`; menyemak turutan 10 unit Tahun 2–6 dan kesamaan objektif/evidens RPT–RPH Tahun 5. **Larian CI belum disahkan pada saat laporan ini ditulis.**

## 3. Perkara belum lulus

- Verifikasi visual halaman-halaman Buku Teks Tahun 2–6, hasil kerja, bahan dan keselamatan untuk setiap aktiviti.
- Padanan **makna** SK/SP dengan aktiviti dan objektif, bukan hanya padanan kod atau nama unit.
- Takwim rasmi dan tarikh PdP 2027 berbeza Kumpulan A/B, termasuk cuti umum dan gantian negeri.
- Pemeriksaan visual dokumen Word/PDF RPH satu muka surat A4 dan RPT PDF landskap.
- CI, ujian integrasi database, Word/PDF dan Telegram staging. Tiada bukti akses pengguna LIVE.

**Keputusan:** Kandungan tersedia untuk semakan lanjut; **jangan tandakan FINAL READY, merge ke main, atau hidupkan bot** hanya berdasarkan ujian ini.
