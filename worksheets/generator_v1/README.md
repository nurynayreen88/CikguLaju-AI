# CikguLaju — Penjana PDF Lembaran Latihan v1 (DRAF)
 
## Tujuan
Membekukan reka bentuk Matematik Tahun 4 Batch 03 untuk penggunaan merentas chat.
Ini ialah pembinaan semula, bukan pemulihan kod Python asal yang hilang.
Jangan anggap sebagai READY sehingga kalibrasi, ujian dan semakan visual lengkap.

## Fail wajib
1. `generate.py` — kod penjana yang sama, jangan ditulis semula oleh AI.
2. `requirements.txt` — versi pustaka yang dikunci.
3. `sample_batch04.json` — contoh struktur kandungan (dua worksheet, bukan Batch 04 lengkap).
4. PDF asal **CIKGULAJU_MATEMATIK_T4_BATCH_03_MURID.pdf** (28 halaman).
5. `design.lock.json` — terhasil selepas kalibrasi pertama; simpan dan gunakan semula.
6. Fon penuh yang sama seperti PDF asal, dipasang secara sah pada komputer penjana.
   Jangan gunakan fon pengganti atau mengekstrak fon subset sebagai fon penuh.

## Jalankan
Python 3.11 atau 3.12. Pasang pustaka:
```sh
python -m pip install -r requirements.txt
```
Kalibrasi pertama sahaja (buat semakan visual sebelum meluluskan lock):
```sh
python generate.py --reference CIKGULAJU_MATEMATIK_T4_BATCH_03_MURID.pdf --input sample_batch04.json --lock design.lock.json --init-lock --output QA_SAMPLE
```
Jika fon tidak ditemui, berikan lokasi fon yang sudah dipasang dengan `--font-dir`.
Jika kalibrasi gagal, jangan padam lock atau longgarkan semakan secara sembarangan;
semak punca dan versi kod. Simpan kod, PDF rujukan dan lock yang sudah diluluskan bersama.
Batch baharu:
```sh
python generate.py --reference CIKGULAJU_MATEMATIK_T4_BATCH_03_MURID.pdf --input batch_baru.json --lock design.lock.json --output BATCH_BARU
```
Folder output mestilah belum wujud. Tiada overwrite. Tiada Google Docs.

## Kontrak reka bentuk
- Header/footer dipotong terus daripada PDF diluluskan; medan dinamik sahaja diganti.
- Font, saiz halaman, hash PDF rujukan, hash kod dan versi pustaka dikunci.
- Header sama pada kedua-dua halaman; tajuk, tema, nama, kelas, tarikh hanya halaman pertama.
- Maksimum dua halaman murid; skema berasingan.
- A/B/C ialah bahagian soalan, bukan tahap penguasaan.
- Kotak pengiraan tidak bercantum. Garisan hanya untuk ruang jawapan yang diperlukan.
- Gunakan rajah matematik yang tepat, bukan ilustrasi vektor hiasan.
- Bentuk soalan mengikut SP dan buku rasmi; nombor, konteks dan soalan asli.
- Jangan kecilkan fon untuk memaksa kandungan muat. Penjana menolak limpahan ruang.
- Layout yang disediakan: vertical, division, work, problem, short, choice, matching,
  table, clock dan timeline. Layout lain perlu versi kod berasingan yang disemak.
- Buat latihan berlainan bentuk, bukan sekadar menggantikan nombor untuk semua bahagian.
- Penjana hanya menguji struktur, ID jawapan, ruang dan keseragaman mekanikal.
  Ia tidak membuktikan soalan sejajar dengan DSKP atau semua jawapan benar.
- Mata wang asing perlu jadual sumber sebenar bertarikh dan tidak boleh direka.
- Satu worksheet setiap PdP/Lesson sebenar setelah pemetaan disahkan.

## Input JSON
Gunakan `sample_batch04.json` sebagai contoh. Setiap worksheet mempunyai:
`id`, `subject`, `sp`, `theme`, `title`, `source`, `pages` (1–2),
`answers` (ID soalan → jawapan).
Setiap halaman ialah senarai bahagian `label`, `kind`, `prompt`, `items`.
Jenis data:
- vertical: terms (senarai angka/amaun dalam teks), op (+, −, ×)
- division: dividend (teks), divisor (integer 1–99)
- work/problem/short: text
- choice: text, options
- matching: left, right (acak pilihan kanan; kunci jawapan dengan ID)
- table: headers pada bahagian, cells pada item; null ialah ruang jawapan
- clock: hour (1–12), minute (0–59)
- timeline: start/end format HH:MM; tempoh merentasi tengah malam dibenarkan

## QA wajib sebelum READY
1. Semak sumber DSKP, buku teks dan buku aktiviti jika tersedia.
2. Padankan tajuk dengan nombor PdP produksi yang sebenar.
3. Semak pengiraan dan skema secara bebas; semua ID mesti padan.
4. Buka setiap fail PNG dalam output/preview untuk murid dan skema.
5. Bandingkan halaman contoh dengan PDF Batch 03: header, fon, warna,
   jarak, ruang jawapan, ketepatan rajah dan nombor halaman.
6. Semak cetakan A4 pada skala 100%, terutama bagi aktiviti ukuran.
7. Kekalkan status DRAFT_VISUAL_QA_REQUIRED sehingga semua semakan lulus.
8. Jangan masukkan ke Web sehingga lulus QA; jangan ubah bahan terdahulu.

## Arahan untuk chat baharu
> Gunakan kod penjana CikguLaju v1 dalam folder worksheets/generator_v1
> pada commit yang telah diluluskan, bersama PDF asal Batch 03 dan design.lock.json.
> Jangan reka template baru, jangan gunakan Google Docs, jangan ubah generate.py
> atau lock. Sediakan kandungan JSON baharu sahaja berpandukan DSKP dan buku rasmi.
> Jana PDF terus, semak visual semua halaman dan skema. Jika fon, kod, rujukan atau
> persekitaran penjana tidak sepadan, hentikan dan laporkan sebab; jangan ubah reka bentuk.
> Kekalkan semua bahan sedia ada.

## Status semasa
Kod ini belum dapat dijalankan dalam sesi asal kerana ralat ClientError pada
persekitaran Python/container. Belum ada lock terkalibrasi atau PDF yang
disahkan sepadan. Jangan merge ke produksi berdasarkan kewujudan kod sahaja.
