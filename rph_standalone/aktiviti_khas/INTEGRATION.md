# RPH Aktiviti Khas — Panduan integrasi selamat

Status: DRAF UNTUK SEMAKAN. PR #412 belum digabung atau diterbitkan ke Telegram/Web.

## Keputusan semakan kandungan terkini

- 59 rekod DRAF: 20 Transisi Tahun 1 + 39 Tamat Sukatan (13 subjek x 3 tahap Tahun 1–2, 3–4, 5–6).
- 13 subjek eksplisit: Bahasa Melayu, Bahasa Inggeris, Matematik, Sains, Pendidikan Islam, Pendidikan Moral, Pendidikan Seni Visual, Pendidikan Jasmani, Pendidikan Kesihatan, Pendidikan Muzik, Bahasa Arab, Sejarah dan Reka Bentuk dan Teknologi.
- Setiap aktiviti Tamat Sukatan dipaut pada satu subjek sahaja, dengan tajuk, objektif, induksi, tiga langkah, BBM, penilaian dan penutup berlainan mengikut tahap. Tiada label 'Semua subjek'.
- Guru melaksanakan tugas konkrit, murid menghasilkan produk/bukti, rakan menyemak dan guru memberi maklum balas. Panjang minimum 185 aksara per langkah ialah ujian struktur, bukan kelulusan pedagogi.
- Menu tamat sukatan sepatutnya membolehkan guru memilih Tahun kemudian Subjek dahulu, sebelum aktiviti; GET options dengan subject=Matematik akan menapis rekod. POST render wajib mempunyai subjek yang sepadan.
- Workflow tambahan Word A4 Audit akan memeriksa penukaran semua 59 Word ke PDF melalui LibreOffice. Jangan terbitkan selagi dokumen satu halaman tidak disahkan.

## Sumber

- catalog_v1.json: 20 aktiviti Transisi Tahun 1 dan 39 variasi Tamat Sukatan, tiga tahap.
- engine.py: membaca sumber secara read-only, SHA-256 parity, Word dan PDF A4.
- web/telegram_special_activity_api.py: API dalaman Telegram, Bearer token, dinyahaktifkan secara lalai.
- tests/test_aktiviti_khas_catalog_20261106.py dan tests/test_aktiviti_khas_render_20261106.py: audit sumber, pengasingan tahap, Word/PDF dan API.
- scripts/audit_aktiviti_khas_50.py: audit 50 Word melalui LibreOffice serta semua PDF untuk satu halaman A4; perlu dijalankan dalam QA yang ada LibreOffice.

## Pendaftaran (staging sahaja)

Selepas aplikasi Flask sedia, panggil register_if_enabled(app) daripada web.telegram_special_activity_api. Jangan daftarkan blueprint terus pada Web awam.

Persekitaran staging: CIKGULAJU_SPECIAL_RPH_ENABLED=1 bersama CIKGULAJU_WEB_NATIVE_RPH_ENABLED=1 dan CIKGULAJU_AUTHORITATIVE_API_TOKEN sekurang-kurangnya 32 aksara. Kekalkan feature flag dimatikan pada produksi sehingga diterima dan diuji.

Web mesti menjalankan Telegram login dan pemeriksaan entitlements serta kuota yang atomik dahulu. Browser tidak boleh melihat API token dalaman atau memanggil endpoint Telegram secara langsung. Jangan cipta pending bill, ubah pembayaran atau kuota semasa memaparkan menu.

## Endpoint

GET /internal/rph/v1/aktiviti-khas/options?kind=SELEPAS_TAMAT_SUKATAN&year=5

GET /internal/rph/v1/aktiviti-khas/options?kind=TRANSISI_TAHUN_1&year=1&phase=Fasa%20Kesediaan

POST /internal/rph/v1/aktiviti-khas/render menerima selection(kind, year, activity_id, subject), source_digest daripada GET, teacher(class,date,time,students), format(word/pdf). Web tidak boleh menghantar teks aktiviti, SK/SP atau fail yang direka.

## Aliran menu apabila integrasi diluluskan

Sediakan Bahan PdP → RPH Aktiviti Khas → [Transisi Tahun 1 / Tamat Sukatan] → Tahun → Fasa (jika Transisi) → Aktiviti → Kelas, Tarikh, Masa, Bilangan Murid → Papar Bahan → Word/PDF.

- Transisi rasmi Tahun 1 sahaja. Tahun 2 boleh guna aktiviti serupa sebagai Aktiviti Awal Persekolahan, bukan dilabel Program Transisi rasmi.
- Tamat Sukatan: Tahun 1–2, Tahun 3–4, Tahun 5–6 masing-masing mempunyai versi langkah, objektif dan penilaian berbeza.
- Aktiviti Khas bukan PdP rasmi dalam RPT; jangan cipta SK/SP atau nombor Unit/Lesson.
- Gunakan sumber yang sama untuk Telegram dan Web. Tiada AI runtime.

## Antara muka data yang siap untuk integrasi

Semua route di bawah API **dalaman Telegram sahaja** dan memerlukan Bearer token yang tidak boleh dihantar kepada browser. Sila guna Web proxy yang telah mengesahkan pengguna dan entitlement apabila benar-benar disambungkan.

1. GET /internal/rph/v1/aktiviti-khas/subjects?kind=SELEPAS_TAMAT_SUKATAN&year=6 -> 13 nama subjek.
2. GET /internal/rph/v1/aktiviti-khas/options?kind=SELEPAS_TAMAT_SUKATAN&year=6&subject=Matematik -> ID S03C.
3. GET /internal/rph/v1/aktiviti-khas/preview?kind=SELEPAS_TAMAT_SUKATAN&year=6&subject=Matematik&activity_id=S03C&source_digest=<hash> -> objektif, BBM, enam fasa beserta tempoh, pentaksiran dan status DRAF. Preview baca sahaja; **tidak menggunakan kuota**.
4. POST /internal/rph/v1/aktiviti-khas/render -> Word/PDF untuk pilihan dan digest yang sama; jangan benarkan pengguna memuat turun melalui API dalaman tanpa laluan kebenaran sedia ada.

Fail sampel untuk audit manusia: GitHub Actions 'RPH Aktiviti Khas - Review Pack' menjana satu ZIP DRAF berisi 59 Word, 59 PDF, MANIFEST.json (SHA-256 setiap fail) dan BACA_DAHULU.txt. Semak aktiviti secara individu sebelum menandakan READY. Pakej ini **bukan** pengganti muat turun berbayar pada sistem produksi.

## Pintu kelulusan sebelum LIVE

- [x] 59 kandungan berstruktur dan ID unik.
- [x] Contoh Word dan PDF A4 satu halaman diperiksa secara visual.
- [x] GitHub Actions mengesahkan 59 PDF satu halaman dan ujian API.
- [ ] Semak semua 59 Word menjadi satu halaman A4 dengan LibreOffice.
- [ ] Semakan guru bagi semua aktiviti termasuk pelaksanaan KP2027.
- [ ] Daftar endpoint di Telegram staging dan tambah Web proxy berlindung.
- [ ] Ujian login, free quota, langganan, idempotency, cetak telefon/PC.
- [ ] Semak regresi RPH biasa, RPT, Telegram, bayaran serta DB.
- [ ] Hanya selepas lulus, alihkan status DRAF ke READY dan jadualkan penerbitan tanpa menimpa data.
