# CikguLaju AI — Pusat Sehenti Digital Guru Sekolah Rendah
**Checkpoint: 12 November 2026 — STAGING / BELUM LIVE**

## Skop keputusan produk
- CikguLaju AI khusus **sekolah rendah Tahun 1–6**. Tiada sekolah menengah.
- Jenama memfokuskan PdP dan bahan mengajar harian, bukan dakwaan bahawa semua modul dirilis.
- Fungsi produksi sedia ada dikekalkan: RPH Hari Ini, Sediakan RPH, RPH Aktiviti Khas, RPT 2027, profil/jadual, Rakan Pembangun RM20, komen, admin dan referral persendirian.
- Jangan tambah menu PBD, UASA, BBM atau lembaran kerja berdiri sendiri sebelum sumber, endpoint, hak akses dan ujian siap.

## Perubahan dalam cabang ini
1. Ayat muka depan dan identiti portal jelas menyebut guru sekolah rendah Tahun 1–6.
2. RPH Hari Ini menunjukkan hasil sebagai pusat bahan PdP mengikut kelas tanpa mengubah urutan pilihan atau endpoint janaan.
3. rph-today.js mengenali **Student Book English Tahun 4 sahaja**, menggunakan URL PDF sumber dalaman yang disahkan oleh extra-materials (jenis student_book).
4. Penapis menolak sumber buku teks generik, pautan luar yang tidak disahkan, Student Book Tahun 3 dan Student Book bukan English.
5. Workbook English dan audio asal Muzik terus berfungsi secara berasingan.
6. Pemeriksaan metadata tidak mencaj kuota. Muat turun RPH masih menggunakan endpoint dan pengesahan kuota sedia ada.

## Kebergantungan release
- Backend Web English Tahun 4 Student Book dan link PDF **belum ada dalam cabang produksi yang menjadi base**. Ia berada di PR #559 (staging/web-english-y4-studentbook-20261111).
- Pasangan Telegram source-PDF berada di PR #558 dan pembetulan sumber Telegram lama di PR #567. Kebenaran pengedaran petikan buku perlu disahkan.
- Sehingga PR #559 serta prasyaratnya disatukan dan deployment/ujian live lulus, paparan Student Book baharu ialah **fungsi bersyarat**, bukan tawaran live. Tiada pautan rekaan atau fail buku penuh.
- Perlu ujian sebenar Web–Telegram pada akaun percubaan dan berbayar, pengesahan baki kredit tidak berkurang untuk semakan metadata/Workbook/Student Book, dan klik muat turun pada peranti mudah alih.
- **Jangan merge/deploy automatik**, jangan tukar akses atau harga, jangan buat migrasi Supabase, jangan keluarkan status READY berdasarkan ujian statik sahaja.

## Langkah seterusnya
1. Semak CI untuk kod dan aliran RPH Hari Ini sedia ada.
2. Selesaikan integrasi PDF English Tahun 4 bersama tiga PR sumber di atas.
3. Uji dengan guru sebenar: sesi buka web → pilih slot → dapat bahan → berjaya muat turun, dan rekod punca pengguna berhenti sebelum log masuk / sebelum janaan (tanpa data murid).
4. Selepas penggunaan harian stabil, keutamaan kandungan seterusnya ialah **bank lembaran kerja yang benar-benar siap dan berpaut pada Lesson/PdP**, bukan menu kosong.

## Sambungan: pengalaman pengguna baharu tanpa login (12 Nov 2026)
- Halaman umum kini menerangkan empat fungsi sedia ada: PdP Hari Ini, RPH Word/PDF, RPT 2027 dan bahan sokongan yang benar-benar tersedia. Tiada dakwaan semua Lesson ada Workbook/audio.
- Pelawat boleh membuka panduan "Tengok cara ... tanpa log masuk" menggunakan HTML `details`. Panduan ini berlabel **bukan RPH sebenar**; tidak memanggil API kurikulum, tidak menjana bahan dan tidak mengurangkan baki percubaan.
- CTA percubaan membawa ke komponen Telegram Login sedia ada; tidak membuat aliran pendaftaran atau mekanisme kuota kedua.
- Pautan buka bot Telegram diberi hanya apabila `/api/auth/capabilities` mengesahkan `bot_username` dan nama lulus penapisan format ketat. Tiada bot username atau deep link direka.
- Ujian tambahan `tests/test_guest_onboarding_20261112.cjs` menjaga halaman umum, sumber bot yang disahkan, login asal, admin/referral tersembunyi dan ketiadaan output palsu.
- **Belum mengira pelawat anonim atau kadar konversi**. Analisis admin sedia ada mengira akaun/login; jangan membuat anggaran kadar konversi pelawat tanpa event sah yang membolehkan pengiraan.
- Status ini masih staging. Perlu semakan sebenar Android/mobile, Telegram Login Widget, akaun baharu, akses pautan bot serta kesan pada masa muat laman sebelum release.

