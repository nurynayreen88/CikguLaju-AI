# Matematik v59 — 120 soalan PBD asli untuk 30 RPH pertama dalam pasangan Tahun 4

**Tarikh:** 7 November 2026 • **SKOP RPH SAHAJA** • **DRAF STAGING** • **QA TEKNIKAL PASS** • **FINAL READY AKADEMIK = NO**

## Dapatan akademik dan pembetulan sebenar
- **34 pasangan RPH Tahun 4** sudah mempunyai aktiviti asas serta pembuka berbeza (v57/v58), tetapi **30 lesson pertama** masih menggunakan arahan pentaksiran generik seperti “empat soalan individu” tanpa butiran latihan.
- **4 lesson pertama** yang sudah mempunyai tugasan khusus tidak diubah: **T4-L022, T4-L039, T4-L056, T4-L060**.
- Dalam v59, **30 RPH** tersebut kini mengandungi **4 soalan PBD nyata**, disusun ringkas untuk **10 minit pengukuhan/pentaksiran**, dengan kriteria kejayaan 3 daripada 4 soalan betul.
- **120 soalan asli** telah dibina daripada **SK/SP dan Aktiviti 1/2 RPH sedia ada**. Bentuk soalan termasuk nombor bulat, anu, pecahan/peratus, wang, masa, panjang, jisim, isi padu, ruang, koordinat, kadaran, nisbah dan data.
- Semua 120 soalan mempunyai **panduan jawapan guru berasingan** dalam CSV. **109 jawapan pengiraan disemak dengan matematik tepat**, **7 tugasan koordinat/kategori disemak berdasarkan maklumat soalan**, dan **4 tugasan mengukur objek sebenar memerlukan semakan guru mengikut objek/alat yang digunakan** (toleransi 1 mm).
- Contoh: T4-L010 empat pengiraan bahagi tepat (pembahagi 11, 18, 100 dan 1000); T4-L025 empat pecahan daripada kuantiti termasuk nombor bercampur; T4-L099 perimeter, luas segi empat tepat, luas segi tiga dan isi padu.
- **Tiada soalan didakwa sebagai petikan Buku Teks rasmi.** Soalan ialah bahan asli yang sepadan dengan kemahiran/aktiviti RPH. **Item latihan Buku Teks 34 pasangan tetap belum disahkan satu per satu**.

## Integriti dan ujian sebenar
- **Sumber:** `CIKGULAJU_MATEMATIK_v58_585_RPH_RUJUKAN_BUKU_T4_DAN_INDUKSI_STAGING.zip`, SHA256 `bb8d1e727c383efd2bfbe2b748570f7b6f4aeb99c7ffffa4f4426bd5baafdc13`.
- **Hasil:** `CIKGULAJU_MATEMATIK_v59_585_RPH_PBD_30_PASANGAN_T4_STAGING.zip`, **48,994,065 bytes**, SHA256 `79a759be40fd8aadebbf3318d784e042239d290e8cc36b4136380c8fb5c215eb`.
- **30 RPH ×3 format (Word/PDF/Markdown) berubah pada satu medan PBD sahaja; 555 RPH lain byte-identical** dengan v58. Tiada perubahan objektif, SK/SP, buku rujukan, nombor Lesson atau masa.
- ZIP: **585 Word, 585 Markdown, 585 PDF individu A4 satu halaman**, lima PDF gabungan 117 halaman; hanya gabungan Tahun 4 dijana semula. CRC ZIP lulus; tiada nama pendua.
- Semua **30 DOCX dikonversi kepada PDF** dan disemak satu halaman A4, kandungan berada dalam sempadan; **8 contoh visual diperiksa** (L010, L018, L025, L070, L091, L102, L107, L116).
- **12/12 ujian terhadap ZIP v59 sebenar PASS** di `/mnt/data/math_ready_audit/test_v59_actual_archive.py`, termasuk SHA, CRC, 30 perubahan, 555 tidak berubah, 120 soalan/jawapan, semua PDF A4, lima gabungan, metadata HOLD dan tiada fail RPT.
- Artefak guru berasingan: `CIKGULAJU_MATEMATIK_v59_SKEMA_GURU_120_SOALAN_T4_STAGING.pdf` **15 halaman**, jadual 30 RPH ×4 soalan dengan jawapan dan nota.
- Audit lengkap **disertakan dalam ZIP**:
  - `AUDIT/V59_30_PBD_BEFORE_AFTER.csv`
  - `AUDIT/V59_120_PBD_QUESTIONS_ANSWER_KEY.csv`
  - `AUDIT/V59_RELEASE_GATE.json` (`BA_year2_3_ref_count=234`, `final_ready=false`).
- Fail audit luaran untuk pengguna: `/mnt/data/math_ready_audit/matematik_v59_30_RPH_PBD_T4_before_after.csv` dan `/mnt/data/math_ready_audit/matematik_v59_120_soalan_pentaksiran_skema_jawapan_T4.csv`.
- ZIP besar tidak disimpan dalam GitHub awam. **Ujian GitHub** terhadap manifest serta loader berasingan daripada ujian sebenar ZIP 12/12 yang dilakukan setempat.
- Pratonton opt-in staging: `rph_standalone/matematik/staging_preview_v59.py`, hash SHA-256 v59 dikunci, gagal tertutup jika release gate tidak padan. Tidak diimport ke sistem live.

## Kawalan pelepasan
- **JANGAN MERGE/DEPLOY PRODUKSI**. `final_ready=false`, `rpt_changed=false`, `production_modified=false`.
- **RPT 2027 dikendalikan dalam chat lain, tidak dibaca/diubah/dijana atau ditulis oleh v59.**
- Tidak menyentuh database kanonik, akaun, kuota, langganan, bayaran, jadual waktu guru atau Telegram/Web live.
- **34 pasangan Tahun 4 belum disahkan latihan Buku Teks pada aras soalan**; 0 signoff formal guru untuk keseluruhan 585 RPH.
- **Ujian Telegram–Web staging E2E sebenar belum dilakukan**, dan ujian mock/ZIP tidak boleh dijadikan bukti integrasi live.
