# Audit integrasi Web–Telegram English Tahun 4 — 11 November 2026

## Bukti dua-PR (staging sahaja)
- Web: PR #559, cabang `staging/web-english-y4-studentbook-20261111`.
- Telegram: PR #558, commit sumber dipin `e4ca75a71b4c1d2bc2579785629414674fae03a2`.
- Workflow: `.github/workflows/web-english-y4-cross-pr-contract-staging.yml`; ujian: `tests/test_web_english_y4_partner_contract_20261111.py`.
- Dua checkout GitHub yang berbeza dijalankan dalam GitHub Actions. API Flask kedua-duanya dihubungkan melalui penyesuai WSGI offline, dan menggunakan fail PDF asal dalam repositori.
- Jalur auth Telegram dalam ujian ialah stub Bearer untuk persekitaran offline; auth sebenar turut diliputi ujian PR Telegram, namun **ujian rangkaian LIVE dengan token sebenar belum dijalankan**.
- Tiada request terhadap perkhidmatan LIVE, tiada transaksi Supabase, tiada potongan kredit dan tiada deployment.

## Keputusan ujian silang
- Lesson 103: ujian asal mengekstrak 73, 74, 75; **audit SOW lanjut mendapati dua halaman tambahan itu milik Lesson 104**. Kontrak terkini menyemak PDF halaman 73 sahaja daripada `y4_student_021_100.pdf`.
- Lesson 157: rujukan SOW utama ialah **110–111** (dua halaman); halaman 133 ialah pilihan CLIL berasingan dan tidak dicampur.
- Lesson 43: sumber asal lima halaman 27–31 ialah peta salah; diperbetulkan ke **Phonics 3, Student Book halaman 121** mengikut Scheme of Work Year 4. Ujian silang perlu mengesahkan satu halaman sumber sahaja.
- Lesson 30: **Student Book dan Workbook** muncul berasingan dalam senarai bahan dan kedua-duanya boleh dimuat turun sebagai PDF sumber sebenar.
- Pengadang kegagalan separa: jika Workbook API gagal, Student Book yang sah kekal dipaparkan/muat turun; jika Student Book gagal, Workbook yang sah masih dipaparkan/muat turun.
- Login tiada → 401; Unit yang tidak sepadan → 400; Bearer Telegram tiada → 401.
- Cache PDF Web → `no-store, private`.
- **5/5 ujian silang lulus** dalam GitHub Actions run **43016729997**, termasuk pengadang kegagalan sebelah sumber. Bukti bertahap: 4/4 run 43016329993 dan 3/3 run 43016057275.

## Render Web dependency release gate — semakan 11 Nov 2026
- Servis produksi `cikgulaju-web` (Render `srv-dbm5go8u01pc738f40cg`) menggunakan cabang `production/cikgulaju-web-20261105`, auto-deploy berasaskan commit, dan pada masa audit menggunakan build command `pip install 'flask==3.1.3' 'gunicorn==23.0.0'`.
- Ini **belum memasang pypdf** yang diperlukan bagi pembacaan PDF Workbook dan Student Book pada Web. Tanpa perubahan build, muat turun baharu boleh mengembalikan ralat walaupun CI berasingan lulus.
- Fail `requirements-web-render.txt` di staging mengunci Flask 3.1.3, Gunicorn 23.0.0, pypdf 5.1.0. Workflow silang PR kini memulakan persekitaran ujian daripada fail ini **sebelum** memasang pustaka QA tambahan.
- **Urutan pelepasan selamat**: (1) Sahkan hak edaran serta rujukan buku dan PR Telegram #558; (2) Uji Telegram API di servis sebenar; (3) pada cabang Web produksi *semasa*, ubah build Render dahulu kepada `pip install 'flask==3.1.3' 'gunicorn==23.0.0' 'pypdf==5.1.0'` dan sahkan redeploy/health sehingga LIVE — perubahan ini tidak bergantung kepada fail baharu; (4) hanya selepas itu gabung PR #559 ke cabang Web yang auto-deploy; (5) sahkan muat turun sebenar dan status kredit tidak terpotong; (6) selepas fail keperluan wujud di produksi, pilihan mengemas kini build ke `pip install -r requirements-web-render.txt` boleh dibuat pada pelepasan berasingan.
- **TIDAK DILAKSANAKAN DI PRODUKSI** dalam audit ini; ia masih kawalan pelepasan.

