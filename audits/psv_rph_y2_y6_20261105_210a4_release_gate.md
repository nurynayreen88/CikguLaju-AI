# PSV Tahun 2–6 — audit RPH 210/210, PDF + Word A4 | 5 November 2026

**Status kelulusan yang tepat:** **LULUS QA TEKNIKAL STAGING / BOLEH PILOT DALAMAN; BELUM FINAL READY UNTUK PENGGUNA PRODUKSI.**

PR staging: https://github.com/nurynayreen88/CikguLaju-AI/pull/196  
**Jangan merge PR #196, jangan pindah RPH ke main, jangan ubah DB atau Telegram LIVE sehingga gerbang kandungan dan runtime selesai.**

## Keputusan berasaskan bukti

| Gerbang | Hasil | Sumber bukti |
|---|---|---|
| Inventori RPH T2–6 | 210/210 fail: 42 setiap tahun | GitHub branch staging, `rph_standalone/psv/year{2..6}/lesson_001..042.md` |
| RPT ↔ RPH / unit | 210/210 rekod & 50/50 crosswalk unit, backup disemak | CI Python, `tests/test_psv_rpt_rph_alignment.py`, `tests/test_psv_rpt_rph_source_order.py` |
| Kewujudan kod SP | Semua kod SP yang digunakan dalam 210 RPT dijumpai dalam DSKP tahun yang sepadan | `rpt_2027/psv/dskp_sp_code_presence_audit_20261105.json`, PDF DSKP T2–6 dalam Google Drive |
| Ujian regresi staging | **21/21 lulus** selepas memperjelaskan cerminan motif PdP 031 T6 | https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41873591285 |
| RPH PDF pratonton (ReportLab) | **210/210** satu halaman A4 | Ujian `test_all_210_staged_pdf_previews_fit_exactly_one_a4_page` dalam CI di atas |
| RPH Word pratonton (LibreOffice sebenar) | **210/210** satu halaman A4; tiada ralat, tiada halaman tambahan | https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41874076050 ; laporan `psv-staging-210-word-a4-report` |
| Aliran export | Sumber DRAF ditolak kecuali `--preview` dalaman yang eksplisit; status DRAF tidak dicetak dalam pratonton | `rph_standalone/psv/preview_a4.py` dan `tests/test_psv_preview_a4.py` |
| Telegram produksi | **Tidak diubah; tidak diuji** | Tiada merge, tiada app.py atau DB, tiada release |
| Makna semua SK/SP + halaman buku teks | **Belum ada bukti pengesahan semantik 210/210 satu-persatu** | Gerbang kandungan masih terbuka |

**Had pengesahan:** 210/210 lulus semakan inventori, kod dan output A4; kejayaan ini tidak sama dengan semakan pedagogi setiap halaman buku teks atau kesahan setiap tafsiran SP. Keseragaman Word yang diuji merujuk penjana **QA staging baharu**, belum penjana Telegram LIVE. Tarikh/negeri dalam RPT 2027 juga belum selesai.

## Pembaikan kandungan terkawal
- **Tahun 4 Unit 10 PdP 038–040**: Harum Mewangi ukiran sabun; mengekalkan motif timbul, menurunkan bahagian latar dengan **alat tumpul** tanpa pisau murid, membersihkan sisa dengan berus, kemasan kain net/reben, apresiasi dan bukti PBD. RPT T4 objektif/evidens ditulis semula tepat.
- **Tahun 5 Unit 10 PdP 038–040**: Bunga Kemboja Emas. Membezakan **tekat timbul sebenar** (mempulur, benang hias, ikat menggunakan jarum sulam tumpul dengan guru) daripada sekadar tampalan benang. Objektif, PBD, RPT dan rujukan Unit10 dikemas kini.
- **Tahun 6 PdP 028–039**: Pembetulan batch terdahulu atas teknik cucuk sanggul, tanjak, Wau Bulan Sirih Pinang dan beg batik. PdP 031 turut diperjelas penggunaan **susunan cerminan motif** secara eksplisit selepas dapatan CI.
- **Tahun 6 18 RPH lain**: kriteria kejayaan generik diganti evidens PBD yang wujud dalam RPT.
- **Semua versi asal** untuk pembetulan terkawal disimpan sebagai backup dalam folder PSV dan sejarah GitHub. Perubahan tidak memadam fail lama atau mengubah rekod pengguna.

## Gerbang sebelum FINAL READY sebenar
1. Audit semantik **210 PdP satu persatu**, membandingkan isi SP DSKP dan aktiviti pada halaman Buku Teks yang tepat; pastikan bahagian Seni Visual Tahun 2–4 tidak terserap Seni Muzik.
2. Semak hasil cetakan **visual** pada sampel ekstrem (paling panjang, tahap awal/akhir, kraf 3D) dan kesesuaian bahasa supaya guru boleh terus menggunakannya; PDF/Word telah lulus bilangan halaman automatik tetapi belum semakan visual penuh.
3. Uji integrasi penjana RPH PSV pada **runtime staging** dan kesan terhadap menu/tarikh/kelas, termasuk penapisan pengguna. Penjana QA sementara **jangan dianggap** sudah disambung ke Telegram.
4. Sebarang persediaan pelepasan perlu mengambil `main` semasa dan membuat port terpilih; PR #196 kini besar dan mungkin berkonflik dengan RPT PSV yang sudah berada di `main` daripada PR #257. Jangan merge keseluruhan branch lama.
5. Kelulusan pelepasan berasingan untuk RPT 2027 (tarikh Kumpulan A/B dan cuti gantian negeri) jika RPT ingin dilabel muktamad.

## Polisi keselamatan
- `main`, database produksi dan Telegram LIVE: **tiada perubahan**.
- PR #196 **draft**, kekal staging.
- Fail sumber RPH: **DRAF SEMAK**, bukan READY untuk paparan pengguna.
- Peratus siap terdahulu ~90% bermaksud kemajuan penulisan kandungan, bukan peratus lulus audit semantik.
- Keputusan gerbang: **QA TEKNIKAL LULUS, FINAL READY BELUM DILULUSKAN.**

## Perintah semakan boleh ulang
```sh
python -m unittest -v tests.test_psv_rpt_rph_alignment tests.test_psv_rpt_rph_source_order tests.test_psv_preview_a4
python tools/verify_psv_word_a4.py --batch-size 25
```
Kedua-duanya dipanggil oleh workflow staging yang tidak deploy atau menulis ke DB.
