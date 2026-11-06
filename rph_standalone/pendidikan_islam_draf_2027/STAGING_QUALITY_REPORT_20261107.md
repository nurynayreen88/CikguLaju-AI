# Pendidikan Islam 2027 — Batch 2: audit 80% subjek kedua terendah (STAGING)

**Tarikh:** 7 November 2026  
**PR:** #443 `staging/rph80-pendidikan-islam-second-20261107`  
**Status:** **DRAF / HOLD / NO_GO** — belum mendapat pengesahan 80% kualiti kandungan. Tiada merge ke main atau deployment.

## Keputusan selepas pemurnian

| Metrik | Sebelum | Selepas | Maksud |
|---|---:|---:|---|
| Jumlah Lesson katalog Tahun 2–6 | 696 | **696** | Identiti kekal; T2=112, T3=147, T4=151, T5=143, T6=143 |
| RPH draf dapat dibaca | 690 | **690** | Belum diperakui; bukan RPH LIVE |
| Rekod ditahan | 6 | **6** | Tiada kandungan guru yang dibuka |
| RPH draf beraktiviti utama ≤2 langkah | 563 | **3** | Ukuran struktur sahaja; bukan markah pedagogi |
| RPH yang ditambah langkah/PBD berasaskan SP | 0 | **560** | Semua perubahan draf memerlukan pengesahan pakar |
| RPH draf dengan ≥3 langkah aktiviti utama | 127 | **687** | **99.57%** liputan mekanikal; **BUKAN 99.57% kualiti** |
| Kes sumber berisiko yang sengaja tidak dilengkapkan | — | **3** | T4 L083 dan T6 L137/L141 |
| Skor kualiti akademik yang disahkan | Belum ada | **Belum ada** | 80% belum boleh diisytihar |

Ranking editorial lampau **51%** (kedua terendah selepas Sains 45%) ialah angka kasar, bukan penilaian kandungan setiap Lesson. Skor akademik baharu kekal `null`; `quality_80_certified=false`; `release=NO_GO`.

## Perubahan di RPH staging

- Membetulkan **685** draf yang sebelum ini memulakan Aktiviti Utama dengan nombor `2.` agar bermula `1.`; menyusun 5 perenggan panjang Tahun 4 menjadi langkah.
- Menambah aktiviti serta PBD individu untuk **560** RPH yang dahulunya terlalu ringkas, merangkumi Jawi (latihan suku kata/imbuhan, ejaan hamzah, kata pinjaman, teks bertema, khat), al-Quran (bacaan, tasmi, hafazan, hukum tajwid, kefahaman), Akidah, Ibadah, Sirah, Adab dan Hadis.
- Langkah disesuaikan menggunakan **SP dan bidang sedia ada**, tanpa mencipta kod SK/SP, ayat mushaf atau lafaz hadis.
- Metadata `staging_enrichment` menyimpan aktiviti sebelum ubah, bidang pembetulan, serta status `content_expert_approved=false` dan `publication=HOLD`. Sumber asal Word/ZIP tidak ditimpa dan cap `source_sha256` kekal merujuk **sumber asal**, bukan bukti bahan draf baharu disahkan.
- Kes kesalahan topik yang diperbetul: **T3 L087** rujukan dalil *adab tidur* dalam aktiviti ditukar kepada *menuntut ilmu* mengikut SP; **T3 L109** *ikhfa hakiki* yang tersilap dalam aktiviti ditukar kepada *iqlab* mengikut SP; **T5/T6 L111** telah dikelaskan semula sebagai latihan *khat*, bukan hamzah (perkataan Hamzah ialah contoh nama dalam SP).
- Skrip `pi_quality_audit.py` kini memaparkan bilangan pengayaan draf, risiko sumber, liputan ≥3 langkah dan **tidak** menukar angka tersebut menjadi skor kualiti akademik.
- CI GitHub Actions menjalankan ujian katalog, pengasingan enam tahanan, semakan status DRAF, integriti penomboran, ralat topik diketahui, dan penjanaan lejar QA/editor sebagai artefak sementara.

