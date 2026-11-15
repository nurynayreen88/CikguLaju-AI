# RPT 2027 — 56 PDF format seragam, checkpoint 7 November 2026

**Status: SIAP PENYELARASAN FORMAT STAGING; BELUM FINAL READY untuk pengguna.** Tiada modifikasi data pengguna, Telegram/Web, DB master, atau `main`; semua hasil ialah ZIP/artifact penjanaan CI dan calon staging PR #441.

## Hasil QA keseluruhan

- **56 kombinasi subjek × Tahun** mempunyai PDF landskap A4 dengan **5 lajur** `MINGGU / TARIKH | UNIT / TAJUK / PDP | SK | SP | CATATAN / BAHAN`; muka depan: slot logo, nama sekolah, nama guru.
- Jumlah **1,628 halaman PDF** daripada ZIP gabungan lokal diperiksa menggunakan PyMuPDF; 56 nama PDF unik, 12 subjek, tiada fail tiada muka depan atau bukan landskap.
- Sel minggu berulang ditandakan mengikut sumber tarikh A/B, dengan merge sehingga batas muat halaman; bagi PdP tinggi, label minggu diulang pada kumpulan muka surat seterusnya untuk mengelak kehilangan baris.
- **21 PDF:** Pendidikan Seni Visual (T2–6), Pendidikan Moral (T2–6), PJPK (T2–6), RBT (T4–6), Sejarah (T4–6). **Tidak** termasuk 3 simulasi RBT sebagai tambahan.
- **20 PDF:** Bahasa Melayu (T2–6), Pendidikan Islam (T2–6), Bahasa Arab (T2–6), Pendidikan Muzik (T2–6).
- **5 PDF English:** Tahun 2–6, 160 Lesson/setahun, 800 Lesson; diolah daripada RPT PDF sumber tanpa mengira halaman fizikal sebagai minggu.
- **5 PDF Matematik:** Tahun 2–6, 117 Lesson/setahun, 585 Lesson; diolah daripada RPT PDF sumber.
- **5 PDF Sains:** Tahun 2–6, 51 + 45 + 79 + 83 + 84 = **342 PdP berciri identiti tetap** daripada snapshot v25.82; **RPT SEPARA**, bukan sukatan akhir.

## Sains: 342/342 SP dipadankan tanpa rekaan

- **307/342** padanan pernyataan penuh SK/SP daripada jadual `curriculum_standards` DB v26.00 yang telah disahkan.
- **35/342** SP Tahun 2 (20) dan Tahun 3 (15) tidak disimpan dalam crosswalk v26.00, tetapi wujud pada PDF DSKP rasmi KPM. Semuanya diambil secara baca-sahaja daripada lajur *Standard Pembelajaran* dokumen tersebut dengan nomor halaman PDF dan SHA-256 dokumen.
- Ledger staging: `rpt_2027/sains/dskp_sains_y2_y3_35_missing_sp_text_20261107_DRAF.json`. Tahun 2 sumber PDF KPM 2016; Tahun 3 PDF KPM 2017. Antara halaman yang turut diperiksa visual: T2 PDF halaman 60 dan 73, T3 PDF halaman 66 dan 75; teks asal tidak dinormalkan secara senyap, termasuk ejaan yang tampak tidak lazim di sumber.
- Kod SP diluluskan sebagai **padanan teks sumber**, **bukan** kelulusan keseluruhan urutan, aktiviti atau RPH PdP. **Tiada input AI/teks ciptaan** untuk standard yang tidak ditemui.
- Kalendar Sains ialah **agihan minggu A/B cadangan** berasaskan master 2027, bukan tarikh pengajaran yang diputuskan berdasarkan jadual guru; M01, M06, M44 tidak diperuntukkan dalam simulasi. RPH Sains sebenar mungkin mempunyai lebih banyak PdP daripada 342 rekod checkpoint.
- Tahun 3 mengandungi 12 calon tajuk paparan dibetulkan daripada ledger DSKP asal; PdP 001–045 asal v25.82 tetap direkod, buku m/s ditanda calon, bukan disahkan visual.

## Penutupan teknikal CI

