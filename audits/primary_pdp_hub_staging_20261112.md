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

## Pemulihan bank worksheet lama (12 November 2026)
- Pengguna mengesahkan mahu menggunakan bahan awal pembangunan sebagai **dummy/staging** dan membaikinya sebelum pengguna produksi melihatnya.
- Fail sumber yang benar-benar wujud dalam repo termasuk `CikguLaju_Worksheet_Content.db`, `CikguLaju_Templates_02.db` hingga `_10.db`, `CikguLaju_Visuals_04.db`/`_06.db` dan DB kurikulum lama `CikguLaju_Curriculum_Master_v24_95_MATERIAL_AUDIT.db`.
- Rekod sejarah v23.97/v23.98 menyebut 20,332 **sumber kurikulum** dan 17,875 sumber yang boleh diproses tanpa lukisan baharu, bukan 20,332 worksheet siap/approved. Queue 4,378 artwork tasks pada v23.99 bukan imej siap. Oktober 2026 BBM/Worksheet OFF atas isu kualiti; tiada kebenaran untuk membuka semula secara automatik.
- Inventori terasing: `audits/legacy_worksheet_sources_staging_20261112.json` (semua `UNREVIEWED`, gate `OFF`).
- Skrip `tools/audit_legacy_worksheet_banks_20261112.py` membaca SQLite secara `mode=ro&immutable=1`, hanya mengeluarkan hash, integrity, nama jadual dan bilangan rekod yang berkaitan; tiada salinan kandungan murid, tiada mutasi DB, tiada Supabase, tiada Telegram.
- CI `tests/test_legacy_worksheet_inventory_20261112.py` menjaga fail tidak berubah, tiada `READY` tersirat, nama fail terkawal, fail missing/symlink tidak dibaca; workflow memeriksa fail DB sebenar dalam staging dan menyimpan hasil hanya sementara pada runner.
- Langkah seterusnya: kenal pasti skema dan kandungan calon, padan Tahun 1–6/DSKP/SK/SP/Unit/Lesson; audit kesesuaian pedagogi, ejaan, hak edaran, visual dan ruang jawapan; baiki format; sediakan PDF/Word; hanya kemudian tandakan calon `READY` secara manual dan buka dalam UI. Bahan belum lulus tidak muncul di Web/Telegram.
- Fail demo Tahun 1 lama dalam Library (`CikguLaju_Demo_Worksheet_Tahun1_Semua_Subjek.pdf`, `CikguLaju_Worksheet_Commercial_BW_Tahun1_v23_22.pdf`) ialah **contoh reka bentuk**, bukan bukti bahan rasmi yang lulus audit.