## Had dan langkah seterusnya
- Ujian menggunakan kod sebenar dan fail PDF sebenar, tetapi *penghantaran antara proses* menggunakan WSGI mock, **bukan** trafik HTTPS sebenar antara servis Render.
- Tidak mengesahkan hak edar setiap halaman, visual cetakan setiap Lesson, identiti akaun pengguna sebenar atau baki kredit dalam Supabase.
- Apabila PR #558 berubah, **kemas kini pin SHA** dalam workflow dan jalankan semula ujian, supaya bukan menguji pasangan kod yang lapuk.
- **STAGING HOLD / DRAF**: Jangan gabung atau deploy ke pengeluaran sehingga ujian Render ↔ Telegram sebenar dan pengesahan akademik/sumber selesai.

## Audit lengkap 81 pemetaan Student Book — 12 Nov 2026
- PR Telegram #558 commit `e4ca75a71b4c1d2bc2579785629414674fae03a2` menambah ujian `test_all_81_original_source_mappings_fail_closed_or_extract_exact_pdf_pages` yang membaca peta asal `app.py`, menilai semua 81 pilihan, mengesahkan 80 excerpt 1–4 halaman, dan menguji PDF dipulangkan terhadap content stream fail sumber bagi setiap halaman.
- Lesson 43 dengan peta lama lima halaman kini diperbetulkan kepada halaman tunggal 121 di resolver API;  Lesson 103 memulangkan 73–75 dan Lesson 157 halaman utama 110 sahaja. Semakan chunk sempadan dan endpoint Bearer sedia ada kekal.
- CI Telegram `English Workbook PDF and Music external links source QA` run **43118922500**: **SUCCESS** pada commit `28aca5abef094588906114d7985930a01affdd4f`.
- Workflow silang Web–Telegram kini memin commit itu, menggantikan pin lama. Ujian WSGI berasingan masih perlu lulus pada head Web terkini.
- Bukti ini ialah semakan pemetaan dan stream PDF sumber sebenar dalam repositori, **bukan** pengesahan visual buku cetak, kebenaran hak edaran atau pemeriksaan LIVE.

## Sambungan 12 Nov 2026 — pembetulan kandungan Phonics 3

- Penemuan audit: Lesson 43 sepatutnya Phonics 3, Student Book **p.121**, bukan lima halaman Unit 3 **p.27–31**. Rujukan utama: https://online.anyflip.com/aecw/prtt/files/basic-html/page133.html .
- PR Telegram #558 memperkenalkan pembetulan bersyarat hanya untuk pemetaan lama yang sepadan tepat. Tidak melonggarkan had 1–4 halaman untuk Lesson lain; ujian sumber kini meliputi 81 pemetaan.
- Ujian silang Web–Telegram dipinda untuk menguji PDF p.121 sebenar daripada `y4_student_101_177.pdf`, dan pin Telegram diperbaharui.
- Belum membetulkan pemetaan legasi `app.py`, belum ada ujian akaun guru LIVE atau kelulusan hak edar; **STAGING HOLD**.

## Pembetulan kontrak selepas audit SOW (12 November 2026)

