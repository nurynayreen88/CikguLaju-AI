# Audit integrasi Web–Telegram English Tahun 4 — 11 November 2026

## Bukti dua-PR (staging sahaja)
- Web: PR #559, cabang `staging/web-english-y4-studentbook-20261111`.
- Telegram: PR #558, commit sumber dipin `c0fb43edb4384869fd49c918c0b8afa0020aee93`.
- Workflow: `.github/workflows/web-english-y4-cross-pr-contract-staging.yml`; ujian: `tests/test_web_english_y4_partner_contract_20261111.py`.
- Dua checkout GitHub yang berbeza dijalankan dalam GitHub Actions. API Flask kedua-duanya dihubungkan melalui penyesuai WSGI offline, dan menggunakan fail PDF asal dalam repositori.
- Jalur auth Telegram dalam ujian ialah stub Bearer untuk persekitaran offline; auth sebenar turut diliputi ujian PR Telegram, namun **ujian rangkaian LIVE dengan token sebenar belum dijalankan**.
- Tiada request terhadap perkhidmatan LIVE, tiada transaksi Supabase, tiada potongan kredit dan tiada deployment.

## Keputusan ujian silang
- Lesson 103: ketiga-tiga halaman Student Book **73, 74, 75** diekstrak dan kandungan stream PDF yang dihantar oleh Web sepadan dengan halaman asal dalam `y4_student_021_100.pdf`.
- Lesson 157: hanya halaman utama **110**; halaman tambahan 133 tidak disertakan.
- Lesson 43: rujukan lima halaman kekal ditahan, API muat turun tidak mendedahkan PDF.
- Lesson 30: **Student Book dan Workbook** muncul berasingan dalam senarai bahan dan kedua-duanya boleh dimuat turun sebagai PDF sumber sebenar.
- Pengadang kegagalan separa: jika Workbook API gagal, Student Book yang sah kekal dipaparkan/muat turun; jika Student Book gagal, Workbook yang sah masih dipaparkan/muat turun.
- Login tiada → 401; Unit yang tidak sepadan → 400; Bearer Telegram tiada → 401.
- Cache PDF Web → `no-store, private`.
- **5/5 ujian silang lulus** dalam GitHub Actions run **43016729997**, termasuk pengadang kegagalan sebelah sumber. Bukti bertahap: 4/4 run 43016329993 dan 3/3 run 43016057275.

## Had dan langkah seterusnya
- Ujian menggunakan kod sebenar dan fail PDF sebenar, tetapi *penghantaran antara proses* menggunakan WSGI mock, **bukan** trafik HTTPS sebenar antara servis Render.
- Tidak mengesahkan hak edar setiap halaman, visual cetakan setiap Lesson, identiti akaun pengguna sebenar atau baki kredit dalam Supabase.
- Apabila PR #558 berubah, **kemas kini pin SHA** dalam workflow dan jalankan semula ujian, supaya bukan menguji pasangan kod yang lapuk.
- **STAGING HOLD / DRAF**: Jangan gabung atau deploy ke pengeluaran sehingga ujian Render ↔ Telegram sebenar dan pengesahan akademik/sumber selesai.
