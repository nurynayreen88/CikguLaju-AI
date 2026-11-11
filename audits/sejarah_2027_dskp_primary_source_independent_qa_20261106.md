# Audit bebas Sejarah Tahun 4–6 — pusingan pengesahan 6 November 2026

**Skop:** PR #341, cabang `staging/sejarah-rpt-rph-y4-y6-2027-20261105`. Semakan dibuat pada commit sumber `35fc39e6c9638551847e2102ef46421315f4b4c7`. **DRAF, BUKAN FINAL READY.**

## A. Semakan kembali kepada tiga DSKP KPM dalam Google Drive

Dokumen sumber yang dibaca sebagai teks PDF:
- T4: `GuruBesar_DSKP_Sejarah_Tahun_4.pdf`, Drive `1lKTJr3UpUn-miV_FUwIu46kV4KWZr4zP`.
- T5: `GuruBesar_DSKP_Sejarah_Tahun_5.pdf`, Drive `1eOv2FMk3LWsb6O7W4bsQFjVUylQDsGri`.
- T6: `GuruBesar_DSKP_Sejarah_Tahun_6.pdf`, Drive `1BN6nJjse61rXyaA9YKTsiIJm7ylmQc4Q`.

Kaedah: setiap kod SP dan lafaz SP dalam peta `curriculum/sejarah/y{4,5,6}_dskp_crosswalk_DRAF.json` disemak terhadap teks ekstrak DSKP sebenar. Untuk lafaz, normalisasi hanya ruang/baris, tanda baca dan variasi tanda sempang/petik; **bukan** kesetaraan semantik atau pengesahan visual PDF. Hasil:
- T4: **76/76 kod** dan **76/76 lafaz** ditemui.
- T5: **84/84 kod** dan **84/84 lafaz** ditemui.
- T6: **68/68 kod** dan **68/68 lafaz** ditemui.
- **Keseluruhan 228/228** kod dan teks SP ditemui. Ini pemeriksaan teks dokumen, bukan pengesahan visual sel/jadual DSKP.

## B. Audit silang 108 RPH JSON

Data pada `rph_standalone/sejarah/y4_2027_rph_DRAF.json`, `y5_2027_rph_DRAF.json`, `y6_2027_rph_DRAF.json`:
- 36+36+36 = **108 RPH**; tiada ID berulang.
- Semua SK setiap RPH wujud dalam peta DSKP untuk tahunnya.
- Semua kod SP RPH wujud di bawah SK yang betul; teks `core_sp` dan `values_sp` tepat sama dengan rekod DSKP yang dipadankan; tiada isu dikesan dalam pemeriksaan programatik.
- 108/108 menjumlahkan **60 minit** bagi set induksi, dua aktiviti, pengukuhan/PBD dan penutup.
- 108/108 mempunyai `checked_focus_pages.text_checked=true` dan julat halaman cetakan; **55** bertahap `TEXTBOOK_TEXT_READ_FROM_DIGITAL_REHOST_NOT_VISUAL`, **53** bertahap `DIGITAL_BOOK_TEXT_TOPIC_PAGE_CROSSWALK_NOT_VISUAL_EXERCISE`. Kedua-duanya **tidak bermaksud** latihan tepat diperiksa visual.
- **0/108** pengesahan visual halaman latihan sebenar, **0/108** kelulusan individu guru dan **0/108** status FINAL READY. Semua harus kekal DRAF.
- **97/108** RPH masih menggunakan awalan Aktiviti 1 “Guru membimbing murid menyemak sumber serta istilah Sejarah yang berkaitan” dan Aktiviti 2 “Guru menyoal hubungan fakta, konteks masa atau tempat”. Sambungan ayat mengandungi kandungan khusus, tetapi langkah guru masih terlalu bersifat templat; ini **isu mutu pedagogi** untuk pemurnian individu, bukan kegagalan kod DSKP.
- **97/108** rekod tiada objek `page_specific_evidence` walaupun mempunyai `textbook_reference.checked_focus_pages`. Ini **ketidakseragaman metadata bukti** yang perlu dijelaskan/diseragamkan sebelum audit akhir; jangan menukarnya menjadi bukti visual palsu.

## C. Semakan sampel terhadap halaman buku digital asal

Sampel tekstual disemak semula secara langsung (bukan semakan visual penuh):
1. **T5 PdP 001**, halaman cetakan 4, https://online.anyflip.com/iawvx/fevz/files/basic-html/page10.html — definisi raja/kerajaan serta aktiviti mencari maklumat institusi raja sepadan dengan fokus 6.1.1.
2. **T5 PdP 002**, halaman cetakan 7, https://online.anyflip.com/iawvx/fevz/files/basic-html/page13.html — menerangkan daulat/derhaka dan aktiviti menjelaskan kepentingan taat setia; selaras fokus 6.1.3 dan K6.1.7.
3. **T5 PdP 005**, halaman cetakan 18–19, https://online.anyflip.com/iawvx/fevz/files/basic-html/page24.html dan https://online.anyflip.com/iawvx/fevz/files/basic-html/page25.html — menerangkan agama/kepercayaan awal dan bukti batu bersurat; selaras 6.2.1 dan sebahagian bukti bagi 6.2.2, bukan semakan keseluruhan bab.
4. **T5 PdP 007**, halaman cetakan 25, https://online.anyflip.com/iawvx/fevz/files/basic-html/page31.html — teks memuatkan nilai toleransi/kasih sayang/kesederhanaan/perdamaian dan tugasan perbincangan empat kumpulan; RPH berasaskan nilai perpaduan, namun **tidak boleh dilabel latihan buku asal yang tepat** tanpa pemeriksaan visual dan perbandingan hasil tugasan.

Semakan sampel **tidak** membenarkan sebarang tanda `exact_activity_page_confirmed=true`, `teacher_approval=true`, `release_ready=true`, atau `status=FINAL_READY`.

## D. Keputusan dan tindakan yang masih diperlukan

**LULUS TEKS DSKP / AUDIT STRUKTUR; GAGAL PAGAR PENERBITAN KERANA BUKTI BELUM CUKUP.**

Tindakan seterusnya yang terhad kepada staging:
1. Murnikan **97** awalan aktiviti templat kepada arahan guru/murid yang mengikat bukti halaman, kemahiran sejarah, dan hasil PBD setiap PdP; selaraskan JSON, Markdown dan HTML tanpa mengubah SK/SP.
2. Semak **108** latihan/imej halaman buku asal satu persatu, dengan bukti yang boleh diaudit serta perbezaan edisi dicatat.
3. Pengesahan pedagogi manual guru Sejarah bagi setiap PdP; kekalkan manifest kelulusan bebas kosong sehingga bukti sebenar wujud.
4. Uji profil/logo sekolah, tarikh jadual negeri sebenar dan pariti penghantaran **runtime** Telegram/Web; CI render yang lulus belum membuktikan hal ini.
5. Jalankan semula semua QA staging selepas sebarang pindaan; jangan `merge` atau `deploy` ke `main` tanpa pelepasan sah.

**Jejak audit:** Pusingan ini hanya menyemak dan mencatat dapatan. Tiada data akaun, pembayaran, jadual pengguna, DB produksi, RPH atau bendera kelulusan disentuh.
