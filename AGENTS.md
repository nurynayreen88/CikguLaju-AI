# CikguLaju AI — Peraturan kemaskini dan pelepasan bahan

> Keputusan pemilik projek (13 November 2026): **setiap kerja yang dibaiki mesti terus disimpan dan diurus untuk dimasukkan**, supaya tidak tertinggal antara sesi/perbualan.

## Aliran wajib bagi SETIAP pembaikan
1. **Semak sumber asal.** Kenal pasti Tahun, Subjek, Tema/Unit/Tajuk, Lesson/PdP, SK/SP dan rujukan DSKP/RPT/SOW/buku teks/buku aktiviti yang sah. Jangan cipta halaman, SK/SP, audio, atau aktiviti buku.
2. **Simpan perubahan pada sesi yang sama.** Gunakan branch khusus dan commit sebenar; jangan tinggalkan hasil sebagai cadangan dalam chat sahaja. Buka pull request (PR) yang menyatakan apa yang berubah, rujukan sumber, ujian dan risiko.
3. **Uji sebelum gabung.** Jalankan ujian yang bersesuaian (unit, pemetaan buku, integriti kandungan, Word/PDF A4 dengan kotak sejajar (satu halaman jika muat tanpa memendekkan isi sah), Web/Telegram untuk aliran terlibat). Pastikan tindakan guru dan murid jelas, aktiviti tidak generik, PBD boleh diukur, dan nota dalaman pembangunan tidak muncul dalam fail pengguna.
4. **Gabung segera setelah lulus.** Apabila pengesahan kurikulum yang diperlukan dan ujian berjaya, gabung PR ke `main` dalam sesi yang sama; elakkan PR pembaikan yang sudah lulus dibiarkan tanpa sebab.
5. **Sahkan operasi pengguna.** Merge `main` **bukan** bukti bahawa bahan sudah tersedia di Web/Telegram. Sahkan deployment Render, sambungan servis, janaan/muat turun sebenar dan rekod status. Jangan sebut `LIVE` sebelum pengesahan.
6. **Jika tidak lulus atau tidak dapat diverifikasi:** kekalkan PR sebagai `HOLD` / draft, nyatakan halangan serta ujian yang belum disahkan dalam `docs/LOG_KEMASKINI_BAHAN.md`; jangan deploy bahan tidak tepat. Sambung dari rekod itu dalam sesi berikutnya.

## Kawalan keselamatan
- Non-destructive: kekalkan bahan asal, data pengguna, rekod bayaran, kuota dan pangkalan data; jangan reset/overwrite untuk mempercepat pelepasan.
- RPH/RPT untuk pengguna mestilah berkualiti dan bersandarkan sumber, bukannya placeholder/generik. Bahan yang belum siap hanya boleh dipaparkan sebagai 'Akan Datang', bukan pautan muat turun palsu.
- Perubahan besar atau berisiko pada produksi mesti melalui semakan tambahan. Jangan auto-merge tanpa CI atau jika terdapat isu kurikulum yang belum selesai.
- Rekod setiap perubahan dan **status sebenar** di `docs/LOG_KEMASKINI_BAHAN.md`: `DALAM SEMAKAN`, `HOLD`, `MERGED MAIN`, `LIVE DISAHKAN`. Bezakan status kod dan status pengguna.

## Syarat format RPH PREMIUM — WAJIB mulai 21 November 2026

**Keputusan pemilik projek (diperjelas 21 November 2026): HANYA SATU reka bentuk kotak RPH untuk SEMUA subjek/tahun/program.** Semua kotak utama (kepala/maklumat guru, SK/SP, aktiviti, pemulihan-pengayaan, refleksi) mesti **mempunyai struktur dan gaya kotak yang seragam, sama lebar keseluruhan dan sejajar di kiri/kanan dalam dokumen yang sama**. **Pendidikan Islam (Jawi) dan Bahasa Arab (Arab) sahaja menggunakan arah kanan-ke-kiri (RTL); semua subjek lain LTR.** RTL ialah perbezaan arah tulisan/urutan kolum sahaja, **bukan pengecualian untuk bentuk atau lebar kotak**. **Kotak kecil maklumat guru** (**Kelas, Tarikh, Hari, Masa, Bilangan Murid**) berada di **kanan atas** untuk semua subjek LTR, tetapi di **kiri atas** untuk Pendidikan Islam/Jawi dan Bahasa Arab/Arab RTL; kotak identiti pelajaran yang lebar berada di sebelah bertentangan, dengan jumlah bingkai luar tetap sama; input guru kosong mesti **kosong tanpa garisan atau placeholder**. Gunakan warna pastel ringan mengikut subjek, susun atur A4 formal dan tajuk Aktiviti 1/2/3 bold pada baris berasingan. Kekalkan EMK/KBAT/PAK21, PBD, pemulihan/pengayaan, refleksi serta **teks SK/SP dan aktiviti daripada sumber disahkan**.