| Jenis | Bilangan PDF | Ujian | CI |
|---|---:|---|---|
| Batch 21 asal | 21 | A4, 5 lajur, muka depan, jadual minggu, kompilasi | [run 42321533184](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42321533184) |
| BM / PI / Bahasa Arab / Muzik (Amiri + minggu bergabung PI) | 20 | 20 PDF, 40 PNG QA, Jawi/Arab, SP/lesson, landscape | [run 42323245723](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42323245723) |
| English | 5 | 800 Lesson, PDF A4, SK/SP sumber | [run 42321533173](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42321533173) |
| Matematik | 5 | 585 Lesson, PDF A4, SK/SP sumber | [run 42321263685](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42321263685) |
| Sains | 5 | 342 PdP; 342/342 teks SK/SP; sumber KPM 35, 5 PDF dan PNG | [run 42324005525](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42324005525) |

## Baki jurang sebelum RPT boleh ditetapkan READY/LIVE

1. **Sains**: 342 snapshot ialah sebahagian sumber RPH lama, belum sama dengan master rancangan lengkap. Agihan lesson mengikut guru/negeri belum diluluskan. Sahkan susunan 2027 dan PdP sebenar dalam runtime Telegram/Web terlebih dahulu.
2. **Bahasa Arab dan Muzik**: sebahagian RPT mempunyai kod SK/SP tanpa pernyataan penuh. Audit silang DSKP penuh perlu dilengkapkan.
3. **Pendidikan Islam**: enam rekod ditahan dalam asal sumber RPH; tiada SK/SP rekaan untuk menggantikannya. Semak Jawi, Quran, masa dan kelengkapan.
4. **RBT**: 96 PdP Tahun4–6 tidak diberi minggu/tarikh sebenar; 32 slot setahun ialah calon, bukan mingguan yang diluluskan.
5. **Semua subjek**: perbezaan jadual sekolah mengikut negeri/cuti/gantian, cetakan sumber/BT/BA, ketepatan semua standard, pengesahan RPT 2027 dan ujian penggunaan muat turun Telegram/Web masih memerlukan QA release tersendiri. Jangan salah tafsir lulus PDF sebagai lulus isi akademik.
6. **KP2027 Tahun 1** dan **semua menengah** tidak termasuk dalam 56 kombinasi ini. Jangan guna RPT KSSR Tahun1 lama untuk kurikulum KP2027.

## Kawalan

**STAGING ONLY.** PR #441 masih DRAF. Jangan merge/deploy, jangan overwrite DB dan jangan silently switch sumber aplikasi. Sumber GitHub asal kekal; ZIP kompilasi ialah hasil semakan sah antara 56 PDF, bukan artifact LIVE.

## Sambungan 7 November — Muzik SP DSKP 175 PdP dan semakan akhir 56 PDF

