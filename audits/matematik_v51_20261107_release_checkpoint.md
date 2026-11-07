# Matematik v51 — RPT 2027 x RPH 585 dan pembetulan skop SP

**Tarikh:** 7 November 2026. **Status: TECHNICAL QA PASS; ACADEMIC FINAL READY = NO; STAGING ONLY.**

## Asal dan integriti
- Input: `CIKGULAJU_MATEMATIK_v50_585_RPH_GEOMETRI_DAN_GRAF_STAGING.zip`, SHA-256 `895c87161dd7b62d9cecdea20b1d9efdf7ce0b77a14915d4edc186c4d2c9cdbb`.
- Output: `CIKGULAJU_MATEMATIK_v51_585_RPH_SP_PENUH_PDP_TEPAT_STAGING.zip`, **48,780,476 bytes**. SHA-256 `22382da12f876fd63b294ec6f69cd4cc7bcc14e596e73558f43d2cea921f7e94`.
- Arkib v51: 585 Word, 585 Markdown, 585 PDF satu halaman A4, lima PDF gabungan tahun 2–6. `testzip() == None` dan semakan PDF teks/muka surat pada 585 Lesson PASS.
- **16 RPH / 50 medan** disunting; **569** yang lain tidak disentuh pada fail Word/PDF/Markdown. PDF gabungan Tahun 3, 4, 5 dijana semula. Contoh output DOCX dirender melalui LibreOffice dan PNG diperiksa secara visual (T3-L032; T4-L018, L022; T5-L057, L058, L070, L071). Tiada dokumen individu yang melebihi A4.
- Semua perubahan dan teks sebelum/selepas: `audits/matematik_v51_16_rph_sp_objektif_aktiviti_semakan_20261107.csv`. Bukti DSKP PDF asal disemak pada halaman fizik Tahun 3 p54, Tahun 4 p48/p52/p62, Tahun 5 p58/p62. **Pernyataan baharu disusun ringkas berdasarkan kandungan DSKP, bukan transkrip verbatim.**

## Pembetulan bermakna
- **T3-L032/033:** SP dan objektif yang asal terhenti pada perkataan **'melibatkan'** diperjelas dengan pasangan penyebut dibenarkan oleh DSKP 3.1.5/3.1.6. Aktiviti tambah/tolak pecahan berpenyebut sama tidak diubah, kerana ia subkemahiran yang sah.
- **T4-L018/019:** RPH SP1.9.1 hanya menyebut operasi tambah/tolak. DSKP asal turut mengandungi **darab/bahagi dalam lingkungan 100 000 dan situasi harian**. SP dan objektif diperjelas; aktiviti darab/bahagi asal kini dinyatakan dalam skop SP yang betul.
- **T4-L022/023:** keterangan SP2.1.3 sebelumnya dilabel ringkasan terlalu pendek; sempadan dua jenis penolakan pecahan dan jenis nombor diperjelas.
- **T4-L068–071:** keterangan SP bagi penukaran / tambah-tolak / darab-bahagi unit masa diperinci termasuk skop jam–hari, hari–minggu, bulan–tahun, tahun–dekad/abad dan had nombor hingga dua digit.
- **T5-L057/058:** SP4.1.1 memerlukan tempoh **hari-jam, bulan-hari, tahun-bulan-hari**. Aktiviti lama hanya mengira 9:20–10:05 dalam minit, jadi set induksi, A1, A2, PBD dan BBM dibina semula menggunakan garis masa serta tarikh kalendar (contohnya 1 Feb 2025→5 Apr 2026 =1 tahun 2 bulan 4 hari).
- **T5-L068/069:** penukaran unit mm–cm–m–km dalam perpuluhan hingga tiga tempat dinyatakan lengkap dalam SP/objektif.
- **T5-L070/071:** SP5.1.2 memerlukan penukaran ukuran panjang **dalam pecahan**, sedangkan aktiviti terdahulu kebanyakannya perpuluhan. Set induksi, A1, A2, PBD, BBM dan objektif diperbaiki menggunakan 1/2 m=50cm, 3/4km=750m, 7 3/8km=7 375m, dan lain-lain contoh pecahan yang benar.

## Keselarasan RPT 2027
- Lima PDF `RPT_Matematik_Tahun_{2..6}_2027_v28_SEMENTARA.pdf` diambil daripada **Google Drive pengguna** (dokumen RPT v28 masih bertanda DRAF/SEMENTARA).
- **585/585** pasangan Tahun/Lesson (117 setiap tahun) ditemui tepat sekali, dengan kod SP yang sama dalam RPT dan RPH. Bukti lengkap: `audits/matematik_v51_585_rpt2027_vs_rph_20261107.csv`.
- **585/585** nombor **Minggu RPT** dalam RPH padan dengan RPT; tiada RPH terjadual di luar julat Minggu 01–44. Bukti: `audits/matematik_v51_585_rpt_week_vs_rph_20261107.csv`.
- Kerangka kalendar A/B RPT bermula **4 Jan 2027** dan berakhir **2 Dis 2027 (A) / 3 Dis 2027 (B)**, sepadan dengan kalendar KPM yang dilaporkan 2–3 Oktober 2026. Portal KPM `https://www.moe.gov.my/index.php/kalendar-akademik-semasa`; berita Bernama `https://www.bernama.com/bm/am/news.php?id=2614792`.
- Rentang hari minggu A (Ahad–Khamis, kecuali minggu mula 4 Jan) dan B (Isnin–Jumaat) secara aritmetik sepadan. **Ini tidak sama dengan ujian cuti tambahan KPM, cuti umum negeri atau jadual PdP harian**.
- Keseragaman kod dan minggu antara dua dokumen yang mungkin berkongsi sumber tidak dengan sendirinya membuktikan ketepatan akademik terhadap buku teks/latihan.

## Pelepasan masih ditahan
- **0/585 signoff akademik formal** bagi padanan setiap latihan Buku Aktiviti/Buku Teks dengan SP dan PBD; pembetulan ini hanya ditandai sebagai SOURCE_SCOPED_EDITORIAL/CURRICULUM CORRECTION. Banyak rujukan halaman masih topik/indikatif, bukan nombor latihan yang disahkan.
- **34 pasangan** Year4 SP sama tetapi sesi berbeza masih memerlukan penilaian item buku teks. Fail Buku Teks Tahun 4 306MB melebihi had peringkat muat turun connector; tidak boleh menganggap kesemuanya verified.
- Pemadanan negeri/Kumpulan A-B **cuti umum, cuti ganti, cuti tambahan KPM 2027** dengan jadual guru dan RPH Hari Ini/Minggu Ini belum diuji E2E.
- **Telegram-Web staging sebenar** belum menjalankan ujian E2E pada DB kanonik. Ujian loader sintetik/local tidak mewakili pengeluaran sebenar.
- `final_ready=false`, `production_modified=false`. **Jangan merge/deploy**, dan jangan ubah kuota, bayaran, akaun atau data pengguna.
- ZIP besar tidak diupload ke GitHub awam/Library yang mempunyai had kapasiti. Fail CSV matriks QA kecil disimpan dalam `/CikguLaju/Matematik_2027_STAGING/`.

PR #444: https://github.com/nurynayreen88/CikguLaju-AI/pull/444