## Audit kandungan worksheet lama, bukan sekadar schema — 12 Nov 2026
Ujian read-only pada sumber sebenar telah selesai dan merekodkan:
- `worksheet_blueprints` = **4,316**; `worksheet_item_templates` = **4,316**; hanya **4 kunci rangka** dan **4 kunci templat item** berbeza. Semua mempunyai field tajuk/arahan/pola/ruang dan `verified_alignment=1`, namun ini cuma padanan kurikulum, **BUKAN** soalan siap.
- Empat subjek sekolah rendah (BM, English, Matematik, Sains) untuk Tahun 1–6 wujud dalam bank. Tiada bukti bahawa kesemua soalan lengkap, semakan mata pelajaran semasa atau Lesson/PdP telah disahkan.
- 20,332 `shared_learning_resource`, dengan 16,029 `VERIFIED_CURRICULUM_ONLY` dan 4,303 `VERIFIED_SHARED`. 20,332 baris `bbm_material_delivery` dilabel `RELEASE_READY` **dalam DB lama**; label itu tidak mengatasi gate kualiti terkini.
- DB visual 06 menyimpan 240 aset lama (`approved=1`), tetapi kesesuaian visual, resolusi, hak edar serta kesesuaian umur mesti dinilai semula.
- Senarai semakan padanan material mempunyai 6,349 `PENDING_REVIEW` dan 503 `NEEDS_BUILD`.
- Gate baharu `web/legacy_worksheet_quality_gate_20261112.py` mengklasifikasi **4,316/4,316 `REPAIR_REQUIRED`**. Isu yang dikesan (boleh bertindih): 4,316 tajuk umum `Aras/Level`; 4,316 tiada item murid bernombor; 3,341 penanda ruang/imej seperti `[ANSWERSPACE:]`; 1,079 masih arahan kepada penjana.
- Gate tidak pernah memberi `READY`; bahan yang kelihatan lengkap hanya mendapat status `REVIEW_REQUIRED` untuk kelulusan manual. CI `tests/test_legacy_worksheet_quality_gate_20261112.py` mengesahkan perlindungan ini.
- Contoh pembaikan pertama: `supplementary_materials/math/year1/repair_demo_sk1_1_sp1_1_1_20261112.json`, Tahun 1 Matematik, SK1.1 SP1.1.1 perbandingan kuantiti. Enam tugasan murid ditulis semula daripada rangka umum kepada soalan/objek/jawapan pilihan yang jelas. Fail Word dan PDF satu halaman A4 telah dihasilkan dan diperiksa secara setempat, **belum** menjadi fail muat turun Web. Teks sumber terasing dan `publish=false`, `approval=NOT_APPROVED_FOR_PRODUCTION`, Lesson/PdP belum disahkan; CI menguji pembaikan hanya menjadi calon `REVIEW_REQUIRED`.
- Hak cipta: soalan demonstrasi baharu adalah asal, bukan petikan buku teks. Rujukan kurikulum untuk SP1.1.1 diperiksa daripada DSKP KSSR Semakan Matematik Tahun 1 (perbandingan banyak/sedikit/sama banyak). Padanan Lesson dan muka surat belum dimuktamadkan.
- Sehingga keluaran sebenar diluluskan, **jangan aktifkan semua 4,316 dummy worksheet**, jangan ubah kuota/RPH, dan jangan menimpa DB lama/Telegram/Web produksi.

## Sambungan Sains Tahun 1 — contoh pemulihan kedua (12 November 2026)
- Rujukan DSKP KSSR Semakan 2017: **Sains Tahun 1, SK1.1 Kemahiran Proses Sains / SP1.1.1 Memerhati**. Fokus penggunaan deria untuk membuat pemerhatian; **Lesson/PdP dan halaman buku teks belum disahkan**.
- Sumber asal `CikguLaju_Worksheet_Content.db` mempunyai rangka generik. Bahan baharu disusun sebagai **enam aktiviti pemerhatian sebenar** dan direkodkan di `supplementary_materials/science/year1/repair_demo_sk1_1_sp1_1_1_20261112.json`, bukan dakwaan bahawa worksheet siap dipulihkan secara automatik.
- Tugasan: warna pensel; bentuk pemadam; tekstur kain bersih; permukaan sudu plastik; deria mendengar ketukan meja; menulis satu perbezaan pensel dan pemadam. Jawapan yang bergantung pada objek tidak dipraisi. Nota guru dan keterangan penilaian disimpan dalam `teacher_only` tetapi **tidak dicetak**.
- Skrip dalaman `tools/render_science_y1_worksheet_20261112.py` menghasilkan PDF A4 dan Word boleh edit, tanpa route Web/Telegram, tiada kuota, tiada akses data pengguna dan tiada Supabase. Teks/ruang jawapan diperbesar untuk murid Tahun 1.
- Semakan setempat Word->PDF/PNG dan ReportLab->PDF/PNG menghasilkan **1 halaman A4 setiap format**, tiada potongan, ruang jawapan jelas. Ujian `tests/test_repaired_science_y1_dummy_20261112.py` menjaga identiti kurikulum, enam soalan, larangan skema jawapan dicetak, dan `publish=false`.
- Status **STAGING_INTERNAL / NOT_APPROVED_FOR_PRODUCTION**. Semakan guru masih diperlukan untuk kesesuaian bahan (objek bersih serta keselamatan deria), SK/SP tepat, Lesson/PdP, halaman buku teks jika ada, dan sebarang perubahan KP2027 sebelum penerbitan.