- DSKP Muzik Tahun 2–6 daripada sumber KPM telah dibaca semula; **99 entri SP mengikut kod-tahun** tersedia dalam lima JSON crosswalk dengan SHA256 PDF asal. **175/175 PdP** kini memaparkan tajuk SK dan pernyataan teks SP sebenar dalam RPT **staging**. Dua kod DSKP yang tidak digunakan dalam sumber RPT (T2 2.3.1; T3 2.4.3) tidak dijadikan PdP baharu.
- **Pengecualian sumber bercetak dikekalkan:** Tahun 2 SK Elemen Muzik dicetak sebagai 1.1.1; Tahun 4 SK 3.1 mempunyai SP 3.2.x dan SK 4.1 mempunyai SP 4.2.1. Notasi muzik/rajah/skor yang tidak ditangkap oleh teks perlu dirujuk pada PDF DSKP asal, bukannya dijana secara rekaan.
- Pengesahan CI Music + 20 PDF lain: [run #42326793688](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42326793688) **LULUS**. Audit sumber `audits/muzik_rpt_2027_175_pdp_full_dskp_statement_display_20261107.md`; kod `rpt_2027/common/music_dskp_full_statement_staging.py`.
- Semakan menggunakan ZIP gabungan hasil CI: **56 PDF, 12 subjek, 1,630 halaman** (penambahan 3 halaman daripada isi SP Muzik penuh); semua halaman **landskap**, kotak teks dalam sempadan PDF, kulit hadapan mempunyai ruang logo/nama sekolah/nama guru, jadual lima lajur hadir. 3 simulasi RBT kekal diasingkan dan tidak dikira.
- **Bahasa Arab:** audit baharu `audits/bahasa_arab_rpt_2027_298_pdp_dskp_code_presence_20261107.json` membandingkan **298 PdP** dengan PDF DSKP sumber. Tahun 3–6 mempunyai **98/98 kod SP unik** dalam teks DSKP (23+25+25+25), tetapi ini bukti **kehadiran kod**, bukan pernyataan penuh atau semantik. PDF Tahun 2 mempunyai lapisan teks rosak: hanya kod `1.1.1` dapat diekstrak walaupun indeks RPT Tahun 2 mempunyai 19 kod SP; **jangan secara automatik anggap 18 kod tiada**. Bahagian Tahun 2 mesti dibaca menggunakan susun atur asal.
- Semua sumber CSV/RPH, DB dan produksi kekal tidak diubah. **FINAL READY masih BLOCKED** untuk RPT Sains separa, Bahasa Arab, rekod PI ditahan, minggu RBT dan integrasi runtime.


**QA catatan Muzik terakhir:** kod status dalaman `RPT_2025_26_BELUM_BUKU_DAN_AUDIO_VERIFIED`, `CADANGAN_PENGUKUHAN_BUKAN_PROJEK_RASMI` dan risiko slot cuti negeri dipaparkan kepada guru sebagai ayat ringkas yang setia pada maksud asal. Nilai mentah kekal pada `source_status_original`. CI [#42327584278](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42327584278) LULUS; pakej 56 PDF diperiksa semula: **1,630 halaman**, 12 subjek, landskap, 5 lajur, tiada blok di luar halaman.


## Audit semula 56 artifak + rujukan Arab (7 November 2026, checkpoint akhir sesi)

**STATUS: QA FORMAT LULUS — KESEDIAAN AKADEMIK DAN PRODUKSI MASIH BLOCKED.** Bukti dikumpulkan daripada artifak GitHub Actions dan diuji semula secara bebas menggunakan PyMuPDF tanpa mengubah DB atau aplikasi.

- **56 PDF / 12 subjek / 1,631 halaman** pada penjana terkini: 21 subjek batch awal + 20 BM/PI/BA/Muzik + 5 English + 5 Matematik + 5 Sains separa. Pertambahan satu halaman daripada pemaparan rujukan DSKP Arab, bukan pertambahan PdP.
- Semua 56 fail A4 landskap, halaman muka depan dengan slot logo/nama sekolah/nama guru, jadual lima lajur, **0 teks keluar sempadan**, **0 NUL sebenar**, **0 fail tidak sah**. Manifest SHA-256 setiap PDF dan fail CSV audit wujud dalam ZIP pratonton setempat (bukan keluaran LIVE).
- **298/298 PdP Bahasa Arab Tahun 2–6** kini memperlihatkan halaman PDF DSKP bagi kod SP tepat daripada ledger 117 kod unik. Nombor halaman itu ialah **halaman PDF**, bukan halaman bercetak; teks penuh Arab, semakan semantik dan kelulusan akademik **belum** diperoleh. Setiap baris kekal bertanda DRAF. `tests/test_bahasa_arab_rpt2027_source_page_audit.py` memaksa padanan 298/298.
- Label Latin `Unit N:` dan fokus guru kini dipisahkan dalam sel asal daripada aksara Arab supaya susunan paparan RTL tidak songsang. PDF Bahasa Arab T2 halaman jadual pertama disemak secara visual daripada artifak CI baharu.
- Ujian GitHub Actions `42333071890` (20 PDF / unit tests dan visual QA) dan `42333071897` (21 PDF + simulasi) **LULUS** pada commit `f9ad389bd586690c499b2b36b55bcea66d08beb5`.
- Audit bebas mendapati lima PDF Bahasa Arab masih memaparkan placeholder SK/SP berpernyataan belum disahkan, dua PDF Pendidikan Islam (T2/T6) memaparkan rekod `held`, lima PDF Arab dan tiga PDF RBT belum ada agihan minggu sebenar; Sains masih 342 PdP snapshot SEPARA, bukan pelan lengkap. Tahun 1 KP2027 dan menengah dikecualikan.

**Release gate: FAIL-CLOSED.** Jangan merge, tukar laluan muat turun Web/Telegram atau mengumumkan FINAL READY hanya kerana 56 PDF kelihatan kemas. Sahkan sumber individu SK/SP, BT/BA, cuti negeri, RPH–RPT parity, profil Web–Telegram dan ujian native terakhir terlebih dahulu.
