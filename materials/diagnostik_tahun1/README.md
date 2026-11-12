# CikguLaju AI — Ujian Diagnostik Tahun 1 (2027)

Pengesanan awal selepas murid mula sekolah, bukan saringan kemasukan Tahun 1.
Item asal CikguLaju AI, bukan peperiksaan rasmi KPM atau penetapan TP PBD.

## Kandungan pakej semakan

- Bahasa Melayu (2 halaman, 20 markah): lisan, arahan, huruf, bunyi awal, perkataan, tulisan, pratulis.
- Bahasa Inggeris (2 halaman, 20 markah): listening, speaking, gambar, letters, tracing.
- Matematik (2 halaman, 20 markah): nombor, padanan, banding, bentuk, pola, tulisan.
- Pemerhatian kesediaan (2 halaman): 10 aspek, skala 0/1/2/TB.
- Panduan Guru (Word dan PDF), Analisis Kelas (Excel), PDF lembaran murid gabungan dan ZIP semua.

catalog.json menyimpan nama, MIME, saiz dan SHA-256 yang telah diperiksa. Fail
binari masih perlu dipasang secara berasingan di pelayan; metadata bukan fail.

## Integrasi Web — tindakan seterusnya

Paparkan di Sediakan Bahan PdP > Tahun 1 > Ujian Diagnostik, berasingan daripada
aliran RPH. Jangan ubah aliran Tahun/Subjek/Tema/Unit/Tajuk/Lesson, data kurikulum,
kredit percuma, langganan, pembayaran atau rekod pengguna.

1. Pasang kandungan ZIP sebenar di direktori aset persistent server dan set
   CIKGULAJU_T1_DIAGNOSTIK_ASSETS_DIR kepada direktori itu. Jangan muat naik
   analisis murid sebenar ke folder awam.
2. Pada proses Web sedia ada, daftar blueprint daripada
   web.diagnostik_tahun1_resources.create_blueprint(access_checker).
   access_checker mesti menggunakan mekanisme log masuk dan hak akses Web
   sedia ada; tiada checker bermaksud akses ditolak.
3. Aktifkan CIKGULAJU_T1_DIAGNOSTIK_ENABLED=1 selepas QA akses.
   Flag dimatikan bermaksud laluan 404.
4. Selepas log masuk, komponen Web membaca
   GET /bahan/diagnostik/tahun-1. Item berstatus ready ada download_url;
   item berstatus akan_datang jangan diberi butang muat turun.
5. Muat Turun Semua tersedia hanya apabila ZIP sebenar lulus semakan SHA-256.
   Jangan gunakan pautan sandbox ChatGPT sebagai URL produksi.
6. Telegram perlu pendaftaran menu sendiri yang mematuhi hak akses semasa;
   bahagian itu belum diubah dalam cabang ini.

## Ujian

python -m unittest discover -s tests -p test_diagnostik_tahun1_resources.py

Semakan fail hilang, checksum tidak sah, akses tidak dibenarkan, flag tidak aktif
dan penghantaran fail sah diliputi. Jalankan juga QA integrasi pada staging.

## Status sebenar

- Pakej fail untuk guru: SIAP.
- Metadata dan modul backend berpengawal: SIAP DI CABANG SEMAKAN.
- Fail binari di Web: BELUM DIPASANG/DISAHKAN.
- Menu Web/Telegram pengguna: BELUM DIDAFTAR.
- Produksi: BELUM DI-DEPLOY.
