# Matematik v58 — RPH Tahun 4: rujukan bab buku teks dan set induksi

**7 November 2026 • STAGING DRAFT • QA teknikal ZIP sebenar 15/15 PASS • AKADEMIK FINAL READY = NO**

## Batas kerja
- **Hanya RPH Matematik Tahun 2–6.** RPT 2027 dikendalikan dalam aliran lain dan **tidak dibaca, diubah, dijana atau dipersembahkan sebagai kerja v58**.
- Tiada perubahan DB, pengguna, kuota, bayaran, Render produksi, Telegram atau Web.
- PR #444 kekal draf; jangan gabung atau deploy.

## Perubahan sebenar pada RPH
- **Buku Teks Matematik Tahun 4 Sekolah Kebangsaan**, Dewan Bahasa dan Pustaka (2019), teks halaman awam: https://anyflip.com/coll/xosm/basic . Jadual kandungan buku memaparkan bab dan halaman bercetak seperti:
  - Bahagi hlm **37–43**; operasi bergabung tambah/tolak **28–29**; darab/bahagi **43–47**;
  - Penolakan pecahan **75–79**; pecahan daripada kuantiti **83–85**; masalah pecahan/perpuluhan/peratus **97–102**;
  - Wang **105–134**; masa **139–168**; ukuran/jisim/isi padu **171–197**; ruang **199–214**; koordinat/nisbah/kadaran **215–231**; pengurusan data **233–242**.
- **32 daripada 34 pasangan** RPH Tahun 4 sebelumnya cuma menyebut `(unit/tajuk berkaitan)`. **64 RPH** mendapat rujukan bab/himpunan halaman Buku Teks yang boleh dicari, tanpa menukar nombor Lesson, kod SP, objektif atau latihan.
- **2 pasangan sedia khusus dikekalkan 100%**: T4-L022/L023 sudah menyebut DSKP SP2.1.3(i–ii), Buku Teks p75–78; T4-L056/L057 mempunyai sumber mata wang Buku Teks p126 dan kadar semasa BNM bertarikh. Keempat-empat RPH tersebut **byte-identical**.
- **9 set induksi pertama yang masih meleset daripada SP** diperbetulkan, pada T4-L010 (bahagi), L025 (pecahan daripada kuantiti), L027 (pecahan tak wajar/nombor bercampur), L029 (tambah pecahan), L043 (darab wang), L045 (bahagi wang), L049 (darab/bahagi wang), L087 (tambah/tolak isi padu) dan L089 (darab/bahagi isi padu). Aktiviti 1 sedia ada menjadi asas untuk pencetus sebenar. Setiap pasangan tetap mempunyai intro yang berbeza antara dua PdP.
- Keseluruhan **73 seksyen berubah pada 64 RPH**, dengan **521 RPH individu lain kekal byte-identical** dibandingkan v57 dalam Word/PDF/Markdown.
- Sumber hanya **rujukan bab dan julat halaman bercetak**, **bukan pengesahan setiap latihan atau item buku**. Kehadiran contoh dan rujukan bukan kelulusan formal 34 pasangan.

## Fail dan jaminan QA
- Input: `CIKGULAJU_MATEMATIK_v57_585_RPH_PASANGAN_T4_INDUKSI_STAGING.zip`, SHA256 `07bada94723bde54d958c11fcdfc3e46b06e59aefbcf63e26926144365331332`.
- Output: `CIKGULAJU_MATEMATIK_v58_585_RPH_RUJUKAN_BUKU_T4_DAN_INDUKSI_STAGING.zip`, **48,954,101 bytes**, SHA256 `bb8d1e727c383efd2bfbe2b748570f7b6f4aeb99c7ffffa4f4426bd5baafdc13`.
- Arkib 585 Word, 585 Markdown, 585 PDF individu satu halaman A4, lima PDF gabungan ×117 muka surat. **Hanya PDF gabungan Tahun 4 dibina semula**; yang lain kekal bait demi bait.
- **64 Word** dirender melalui LibreOffice, semuanya A4 satu halaman dan tiada teks di luar margin. Contact sheet visual 8 dokumen diperiksa: T4-L010, L025, L027, L029, L043, L049, L087, L089.
- **15/15 ujian pada ZIP sebenar PASS**: SHA256, CRC, tiada pendua ZIP, bilangan 64 rujukan dan 9 intro, empat RPH sedia khusus utuh, tepat 64 RPH berubah / 521 kekal, 64 Markdown/Word/PDF selari, 585 A4, lima gabungan 117 muka surat, gabungan tahun lain unchanged, tiada fail RPT, final_ready false dan audit sepadan manifest.
- Bukti lengkap **di dalam ZIP**: `AUDIT/V58_73_RPH_SECTIONS.csv`, `AUDIT/V58_64_TEXTBOOK_CHAPTER_REFERENCES.csv`, `AUDIT/V58_RELEASE_GATE.json`. CSV audit juga sebagai artifak perbualan.
- Loader pratonton baru `rph_standalone/matematik/staging_preview_v58.py` bersifat opt-in, hash ZIP dikunci dan fail-closed jika tidak sepadan; **bukan integrasi produksi**.
- GitHub menyimpan hanya audit manifest, checkpoint dan ujian kecil; ZIP besar tidak dimuat naik ke GitHub awam.

## Baki HOLD sebelum FINAL READY
- **34 pasangan Tahun 4 belum lulus semakan latihan item demi item** menggunakan naskhah Buku Teks dan penilaian pedagogi; `BT4_item_level_exercises_verified=0` di gate ini.
- Semakan akademik 585 RPH secara menyeluruh belum selesai; **0 signoff guru formal**.
- **Telegram–Web staging E2E sebenar** terhadap database kanonik belum dilaksanakan. Ujian ZIP local dan mock bukan bukti sistem sudah dipasang.
- `final_ready=false`, `production_modified=false`, `rpt_changed=false`; **jangan merge/deploy**.
