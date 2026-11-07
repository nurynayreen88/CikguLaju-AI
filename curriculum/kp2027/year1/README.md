# CikguLaju — KP2027 Tahun 1 (fokus 7 November 2026)

**Status: DRAF/HOLD. Tidak boleh digunakan untuk janaan RPH/RPT pengguna sebelum Dokumen Kurikulum (DK) muktamad disahkan.**

## Kemajuan sebenar

- **36 RPH editorial Tahun 1**: Alam dan Manusia 7, Bahasa Melayu 7, Matematik 7; Pendidikan Islam, Bahasa Arab, Bahasa Inggeris, Pendidikan Moral, PJPK masing-masing 3.
- Fail semakan utama ialah [year1_editorial_master_36_20261107_v2.json](year1_editorial_master_36_20261107_v2.json). Fail awal `year1_editorial_master_36_20261107.json` **telah digantikan oleh v2 untuk tujuan semakan**; jangan gunakan kerana aktiviti pola/tertib nombor Tahun 1 Matematik belum dibetulkan pada versi itu.
- Semua 36 contoh mempunyai objektif cadangan, BBM, tindakan guru/murid, pengukuhan/PBD dan pembezaan. **0/36 READY**, tiada versi Word/PDF pengguna, tiada RPT rasmi, tiada import ke DB, tiada deployment Web/Telegram.
- C01–C07 ialah turutan **calon editorial**, bukan PdP rasmi. Dokumen masih tidak mengandungi kod SK/SP/SPi disahkan mahupun halaman buku teks KP2027.

## Penemuan sumber baru — BM Tahun 1

PDF penataran 118 halaman [SLOT 5-8 KUPAS DAN KUASAI KEMAHIRAN (compressed)](https://drive.google.com/file/d/1OYy3lh95ifjf31ymPuwF-zLOcfkYF1Jv/view), SHA-256 `447b499db78253c4c3f0559afa791691a010c58d076666917a060531b9637691`, mengandungi **26 kod SP** calon mengikut empat kemahiran (mendengar 7, bertutur 8, membaca 6, menulis 5). Tiga halaman PDF (7, 61 dan 109) telah diperiksa visual, dan kod lain ditemui melalui teks. Kumpulan SK/SJK perlu dipisahkan dan versi DK muktamad belum disahkan.

- [Indeks 26 kod + halaman PDF + cadangan crosswalk 7 draf BM](bm_year1_training_sp_page_index_20261107.json).
- Semua padanan RPH–SP di situ ialah *proposed*, bukan kelulusan. Draf BM C04 tiada padanan tepat sementara; C03 merangkumi dua kemahiran dan perlu pertimbangkan pecahan PdP.
- Untuk SK, pastikan PDF DK BM SK rasmi — bukan bahan SJK — sebelum menyalin standard ke pangkalan kurikulum.

## Penemuan sumber baru — Matematik Tahun 1

PDF penataran 19 halaman [Perbandingan KSSR Semakan 2017 vs DKP2027](https://drive.google.com/file/d/13x97bYD4fEHF_QvQQqy3f0ZWbCwC_LUD/view), SHA-256 `7119fa3789bb67bcf55d727e4e5090c7d092dfc17fc5b6fe0d997fa20f88c935` menunjukkan pada halaman PDF 6 **7 tajuk, 30 SP, 7 waktu seminggu, 30 minit satu waktu**. Halaman PDF 7 menjelaskan kandungan yang berpindah: anggaran, pembundaran, pola nombor, rangkaian nombor dan nilai tempat ke Tahun 2/3; pecahan ke Tahun 3; tambah berulang/tolak berturut ke Tahun 2.

Senarai 30 kod disokong fail penataran [AGIHAN KUMPULAN KUPASAN SP.xlsx](https://drive.google.com/file/d/1jXscf3gs8KIpZ4BTPVdRvSD-q9Lz4oVG/view); ini bukti **kod**, bukan teks penuh DK. Indeks: [math_year1_training_30_codes_20261107.json](math_year1_training_30_codes_20261107.json).

- Dalam fail master v2, RPH Matematik C03, C04, C07 dibetulkan: pengelasan bentuk 2D, padanan bilangan–objek, pengenalan wang; bukan lagi pola/tertib nombor yang berisiko mengimport kandungan lama.
- Tempoh cadangan aktiviti Matematik ditetapkan 30 minit per contoh berdasarkan bukti penataran; rujukan final DK dan jadual sekolah masih diperlukan.
- Sumber tahun sebelumnya **tidak** digunakan untuk mengisi SP, tema atau buku teks KP2027.

## Alam dan Manusia

[Portal penataran Alam dan Manusia Tahun 1](https://sites.google.com/moe-dl.edu.my/gurupenataranalamdanmanusiakp2/home) memaparkan contoh aktiviti penghasilan karya dan pembentangan peranan pasukan keselamatan (angka 3.1.11/3.1.12 disebut dalam laman penataran), serta model pengajaran berpasukan. Fail DK PDF asal masih perlu diperoleh untuk sahkan kata demi kata SP/SPi, versi dan halaman. Draf ADM C04 bertema karya visual dan pembentangan **tidak boleh** diberi kod rasmi sebelum semakan DK.

## Sumber dan disiplin penyimpanan

Sumber tambahan [folder penataran Sarawak — Tahun 1 Perdana](https://drive.google.com/drive/folders/1U9CZ9_n-S3J97xdV9v3hTJ-xU4-cvhWZ) mengandungi bahan penataran mengikut subjek. Rekod ini ialah pautan rujukan, bukan lesen untuk menerbitkan semula fail asal.

Tiada perubahan `app.py`, SQLite utama, kuota pengguna, Telegram, Web atau Render. Bahan KP2027 Tahun 1 mempunyai fail staging berasingan. Tingkatan 1 kekal di inventori terdahulu tetapi **tidak** diperluas dalam batch ini.

## Syarat READY

1. Dapatkan DK asal versi tepat untuk setiap subjek; periksa penerbit/edisi/tarikh, rekod SHA-256 dan halaman.
2. Sahkan setiap kod serta teks standard terhadap **DK asal** dan pastikan aliran sekolah (SK/SJK) sepadan.
3. Bandingkan semua draf dengan kehendak standard; pecahkan/gugurkan aktiviti yang tidak kena, susun jumlah PdP dan peruntukan waktu sebenar.
4. Bina RPT 2027 Kumpulan A/B selepas sumber, susunan PdP dan takwim lengkap; nombor minggu bukan ID lesson.
5. Jana Word/PDF satu halaman setiap RPH, audit satu persatu bersama evidens PBD dan ujian muat turun.
6. Uji staging Telegram–Web dengan satu sumber authoritative sebelum membenarkan penerbitan.

Ujian:
`python -m unittest discover -s tests -p 'test_kp2027_year1_training_evidence_20261107.py' -v`.

**Status terakhir: 36 calon RPH; BM 26 kod calon dari penataran; Matematik 30 kod calon dari penataran; 0/36 RPH READY.**
