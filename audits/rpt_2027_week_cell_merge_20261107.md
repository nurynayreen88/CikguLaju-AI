# Audit penggabungan sel Minggu/Tarikh — RPT 2027 (7 Nov 2026)

**Skop:** 21 PDF pratonton DRAF dalam PR #441; tiada penggantian RPT pengguna di Web/Telegram.

## Keputusan reka letak

1. Sel **MINGGU / TARIKH** dijadikan *rowspan sebenar* apabila beberapa PdP/Lesson berturutan mempunyai **label minggu yang sama dan tarikh Kumpulan A/B yang sama**.
2. Satu sel minggu meliputi semua PdP dalam kumpulan. PdP, unit, SK, SP dan catatan tetap berbaris **satu PdP satu baris**; tiada pengguguran atau penggabungan standard.
3. Sel minggu menggunakan tona hijau cair untuk memudahkan semakan mata. Garis antara PdP diteruskan dari lajur 2–5, bukan menyeberang sel minggu yang digabung.
4. Jika minggu atau tarikh berbeza, sel tidak digabung. Minggu kosong/placeholder seperti RBT tidak digabung sehingga agihan rasmi diketahui.
5. Jika terdapat minggu yang sama tetapi bukan rekod berturutan, jangan gabung melalui helaian yang lain. Peraturan ialah kumpulan berturutan sahaja.
6. Bila cukup halaman, keseluruhan kumpulan dijaga supaya label minggu tidak tertinggal bersendirian pada helaian sebelumnya.

## Pengesahan

- Unit tests ditambah untuk kes positif, kes tarikh tidak sepadan dan kes RBT belum ditetapkan.
- GitHub Actions: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42264804046 — **lulus** (21 PDF).
- Artifak PDF/PNG: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42264804046/artifacts/13526587250
- Pratonton visual muka surat kedua Pendidikan Moral Tahun 2 serta PJPK Tahun 3 menunjukkan sel minggu yang digabung merentasi dua PdP; RBT Tahun 4 kekal satu sel per PdP kerana minggu belum tersedia.

## Isu kritikal yang masih terbuka

**SK dan SP pada 21 PDF ini masih terhad kepada kod** daripada CSV/manifest, contohnya `1.1` atau `1.1.1`. Ini tidak memenuhi kehendak guru untuk **kod serta pernyataan penuh SK/SP**. TIDAK BOLEH melabel PDF ini sebagai FINAL READY atau menerbitkannya di Web/Telegram sehingga pernyataan standard diperoleh daripada sumber DSKP sah dan dipadankan per PdP tanpa menokok tambah.

Kalendar A/B 2027, cuti negeri/gantian, halaman buku teks dan signoff kandungan juga belum lengkap. Tiada perubahan DB, Telegram, Web, `app.py` atau kuota.


## Kemas kini setelah penambahan pernyataan dan reka letak muka depan

Pernyataan terdahulu bahawa SK/SP masih kod sahaja adalah rekod keadaan *sebelum pembetulan*. Pada versi staging PR #441 yang lebih baharu, penjana telah dipadankan kepada fail pernyataan DSKP berpunca daripada sumber asal: PSV T2–6, RBT T4–6, Moral T2–6, Sejarah T4–6 dan PJPK T2–6 (PJ dan PK mempunyai kamus kod berlainan). **Ini ialah pemetaan teks DRAF, bukan kelulusan visual setiap standard atau tarikh negeri.**

Muka depan **setiap satu daripada 21 PDF** kini standard dan sengaja terhad kepada:
- Ruang/kotak **LOGO SEKOLAH** (pilihan fail logo PNG/JPG jika dibekalkan);
- **NAMA SEKOLAH** (pilihan isi nama; jika tiada, tersedia garisan kosong);
- **NAMA GURU** (pilihan isi nama; jika tiada, tersedia garisan kosong).
- Tajuk wajib untuk mengenal pasti dokumen: **RANCANGAN PENGAJARAN TAHUNAN 2027**, mata pelajaran dan tahun.

Tiada alamat, kelas, nama negeri, kumpulan, rujukan cuti, watermark DRAF, nama bot, catatan sampingan atau nombor halaman pada **muka depan**. Kumpulan A/B, tarikh cadangan, nota sumber, tanda DRAF dan nombor halaman masih wujud apabila sesuai pada **halaman jadual**, bukannya pada kulit depan.

**Ujian:** GitHub Actions `42270875261` lulus; set artifak 21 PDF `13529262174`. Pemeriksaan semua 21 halaman muka depan dan halaman jadual pertama turut dibuat secara programatik; empat kulit depan contoh daripada PSV, PJPK, Sejarah dan Moral diperiksa secara visual. Ujian berasingan mengesahkan penjana menyokong laluan logo PNG serta nama sekolah/guru yang dibekalkan, tetapi Web/Telegram masih **belum disambungkan** untuk mengisi profil pengguna secara automatik.

**Pagar keselamatan kekal:** bukan FINAL READY sehingga pernyataan SK/SP dinilai terhadap halaman DSKP asal, kelulusan guru dan kalendar A/B negeri selesai. Tiada merge/deploy dan tiada pertukaran dokumen aktif pengguna.