## Submenu 📄 Lembaran Kerja di bawah Sediakan Bahan PdP (12 November 2026)
- Hanya label menu sedia ada `rph` diberi nama **Sediakan Bahan PdP** (bukan route baharu). Aliran Tahun → Subjek → Tema/Unit/Tajuk → Lesson/PdP → Jana Bahan, RPH Hari Ini dan butang Word/PDF asal tidak diubah.
- Dalam panel hasil selepas `Jana Bahan`, submenu HTML `<details id="worksheet-submenu" hidden>` tersedia secara bersyarat. Ia **hanya** muncul apabila `extra-materials` memulangkan sekurang-kurangnya satu worksheet PDF atau Word dengan pautan auth dalaman yang tepat **dan** Tahun=4, Subjek=ENGLISH, Unit dan Lesson sama dengan pilihan guru.
- PDF dan Word dipindahkan ke submenu; RPH, Workbook, audio tetap dalam senarai sedia ada. Paparan submenu mengandungi pilihan format, notis bahan ciptaan guru dan makluman bahawa muat turun worksheet tidak menggunakan kredit RPH.
- Submenu dimatikan dan dibersihkan setiap kali pengguna menukar pilihan Lesson atau apabila semakan bahan diulang. Pautan silang Lesson, URL luar, URL tidak sepadan, parameter tambahan/pendua, judul kosong dan dummy Matematik/Sains Tahun 1 tidak diterima.
- Bahan Tahun 1 Matematik/Sains daripada pemulihan bank 4,316 rangka tetap **STAGING_INTERNAL** dan tidak dipaparkan dalam submenu ini selagi belum ada kelulusan manual, padanan Lesson/PdP dan laluan pengedaran sah.
- Ujian `tests/test_web_worksheet_submenu_20261112.cjs` ditambah dalam workflow utama. **HOLD untuk produksi:** semak integrasi PR #559 Student Book supaya Workbook+Student Book+worksheet tidak berkonflik, sahkan click/Word/PDF sebenar pada Web dan telefon, serta hak edaran bahan asal.

## 12 November — integrasi tiga sumber English Y4 (staging sahaja)
- Digabung secara *additive* ke PR #568 kontrak Web Student Book dari PR #559, tanpa memadam sumber Workbook Telegram atau empat Worksheet PDF/Word English Tahun 4.
- `web/native_telegram_extra_materials_20261106.py` kini mengesahkan identiti Student Book `year=4`, Lesson yang tepat serta PDF 1–4 halaman yang sah dan tidak terenkripsi. Render memerlukan `pypdf` sebelum ciri ini dilancar; fail `requirements-web-render.txt` disalin ke staging tetapi konfigurasi Render LIVE tidak diubah.
- `/api/web/rph/extra-materials` menyenarai tiga sumber secara bebas (Workbook, Student Book, Worksheet PDF/Word). Kegagalan satu tidak menyembunyikan sumber lain. Tiada sumber yang direka apabila metadata tiada.
- `/api/web/rph/english-student-book` memerlukan sesi sah dan pengesahan Tahun/Subjek/Unit/Lesson; PDF diperoleh terus daripada Telegram private bridge, tidak menggunakan kredit RPH. Param berulang ditolak.
- UI bahan manual hanya menerima pautan dalaman dengan identiti Year/Unit/Lesson tepat, tidak memindahkan Student Book/Workbook ke submenu Worksheet. PdP Hari Ini menggunakan guard Student Book sedia ada.
- Ujian berasingan `tests/test_web_english_three_source_merge_20261112.py` dan `.cjs` ditambah ke Actions; semua bergantung pada sumber dummy yang dimock, bukan Telegram/Render LIVE.
- **HOLD**: PR #558/#567 (dan final PR #559) masih perlu diselaraskan, pemeriksaan hak edar/halaman fizikal dan muat turun HTTPS akaun sebenar belum dibuat. Tiada merge main, tiada deploy, tiada perubahan Supabase/credit/produk.
