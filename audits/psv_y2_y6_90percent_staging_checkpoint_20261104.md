# PSV Tahun 2–6 — checkpoint sasaran 90% kandungan, kekal STAGING
Tarikh: 4 November 2026
PR: https://github.com/nurynayreen88/CikguLaju-AI/pull/196
Branch: `psv-y2-y6-rpt-rph-2027-staging-20261104`

## Keputusan
**SASARAN ±90% KANDUNGAN DRAF / STAGING REVIEW. BUKAN 90% SK/SP disahkan satu-persatu, BUKAN FINAL READY, BUKAN LIVE.**

- **210/210 RPH** wujud (Tahun 2–6: 42 setiap tahun). Audit terdahulu menunjukkan padanan nombor PdP, tajuk, SK/SP yang direkodkan, struktur aktiviti dan pautan RPT konsisten. Ini audit kandungan fail, bukan pensijilan pedagogi seluruh DSKP.
- **5 RPT CSV** mengandungi 42 rekod setiap tahun; asalnya juga tersedia RPT HTML lanskap per tahun. RPT T2–T6 sudah disalin ke main melalui PR #257 secara berasingan; semua penambahbaikan dalam checkpoint ini hanya di branch staging PR #196.
- **30 RPH Tahun 6 diperhalus dalam pusingan ini**: 12 RPH (PdP 028–039, Unit 8–10) diperbaiki substantif mengikut aktiviti dan halaman asal buku teks; 18 RPH lain (PdP 001, 010–018, 021, 024–027, 040–042) digantikan kriteria kejayaan generik dengan evidens PBD yang sedia dinyatakan dalam RPT. Semua SP asal dikekalkan.
- **RPH 028 dan 029 kini berlainan**: bunga kertas lipat empat / cantuman cekak tiruan dibandingkan dengan tanjak origami segi tiga berlipat, aksesori warisan tanpa alat tajam.
- **RPH 030–034**: Wau Bulan Sirih Pinang sebagai model **permainan**, berpandukan motif daun sirih dengan susunan cerminan, kajian warna, potong/tampal bahan, rambu, pemegang, dan apresiasi. Rujukan BT pp 68–75.
- **RPH 035–039**: Beg Batik Rekaanku ialah beg 3D untuk menyimpan **alatan seni**, dengan pilihan motif flora, susunan corak, panel kain kapas, resis gam PVA atau oil pastel tanpa lilin panas, warna, cantuman felt/velkro, gambar dan apresiasi. Rujukan BT pp 76–87.
- **RPT T6 CSV dan HTML diselaraskan untuk 12/12 PdP** (objektif, evidens, halaman). Baris lain tidak diubah. Peta sumber 50 unit dikemas kini khusus unit T6 8, 9, 10.
- **Audit semula selepas pembetulan: 42/42 RPH Tahun 6** lulus ujian baca-silang terarah: kewujudan struktur 60 minit (5+15+25+10+5), padanan kod SK/SP RPT, evidens PBD RPT dalam RPH dan status DRAF. **0/42 kriteria kejayaan generik lama** dalam 42 fail aktif Tahun 6.
- **Bukti regresi** ditambah ke `tests/test_psv_rpt_rph_source_order.py`: 12 PdP buku teks dan 18 kriteria PBD terukur. Ujian dibuat melalui bacaan terus GitHub dan perbandingan berprogram; **Python unittest/CI GitHub belum dilaporkan lulus**.

## Backup dan kawalan
- Backup sebelum pembetulan 12 RPH: `rph_standalone/psv/year6/backups_pre90_textbook_unit8_10_20261104.json`.
- Backup sebelum pembetulan 18 kriteria: `rph_standalone/psv/year6/backups_pre90_pbd_success_20261104.json`.
- Backup RPT T6 sebelum selaras 12 baris: `rpt_2027/psv/backups/RPT_PSV_Tahun_6_before_unit8_10_refine_20261104.csv`.
- Snapshot sedia ada untuk Tahun 2–6 sebelum audit 90% kekal; tiada reset atau pemadaman data.
- **Semua RPH dan RPT kekal `DRAF_SEMAK` dalam staging.** Tiada merge PR, perubahan `main`, deploy bot, migrasi DB, atau perubahan Telegram.
- PR #196 berkonflik dengan `main` kerana terdapat kerja berasingan yang telah digabung, termasuk RPT PSV PR #257. **Jangan paksa merge**: untuk keluaran kelak perlu banding fail PSV terpilih dengan versi baharu `main` terlebih dahulu.

## Baki sebelum status FINAL READY / muat turun pengguna
1. Semak **ketepatan maksud SP DSKP dan aktiviti buku teks secara visual semua 210 PdP**, terutama bahan/teknik 3D dan semua projek.
2. Jana dan semak **210 RPH Word/PDF satu muka A4**; saiz fail teks sahaja tidak membuktikan muat satu muka.
3. Semak RPT landskap bercetak bermuka depan, Kumpulan A/B dan tarikh negeri 2027 termasuk cuti gantian / cuti sekolah; julat minggu cadangan tidak boleh dianggap tarikh kelas.
4. Jalankan `python -m unittest tests.test_psv_rpt_rph_alignment tests.test_psv_rpt_rph_source_order` di persekitaran yang ada semua fail dan lihat keputusan CI.
5. Uji integrasi RPH sebenar di staging bot. Jangan keluarkan label dalaman semakan kepada guru, dan jangan aktifkan fail yang masih DRAF.
6. Selesaikan konflik PR #196 secara **selektif**, tanpa menimpa RPT dalam main yang sudah disertakan oleh PR #257 atau subjek lain.

## Sumber kandungan sah untuk batch ini
- Buku Teks PSV Tahun 6 (Unit 8–10): https://anyflip.com/xlqtw/jdtl/basic/51-100
- RPT PSV Tahun 6 2026: https://anyflip.com/zxzlm/tuth/basic
- DSKP KSSR Semakan 2017 PSV Tahun 6: https://asiemodel.net/wp-content/uploads/2022/08/8.-DSKP-KSSR-SEMAKAN-2017-PENDIDIKAN-SENI-VISUAL-TAHUN-6_ISBN_.pdf

**Peringatan:** Label "90%" dalam checkpoint ini ialah **kemajuan penyediaan draf kandungan** untuk tujuan pengurusan, bukan markah audit rasmi atau arahan penerbitan. Status produksi belum READY.
