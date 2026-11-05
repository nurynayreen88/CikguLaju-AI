# Audit permulaan Bahasa Arab Tahun 2–6 — 5 November 2026

**Keputusan:** DRAF / staging sahaja. **0 RPH FINAL READY**, **5 RPH contoh PdP 001** telah disediakan untuk semakan; bukan keseluruhan subjek. Belum ada perubahan pada app.py, Telegram/Web LIVE, DB v26.00 atau jadual guru.

## Penemuan sebenar
| Tahun | DSKP | Buku teks | RPT 2026 | RPH contoh | Sekatan penerbitan |
|---|---|---|---|---|---|
| 2 | PDF Drive; teks boleh baca | PDF Tahun 2 ditemui pada portal sekolah KPM; belum semak muka surat | RPT 2026 Kumpulan B ditemui | 1 DRAF | Halaman buku dan SP individu |
| 3 | PDF Drive; teks boleh baca | Drive PDF imej (CamScanner); tidak boleh diekstrak secara terus | RPT 2026 Kumpulan B ditemui | 1 DRAF | Audit visual buku, semua halaman |
| 4 | PDF Drive; teks boleh baca | PDF berteks; 4 unit, halaman bercetak 1–112 | RPT 2026 Kumpulan B ditemui | 1 DRAF | Semak halaman spesifik setiap PdP |
| 5 | PDF Drive; teks boleh baca | PDF berteks; 4 unit, halaman bercetak 1–112 | RPT 2026 Kumpulan B ditemui | 1 DRAF | Semak halaman spesifik setiap PdP |
| 6 | PDF DSKP Tahun 6 ditemui pada laman panitia KPM, belum baca kandungan penuh | PDF Drive; ekstraksi teks kosong | RPT 2026 Kumpulan B ditemui | 1 DRAF | Semak DSKP serta buku secara visual |

## Semakan unit buku teks yang mempunyai teks
**Tahun 4 (rujukan halaman bercetak untuk unit sahaja):** (1) الشهور الميلادية 1–28; (2) من في المدرسة؟ 29–56; (3) أحب مدرستي 57–84; (4) بيتي جنتي 85–112.

**Tahun 5:** (1) في المطبخ 1–28; (2) ما ألذ الطعام! 29–56; (3) هيا نشترك في الأنشطة الصفية 57–84; (4) رفقا بالحيوانات! 85–112.

## Kawalan kualiti dan operasi
1. Jangan guna jadual minggu RPT 2026 sebagai identiti PdP; susun lesson/PdP secara berturutan untuk 2027 dan sesuaikan cuti Kumpulan A/B berasingan.
2. RPH hendaklah menyatakan objektif boleh ukur, aktiviti guru/murid, bahan, PBD dan penutup; sasaran 1 halaman Word A4 selepas dirender. Draf Markdown sedia ada belum menjalani ujian render.
3. Jangan salin/palsukan halaman buku teks: julat *unit* tidak sama dengan halaman pengajaran individu.
4. DSKP dan SP mesti dipadankan setiap satu daripada PDF sumber, bukan disalin daripada RPT pihak ketiga tanpa pengesahan.
5. Sehingga audit setiap PdP lulus, metadata kekal DRAF dan tiada adapter runtime/telegram/web disambungkan.
6. Semak DB v26.00 yang benar-benar dipasang sebelum insert/upsert; ambil backup, bezakan rekod semasa dan jangan padam atau overwrite.
7. Apabila lulus, penjana Telegram dan Web mesti menggunakan sumber/format RPH yang sama.

## Pautan sumber
- DSKP T2–T5: lihat `rph_standalone/bahasa_arab/source_manifest_20261105.json`.
- DSKP T6: https://sites.google.com/moe-dl.edu.my/ba2k26/dokumen-standard-kurikulum/dskp-mata-pelajaran-terkini
- Buku teks T2: https://sites.google.com/moe-dl.edu.my/sketta2bahasaarab/buku-teks-digital
- RPT 2026 T2–T6: https://anyflip.com/zxzlm/jffk/basic ; https://anyflip.com/zxzlm/vmip/basic ; https://anyflip.com/zxzlm/xrtv/basic ; https://anyflip.com/zxzlm/ucjc/basic ; https://anyflip.com/zxzlm/bmaa/basic

**Catatan:** RPT 2026 yang ditemui adalah Kumpulan B dan bukan pengesahan tarikh RPT 2027. Audit ini tidak mengesahkan semua SK/SP, bukan jaminan bahan LIVE dan tidak menandakan subjek selesai.
