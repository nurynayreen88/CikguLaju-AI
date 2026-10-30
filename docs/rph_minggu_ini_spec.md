# RPH Minggu Ini — Spesifikasi Pelaksanaan

Status: staging specification; belum diintegrasi ke app.py.

## Aliran pengguna
1. Tekan menu **RPH Minggu Ini**.
2. Dapatkan negeri/kumpulan sekolah, minggu persekolahan semasa dan jadual waktu yang disahkan.
3. Semak cuti sekolah, cuti umum, cuti gantian daripada pangkalan data kalendar yang disahkan.
4. Papar hari yang dikecualikan secara automatik dan minta guru sahkan cuti tambahan: cuti peristiwa, cuti sendiri, separuh hari, sesi/kelas tertentu.
5. Papar pratonton sesi PdP yang layak dijana, termasuk hari, masa, kelas, subjek, Lesson/PdP, SK/SP dan jumlah dokumen.
6. Guru tekan **Sahkan & Jana Semua RPH**.
7. Jana dokumen menggunakan penjana RPH sedia ada dan pakejkan Word/PDF ke ZIP; laporkan kejayaan/gagal per sesi.

## Invarian data
- Jangan ubah atau reset rekod RPT, jadual, sejarah RPH atau kuota.
- Cuti/batal kelas bukan bukti Lesson/PdP telah dilaksanakan; jangan naikkan urutan Lesson/PdP bagi sesi dibatalkan.
- Elak dokumen berganda dengan kunci idempotensi berasaskan pengguna, minggu, kelas, sesi dan Lesson/PdP.
- Semak kelayakan pakej dan kuota sebelum mula; caj kuota hanya selepas dokumen berjaya, mengikut polisi yang berkuat kuasa.
- Jika penjanaan separa gagal, boleh sambung sesi gagal tanpa caj atau penjanaan semula yang tidak perlu.
- Cuti rasmi mesti disahkan sumbernya; jika data tidak lengkap, minta pengesahan guru dan jangan andaikan hari bercuti.
- Kalendar Kumpulan A/B dan cuti gantian mengikut negeri; tidak andaikan semua negeri bekerja Isnin–Jumaat.
- Simpan keputusan pengesahan guru dan audit log, tanpa menandakan PdP dilaksanakan secara automatik.

## Integrasi sebelum kod produksi
- Audit handler Telegram untuk menu dan callback RPH Hari Ini.
- Audit pembaca jadual, sumber kalendar, pemetaan RPT/Lesson dan penjana Word/PDF.
- Audit transaksi kuota dan proses penghantaran Telegram/ZIP.
- Ujian: tiada cuti, cuti rasmi, cuti tambahan, separuh hari, pembatalan satu kelas, minggu tanpa PdP, kegagalan separa, ulang klik, minggu lintas bulan/tahun, Kumpulan A/B.
- Merge hanya selepas ujian regresi RPH Hari Ini lulus.