## Pilot Bank Lembaran Kerja — empat fail English Tahun 4
- Sumber tunggal: empat worksheet yang telah didaftarkan dalam modul Telegram `english_supplementary_materials.py`. Lesson **004, 079, 089, 090** sahaja, bukan semua Year 4 atau Tahun 1–6.
- Tambahan Web `web/english_y4_worksheet_pdf_20261112.py` memproses fail Markdown buatan guru daripada `supplementary_materials/english/year4`, memeriksa path/identiti Lesson dan membina **PDF A4 untuk murid** (satu halaman atau fail closed).
- PDF murid sengaja mengecualikan nota Purpose, Teacher assessment dan Answer key. Ia dilabel jelas sebagai bahan tambahan ciptaan guru, **bukan halaman buku teks rasmi**.
- `/api/web/rph/extra-materials` memaparkan worksheet hanya untuk Tahun 4 English dan Lesson sumber tepat. Workbook Telegram dan worksheet tempatan adalah dua sumber bebas; kegagalan satu tidak membenarkan pemalsuan yang lain.
- `/api/web/rph/english-worksheet` hanya untuk akaun sah melalui `_account`, mengulangi semakan Tahun/Unit/Token, tidak membuat pemotongan 10 kredit RPH.
- `/api/web/demo/worksheet.pdf` dibuka tanpa login untuk **satu contoh tetap Lesson 004**; ia tidak menerima query, tidak membaca data peribadi, tidak memanggil penjana Telegram/kuota, dan tidak memberi akses awam kepada Worksheet 079/089/090 atau Workbook/Student Book.
- CTA contoh di halaman guest adalah bahan sebenar (selain panduan tiga langkah yang tetap dilabel bukan RPH sebenar). Kandungan ini dibenarkan untuk diuji dalam staging sahaja sehingga pemilik mengesahkan hak edaran dan keputusan release.
- Ujian `tests/test_web_english_y4_worksheet_20261112.py` memeriksa halaman PDF sebenar melalui pypdf, tiada skema jawapan, authentication, Lesson/token mismatch, ketiadaan kuota, pengasingan Workbook, dan satu contoh PDF awam.
- QA yang belum selesai: semak rupa fizikal empat PDF di telefon dan pada cetakan A4, semak pedagogi kandungan berserta SOW sebenar, uji alamat public sample pada Render staging, kemudian buka kepada guru ujian. Jangan isytihar *Bank Lembaran Kerja Tahun 1–6 READY*.
- Ketika menggabung PR #559 dan PR #568, satukan semula metadata `extra-materials` supaya **Workbook + Student Book + worksheet** kekal bebas. Jangan overwrite salah satu ciri.

## Sambungan: salinan Word boleh edit (12 November 2026)
- Empat Lembaran Kerja tambahan English Y4 yang sama (Lesson 004/079/089/090) kini mempunyai **dua format**: PDF A4 untuk dicetak dan Word (.docx) yang boleh disunting oleh guru. Bahan tidak ditambah secara generik untuk Lesson lain.
- Pelaksanaan `web/english_y4_worksheet_word_20261112.py` menggunakan _source dan _student_lines daripada renderer PDF sedia ada: tajuk, aktiviti, ruangan jawapan dan kotak semak kekal; nota Purpose, Teacher assessment serta Answer key dikeluarkan.
- Endpoint berasingan `/api/web/rph/english-worksheet-word` mengulangi login dan semakan identiti Tahun/Subjek/Unit/Token yang sama dengan PDF, tidak menyentuh penjana atau baki percubaan.
- Senarai bahan manual dan PdP Hari Ini memaparkan Word hanya apabila `extra-materials` memulangkan URL dalaman asal yang disahkan; tiada menu Word kosong. Contoh awam tanpa login masih **PDF Lesson 004 sahaja**, bukannya Word atau PDF bebas mengikut parameter.
- CI staging diperluas memeriksa sumber, hak akses, format DOCX, dimensi A4, tiada skema/nota guru dalam teks murid, dan bukan perubahan kredit. Catatan tambahan: pemeriksaan susun atur Word Lesson 090 dengan LibreOffice tempatan menghasilkan satu halaman A4 tanpa pemotongan; ini belum menggantikan semakan keempat-empat fail dalam Render/mobile.
- Kekal HOLD sebelum deploy: perlu gabung selamat dengan PR #559 Student Book, semakan reka letak keempat-empat Word/PDF dan ujian klik real di telefon serta hak edaran bahan.
