# Audit individu 210 RPH PSV Tahun 2–6 — 5 November 2026

**Status: SEMAKAN DOKUMEN INDIVIDU SELESAI; PENGESAHAN HALAMAN BUKU TEKS INDIVIDU BELUM LENGKAP.**
**PR #267 STAGING sahaja. Jangan merge, deploy, cipta fail kelulusan, atau tukar semua RPH kepada READY.**

## Rekod penuh 210 RPH
Lihat [CSV audit berbaris untuk setiap PdP](../rph_standalone/psv/audits/psv_individual_210_review_20261105.csv). Satu baris = **satu RPH individu** dengan tahun, PdP, fail, unit, fokus, teknik, SK, SP, rujukan muka surat, sumber dan nota terbuka. Semakan ini berasaskan pembacaan 210 fail pada branch PSV semasa (metadata, SK/SP, rujukan dan aktiviti utama). Ujian CI terdahulu turut menyemak struktur lima fasa, padanan RPT dan A4; bukti CI tidak menggantikan semakan kandungan Buku Teks.

- Tahun 2: 42/42 RPH telah dibuka dan dibandingkan pada peringkat dokumen; **bukan** 42/42 semakan visual buku.
- Tahun 3: 42/42 RPH telah dibuka dan dibandingkan pada peringkat dokumen; **bukan** 42/42 semakan visual buku.
- Tahun 4: 42/42 RPH telah dibuka dan dibandingkan pada peringkat dokumen; **bukan** 42/42 semakan visual buku.
- Tahun 5: 42/42 RPH telah dibuka dan dibandingkan pada peringkat dokumen; **bukan** 42/42 semakan visual buku.
- Tahun 6: 42/42 RPH telah dibuka dan dibandingkan pada peringkat dokumen; **bukan** 42/42 semakan visual buku.

## Pengesahan buku dan DSKP
- T2 [Pendidikan Kesenian Tahun 2](https://fliphtml5.com/laiqy/thik/Buku_Teks_Pendidikan_Kesenian_Tahun_2/): 10 unit; kandungan terbahagi kepada Seni Visual dan Seni Muzik. Gunakan bahagian Seni Visual sahaja.
- T3 [Pendidikan Kesenian Tahun 3](https://fliphtml5.com/itcew/awun/Pendidikan_Kesenian_Tahun_3/): 10 unit; contoh teknik silang pangkah, montaj, mobail, Parang Ilang, anyaman.
- T4 [Pendidikan Kesenian Tahun 4](https://fliphtml5.com/jfuhh/hbrx/Buku_Teks_Pendidikan_Kesenian_Tahun_4/): 10 unit; Unit 10 *Harum Mewangi* ialah ukiran timbul sabun, **bukan** diorama.
- T5 [Pendidikan Seni Visual Tahun 5](https://anyflip.com/gygr/pity/basic): 10 unit disokong RPT dan senarai isi kandungan. Tiada bukti pembacaan penuh halaman buku asal bagi setiap PdP; semua T5 kekal tertangguh pengesahan buku langsung.
- T6 [Pendidikan Seni Visual Tahun 6](https://fliphtml5.com/hkvtu/cnbo/Pendidikan_Seni_Visual_Tahun_6/): 10 unit; fokus folio vs gambar akhir, wau, beg batik diperiksa secara terpilih.
- DSKP T2–4 memang mencetak SP `3.3.x` di bawah SK `5.1` untuk projek; jangan menukarnya sewenang-wenang. T5/T6 projek menggunakan `5.1.x`.

## Isu dikenal pasti dan tindakan
1. **Tahun 3 PdP 003, 007, 011, 018, 024, 028, 032:** rujukan muka surat berbentuk `8–8`, `16–16`, `24–24`, `42–42`, `52–52`, `60–60`, `68–68`. Dinormalkan kepada halaman tunggal dalam **RPH dan RPT staging**. Ia tidak membuktikan aktiviti pada halaman itu telah diluluskan secara visual.
2. **Tahun 2–5:** bahagian penerokaan, arahan guru, dan PBD menggunakan beberapa rangka ayat berulang. Teknik berbeza mengikut unit, tetapi kesesuaian pedagogi khusus PdP perlu dinilai sebelum READY.
3. **Tahun 5:** sumber rujukan secara silang masih perlu audit halaman buku secara langsung bagi 42 RPH.
4. **Tahun 6 PdP 013, 017, 034 dan 039:** `3.1.1` ialah folio, `3.2.3` gambar akhir. Pastikan keduanya wujud dalam evidens.
5. **RPT 2027 Kumpulan A/B:** pengesahan kalendar/cuti gantian negeri belum diselesaikan.

## Takrif keputusan
- `RPH_DIBACA` = fail individu dibuka dan dibaca pada medan utama; tidak sama dengan `BUKU_TEKS_VISUAL_SAH`.
- `UNIT_BUKU_ASAL_DIRUJUK` = buku asal mengesahkan unit/topik, bukan halaman aktiviti individu.
- `BELUM_READY` = tidak diluluskan untuk penerbitan. **0/210** mempunyai sijil audit visual buku yang lengkap dalam pusingan ini.

## Gerbang akhir
Bagi setiap baris CSV, buka *halaman tepat* buku asal, banding arahan sebenar dengan tindakan guru/murid, bahan dan keselamatan, semak maksud SK/SP (bukan kod sahaja), kemudian rekod bukti semakan dan tetapkan `PASSED` atau `FIX_REQUIRED`. Hanya apabila semua 210 mempunyai bukti, CI semasa hijau dan integrasi native Telegram staging berjaya boleh disediakan fail kelulusan sah dan ditimbang merge ke `main` terkini. Jangan lakukan deploy secara automatik daripada PR ini.
