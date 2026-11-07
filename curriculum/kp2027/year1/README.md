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

## Sambungan audit — 7 November 2026 (Tahun 1 sahaja)

### Bahasa Melayu SK: padanan Mendengar berasaskan bukti

- [7 RPH SK untuk kemahiran Mendengar](bm_sk_listening_7_source_grounded_rph_20261107.json) kini ditulis secara berasingan untuk SP calon penataran **1.1.1–1.1.3** dan **1.2.1–1.2.4**. Setiap satu mempunyai objektif boleh nilai, BBM, set induksi, Aktiviti 1/2, pengukuhan/PBD, guru–murid, pembezaan dan pembentukan karakter.
- Semakan visual PDF penataran membuktikan teks **SK berlainan daripada SJK** untuk kod 1.2.3/1.2.4. Indeks sumber yang menyatakan kedua-dua variasi: [BM SP index v2 (SK/SJK)](bm_year1_training_sp_page_index_20261107_v2_SK_SJK.json). Jangan gunakan kod sama tanpa menyebut jenis sekolah.
- Tujuh RPH baharu ini boleh bertindih dengan tujuh draf BM editorial terdahulu. **Jangan campur atau jumlahkan sebagai lesson rasmi RPT.** Mereka adalah calon untuk mengganti draf lama setelah audit, bukan 7 PdP tambahan kurikulum.
- Sumber bukti ialah PDF penataran Tahun 1, **bukan DK muktamad**. Nombor waktu BM tidak diisi kerana peruntukan rasmi belum disahkan.

### Matematik: percanggahan antara dua bahan penataran

- Slaid perbandingan 19 halaman menyebut **7 tajuk dan 30 SP** secara keseluruhan. Namun jumlah SP yang tercetak pada tujuh panel tajuk ialah **28** (5 + 6 + 2 + 3 + 3 + 5 + 4).
- Senarai *AGIHAN KUMPULAN KUPASAN SP.xlsx* menyenaraikan **30 kod**, dengan empat kod prefiks 3.x untuk Wang, sedangkan panel Wang di slaid mengira **2 SP**. Semua enam kumpulan tajuk lain sepadan; beza tepat **2** kod belum terjawab.
- Rekod perbezaan: [Math source count reconciliation](math_2027_source_count_reconciliation_20261107.json). **Jangan** memaksa angka 28 atau 30 dengan membuang/menambah kod tanpa teks DK asal.
- Slaid DKP2027 pada halaman PDF 6 menyatakan **7 waktu seminggu × 30 minit**; ini bukti penataran, bukan jadual akhir sekolah tertentu.

### Pintu keluaran belum dibuka

- Semua rekod baharu serta master 36 masih **DRAF/HOLD** dan `approved_for_web=false` serta `approved_for_telegram=false`.
- Tiada `app.py`, DB aktif, kuota pengguna, Telegram atau Web diubah.
- Ujian sumber: `python -m unittest discover -s tests -p 'test_kp2027_y1_training_alignment_20261107.py' -v`.
- Seterusnya: sahkan PDF DK BM SK dan Matematik Tahun 1, betulkan teks SP, selaraskan 36 calon dengan 7 RPH sumber-berpandu, bina turutan PdP RPT A/B hanya selepas liputan standard disahkan.

### Alam dan Manusia: model RPH penataran yang lebih khusus

- [RPH Pasukan Keselamatan (model pengajaran berpasukan)](alam_manusia_pasukan_keselamatan_team_teaching_20261107.json) disediakan sebagai contoh guru Tahun 1, berpandukan portal penataran Alam dan Manusia yang menyebut 3.1.11/3.1.12, **bukan halaman DK akhir**.
- Contoh 60 minit bagi 30 murid: Set Induksi 6, rancang karya 10, hasilkan karya 20, galeri 16, PBD/penutup 8. Guru A mengajar, Guru B memerhati evidens setiap murid; penyesuaian seorang guru turut disediakan.
- Nombor kod di atas adalah **petunjuk sumber penataran**, bukan standard rasmi yang telah dimasukkan ke rekod DK. Nilai `official_sp`, `official_sk`, halaman DK, buku teks, tahap penguasaan serta kelulusan masih kosong dan status kekal DRAF/HOLD.


## Batch sumber-berpandu penuh Bahasa Melayu SK — 26 calon SP

- Fail induk untuk **semakan akademik sahaja**: [bm_sk_26_training_sp_draft_master_20261107.json](bm_sk_26_training_sp_draft_master_20261107.json). Liputan tepat satu calon RPH bagi setiap 26 kod SP daripada PDF penataran BM Tahun 1: **7 Mendengar, 8 Bertutur, 6 Membaca, 5 Menulis**.
- Empat sumber asal disimpan secara berasingan: [Mendengar](bm_sk_listening_7_source_grounded_rph_20261107.json), [Bertutur](bm_sk_speaking_8_source_grounded_rph_20261107.json), [Membaca](bm_sk_reading_6_source_grounded_rph_20261107.json), [Menulis](bm_sk_writing_5_source_grounded_rph_20261107.json).
- Setiap RPH mempunyai satu kod latihan SP, bukti halaman PDF penataran, objektif boleh nilai, BBM, Set Induksi, **Aktiviti 1**, **Aktiviti 2**, penutup/PBD, tindakan guru dan murid, pembezaan serta nilai karakter.
- Semakan semula teks PDF membuktikan **25/26 penyataan latihan adalah padanan langsung**; item 1.2.2 mempunyai senarai bernombor i–iii dan tanda baca tidak konsisten dalam PDF. Ia kini direkod secara berstruktur (ucapan selamat, penghargaan, permohonan maaf) tanpa menggugurkan makna sumber, dan akar penyataannya dipadankan semula secara literal.
- **Perbezaan aliran SK/SJK:** 1.2.3 dan 1.2.4 (Mendengar), serta 2.2.1 dan 2.2.2 (Bertutur) tidak boleh digunakan saling tukar. Versi draf ini menggunakan penyataan **SK** daripada bahan latihan dan perlu pengesahan DK akhir.
- Fail ini **bukan** 26 PdP yang diiktiraf sebagai urutan RPT. Bilangan 36 draf dalam master KP2027 terdahulu masih kekal, dan pakej 26 BM SK ialah calon semakan **penggantian/penambahbaikan**, bukan jumlah tambahan 26 PdP. Tiada data lama dipadam/ditimpa.
- Tiada pembuktian sah DK akhir, peruntukan masa BM, halaman buku teks KP2027, jumlah PdP setahun, jadual negeri Kumpulan A/B atau kelulusan guru. **0/26 READY** dan **0 standard DK akhir disahkan**.
- Ujian kawalan integriti: `python -m unittest discover -s tests -p 'test_kp2027_year1_bm_sk_26_source_20261107.py' -v`; turut dijalankan dalam workflow PR.