- **Kekalkan susunan kepala yang pemilik telah setujui:** identiti RPH di kiri dan maklumat guru di kanan bagi LTR; identiti RPH di kanan dan maklumat guru di kiri bagi PI/BA RTL. Nama mata pelajaran cukup sekali sahaja pada kepala, tidak diulang dalam jadual SK/SP. Jangan mengubah kedudukan kotak hanya kerana membuat pembetulan lain.
- **Peraturan KEKAL bagi semua kerja RPH akan datang:** Jangan mengubah kedudukan kepala, gaya kotak, lebar luar, kekosongan medan, label Aktiviti pada baris baharu atau kandungan SK/SP tanpa ujian Word/PDF sebenar. Semua subjek SK, DLP, PPKI, SJKC, SJKT, KP2027 dan laluan Web/Telegram mengikut syarat yang sama. **Contoh 16 halaman di menu log masuk hanyalah rujukan visual, bukan pengesahan fail sebenar.** Setiap penjana baharu mesti mendaftar audit kepada `docs/RPH_PREMIUM_SPECIALTY_AUDIT_20261121.md` dan ujian automatik. Bagi penjana DLP/PPKI yang menggunakan `dlp_year2_rph.py`, pembaca ujian ketat ialah `web/rph_premium_readback_20261121.py`. Jika output sebenar gagal audit, kekalkan status HOLD dan lindungi janaan lama yang masih sah.
- **Rujukan autoritatif:** [docs/RPH_PREMIUM_STANDARD_20261121.md](docs/RPH_PREMIUM_STANDARD_20261121.md) dan [daftar subjek/format](docs/rph_premium_contract_20261121.json). Syarat ini mesti digunakan untuk **subjek baharu dan subjek yang belum selesai**, bukan sekadar 9 subjek LTR semasa.
- **Satu reka bentuk, penjana berbeza:** Sains, DLP dan PPKI kekal LTR dengan kotak luar sama seperti semua subjek. Hanya Pendidikan Islam/Jawi dan Bahasa Arab/Arab mempunyai arah RTL, dengan geometri kotak luar tetap sama. Pelihara tulisan, urutan kolum, label, SK/SP dan pelajaran; **jangan** menimpa penjana khusus menggunakan adapter LTR secara pukal. Audit Word **dan** PDF secara berasingan. Saiz mm Word dan PDF boleh berbeza mengikut margin, tetapi tepi kotak dalam *setiap* fail wajib sama.
- **Pintu pelepasan:** PR bagi setiap penjana/keluarga subjek baharu mesti ada contoh output sebenar, semakan A4 dan tepi luar semua jadual, padanan teks Word/PDF/SK/SP, ujian format khas dan bukti deploy serta muat turun sebelum status `LIVE DISAHKAN`. Jangan guna kuota guru untuk ujian tanpa izin. Periksa laluan `selected.source` Web/Telegram secara individu; deploy penjana umum tidak membuktikan setiap sumber telah siap.
- Perubahan kepada palet/subjek native wajib mendaftar alias dalam kontrak dan lulus ujian `tests/test_rph_premium_contract_20261121.py`. Jika gagal, kekalkan `HOLD` dan rekod di isu #1182, **jangan** longgarkan ujian untuk membenarkan kerosakan format.

## Templat laporan akhir setiap kerja
- Bahan/komponen yang diperbaiki
- Pautan PR + commit
- Ujian yang lulus / belum lulus
- Status: MERGED MAIN atau HOLD
- Status Web dan Telegram: LIVE DISAHKAN / BELUM DISAHKAN
- Langkah susulan khusus jika ada

Jangan sekali-kali menyatakan perubahan telah dimasukkan atau tersedia kepada pengguna tanpa bukti yang sepadan.
