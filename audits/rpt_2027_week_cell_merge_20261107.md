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
