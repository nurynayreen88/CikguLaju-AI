# CikguLaju Pendidikan Islam 2027 — keputusan prapenerbitan V7

**Tarikh:** 5 November 2026  
**Status:** NO-GO untuk penerbitan awam; bahan staging kekal tidak disentuh.  
**Skop:** RPH dan RPT Tahun 2–6.  

## Audit terkini terhadap fail sebenar
- 696/696 RPH Word unik wujud dalam bundle; tahun 2=112, 3=147, 4=151, 5=143, 6=143.
- Semua 696 Word memuatkan label/nota audit/draf dalaman. Semua 696 PDF ialah pratonton STAGING sahaja. Jangan mengubah label atau menandakan READY tanpa kandungan disahkan.
- 332 RPH bidang al-Quran mengikut mushaf; **364 RPH bidang bukan al-Quran** memerlukan semakan padanan DSKP dan kegiatan dengan buku teks yang relevan. Nombor halaman buku teks yang sudah **dibuktikan secara individu dalam fail**: 0. Ada satu rujukan halaman DSKP, bukan buku teks.
- 573 RPH mempunyai bahagian aktiviti utama 1–2 baris (537 dua baris + 36 satu baris). Ini satu pencetus semakan mendalam, bukan bukti automatik bahawa isi salah.
- 6 RPH masih ditahan: Tahun 2 Lesson 035; Tahun 6 Lesson 006, 014, 018, 060, 117. T6 Lesson 060 ialah cadangan CikguLaju berasaskan SK/SP, bukan PdP sumber RPT 2026; jangan jadikan rasmi tanpa keputusan panitia.
- 29 lagi RPH ditandakan keutamaan semakan; baki 661 ialah calon ujian guru, **bukan disahkan**.
- Pelan pelengkap lapan pengecualian tasmi' V4 hanya *cadangan*; ia tidak mengubah ayat atau kod SK/SP asal dalam V5.

## Keputusan release gate V7 (uji kedua-dua arkib sebenar)
- Periksa semua 696 Word dan 696 PDF berdasarkan SHA256; fail disemak konsisten.
- NOTA_DRAF_DALAMAN_WORD=696
- BELUM_SAH_GURU_INDVIDU=696
- PDF_PRATONTON_DRAF=696
- RPH_DITAHAN=6
- Keputusan automatik: **NO-GO, exit code 2**. Keputusan ini sengaja *gagal dengan selamat* untuk menghalang aktivasi, bukan ralat CI.

## Sumber asli yang dikenal pasti
Semua lima tahun kini mempunyai pautan DSKP, buku teks dan RPT 2026 di Drive (lihat INDEKS_SUMBER_ASAL_20261105.csv). Pautan sumber bukan bukti bahawa setiap baris Word sudah semak terhadap halaman asal. Tahun 4 RPT 2026, DSKP dan Buku Teks sudah dikenal pasti selepas semakan tambahan.

## Laluan paling selamat ke penerbitan
1. Kembangkan dan sahkan aktiviti berasaskan sumber sebenar untuk 364 Lesson bukan al-Quran, termasuk halaman buku teks cetak dan jalinan SK/SP/PBD.
2. Semak secara individu bacaan/ayat/tajwid untuk 332 RPH al-Quran, khususnya enam Lesson ditahan dan pelan pelengkap V4.
3. Hasilkan Word/PDF *bersih* yang tidak memperlihatkan nota QA dalaman **setelah** sumber diperakui; jangan edit bahan asal. Ujian A4+Jawi setiap PDF akhir.
4. Lengkapkan rekod semakan yang dikunci pada SHA Word/PDF dalam MATRIKS_PENGESAHAN_696.csv. Jangan menerima rekod generik sebagai pengesahan guru.
5. Sediakan fail binary yang selamat pada runtime staging, bukan andaian bahawa Library secara automatik wujud di Render. Uji pemilihan Lesson sebenar, auth berbayar, penghantaran Telegram dan Web, serta regresi subjek lain.
6. Hanya apabila semua gate hijau, keluarkan perubahan berskop kecil ke PR untuk produksi dengan audit fail. Perubahan untuk main pada masa ini **DILARANG**.

**Perlindungan:** Tiada perubahan kepada main, Telegram, Supabase, database aktif, atau bahan lain. Pakej sumber asal V5 kekal sebagai bukti tidak ditimpa.