### Indeks SPi penataran mengikut empat kemahiran

- Empat jadual **Standard Prestasi** telah diperiksa secara visual dalam PDF penataran BM Tahun 1: **Mendengar halaman 33, Bertutur halaman 62, Membaca halaman 91, Menulis halaman 114**. Setiap jadual mengandungi **TP1, TP2, TP3** (12 tafsiran latihan keseluruhannya).
- Fail sumber: [bm_sk_training_spi_4skills_tp1_tp3_20261107.json](bm_sk_training_spi_4skills_tp1_tp3_20261107.json). Tafsiran disalin daripada jadual penataran; **bukan pengesahan versi DK muktamad**.
- Fail induk BM yang disambungkan kepada jadual SPi untuk semakan: [bm_sk_26_training_sp_draft_master_20261107_v2_spi_refs.json](bm_sk_26_training_sp_draft_master_20261107_v2_spi_refs.json). RPH hanya menyimpan rujukan **mengikut kemahiran** dan tidak diberikan TP murid secara automatik.
- **TP keseluruhan memerlukan pertimbangan profesional guru berdasarkan evidens PBD berterusan**, bukan satu aktiviti atau satu contoh RPH sahaja. Larangan penerbitan dan status HOLD kekal; tiada SK/SP/SPi rasmi disisipkan ke DB.
- Ujian semakan semula BM 26 SP bersama 12 tafsiran latihan: `python -m unittest discover -s tests -p 'test_kp2027_year1_bm_sk_26_source_20261107.py' -v`.


## Carian DK Matematik Tahun 1 — 8 November 2026

- [Log carian asal DK Matematik Tahun 1](math_original_dk_search_audit_20261108.json) merekodkan 11 lokasi/sumber yang diperiksa termasuk repositori BPK, laman KPM, folder penataran dan rangka RPT CikguLaju dalam Drive.
- Folder tepat [01_DK MATEMATIK TAHUN 1 (SDPK SEDIA)](https://drive.google.com/drive/folders/1HJM3cW3OuzZjMULqM3AWes4sjLVF6Uvr) ditemui dalam **SLOT 7** folder penataran Matematik Tahun 1 Sarawak, tetapi senarai anak folder yang boleh dilihat oleh akaun bersambung ialah kosong. **Nama folder bukan naskhah PDF.** Kehilangan senarai bukan bukti dokumen tiada di semua tempat.
- Portal rasmi KPM [Kurikulum Persekolahan 2027](https://www.moe.gov.my/kurikulum-persekolahan-2027) menyediakan kerangka umum; laman [Repositori BPK](https://repositori.bpk.moe-dl.edu.my/terbitan) mempunyai antaramuka terbitan/DSKP tetapi PDF DK Matematik Tahun 1 yang lengkap tidak dapat diambil daripada carian yang dilaksanakan.
- Bukti masa **berautoriti**: [Jawapan KPM kepada Dewan Rakyat, 24 Februari 2026, Soalan 59](https://www.parlimen.gov.my/files/jindex/pdf/JDR24022026.pdf) menyatakan waktu KP2027 Matematik **Tahap I = 3.5 jam seminggu**. Ini konsisten dengan **7 waktu × 30 minit** dalam slaid penataran. Jangan gunakan jadual contoh sekolah sebagai jadual mutlak setiap kelas.
- Slaid perbandingan Matematik Tahun 1 masih bercanggah: **30 SP** pada paparan keseluruhan, **28 SP** apabila dijumlahkan tujuh panel tajuk, dan **30 kod** pada lembaran agihan kumpulan. **Wang 2 berbanding 4** kekal isu akademik terbuka. Tiada kod tambahan direka, dibuang atau diberi teks rasmi.
- Dokumen KP2027 Matematik **Tingkatan 1** yang boleh dicapai dalam talian bukan DK **Tahun 1**. DSKP KSSR Semakan 2017/Tahap I Edisi 3 juga tidak boleh mengisi jurang ini.
- Keputusan carian: `ORIGINAL_COMPLETE_DK_NOT_RETRIEVED`; status `SOURCE_HOLD_NOT_READY`. **0 SK/SP baharu disahkan; 0 RPH READY.** Tiada perubahan pada DB aktif atau Web/Telegram.
- Semakan CI: `python -m unittest discover -s tests -p 'test_kp2027_year1_math_dk_search_20261108.py' -v`.