- **Lesson 43**: Phonics 3 p.121 sahaja; sumber lama p.27–31 tersalah cakupan.
- **Lesson 103**: Activity 5 p.73 sahaja; p.74–75 sebenarnya diperuntukkan untuk Lesson 104.
- **Lesson 157**: pilihan utama *What are germs?* p.110–111; CLIL p.133 pilihan lain (bukan disambung).
- Ujian silang dibina terhadap Telegram commit `e4ca75a71b4c1d2bc2579785629414674fae03a2`. Setiap PDF dibanding dengan stream halaman sebenar, tiada buku penuh atau halaman tambahan terdedah.
- Sumber rujukan: https://www.scribd.com/document/774411596/Primary-Year-4-SK-SoW dan https://online.anyflip.com/aecw/prtt/files/basic-html/page133.html .
- **Bukan LIVE**. Pemeriksaan akademik lanjut/hak edaran dan E2E akaun sebenar kekal HOLD; rekod pemetaan dalam `app.py` Telegram lama belum dikemaskini.

## Kontrak tiga PR — sambungan 12 November 2026

- PR #567 (peta Telegram legasi app.py) dipin ke e98872f8a21ca001d1c2041b907ec31346ee4111; PR #558 (API Student Book Telegram) dipin ke aa05d06324806add65304cabd1d1c2c8db0d6aa9; PR #559 (Web) menjalankan ujian silang terhadap kedua-duanya.
- Workflow web-english-y4-cross-pr-contract-staging.yml kini mengambil tiga checkout berasingan. Ujian baharu membandingkan kesemua 81 entri halaman utama daripada peta app.py yang dibetulkan dengan halaman PDF yang dipilih oleh resolver Telegram private.
- Semakan SOW khusus: Lesson 43 = p.121; Lesson 103 = p.73; Lesson 157 = p.110–111. Rekod terdahulu dalam dokumen ini yang menyebut p.73–75 atau p.110 sahaja ialah bukti sejarah sebelum pembetulan dan **bukan keadaan sasaran terkini**.
- Had maksimum empat halaman berturutan, kesahihan PDF, pemisahan Workbook, serta sekatan login/bearer tidak dilonggarkan.
- Ujian tiga PR ini ialah ujian staging offline, bukan semakan rupa buku cetak, hak edaran, konfigurasi pypdf pada Render, atau muat turun sebenar akaun guru. Semua release gate itu masih HOLD; tiada merge/deploy pengeluaran.
- Jika kepala PR #567 atau PR #558 berubah, pindaan pin SHA dan ujian semula diwajibkan sebelum penerbitan.


## Audit liputan 160 Lesson — pengadang 79 tanpa peta Student Book (12 Nov 2026)

- Peta kanonik Telegram legasi mempunyai **81/160** Lesson dengan sumber halaman Student Book utama yang ditentukan.
- Baki **79/160 Lesson** **bukan** secara automatik dianggap salah, tidak lengkap RPH, atau wajib mempunyai halaman Student Book. Ia bermaksud sumber halaman **belum disahkan dalam peta khusus**; sebab itu pautan Student Book bagi Lesson tersebut mesti kekal tidak tersedia.
- Ujian tambahan `test_unmapped_79_lessons_never_offer_student_book` membina katalog Lesson 1–160 penuh daripada nombor Lesson, tetapi tetap menguji peta sumber asal PR #558: setiap satu daripada 79 Lesson tanpa rekod tidak boleh memperoleh metadata atau PDF Student Book pada API private (404). Untuk Lesson yang tersedia dalam katalog Web, senarai bahan tidak boleh memaparkan butang Student Book palsu; permintaan URL terus juga ditolak.
- Semakan ini **tidak menyekat Workbook** yang disahkan dan tidak menjana halaman baharu. Ujian antara cabang kekal menggunakan pin SHA PR #558 dan #567; apabila salah satu berubah, jalankan semula kontrak selepas pin diperbaharui.
- Penambahan kes negatif ialah **QA staging sahaja**; ia tidak mengubah data, akses ahli, kuota, dan fail PDF produksi. Keputusan CI untuk komit terkini mesti diperiksa sebelum menyatakan ujian lulus.
- Untuk penerbitan: audit visual kandungan PDF, hak edaran, pypdf dalam Render, dan HTTPS akaun guru sebenar masih HOLD.