## Tiga Lesson yang tetap memerlukan bukti asal

1. **Tahun 4 Lesson 083 (Hadis):** petikan matan dalam SP sumber mengandungi elipsis / teks tidak lengkap. **Jangan menulis semula matan dari ingatan atau sumber tidak sah.**
2. **Tahun 6 Lesson 137 (Tasmi'):** beberapa surah Juzuk 30 disenaraikan, tetapi tiada julat ayat bernombor bagi setiap surah.
3. **Tahun 6 Lesson 141 (Tasmi'):** isu julat ayat serupa; jangan mereka urutan/ayat.

Enam rekod lain terus ditahan sepenuhnya: Tahun 2 L035; Tahun 6 L006, L014, L018, L060 dan L117.

## Syarat untuk skor 80% sebenar

1. Semak kandungan **setiap** pengayaan dengan DSKP/Buku Teks/Mushaf sahih. Tanda contoh ayat/teks dan halaman buku yang benar-benar digunakan. **77 rekod** masih mempunyai frasa amaran halaman lama yang dapat dikesan oleh audit, tetapi itu bukan jumlah penuh rujukan belum terbukti.
2. Audit ejaan Jawi dan tataletak untuk perubahan baharu oleh guru/pakar. Beri perhatian kepada istilah fiqh, penamaan tajwid, hadis dan contoh nama.
3. Jana semula **Word dan PDF** daripada teks terkini dan sahkan **A4 satu halaman, fon Jawi, keterbacaan** dan pembahagian langkah. Arkib PDF lama **tidak membuktikan** format pembaikan terkini.
4. Uji pemilihan Lesson yang sama, rujukan bahan dan hak akses pada **Telegram dan Web staging**, tanpa mengubah kuota atau database.
5. Kumpul bukti rubrik individu: SK/SP & sumber (25), aktiviti (25), PBD (25), format (15), parity Web–Telegram (10). **≥80/100** memerlukan kelulusan kandungan tanpa ralat kritikal, bukan banyaknya baris.

**Pengesahan:** Semua 696 identiti asal kekal; 690 draf tidak diluluskan secara automatik; enam rekod ditahan selamat; produksi, `main`, database, langganan dan data pengguna tidak diubah.


## Audit penggunaan Buku Aktiviti — tambahan 7 Nov 2026

**Penemuan sumber:** Portal panitia sekolah di domain moe-dl.edu.my menyenaraikan `Buku Aktiviti Pendidikan Islam Tahun 2` dan `Tahun 3` KSSR Semakan, bersama buku teks. Dasar KPM merujuk kepada buku aktiviti yang diperakukan untuk Tahap 1. Namun semakan Drive projek menemui buku teks Pendidikan Islam Tahun 1–6 dan **tidak menemui fail Buku Aktiviti Pendidikan Islam Tahun 2/3**. Maka edisi/nombor halaman tidak boleh dianggap telah diperiksa atau hak mengedar telah diperoleh.

**Pautan rujukan sumber, bukan fail berlesen untuk diterbit semula:**
- https://sites.google.com/moe-dl.edu.my/panitiapendidikanislamtldmkk/buku-teks
- https://sites.google.com/moe-dl.edu.my/lamanbestaripdpc/sumber-bahan/buku-teks-buku-aktiviti
- https://www.moe.gov.my/list-page/497 (SPI KPM Bil. 3 Tahun 2022)

**Keputusan audit fail RPH Tahun 2–6 pada cabang PR #443:**

| Perkara | Bilangan | Keputusan |
|---|---:|---|
| Jumlah Lesson disaring | 696 | 690 aktif DRAF, 6 ditahan |
| RPH Tahun 2/3 aktif | 258 | Tahun 2: 111; Tahun 3: 147 |
| RPH Tahun 2/3 yang menyebut Buku Aktiviti | **0** | Jurang penggunaan; mesti dipadankan |
| Calon pengintegrasian Buku Aktiviti Tahun 2/3 | **191** | Semak latihan/bidang/halaman sebenar dengan SP |
| Lesson tasmi' dengan mushaf sebagai sumber utama | **67** | **Jangan paksa** Buku Aktiviti menggantikan tasmi' |
| RPH Tahun 4–6 aktif | **432** | Buku Aktiviti khusus tidak disahkan; jangan rekaan |
| Halaman/latihan Buku Aktiviti yang betul-betul disahkan | **0** | HOLD; perlu naskhah tulen dan padanan per Lesson |
| Pautan PDF pengguna dalam sistem | **0 baharu** | Hak edar belum disahkan |

**Dasar pengintegrasian selepas bukti halaman ditemui:**
1. Bagi calon Tahun 2/3 (khususnya Jawi, tajwid, Akidah, Ibadah, Sirah, Adab dan Hadis), padankan **Lesson → SP → tajuk bahan → halaman bercetak → nombor latihan/arahan** secara individu; bukan mengikut minggu. Jangan mengambil nombor halaman daripada Buku Teks untuk dilabel sebagai Buku Aktiviti.
2. Tambahkan **satu ayat tepat** dalam Aktiviti Utama atau Penilaian RPH asal, contohnya hanya *selepas terbukti*: `Murid melengkapkan Buku Aktiviti Pendidikan Islam Tahun 2, halaman [DISAHKAN], Latihan [DISAHKAN], dan guru menyemak respons mengikut SP.` Teks berkotak dalam contoh ialah placeholder editorial, **tidak boleh muncul dalam RPH pengguna**.
3. Tiada latihan yang dipaksa untuk tasmi'/hafazan amali. Buku Aktiviti hanya apabila latihan bersesuaian dengan SP yang disahkan, bukan ganti bacaan atau pentaksiran autentik.
4. Tahun 4–6 kekalkan sumber Buku Teks/DSKP dan bahan kendiri; jika naskhah BA lain ditemui, semak kelulusan dan edisi sebelum penggunaan.
5. Sekat ciri `Muat turun Buku Aktiviti` selagi hak edaran, kesahihan sumber, versi dan padanan halaman belum terbukti. Pautan sekolah rujukan awam **bukan** bukti kebenaran host/redistribute PDF dari sistem.

**Artefak staging:** `pi_activity_book_audit.py` menghasilkan `pi_buku_aktiviti_audit_696.json`: identiti, bidang, SP, status cadangan, sumber awam, `page=null`, `exercise=null`, `verified=false`, `can_show_to_teacher=false` bagi 690 DRAF dan rekod tahanan. Ujian regresi mengunci 258/191/67/432 dan larangan nombor halaman palsu.

**Implikasi 80%:** Walaupun aktiviti RPH lain telah diperkaya, skor kualiti **belum disahkan 80%** sehingga kemasukan Buku Aktiviti yang benar-benar relevan disahkan serta ujian Word/PDF A4 selesai. Tiada perubahan live.

## Pemetaan Buku Aktiviti lebih teliti — batch sambungan 7 Nov 2026

Naskhah Tahun 2 dan Tahun 3 ditemui pada portal bacaan awam dan paparan kulit buku berlogo KPM; URL bacaan rujukan:
- Tahun 2: https://anyflip.com/lhat/sebp/
- Tahun 3: https://anyflip.com/lhat/dkui/

**Penemuan kulit buku bukan pemeriksaan latihan/halaman.** Fail Buku Aktiviti asal belum ditemui di Drive projek; kandungan dan halaman bercetak belum dibandingkan dengan 258 SP secara individu. Larangan memuat naik semula buku hak cipta ke GitHub/Render kekal.

### Pemurnian senarai kerja (bukan pembetulan yang sudah diterbit)

| Tahun | Draf aktif | Calon semak latihan BA | Pentaksiran bacaan/hafazan/tasmi' utama |
|---|---:|---:|---:|
| Tahun 2 | 111 | **76** | **35** |
| Tahun 3 | 147 | **98** | **49** |
| **Jumlah** | **258** | **174** | **84** |

Angka 191 daripada audit pertama ialah **senarai kasar** semua draf bukan tasmi' (termasuk 17 RPH yang berfokus khusus kepada bacaan/hafazan). Pemurnian pedagogi ini menurunkan calon padanan latihan bertulis kepada **174** dan memindahkan 17 lagi kepada kumpulan pentaksiran lisan bersama 67 tasmi'. Terdapat **73 RPH Jawi** dalam keutamaan pertama, diikuti 101 RPH Tajwid/Kefahaman/Akidah/Ibadah/Sirah/Adab/Hadis. RPH Tahun 4–6 (432 draf aktif) tidak dipaksa menggunakan naskhah BA Tahun 2/3.

Skrip `pi_ba_match_queue.py` menjana **258 rekod mengikut Lesson + SP asal** dengan topik/kemahiran yang perlu diperiksa dalam buku sebenar: Jawi membaca/membina/menulis, tajwid tertentu, kefahaman al-Quran, serta latihan topik bidang lain. Semua mempunyai `book_printed_page=null`, `book_exercise_id=null`, `match_to_sp_verified=false`, `teacher_sentence=null`, `release=HOLD`.

Cadangan editor bukan latihan daripada buku sebenar. **Tiada ayat Buku Aktiviti ditambah kepada RPH guru, tiada nombor muka surat direka, tiada fail PDF pihak ketiga disalin.** Kesediaan 80% akademik kekal NO-GO sehingga padanan latihan dan halaman disahkan, diikuti ujian Word/PDF A4 serta QA Jawi.

CI: unit test baharu menguatkuasakan bilangan 174/84/73 dan tiada rujukan palsu; fail `pi_ba_candidate_queue_258.json` disimpan sebagai artefak sementara untuk kerja semakan.

## Tambahan bukti sekunder bagi nombor halaman — 7 November 2026

Terdapat **42 padanan calon** yang kini mempunyai petunjuk nombor halaman daripada bahan PdPR atau penerangan video guru: **11 Tahun 2** dan **31 Tahun 3**. Ini **bukan** 42 halaman buku asal yang telah diperiksa atau 42 integrasi siap; keseluruhan kekal `HOLD`.

| Contoh sumber sekunder | Lesson CikguLaju | Halaman yang *dilaporkan* | Status |
|---|---|---|---|
| Video guru Tahun 2, tajuk Kekasihku Rasulullah | T2-L108 | 134–136 | Menunggu semak buku asal |
| Modul PdPR Tahun 3, hukum Ikhfa Hakiki | T3-L097 | 35 | Menunggu semak buku asal |
| Modul PdPR Tahun 3, Jawi menulis imbuhan akhiran | T3-L068 | 52 | Menunggu semak buku asal |
| Modul PdPR Tahun 3, adab menuntut ilmu | T3-L087 | 124–125 | Menunggu semak buku asal |
| Modul PdPR Tahun 3, adab menuntut ilmu | T3-L095 | 126 | Menunggu semak buku asal |
| Nota PdPR Tahun 3, nama Allah Al-Alim dan Al-Hakim | T3-L003 | 65–66 | Menunggu semak buku asal |
| Nota PdPR Tahun 3, akidah Al-Alim dan Al-Hakim | T3-L007 | 67–68 | Menunggu semak buku asal |

Sumber rujukan:
- Modul pembelajaran Tahun 3 (2020): https://anyflip.com/rvse/yhcp/basic
- Arahan PdPR Tahun 3 (2021): https://www.scribd.com/document/521518334/PENDIDIKAN-ISLAM-TAHUN-3
- Video pengajaran Jawi awalan Tahun 3: https://www.youtube.com/watch?v=u-dmxZOf41g
- Video pengajaran Jawi apitan Tahun 3: https://www.youtube.com/watch?v=MSrVyaNELpo
- Video guru Buku Aktiviti Tahun 2, Kekasihku Rasulullah: https://www.youtube.com/watch?v=75s3VFoIe40

**Peraturan:** Modul/video 2020–2021 ialah sumber pelaksanaan guru dan bukan pengesahan cetakan buku edisi 2027. Halaman Buku Teks dan halaman Buku Aktiviti tidak boleh ditukar ganti. Teks RPH tidak akan mengandungi halaman yang belum diperiksa sendiri pada Buku Aktiviti asal. Fail `pi_ba_secondary_evidence.py` menjana `pi_ba_secondary_evidence_42.json`, lengkap `page_number_is_verified_in_original_book=false`, `allow_auto_inject_to_rph=false`, `teacher_sentence=null`. QA menghalang sebarang pelepasan automatik.

**Baki sebenar:** 174 calon Lesson perlu disemak mengikut Buku Aktiviti bercetak/digital yang dapat dibaca, latihan dan SP; 42 daripadanya mempunyai petunjuk halaman sekunder. **0** halaman/latihan diluluskan untuk RPH pengguna, dan tiada hak edar PDF luar dibuktikan.

## Pengesahan bibliografi KPM, kawalan edisi dan tahap akhir kerja semasa

**Sumber rasmi KPM:** https://www.moe.gov.my/storage/files/shares/Banner/E-Katalog%20Buku%20Teks%20KPM.pdf

| Buku arus perdana sekolah kebangsaan | Kod rasmi KPM | Penerbit | Sumber isi kandungan halaman |
|---|---|---|---|
| Buku Aktiviti Pendidikan Islam Tahun 2 | **BA102001** | Dewan Bahasa dan Pustaka | **Belum dapat dibaca/disahkan terus** |
| Buku Aktiviti Pendidikan Islam Tahun 3 | **BA103001** | Dewan Bahasa dan Pustaka | **Belum dapat dibaca/disahkan terus** |

Ini bukti **identiti buku** sahaja, bukan bukti isi latihan/halaman atau kebenaran mengedar buku digital.

**Sumber yang ditolak:** Buku Aktiviti Tahun 2 berlabel BA PAI yang dicetak untuk **KSSRPK Pendidikan Islam Masalah Pembelajaran**, ISBN **978-983-49-1622-0**, tidak boleh digunakan sebagai edisi utama SK KSSR Semakan. Rujukan salah terhad kepada senarai editor `BLOCKED`, dan ujian `test_pi_ba_source_integrity.py` memastikan ia tidak dicampurkan ke cadangan sumber BA arus perdana.

**Bercanggah:** arahan Jawi imbuhan awalan Tahun 3 daripada sumber PdPR 2021 menyatakan p65–66 sedangkan sumber sama turut menggunakan p65–66 untuk Akidah. Rekod **T3-L004** disekat automatik dengan `cross_source_conflict_detected=true`, dan tiada halaman tersebut diperakukan.

**Kerja editor yang telah disiapkan tanpa merosakkan RPH:** 42 petunjuk halaman daripada sumber luar, 258 lejar Lesson/SP, 174 cadangan ayat Buku Aktiviti Jawi **bersyarat** (bukan untuk guru), ujian sumber rasmi dan pengasingan edisi KSSRPK. Fail `pi_ba_sentence_candidates.py` menghasilkan `pi_ba_sentence_candidates_174.json`; setiap calon `injected_into_rph=false`, `book_printed_page=null`, `release=HOLD`. Semua 690 draf dan enam tahanan kekal dalam status asal, tiada perubahan database/API/Web/Telegram.

**Kriteria untuk menyiapkan penerbitan benar-benar:** akses naskhah sebenar berkod BA102001/BA103001, verifikasi **halaman bercetak + arahan latihan + kod SP** bagi 174 calon, semakan ejaan Jawi, paparan Word/PDF A4 dan keseragaman Web–Telegram staging. Ketika bukti ini belum wujud, 0 pemadanan buku aktiviti boleh diluluskan, dan pencapaian 80% akademik belum boleh dinyatakan. Status **NO_GO** diteruskan untuk mengelakkan bahan salah diedarkan kepada guru.
