# CikguLaju AI — Peraturan kemaskini dan pelepasan bahan

> Keputusan pemilik projek (13 November 2026): **setiap kerja yang dibaiki mesti terus disimpan dan diurus untuk dimasukkan**, supaya tidak tertinggal antara sesi/perbualan.

## Aliran wajib bagi SETIAP pembaikan
1. **Semak sumber asal.** Kenal pasti Tahun, Subjek, Tema/Unit/Tajuk, Lesson/PdP, SK/SP dan rujukan DSKP/RPT/SOW/buku teks/buku aktiviti yang sah. Jangan cipta halaman, SK/SP, audio, atau aktiviti buku.
2. **Simpan perubahan pada sesi yang sama.** Gunakan branch khusus dan commit sebenar; jangan tinggalkan hasil sebagai cadangan dalam chat sahaja. Buka pull request (PR) yang menyatakan apa yang berubah, rujukan sumber, ujian dan risiko.
3. **Uji sebelum gabung.** Jalankan ujian yang bersesuaian (unit, pemetaan buku, integriti kandungan, Word/PDF A4 satu halaman, Web/Telegram untuk aliran terlibat). Pastikan tindakan guru dan murid jelas, aktiviti tidak generik, PBD boleh diukur, dan nota dalaman pembangunan tidak muncul dalam fail pengguna.
4. **Gabung segera setelah lulus.** Apabila pengesahan kurikulum yang diperlukan dan ujian berjaya, gabung PR ke `main` dalam sesi yang sama; elakkan PR pembaikan yang sudah lulus dibiarkan tanpa sebab.
5. **Sahkan operasi pengguna.** Merge `main` **bukan** bukti bahawa bahan sudah tersedia di Web/Telegram. Sahkan deployment Render, sambungan servis, janaan/muat turun sebenar dan rekod status. Jangan sebut `LIVE` sebelum pengesahan.
6. **Jika tidak lulus atau tidak dapat diverifikasi:** kekalkan PR sebagai `HOLD` / draft, nyatakan halangan serta ujian yang belum disahkan dalam `docs/LOG_KEMASKINI_BAHAN.md`; jangan deploy bahan tidak tepat. Sambung dari rekod itu dalam sesi berikutnya.

## Kawalan keselamatan
- Non-destructive: kekalkan bahan asal, data pengguna, rekod bayaran, kuota dan pangkalan data; jangan reset/overwrite untuk mempercepat pelepasan.
- RPH/RPT untuk pengguna mestilah berkualiti dan bersandarkan sumber, bukannya placeholder/generik. Bahan yang belum siap hanya boleh dipaparkan sebagai 'Akan Datang', bukan pautan muat turun palsu.
- Perubahan besar atau berisiko pada produksi mesti melalui semakan tambahan. Jangan auto-merge tanpa CI atau jika terdapat isu kurikulum yang belum selesai.
- Rekod setiap perubahan dan **status sebenar** di `docs/LOG_KEMASKINI_BAHAN.md`: `DALAM SEMAKAN`, `HOLD`, `MERGED MAIN`, `LIVE DISAHKAN`. Bezakan status kod dan status pengguna.

## Templat laporan akhir setiap kerja
- Bahan/komponen yang diperbaiki
- Pautan PR + commit
- Ujian yang lulus / belum lulus
- Status: MERGED MAIN atau HOLD
- Status Web dan Telegram: LIVE DISAHKAN / BELUM DISAHKAN
- Langkah susulan khusus jika ada

Jangan sekali-kali menyatakan perubahan telah dimasukkan atau tersedia kepada pengguna tanpa bukti yang sepadan.
