# CikguLaju Matematik T2–T6 — v35 RPH quality and release gate (5 Nov 2026)

**TIDAK FINAL READY UNTUK TELEGRAM/AKADEMIK.** Semua kerja ini pada salinan STAGING; `main`, database pengguna, Telegram, Web dan Render **tidak** diubah.

## Hasil sah pada salinan v35
- Tahun 2,3,4,5,6: 117 Lesson/tahun. **585 fail DOCX, 585 PDF A4 portrait satu halaman, 585 Markdown dan lima PDF gabungan 117 halaman**. ZIP integrity: PASS, nama fail unik, tidak terpotong, fail tidak tertukar tahun/lesson.
- v33: **230 RPH yang masih menggunakan arahan generik** dimurnikan kepada **160 set Tahun–SP**, tanpa mengubah 355 RPH lain. Kewujudan tiga frasa generik sasaran menjadi **0**. Ujian dokumen 585/585 dan tiada set Aktiviti 1+Aktiviti 2+PBD identik.
- v34: **117 RPH Tahun 4** mempunyai set induksi dan BBM yang lebih khusus mengikut SP; **34 Aktiviti 1 Tahun 4** yang terlalu umum diganti dengan contoh dan kaedah pengajaran jelas. RPH Tahun 2, 3, 5, 6 dikekalkan byte-identical daripada v33. 117/117 Word Year 4 berjaya dirender sebagai PDF satu halaman, tiada bahagian hilang atau identiti bertukar.
- v35: pembetulan **kesilapan geometri sebenar** RPH Tahun 4 Lesson 097. Dahulu segi tiga sama sisi dinyatakan tapak 6 dan tinggi 4 untuk luas 12, sesuatu yang mustahil bagi segi tiga sama sisi. Kini contoh luas 12 unit² dinyatakan **segi tiga bersudut tegak**, manakala segi tiga sama sisi perlu tinggi tegak sebenar. Word/PDF baharu diperiksa satu halaman.
- QA matematik: 153 persamaan dikenal pasti; 150 amaran sifar pada keseluruhan v34 setelah memisahkan dua padanan regex sebahagian yang palsu dan kesilapan L097 yang telah dibetulkan dalam v35. Ini **bukan** pembuktian semua konsep matematik dalam 585 lesson.
- v35 SHA-256: `f81236c1c8ba9137d92bf184892b908b38b6dc7dbcf4f5fa0c42655eff45ce1a`; saiz arkib **48,413,126 bytes**. `testzip()` tiada ralat. Five annual PDFs: 117 halaman/tahun.
- Adapter ujian staging fail-closed dibuat di luar production: semak SHA-256, setiap 585 PDF wujud, nombor Lesson tepat, pelanggan percuma ditolak, pengguna berbayar/admin dibenarkan, callback lama kekal, ralat hantar tidak dilaporkan sebagai berjaya. **9/9 unittest lulus secara setempat dengan mock**, bukan Telegram API LIVE.

## Perkara yang masih gagal gate FINAL
1. **585 RPH belum disahkan akademik secara individu** pada halaman aktiviti sebenar Buku Teks/Buku Aktiviti dan instrumen PBD. Kewujudan kod SP dalam semua buku yang diimbas bukan kelulusan aktiviti.
2. Tahun 4 **83 sumber RPH → 117 Lesson** masih pecahan cadangan. Keutuhan setiap daripada 34 Lesson tambahan belum diaudit terhadap sumber RPH asal dan buku teks secara individu.
3. Buku Aktiviti Tahun 2–6, rujukan halaman yang khusus dan integrasi aktiviti workbook masih perlu diaudit.
4. Tarikh PdP, kalendar negeri 2027, cuti ganti serta kesesuaian jadual kelas belum disahkan secara per pengguna.
5. Pakej ZIP v35 belum dipasang/dipaut ke RPH sebenar CikguLaju; **ujian Telegram LIVE, database kanonik v26.00 dan regersi subjek lain belum lulus**. GitHub `main` masih mempunyai route RPT Matematik PDF v28 sahaja.
6. Tiada approval guru individu; jangan paparkan badge FINAL READY/READY tanpa bukti di atas.

## Laluan pelepasan yang selamat
- Simpan paket v35 dan adapter v35 dalam ruang staging; jangan pilih fallback diam-diam.
- Luluskan 585 baris matriks bukti RPH–SP–BT/BA–aktiviti–PBD–PDF dan uji penghantaran Telegram serta akses percubaan/berbayar dengan DB staging.
- Rebase branch terhadap `main` terbaharu (projek lain sedang berjalan serentak), audit diff, backup DB pengguna, baru merge terhad jika semua lulus.

**Status: TECHNICALLY VERIFIED / NOT FINAL READY.**

Audit terdahulu: [v32](./matematik_v32_189_rph_dedup_quality_gate_20261105.md), [v31](./matematik_v31_585_rph_evidence_and_quality_gate_20261105.md), [v30](./matematik_t2_t6_585_rph_v30_technical_qa_20261105.md).