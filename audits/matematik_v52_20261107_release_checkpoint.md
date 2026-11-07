# CikguLaju Matematik v52 — Nisbah dan Pecahan, Audit RPT 2027

**7 November 2026 • STAGING DRAFT • LULUS QA teknikal, belum FINAL READY akademik**

## Pembetulan berpandukan DSKP asal (imej PDF diperiksa)
- Tahun 4 Lesson **104**: SP **7.2.1** dalam RPH lama terpotong pada `nisbah 1`. DSKP Tahun 4 PDF fizikal **76** menetapkan nisbah **1:1 hingga 1:10, 1:100 dan 1:1000**. SP, objektif dan PBD dikemas kini tanpa mengubah urutan lesson.
- Tahun 5 Lesson **107–108**: SP **7.2.1** terhenti pada perkataan `bentuk a`. DSKP Tahun 5 PDF fizikal **72** menetapkan **a : b** bagi (i) bahagian kepada bahagian, (ii) bahagian kepada keseluruhan, (iii) keseluruhan kepada bahagian; unit perlu sama. SP, objektif, set induksi, Aktiviti 1, Aktiviti 2 dan PBD diselaraskan; contoh kad 6 merah +9 biru=15 disemak supaya nisbah **2:3**, **2:5**, **5:3** dipelajari mengikut urutan yang betul.
- Tahun 5 **10 RPH ukuran**: L072, L074, L077 (panjang), L079, L082 (jisim), L089, L090, L091, L092, L093 (isi padu cecair). Semakan DSKP Tahun 5 PDF fizikal **62–63** mengesahkan SP melibatkan **kedua-dua pecahan dan perpuluhan**. Aktiviti/PBD yang sebelumnya menumpukan hanya pada perpuluhan kini mempunyai pengiraan pecahan dan penukaran unit yang nyata; contoh terdahulu yang betul dikekalkan.
- **42 seksyen RPH** disunting pada **13 lesson**: 1 Tahun 4 dan 12 Tahun 5. Bukti sebelum/selepas: `audits/matematik_v52_13_rph_komponen_SP_20261107.csv`. **Tiada kelulusan rasmi item buku** didakwa.

## QA arkib
- Sumber: `CIKGULAJU_MATEMATIK_v51_585_RPH_SP_PENUH_PDP_TEPAT_STAGING.zip` SHA256 `22382da12f876fd63b294ec6f69cd4cc7bcc14e596e73558f43d2cea921f7e94`.
- Hasil: `CIKGULAJU_MATEMATIK_v52_585_RPH_NISBAH_PECAHAN_SP_STAGING.zip` (**48,783,243 bait**), SHA256 `646ec1516189275509382d92cc7228912f7a805b41229d5912f5f1a9ea58f847`.
- Masih mengandungi **585 Word + 585 Markdown + 585 PDF individu + 5 PDF gabungan**.
- **13 Word/PDF/Markdown individu** dikemas kini, **572 lesson lain byte-identical** dengan v51. PDF gabungan Tahun 4 dan 5 dijana semula.
- CRC ZIP lulus, **585/585 PDF** satu halaman A4, semua 13 PDF berubah bebas clipping. Contoh Tahun 4 L104, Tahun 5 L072 dan L107 dirender PNG lalu diperiksa visual.
- **21/21 ujian pratonton setempat menggunakan ZIP v52 sebenar PASS**: akses admin/berbayar, menolak pengguna tidak dibenarkan, hash, Word/PDF lesson tepat, semua 585 PDF, callback lama, tiada DB/kuota, penghantaran gagal tidak dianggap berjaya. **Ini bukan ujian Telegram/Web staging sebenar**.
- Ujian regresi yang ditambah: `tests/test_matematik_ba_v52_preview_20261107.py`, `tests/test_matematik_ba_v52_ratio_fraction_20261107.py`, `tests/test_matematik_ba_v52_arithmetic_20261107.py`.

## Jurang baharu pada RPT 2027
- RPT Matematik Tahun 2–6 PDF **v28 SEMENTARA** daripada Drive telah disemak. Padanan **585/585 nombor Lesson dan kod SP**, serta **585/585 Minggu**, kekal.
- Namun, audit kandungan PDF RPT mengesan **210 kemunculan elipsis `…`**: Tahun 2 = 0; Tahun 3 = **35**; Tahun 4 = **71**; Tahun 5 = **50**; Tahun 6 = **54**. Elipsis terdapat pada sebahagian teks pernyataan SP dan huraian fokus yang dipendekkan. Ini **bukan 210 SP unik**; ia bilangan kemunculan teks. Bukti: `audits/matematik_v52_rpt2027_teks_terpotong_20261107.csv`.
- Oleh itu **RPT tidak dilabel full SP atau final ready** hanya kerana kod SP dan Minggu padan. Teks SP dan huraian RPT perlu dibetulkan melalui reka letak yang muat kandungan sebenar, bukan elipsis automatik; dokumen asal harus terus dikekalkan sehingga versi pengganti diuji.

## Gate pelepasan
- **0/585 signoff akademik formal item latihan BA/BT**; ini tidak bermaksud 0 RPH mempunyai aktiviti baik, hanya belum semua disahkan item demi item.
- **34 pasangan Tahun 4** masih memerlukan audit item Buku Teks; Buku Teks T4 asal ~306MB melebihi had muat turun connector 256MB. Pemeriksaan SP DSKP dan perbezaan aktiviti sahaja belum mencukupi.
- Takwim negeri/cuti ganti 2027 dan fungsi RPH Hari Ini/Minggu Ini belum diuji E2E pada jadual guru.
- **Telegram–Web staging E2E pada DB kanonik belum dijalankan**. Tiada import ke DB, tiada deploy, tiada ubah akaun, kuota, pembayaran atau status langganan.
- `final_ready=false`, `production_modified=false`. PR `#444` kekal **DRAFT STAGING**: **JANGAN MERGE/DEPLOY PRODUKSI**.
