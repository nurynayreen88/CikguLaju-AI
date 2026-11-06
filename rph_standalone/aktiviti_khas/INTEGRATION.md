# RPH Aktiviti Khas — Panduan integrasi selamat

Status: DRAF UNTUK SEMAKAN. PR #412 belum digabung atau diterbitkan ke Telegram/Web.

## Sumber

- catalog_v1.json: 20 aktiviti Transisi Tahun 1 dan 30 variasi Tamat Sukatan, tiga tahap.
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

## Pintu kelulusan sebelum LIVE

- [x] 50 kandungan berstruktur dan ID unik.
- [x] Contoh Word dan PDF A4 satu halaman diperiksa secara visual.
- [x] GitHub Actions mengesahkan 50 PDF satu halaman dan ujian API.
- [ ] Semak semua 50 Word menjadi satu halaman A4 dengan LibreOffice.
- [ ] Semakan guru bagi semua aktiviti termasuk pelaksanaan KP2027.
- [ ] Daftar endpoint di Telegram staging dan tambah Web proxy berlindung.
- [ ] Ujian login, free quota, langganan, idempotency, cetak telefon/PC.
- [ ] Semak regresi RPH biasa, RPT, Telegram, bayaran serta DB.
- [ ] Hanya selepas lulus, alihkan status DRAF ke READY dan jadualkan penerbitan tanpa menimpa data.
