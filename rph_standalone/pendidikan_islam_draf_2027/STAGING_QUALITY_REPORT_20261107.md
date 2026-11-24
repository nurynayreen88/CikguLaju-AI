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

## Penutupan batch sambungan 7 Nov 2026 — daftar verifikasi 174 Lesson

**Kawalan baharu:** fail `PI_BA_REVIEW_REGISTER_174_STAGING.csv` kini disimpan sebagai fail tetap di cabang staging (selain artefak CI yang luput). Setiap baris memuatkan Lesson, tahun, bidang, fokus, kod SP, kod buku KPM, petunjuk halaman yang pernah disebut oleh sumber PdPR, URL asal, dan ruang **kosong** untuk bukti halaman bercetak/latihan serta kelulusan pakar.

| Tahap semakan | Bilangan | Makna |
|---|---:|---|
| Calon latihan Buku Aktiviti T2/3 | **174** | 76 Tahun 2, 98 Tahun 3 |
| Petunjuk halaman sekunder daripada bahan guru | **42** | 42 pautan disimpan, belum bukti buku asal |
| Tanpa petunjuk halaman | **132** | Semakan terus buku diperlukan |
| Konflik rujukan sumber | **1** | T3-L004: p65–66 Akidah/Jawi dalam arahan PdPR |
| Bukti halaman/latihan buku sebenar disahkan | **0** | Jangan menerbitkan nombor halaman |
| RPH guru yang mendapat integrasi BA diluluskan | **0** | Penulisan editor sahaja |

**Pembetulan CI sebenar:** Workflow terdahulu boleh lulus walaupun senarai artefak masih memanggil `pi_ba_secondary_evidence_21.json`, sedangkan skrip menghasilkan `pi_ba_secondary_evidence_42.json`; fail integriti sumber dan 174 calon ayat juga tercicir daripada senarai muat naik. Workflow staging kini menyemak kewujudan **sembilan** fail yang tidak kosong sebelum artefak berjaya dimuat naik. CSV sumber tetap pula diuji terhadap kesemua 174 ID, 42 URL, identiti buku BA102001/BA103001 dan status HOLD.

**Had capaian:** Carian buku asal menemui paparan FlipHTML5/AnyFlip, Scribd dan pautan muat turun melalui portal panitia, tetapi halaman latihan dalaman tidak dapat diambil atau dilihat dengan cukup andal. Teks OCR Scribd bagi Jawi juga tidak memadai untuk pengesahan arahan latihan. Katalog KPM mengesahkan identiti BA102001 dan BA103001 dalam **E-Katalog 2023** sahaja; ia bukan bukti kandungan halaman edisi 2027. Oleh itu, tiada nombor halaman dimasukkan secara andaian ke dalam RPH.

**Penanda selesai yang sah:** Semua kerja penyediaan dan pengasingan data sudah dijalankan serta diuji dalam PR #443; **pengintegrasian latihan ke RPH, penilaian kualiti 80%, ujian Word/PDF A4, semakan pakar Jawi dan parity Telegram–Web belum dapat diperakukan.** Jangan anggap artefak CI berjaya sebagai lesen menerbitkan bahan tersebut.

## Tambahan kawalan kesahihan petunjuk BA — 7 Nov 2026

Setelah membuka dan membaca **dokumen PdPR asal Tahun 3** (bukan scan buku aktiviti), pemeriksaan tambahan membezakan **buku teks** daripada **buku aktiviti**. Sumber PdPR 2021, sebagai contoh, menyatakan Buku Teks **halaman 48** dan Buku Aktiviti **halaman 50** bagi Jawi imbuhan awalan; modul PdPR 2020 pula menyatakan Buku Teks **34–35** dan Buku Aktiviti **35** bagi Ikhfa Hakiki. Pemetaan petunjuk ini hanya membantu editor mencari halaman sebenar, **bukan lesen mengisi halaman dalam RPH**.

**Pengelasan 42 petunjuk sumber yang telah tersimpan:**

| Jenis sumber / risiko | Calon Lesson | Kegunaan |
|---|---:|---|
| Dokumen PdPR guru 2020/2021 dengan halaman BA dinyatakan | **27** | Keutamaan pemeriksaan terus pada buku BA |
| Bahan PdPR lain | **6** | Perlu audit konteks/jenis buku |
| Petunjuk video yang belum diperiksa pada naskhah | **8** | Tidak boleh meneka halaman latihan daripada tajuk video |
| Konflik sumber | **1** | T3-L004: sumber PdPR sama melabel p65–66 sebagai Akidah dan Jawi |
| **Jumlah** | **42** | **0 halaman disahkan pada buku asal, 0 RPH diterbitkan** |

Fail kawalan baharu: `pi_ba_provenance_review.py` dan `test_pi_ba_provenance_review.py`; artefak CI `pi_ba_provenance_42.json`. `pi_ba_verification_register.py` memindahkan kelas asal setiap petunjuk ke lejar JSON/CSV. Fail kekal `PI_BA_REVIEW_REGISTER_174_STAGING.csv` kini melabel lajur **URL sumber SEKUNDER (bukan buku asal)** dan **Jenis sumber sekunder**, supaya 42 pautan PdPR/video tidak dilabel sebagai bukti cetakan asal. 132 calon lain masih tiada petunjuk halaman.

Sumber pemeriksaan PdPR (bukan buku yang boleh diedarkan semula):
- https://anyflip.com/rvse/yhcp/basic — modul PdPR Pendidikan Islam Tahun 3, 2020 (termasuk p35 Ikhfa, p52 Jawi, p124–125 Adab)
- https://www.scribd.com/document/521518334/PENDIDIKAN-ISLAM-TAHUN-3 — tugasan PdPR Tahun 3, 2021 (membezakan halaman Buku Teks dan Buku Aktiviti)

**Pintu kelulusan kekal tertutup**: status `NO_GO` untuk 174 latihan sehingga benar-benar menyemak perintah latihan dan nombor halaman pada BA102001/BA103001, ejaan Jawi dan kesesuaian SP. Selepas itu barulah boleh menulis ayat BA yang tepat bagi Lesson masing-masing, uji satu halaman Word/PDF dan semak semula parity staging Web–Telegram. Tiada muat turun PDF pihak ketiga dihoskan.

## Sambungan mutu RPH tanpa mengubah sumber — 7 Nov 2026

**Masalah nyata:** 690 RPH aktif masih mempunyai **523 baris tambahan** dalam ruangan Bahan, termasuk nota pengesahan, halaman calon dan catatan pembetulan dalaman. Contoh: T2-L067 "PEMBETULAN DIAUDIT", T2-L003 "halaman khusus belum dipadankan", T3-L003 "Rekod padanan SP buku teks lama", T6-L001 "Pemetaan ... memerlukan semakan visual".

**Pembetulan berasingan:** Fail `pi_editor_material_projection.py` menghasilkan **690 paparan draf editor**. Paparan itu hanya mengekalkan senarai bahan teras dalam `display_fields.bahan`, tetapi menyimpan **semua 523** nota asal dalam `editor_only_material_notes` bersama hash sumber `source_material_sha256` sebagai bukti asal tidak diubah. SK, SP, objektif, aktiviti, PBD dan penutup tidak dipinda.

| Tahun | Draf aktif | Nota disimpan untuk editor |
|---|---:|---:|
| 2 | 111 | 127 |
| 3 | 147 | 149 |
| 4 | 151 | 54 |
| 5 | 143 | 53 |
| 6 | 138 | 140 |
| **Jumlah** | **690** | **523** |

Ujian baharu membandingkan 690 paparan dengan JSON sumber, memastikan semua nota kekal tetapi tidak bercampur dalam senarai bahan guru, dan semua enam rekod asal ditahan. `year2.json` hingga `year6.json` **tidak diubah**, dan projek Telegram, Web serta database tidak disentuh. Pratonton ini **untuk editor sahaja**, bukan untuk diedarkan kepada guru.

**CI:** GitHub Actions **Run #72 LULUS**; 11 fail artefak diuji kewujudan dan dimuat naik. https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42320287598

**Had semakan Buku Aktiviti:** Buku KSSR Semakan BA102001/BA103001 dikenal pasti dalam katalog KPM dan disenarai oleh portal sekolah. Scan teks pada salinan web Scribd tidak boleh digunakan untuk memastikan tulisan Jawi serta arahan latihan, manakala akses halaman buku sebenar melalui viewer/download tidak stabil. Oleh itu, **0** halaman dan arahan Buku Aktiviti telah diluluskan untuk dimasukkan ke dalam RPH. Penambahbaikan ini **bukan** pengesahan kualiti 80%, dan semua 690 draf kekal HOLD.


## Sambungan audit 7 Nov — PBD individu dan rekod halaman lama (batch terkini)

Pemeriksaan **semua 690 RPH draf** dalam cabang staging menemukan dua kelemahan yang sebelum ini tidak mempunyai daftar keutamaan gabungan:

| Perkara yang dikesan secara automatik | Tahun 2 | Tahun 3 | Tahun 4–6 | Jumlah |
|---|---:|---:|---:|---:|
| Frasa generik PBD `برداسركن كريتيريا دالم SP` | 14 | 29 | 0 | **43** |
| Nota halaman terdahulu yang masih memerlukan semakan sumber | 77 | 0 | 0 | **77** |
| Rekod yang mempunyai kedua-dua isu | 12 | 0 | 0 | **12** |

Oleh itu terdapat **108 Lesson unik** yang diberi keutamaan `P2_PBD_OR_PAGE` (43 + 77 − 12). Ini **penemuan audit mekanikal**, tidak bermaksud semua RPH lain telah mempunyai PBD tepat atau halaman buku yang sah. Semakan manual DSKP, buku teks, mushaf, Buku Aktiviti dan ketepatan bahasa tetap wajib.

Fail baharu `pi_content_review_queue.py` menjana daftar **696 Lesson** dalam JSON dan CSV, dengan status berasingan:

- `P0_HELD`: 6 rekod tanpa kandungan pengajaran yang dibuka.
- `P1_CRITICAL_SOURCE`: 3 RPH sumber hadis/tasmi' tidak lengkap.
- `P2_PBD_OR_PAGE`: 108 rekod gabungan PBD terlalu umum atau nota halaman terdahulu.
- `P3_ENRICHMENT_REVIEW`: RPH pengayaan lain untuk semakan pakar.
- `P4_FULL_CONTENT_REVIEW`: RPH lain tetap memerlukan audit akademik dan Word/PDF.

Setiap baris menyimpan identiti Lesson, bidang, SP asal, tanda isu serta tindakan semakan editor; tiada teks sumber asal atau halaman buku direka. CSV menggunakan UTF-8 BOM agar tulisan Jawi boleh dibuka dalam aplikasi lembaran kerja tanpa rosak.

**Kawalan:** semua 696 rekod dilarang diterbitkan (`can_publish=false`), peratus akademik kekal `null`, dan `quality_80_certified=false`. Workflow CI akan menjana dua artefak tambahan `pi_content_review_queue_696.json` dan `pi_content_review_queue_696.csv`, kemudian mengesahkan 13 artefak audit sebelum muat naik. Fail RPH asal, `main`, database, kuota, Telegram dan Web tidak disentuh.

**Skop:** Katalog audit ini hanya meliputi Tahun 2–6. Tahun 1/KP2027 tidak terkandung dalam 696 rekod dan tidak boleh dianggap sudah siap.


## Sambungan 7 Nov — 43 PBD dikemaskini secara langsung dalam draf (STAGING)

Selepas penemuan 43 ayat PBD terlalu umum, kini **14 RPH Tahun 2 dan 29 RPH Tahun 3** telah **dikemas kini pada medan `pentaksiran` draf**. Setiap ayat baharu menerangkan hasil SP yang diperhatikan, bukti murid (contohnya padanan kad, bacaan, lakonan, peta cerita, simulasi atau respons bertulis), dan rekod guru untuk bimbingan individu. Pemeriksaan awal memastikan tiada petikan mushaf/hadis, nombor halaman Buku Aktiviti atau kod SP baharu dicipta.

| Perkara selepas pindaan | Bilangan | Tafsiran |
|---|---:|---|
| PBD templat generik lama yang masih dipaparkan dalam draf T2/T3 | **0** | 43 ayat lama diganti dengan ayat PBD berfokus |
| PBD berfokus dalam draf yang **menunggu semakan pakar** | **43** | T2 14 + T3 29; bukan automatik `READY` |
| Teks PBD lama disimpan dalam `staging_pbd_refinement.original_pentaksiran` | **43** | Pindaan boleh dibanding/diundur pada peringkat rekod |
| Nota halaman buku teks lama masih belum disahkan | **77** | Tidak diisi nombor halaman palsu |
| Senarai keutamaan gabungan PBD + halaman | **108 Lesson unik** | 12 daripada 43 PBD turut mempunyai isu halaman lama |
| RPH dengan pengesahan pakar Jawi bagi pindaan ini | **0** | Semua `content_expert_approved=false`, `jawi_orthography_approved=false` |

Pindaan tidak menyentuh SK, SP, objektif, aktiviti asal, buku teks, material Buku Aktiviti, atau enam rekod tahanan. Identiti katalog tetap 696, dengan 690 draf dan enam tahanan. Pembetulan ialah **pengayaan draf kandungan sebenar** namun belum membuktikan skor akademik ≥80% kerana sumber/Jawi/DSKP, pentaksiran dan Word/PDF belum diperakui. `pi_quality_audit.py` dan `pi_content_review_queue.py` mengasingkan bendera `PBD_SP_SASARAN_BELUM_DISAH_PAKAR` daripada bendera teks generik lama serta mengekalkan baris ini dalam keutamaan P2.

**CI Run #85 lulus**: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42322765025. Fail pengguna `main`, DB, Telegram, Web dan Render tidak diubah. PR #443 kekal **DRAFT / HOLD / NO_GO**.


## Semakan penyelarasan tulisan Penutup — 7 Nov 2026

Audit tambahan bagi **690 RPH draf aktif** mengesan **690 bahagian Penutup mengandungi tulisan Rumi** sementara SK/SP, objektif dan sebahagian besar aktiviti ditulis dalam Jawi. Ini **perbezaan gaya skrip yang perlu disahkan dengan format Pendidikan Islam CikguLaju**, bukan bukti kesalahan isi secara automatik.

`pi_quality_audit.py` kini menanda `PENUTUP_RUMI_SEMAK_PENYERAGAMAN_JAWI` bagi setiap rekod terlibat. Tiada transliterasi pukal dijalankan kerana istilah ibadah, nama surah, lafaz hadis, makhraj, ejaan dan keperluan fon Amiri memerlukan semakan khusus. Teks Penutup asal tidak diubah; QA dan kelulusan akhir masih **NO_GO**.

Keutamaan selepas penemuan baharu: pengesahan Jawi/Penutup, **43 PBD spesifik yang belum disemak pakar**, **77 rujukan halaman terdahulu**, **174 Buku Aktiviti Tahun 2/3** dan ujian Word/PDF terkini.


## 7 November 2026 — ujian fizikal Word/PDF penuh + kumpulan penutup Jawi

### Ujian fizikal, menggunakan draf semasa, **bukan penjana runtime**

Tambah `pi_word_pdf_print_audit.py` dan workflow terasing `physical-word-pdf-a4`.
Ujian membina DOCX sementara daripada medan terkini, mengekalkan semua teks SK/SP, objektif, induksi, aktiviti, PBD dan penutup, kemudian menukar ke PDF menggunakan **LibreOffice + fon Amiri**. Ruangan bahan untuk pratonton hanya menggunakan baris sumber pertama, manakala nota editor yang lain tidak diedarkan dalam bahan guru.

| Tahun | Katalog | Ditahan sepenuhnya | Ditahan kerana sumber kritikal | Layak ujian cetakan | A4 satu halaman |
|---|---:|---:|---:|---:|---:|
| 2 | 112 | 1 | 0 | 111 | 111 |
| 3 | 147 | 0 | 0 | 147 | 147 |
| 4 | 151 | 0 | 1 | 150 | 150 |
| 5 | 143 | 0 | 0 | 143 | 143 |
| 6 | 143 | 5 | 2 | 136 | 136 |
| **Jumlah** | **696** | **6** | **3** | **687** | **687** |

**Run #92 lulus:** https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42323952446. Sebanyak **687/687 PDF satu halaman A4**, **0** melebihi satu halaman, **0** gagal penukaran, dan **0** PDF tanpa teks boleh diekstrak; jumlah aksara teks diekstrak per PDF ialah 958–2219, mengikut laporan artefak asal. Artefak hanya JSON/CSV keputusan, bukan dokumen guru. Pengiraan di sini **bukan** bukti fon Jawi bersambung dengan betul pada setiap baris, bukan ujian bot/PDF native, bukan penilaian rupa 100% dan **bukan** kelulusan akademik.

**Run #95 lulus**, termasuk semakan baru pengelompokan penutup: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42324172878.

### Penutup Rumi — senarai semakan pakar yang disatukan

`pi_closing_jawi_review_queue.py` mengekalkan **690 teks penutup asal**, mengelompokkan kepada hanya **78 teks unik** (tanpa mengubah draf), menghasilkan `pi_closing_jawi_review_78.json` dan `.csv` dalam CI, bersama ID semua Lesson yang berkongsi teks. Setiap penggantian Jawi, nama penyemak dan status sumber/Word/PDF dibiarkan kosong sehingga semakan sebenar. **0 penutup diterjemah/diterbitkan secara automatik**.

### Status pelepasan selepas batch penuh

- **43/43 ayat PBD generik dikenal pasti telah dipinda sebagai draf SP-spesifik** (T2 14; T3 29). **43 masih menunggu kelulusan isi/Jawi**; teks asal dipelihara.
- **77 nota halaman** sumber terdahulu belum disahkan (T2), dan **174 calon penggunaan Buku Aktiviti T2/T3** masih belum diberi halaman/latihan asal yang terbukti. Carian nama tepat `Buku Aktiviti` + `Pendidikan Islam`, kod `BA102001`, `BA103001` dalam Drive projek tidak menemui naskhah.
- **6 rekod held** kekal kosong; **3 sumber kritikal** kekal tidak boleh disahkan; tidak dibenarkan mengarang teks hadis atau julat ayat.
- **Tahun 1 tidak termasuk** katalog 696 ini. RPH Tahun 1/KP2027 memerlukan laluan semakan tersendiri.
- **Tiada** semakan visual Jawi pada dokumen PDF cetak sebenar untuk semua rekod, ujian perbandingan Word/PDF native Telegram/Web dan kelulusan kandungan pakar bagi 690 draf.
- **Peratus kualiti akademik bertauliah kekal belum dinilai**, tidak boleh dilabel ≥80%, READY, atau dihantar ke pengguna. `main`, DB, kuota, pembayaran, Web dan Telegram kekal tanpa perubahan. Keputusan keselamatan penerbitan: **STAGING / HOLD / NO_GO**.

**Syarat akhir yang perlu dibuktikan sebelum penerbitan:** naskhah BA dan Buku Teks yang boleh diperiksa mengikut halaman asli, semakan pakar Jawi dan isi setiap Lesson, penyelesaian 9 rekod tahanan/risiko, ujian visual Word/PDF + generator natif Web/Telegram, dan pengesahan Tahun 1 secara berasingan.


## Sambungan 7 November — cadangan penutup Jawi 690/690 + kawalan READY ikut Lesson

**Baki kerja editorial menyediakan calon penutup telah dilengkapkan**, bukan kerja pengesahan isi:

| Perkara | Bilangan | Status |
|---|---:|---|
| Penutup Rumi dalam sumber asal | 690 | Asal dipelihara, tidak ditimpa |
| Teks penutup Rumi unik | 78 | Dipetakan 1→banyak Lesson |
| Draf **cadangan** penutup Jawi | **78/78** | **690/690 penggunaan** kini ada calon |
| Calon penutup Jawi diluluskan pakar | **0** | Bukan bahan pengguna |
| Fail semakan individu dengan SK/SP sumber asal | **690/690** | Setiap Lesson ada calon & bukti hash sumber |
| Tahanan penuh | **6** | Tidak mempunyai medan isi RPH |
| Sumber hadis/ayat kritikal tidak lengkap | **3** | Tidak boleh ditampilkan kepada guru |
| Calon Buku Aktiviti yang perlu pengesahan latihan/halaman | **174** | Tiada halaman latihan disahkan |

Fail baharu (hanya staging): `pi_closing_jawi_candidates_batch2.py` (23 kumpulan/635 penggunaan), `pi_closing_jawi_candidates_complete.py` (78 kumpulan/690 penggunaan), `pi_jawi_closing_lesson_review.py` (690 baris SP/objektif semakan) serta ujian regresi masing-masing. CI menghasilkan `pi_closing_jawi_candidates_690.json/.csv` dan `pi_jawi_closing_lesson_review_690.json/.csv`. Kandungan Jawi ialah **draf editorial yang perlu disemak semula**, termasuk ejaan, istilah agama, pernyataan hasil PdP dan kaitan dengan SP. Fail sumber `year2.json`–`year6.json` **tidak ditimpa untuk penutup Jawi**.

Bagi mencegah anggapan bahawa 100% calon bererti 100% mutu, `pi_release_readiness.py` memberikan pengiraan tahunan yang berasingan: katalog 696 / 690 draf / 6 tahan / 3 sumber kritikal / 687 layak **pratonton editor sahaja**; **0 RPH baharu diluluskan pakar** dan **0 boleh diterbitkan**. Liputan mekanikal tiga langkah 99.57% bukan markah kualiti akademik.

**Sumber Buku Teks Tahun 2 (KSSR Semakan 2017):** dokumen asli dalam Google Drive projek telah disemak secara visual pada isi kandungan dan halaman akhir. Audit `pi_t2_textbook_toc_review.py` kini menyimpan 77 nota lama/18 corak: 74 julat bab selari dengan sempadan pada isi kandungan, 3 catatan **T2-L102, L105, L108** melebihi halaman bercetak terakhir 138 (lama 133–140; cadangan editorial 133–138). Nota asal kekal. Ini **bukan** pengesahan halaman Lesson/SP, dan **bukan** bukti kebenaran mengedar PDF.

Ujian fizikal cetakan editor (Run #92/#95/#108) telah membuktikan 687/687 draf yang diuji menjadi satu halaman A4 dalam penjana percubaan. Ia belum menguji Jawi visual dan penjana sebenar Telegram/Web. Tiada pengesahan Jawi atau kualiti akademik 80% dicapai secara sah. **Kekal DRAFT/HOLD/NO_GO**, DB dan produksi tidak berubah.


## 7 November — sumber primer DSKP Tahun 2 + Buku Teks Tahun 2 dan Tahun 3

### Bukti DSKP Tahun 2 (KSSR)

Naskhah `GuruBesar_DSKP_Pendidikan_Islam_Tahun_2.pdf` dimuat turun dari Google Drive projek (file ID `1m6UG8t7tiCjLdnOo6vRj2jI4lNMniOUr`; SHA-256 `dd4804c118e78c5a4fed1521adf750983c6d119a310cf736b751d4994bc67dac`). PDF 64 halaman dengan **83 kod SP tiga aras** yang boleh diekstrak daripada lapisan teks. DSKP halaman PDF **55**, bercetak **43**, mengandungi **5.4.1–5.4.4** bagi adab mengasihi Rasulullah.

- Daripada **111 draf Tahun 2** (satu rekod ditahan), **81** menggunakan kod SP tiga aras; semua **192 kemunculan kod** (76 kod unik) wujud dalam indeks 83 kod sumber DSKP. **Tiada kod tidak dikenali.**
- **30** draf lain ialah tasmi'/bacaan al-Quran berasaskan julat surah dan ayat. Tiada kod SP tiga aras dipaksa; semakan sempadan ayat/mushaf masih perlu.
- Padanan **kod** sahaja **tidak** mengesahkan ketepatan penyataan SP, pilihan PdP, objektif atau penilaian.

**Dua pembetulan bersumber:** T2-L105 dan T2-L108, pada SP **5.4.3**, sebelum ini menulis `ادب` (adab) tetapi DSKP menggunakan `ادب٢` (adab-adab); teks SP dan objektif dalam draf staging telah dibetulkan. Setiap rekod menyimpan **SP dan objektif asal** sebelum pindaan dalam `staging_direct_dskp_book_crosswalk`, bersama ID naskhah, halaman dan status HOLD. SK, aktiviti dan nota sumber lama tidak ditimpa.

### Bukti Buku Teks Tahun 2 (KSSR Semakan)

Buku sumber Drive `GuruBesar_BukuTeks_Pendidikan_Islam_T2_SK.pdf` (ID `1VDXKCAyEveZCkhMLVVIyl3qg2sZhk9KP`; SHA-256 `f9e2a3469c363cb233eb551d2a33c7979dbc836c7efa623e13046c74219ff654`) diperiksa melalui halaman buku bercetak **134–138** yang memaparkan kod SP:
- **5.4.1:** halaman 134, 137, 138
- **5.4.2:** halaman 134, 138
- **5.4.3:** halaman 135, 137
- **5.4.4:** halaman 136, 138

Tiga draf yang sebelum ini mempunyai julat lama **133–140** kini turut mempunyai **rujukan buku yang disaksikan terus** pada baris pertama BAHAN: **T2-L102 → 134**, **L105 → 134–135**, **L108 → 135–136**. Baris asal dan nota julat lama dipelihara dalam rekod bukti. Padanan kod pada footer buku **tidak sama dengan** pengesahan setiap aktiviti, teks dalil atau PBD; status masih HOLD.

### Buku Teks Tahun 3: Jawi imbuhan awalan

Sumber Drive `GuruBesar_BukuTeks_Pendidikan_Islam_T3_SK.pdf` (ID `1DNXL1vmN3ERz6o4_7jcCVc9m3E42JDSY`; SHA-256 `fcc36cbe9ed64aa7d8cbf17dbf105b73c2e34e4fc988e65d63a12fa2386a4f17`) diteliti pada **PDF 31–34**; halaman tercetak **46–51** ialah Unit Jawi imbuhan awalan yang memaparkan kod **7.1.1/7.1.2** di footer. **PDF halaman 34** sudah beralih ke unit imbuhan **akhiran**, bukan awalan.

- **6 Lesson bacaan SP 7.1.1** (T3-L004, L008, L012, L016, L020, L024): rujukan Buku Teks PI T3 halaman **46–51** ditambah pada baris bahan draf.
- **6 Lesson penulisan SP 7.1.2** (T3-L028, L032, L036, L040, L044, L048): rujukan halaman **49–51** ditambah pada baris bahan draf.
- **6 catatan lama** untuk kumpulan bacaan masih mengandungi calon **PDF halaman 34** yang tersasar ke unit seterusnya; catatan itu diasingkan sebagai rekod audit, **tidak digunakan sebagai rujukan baharu**.
- Sasaran awalan yang khusus dalam setiap RPH masih **belum disemak pakar secara individu**, dan DSKP Tahun 3 belum disahkan melalui kod numerik daripada sumber berkenaan. PDF DSKP Tahun 3 yang diperiksa mengekstrak prosa, tetapi **tidak mengekstrak kod SP numerik** dengan boleh dipercayai; tiada angka pengesahan kod Tahun 3 direka.

### Status selepas pembaikan sumber

| Kerja | Liputan bukti | Keputusan |
|---|---:|---|
| Kod SP Tahun 2 wujud dalam DSKP | 81/81 RPH berkod | Disemak kewujudan kod sahaja |
| SP/objektif 5.4.3 Tahun 2 dibetulkan | 2 RPH | Teks asal dipelihara |
| Rujukan muka surat Buku Teks Tahun 2 | 3 RPH | Sumber diperiksa, kelulusan PBD masih HOLD |
| Rujukan Unit Jawi Buku Teks Tahun 3 | 12 RPH | Sumber diperiksa, contoh khusus masih HOLD |
| Nota PDF Tahun 3 tersasar ke unit berikutnya | 6 nota | Ditanda, tidak dikeluarkan kepada guru |
| Halaman latihan Buku Aktiviti yang disahkan | 0/174 calon | HOLD |
| Mutu akademik ≥80% diperakui | — | **Belum boleh diperakui** |

Fail audit staging: `pi_t2_dskp_code_presence.py`, `pi_t2_54_direct_source_review.py`, `pi_t3_awalan_book_review.py` dan ujian masing-masing. GitHub Actions menghasilkan lejar JSON/CSV, tidak menyimpan naskhah buku teks atau DSKP. Tiada perubahan ke main, DB, Telegram, Web, pembayaran atau kandungan produksi. **PR #443 kekal DRAFT/HOLD/NO_GO**.


### Tambahan Tahun 3 — kod SP pada footer Buku Teks berbanding DSKP sebenar

Pada buku sumber asal Tahun 3 (Drive `GuruBesar_BukuTeks_Pendidikan_Islam_T3_SK.pdf`; SHA-256 telah dicatat di atas), lapisan teks **85 halaman PDF** menghasilkan **83 kod SP unik** daripada penanda halaman buku. Katalog draf **147 Lesson Tahun 3** pula mempunyai **110 Lesson berkod SP** dan **37 Lesson tasmi'/julat ayat tanpa kod tiga aras**. Perbandingan yang mengehadkan tuntutan kepada *kewujudan kod pada buku* menunjukkan:

- **109/110 Lesson berkod** menggunakan kod yang dapat ditemui pada penanda halaman Buku Teks sumber.
- **1 pengecualian: T3-L146 menggunakan SP `6.4.3`**, yang tidak terdapat pada penanda SP bawah halaman Buku Teks diperiksa (PDF 82–85). Ini **bukan bukti kod rasmi salah**. Semakan visual DSKP Pendidikan Islam Tahun 3, file ID `1tjcWRrfcAGk-Y_OpzeQhO253hunaz9RA`, **PDF halaman 51 / bercetak 39**, **mengesahkan SP 6.4.3 memang tertera** sebagai piawaian menerangkan sunnah Rasulullah daripada aspek perkataan dan perbuatan.
- Bagi **T3-L146**, rujukan kepada Buku Teks Tahun 3 halaman tercetak **142–146** dimasukkan di baris bahan staging; medan asal dilindungi dalam `staging_source_sp6433_review`. Pentaksiran khusus masih HOLD.
- Satu lagi isu editor yang ditemukan pada Lesson 146: **objektif kedua menggunakan kata kerja menyenaraikan** sedangkan SP **6.4.4 menyebut merumus**. Ini ditanda sebagai semakan keselarasan aras objektif, **tidak** diperbetulkan secara anggaran.
- Kedua-dua kumpulan tasmi' Tahun 2 (**30**) dan Tahun 3 (**37**) tidak diberikan kod SP tiga aras buatan. Fail `pi_t3_book_footer_code_audit.py` bersama ujian regresi menghasilkan lejar 147 Lesson secara review-only.

**Sempadan bukti:** penanda kod pada Buku Teks bukan DSKP teks penuh; bukti bahawa 6.4.3 wujud dalam DSKP adalah pengesahan halaman tunggal, bukan semakan semua kod Tahun 3. **0** Lesson diluluskan oleh pakar, **0** bahan baharu boleh diterbitkan, PR kekal **DRAFT / HOLD / NO_GO**.


## 7 November 2026 — semakan lanjut DSKP Tahun 3 dan sumber Hadis Tahun 4

### T3-L146 — SP 6.4.3, 6.4.4 dan 6.4.5

DSKP asal Pendidikan Islam Tahun 3 di Drive (ID `1tjcWRrfcAGk-Y_OpzeQhO253hunaz9RA`, bercetak **39**, PDF **51**) telah diperiksa **secara visual**. Penyataan SP 6.4.4 meminta murid *merumus kepentingan* mengamalkan sunnah Rasulullah; SP 6.4.5 meminta murid *mengamalkannya*.

Pembetulan **draf sahaja** dalam `year3.json`:
- Objektif 2 diubah daripada *menyenaraikan* kepada **merumus** (SP 6.4.4).
- Objektif 3 ditambah: **mengamalkan satu sunnah Rasulullah** (SP 6.4.5).
- Empat aktiviti PdP kini merangkumi contoh sunnah perkataan/perbuatan, perbincangan rumusan, padanan dan amali situasi.
- Pentaksiran lama yang mengandungi **soalan orang paling bakhil** dan **aktiviti bersyukur** tidak berkaitan dengan SP diganti dengan PBD membuktikan 6.4.3–6.4.5 melalui penerangan, rumusan dan demonstrasi.
- Teks objektif, aktiviti dan PBD asal dipelihara sepenuhnya di `staging_dskp_l146_alignment`. Tiada penyataan SK/SP dipadam, dan status **HOLD** kekal. Ejaan Jawi draf dan padanan pedagogi akhir tetap memerlukan penyemak bertauliah.

### T4-L083 — petikan hadis memuliakan tetamu dipulihkan daripada sumber primer

Buku Teks Pendidikan Islam Tahun 4 dalam Drive (ID `17x1icc3hkoutTopyjbyi6kIfmxksBo1R`, SHA-256 `dfcd7720c1adc7c6aaec6cfae55ea66a2db2605288359d4f10acef2000ad7451`) **PDF halaman 57 / bercetak 51** mengandungi petikan hadis memuliakan tetamu. DSKP asal dalam Drive (ID `1r5IexeLxm5L025Abj_V-r6NRlDBeoQdJ`, SHA-256 `e30b48edf947002afb466605d8c3375e2876265dcfb73c2161f0e0416669351b`) **PDF 39 / bercetak 27** turut memaparkan petikan tersebut dalam SP 2.1.1.

Draf RPH yang sebelum ini mempunyai ruang matan kosong kini menerima **petikan sumber dengan elipsis yang disengajakan**: `... وَمَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيُكْرِمْ ضَيْفَهُ`. **Ini bukan tuntutan bahawa seluruh teks riwayat telah ditranskripsikan atau disahkan.** Nota sumber, rujukan halaman dan fail asal disimpan, sementara satu langkah PdP yang terlalu ringkas diganti **3 langkah** dengan PBD bacaan dan kefahaman yang relevan.

Teks asal semua medan RPH disimpan di `staging_hadith_original_source_verified.original_fields_preserved`. **T4-L083 kekal di bawah `staging_source_review_required=true`**, tidak layak pratonton guru sehingga semakan Jawi, lafaz dan isi oleh pakar. Fail audit `pi_t4_hadith_source_audit.py` menguji bukti dan melarang dakwaan kelulusan automatik.

### Keputusan ukuran selepas dua pembetulan

- **690** RPH mempunyai draf, **6** rekod masih ditahan tanpa isi.
- **688/690** draf mempunyai **3 langkah PdP atau lebih** (liputan **99.71%**, hanya ukuran mekanikal, bukan mutu akademik).
- **3** rekod kekal kritikal untuk pelepasan: T4-L083 (*petikan sumber ditemui, pakar belum sahkan*), T6-L137 dan T6-L141 (*julat ayat tasmi' belum dibuktikan*). **687** kekal boleh menjalani pratonton/cetakan *editor sahaja*; T4-L083 sengaja tidak dibenarkan.
- Sumber DSKP Tahun 6 (Drive `GuruBesar_DSKP_Pendidikan_Islam_Tahun_6.pdf`) dan Buku Teks Tahun 6 (`6 BUKU TEKS PENDIDIKAN ISLAM TAHUN 6 KSSR SEMAKAN.pdf`) dikenal pasti dalam Drive; buku teks yang diperiksa bersifat **imej sahaja** untuk ekstrak teks. Tiada julat ayat spesifik diandaikan atau ditulis tanpa pengesahan halaman.
- **174** calon Buku Aktiviti T2/T3 kekal tanpa latihan/halaman asal yang disahkan.
- **0** kelulusan akademik/Jawi formal, **0** RPH baru READY atau perubahan DB/Web/Telegram. **PR #443 DRAFT/HOLD/NO_GO** sehingga syarat pelepasan benar-benar dipenuhi.


## 7 November malam — dua tasmi' Juz 30 Tahun 6: pemulihan aktiviti tanpa mereka ayat

Sumber projek **RPT Pendidikan Islam Tahun 6 2027** (Drive ID `1T380Ot_gG58JhxanELMM0z-gr6wmSJcL`, SHA-256 `b39a07b2dd7ef6062912f12fd43e63f87a98b13bde3885c925e88a37dac70e5b`), halaman PDF **48** dan **49**, menyenaraikan:
- **PdP 137** (halaman PDF 48): Juz 30 — Surah `عبس`, `التكوير`, `الإنفطار`, `المطففين`.
- **PdP 141** (halaman PDF 49): Juz 30 — Surah `الطارق`, `الأعلى`, `الغاشية`, `الفجر`.

**Kedua-dua halaman RPT hanya menyenaraikan surah, tanpa nombor ayat mula/akhir.** Ini tidak memberi lesen untuk mengandaikan bacaan keseluruhan empat surah boleh ditasmi' kepada semua murid dalam dua jam. **DSKP KSSR Pendidikan Islam Tahun 6** (Drive ID `1pasG1F0ThshBUNoyLtQCD867bIkhekTZ`, SHA-256 `fd12636abb8b220623ec8c33a0c12261c7f27adc44c02efc5ee2ac04b71fea45`), halaman bercetak **19/PDF31**, pula memperihalkan SK 1.1 *Surah al-Sharh*; Juz 30 empat-surah pada RPT ini ialah **perancangan tasmi' tambahan**, **bukan kod SP tiga aras DSKP yang boleh direka**. Buku Teks Tahun 6 yang ditemukan (Drive `10eHX0E_yg3TOpGvaRTtwBevO90Nq-buf`, SHA-256 `d2f9de10d1e848afaa4c61cf1a8635079883966ebf5b05c3559459c37d050e74`) ialah imbasan tanpa lapisan teks.

Perubahan **editorial sahaja** pada `T6-L137` dan `T6-L141`:
1. Semua nama surah dan medan SK/SP sumber asal **dipelihara**.
2. Set induksi dan objektif bacaan diperjelas; objektif mengandaikan **ayat yang ditetapkan guru** dan tidak memalsukan julat.
3. Aktiviti daripada **dua langkah yang terlalu pendek** kepada **empat langkah**: guru memilih dan merekod surah/julat sebenar; talaqqi dan musyafahah; tasmi' giliran bersama maklum balas; rekod berasingan setiap murid untuk makhraj, tajwid, kelancaran dan pemulihan.
4. Pentaksiran menjadi senarai semak individual berdasarkan **surah/julat ayat pilihan guru**, tanpa menetapkan nombor yang tidak wujud pada RPT.
5. Setiap medan sumber sebelum perubahan disimpan dalam `staging_tasmi_rpt_2027_review.original_fields_preserved`. `actual_ayah_range_verified=false`, `academic_expert_approved=false`, `jawi_orthography_approved=false`, `publication=HOLD`. Dua rekod masih diasingkan daripada pratonton guru kerana `staging_source_review_required=true`.

Audit baharu `pi_t6_tasmi_rpt_2027_review.py` bersama ujian regresi dan artefak JSON/CSV CI melaporkan dua Lesson, lapan nama surah, **0 julat ayat disahkan**, **0 kod DSKP rekaan**. Selepas pembetulan **690/690 draf mempunyai 3+ langkah aktiviti (100% struktur mekanikal)**, tetapi **6 rekod katalog penuh masih ditahan, 3 sumber kritikal masih HOLD, 687 pratonton/cetakan editor sahaja, 0 RPH pakar diluluskan dan 0 READY**. **100% bukan skor mutu akademik**.

Tindakan diperlukan sebelum T6-L137/L141 boleh dianggap sesuai: guru/pakar memilih bahagian ayat sebenar berdasarkan mushaf dan tahap murid, mengesahkan ia munasabah bagi durasi, kemudian menyemak Jawi serta instrumen tasmi' individu. Jangan mendorong pengguna untuk beranggapan empat surah penuh wajib dinilai kepada setiap murid dalam satu sesi.

**DB, Telegram, Web, hak akses dan produksi tidak disentuh. PR #443 tetap DRAFT/HOLD/NO_GO.**


### Lima Lesson Tahun 6 yang ditahan penuh — triage RPT asal, **belum dipulihkan**

RPT Pendidikan Islam Tahun 6 2027 yang sama juga telah diperiksa pada PDF halaman **3, 5, 7, 21 dan 41**; hasilnya disimpan di `pi_y6_held_rpt_2027_source_review.py` sebagai lejar review-only, **bukan janaan bahan**:

| RPH ditahan | Halaman RPT | Penemuan berdasarkan RPT | Halangan sebelum boleh jana |
|---|---:|---|---|
| T6-L006 | 3 | Juz 25, asy-Syura 33–51 | Sahkan mushaf dan beban PdP/tasmi' |
| T6-L014 | 5 | az-Zukhruf 34–73 | RPT sendiri memberi amaran jurang selepas ayat 73 sebelum ad-Dukhan 40 |
| T6-L018 | 7 | ad-Dukhan 40–59 | RPT menyatakan bahagian 1–39 tiada dalam urutan |
| T6-L060 | 21 | Solat ketika sakit, calon SP 4.2.3–4.2.5 | Secara nyata dilabel **cadangan CikguLaju**; perlu semak DSKP sebelum anggap rasmi |
| T6-L117 | 41 | al-Ma'arij 40–44, Nuh 1–28, al-Jinn 1–13 | RPT telah mengecualikan az-Zumar kerana bukan sebahagian Juz 29; sahkan sempadan dengan mushaf |

Kesemua **lima rekod masih tanpa `fields`**, `withheld=true`, `verified_ready=false`. T2-L035 ialah **rekod keenam** yang ditahan dan tidak dimasukkan dalam audit sumber Tahun 6 ini. **0 halaman mushaf diluluskan**, **0 ayat disisip automatik**, **0 kelulusan kod SP DSKP**, **0 bahan guru diterbitkan**. Audit source triage ini hanya membantu proses pembaikan seterusnya dan tidak mencukupi untuk mengangkat status HOLD.


## Semakan Tahun 6 — SK/SP 4.2 solat ketika sakit (DSKP rasmi vs PdP cadangan)

**Sumber primer diperiksa secara visual**, tanpa bergantung hanya kepada RPT:
- DSKP Pendidikan Islam Tahun 6, Drive `1pasG1F0ThshBUNoyLtQCD867bIkhekTZ`, SHA-256 `fd12636abb8b220623ec8c33a0c12261c7f27adc44c02efc5ee2ac04b71fea45`, PDF halaman **46** / bercetak **34**. SK **4.2** bertema konsep solat ketika sakit. SP **4.2.3** aplikasi solat ketika sakit, **4.2.4** analisis kepentingan menunaikannya, **4.2.5** menunaikan kewajipan solat dalam pelbagai keadaan secara beradab dan istiqamah; **ketiga-tiga kod SP itu sah dan tertera pada DSKP**.
- RPT CikguLaju 2027, Drive `1T380Ot_gG58JhxanELMM0z-gr6wmSJcL`, SHA-256 `b39a07b2dd7ef6062912f12fd43e63f87a98b13bde3885c925e88a37dac70e5b`, PDF halaman **21**, memperuntukkan **PdP 059** bagi SK/SP 4.2, dan **PdP 060** secara jelas berlabel *"PdP cadangan CikguLaju: amali solat ketika sakit mengikut kemampuan"*. **Kewujudan kod SP rasmi tidak menjadikan sesi PdP 060 satu Lesson wajib/rasmi yang tersendiri.**

**Pembetulan editorial T6-L059**: soalan KBAT lama membandingkan tatacara solat dengan agama lain (tersasar daripada SP), diganti dengan soalan mengenai cara menunaikan solat ketika sakit mengikut kemampuan. Seluruh pentaksiran asal disimpan dalam `staging_dskp_42_source_editorial_review.original_pentaksiran`; medan SK/SP dan aktiviti asal tidak diubah. Status **HOLD untuk semakan Jawi, PBD dan fiqh**.

**Calon T6-L060**: draf amali tambahan diwujudkan **di luar katalog aktif** sebagai `pi_t6_l060_amali_editor_candidate.json`, dengan 3 objektif, set induksi, **4 aktiviti**, pengukuhan, PBD amali individu, penutup dan senarai bahan. Ia dirancang berbeza daripada PdP 059 yang telah mempunyai aktiviti simulasi, tetapi pengesahan pertindihan pedagogi masih diperlukan. **Rekod asal `year6.json` T6-L060 tidak diberikan sebarang `fields`; `withheld=true`, `verified_ready=false`.** Tidak dinyatakan sebarang tatacara fikah yang khusus tanpa semakan sumber. Calon ini tidak boleh dicapai guru, Web atau Telegram.

**Pagar ujian**: `pi_t6_sp42_primary_source_audit.py` dan `test_pi_t6_sp42_primary_source_audit.py` memastikan halaman DSKP dan RPT tercatat, pembetulan KBAT tidak hilang/menimpa sejarah, kandungan calon tidak meresap ke DB, dan **0** dakwaan Lesson tambahan rasmi, **0** kelulusan pakar/Jawi, **0** READY. Semakan akademik dan ejaan Jawi tetap diperlukan.


## Tahun 2 Lesson 035 — punca pertindihan ayat 224 ditemui dalam RPT 2026 asal

RPT sumber **2026** `Rozayus_RPT_Pendidikan_Islam_Tahun_2_SK_2026.docx` (Drive ID `10nFtY-6tJRhvn8XggwtJRFBNozltQbqk`, SHA-256 `e5328102b4d059616ede2adf5cdf3a357acf1c0d997a2472e135fa120fcb7845`) diperiksa pada baris PdP Quran berturutan: **al-Baqarah 216–224**, kemudian **224–245**, diikuti **246–259**. Pertindihan **ayat 224 sudah ada dalam sumber 2026**, bukan kesilapan yang dicipta RPT 2027.

RPT **2027** `RPT_Pendidikan_Islam_Tahun_2_2027_CikguLaju.pdf` (Drive ID `1R2FNyT0CYb_WTMiw99lnZW9GuPaatz8w`, SHA-256 `86a8e6fb599eb0f65f3a0a888cb29d636223c75896718d058886076a95f6c05d`), PDF **p11** (PdP032), **p12** (PdP035) dan **p14** (PdP038), mengekalkan urutan ini dan dengan jelas menandakan overlap sebagai *belum pasti ulang kaji atau kesilapan sumber*.

**Keputusan penyiasatan:** pertindihan diwarisi; niat asal pengulangan itu **belum dapat dibuktikan**. Tiada julat ayat dipinda, tiada RPH T2-L035 dijana, rekod asal kekal `withheld=true` dan `verified_ready=false`. Modul `pi_t2_l035_rpt_2026_2027_overlap_audit.py` dan ujian mengunci bukti ini untuk semakan guru/pakar. **Tidak boleh secara automatik menukar kepada 225–245** semata-mata untuk menutup pertindihan tanpa pengesahan keputusan sumber.


## Audit al-Quran Tahun 6: Juzuk 25 **67 ayat belum dipetakan**, Juzuk 29 Lesson 117 bersambung (7 November 2026)

Saya membandingkan **kesemua tujuh slot tasmi' Juzuk 25** dalam RPT Pendidikan Islam Tahun 6 CikguLaju 2027 sumber Drive (`1T380Ot_gG58JhxanELMM0z-gr6wmSJcL`, SHA-256 `b39a07b2dd7ef6062912f12fd43e63f87a98b13bde3885c925e88a37dac70e5b`) dengan struktur juzuk/jumlah ayat daripada <https://qurankdn.moha.gov.my/myquran/index.php/juzuk/index>, <https://quran.com/ms/surahs> dan <https://www.amalkit.com/quran/juz-25>.

**Juzuk 25 bermula Fussilat 41:47 dan tamat al-Jathiyah 45:37**; ia mengandungi **246 ayat**. RPT mempunyai tujuh PdP berkenaan:
- **PdP 002:** asy-Syura 42:1–32
- **PdP 006 (ditahan):** asy-Syura 42:33–51
- **PdP 010:** asy-Syura 42:52–53 + az-Zukhruf 43:1–33
- **PdP 014 (ditahan):** az-Zukhruf 43:34–73
- **PdP 018 (ditahan):** ad-Dukhan 44:40–59
- **PdP 022:** al-Jathiyah 45:1–22
- **PdP 026:** al-Jathiyah 45:23–33 + al-Ahqaf 46:1–14 (bahagian al-Ahqaf ialah Juzuk **26**, tidak diambil kira dalam liputan Juzuk 25).

Jumlah ayat Juzuk 25 yang secara nyata ditugaskan oleh RPT tersebut: **179/246**. **Empat jurang tidak bertindih** yang masih tidak disenaraikan:

| Surah | Ayat yang tidak dipetakan | Bilangan |
|---|---|---:|
| Fussilat (41) | 47–54 | **8** |
| az-Zukhruf (43) | 74–89 | **16** |
| ad-Dukhan (44) | 1–39 | **39** |
| al-Jathiyah (45) | 34–37 | **4** |
| **Jumlah** | | **67** |

**Tidak tepat** menggelar susunan RPT ini khatam Juzuk 25 yang lengkap selagi editor belum menyelesaikan pembahagian 67 ayat tersebut. Satu keputusan guru/editor diperlukan sama ada memperuntuk slot berasingan, merangka semula beberapa PdP atau meminda sasaran. **Tiada 67 ayat ini disisip automatik** ke RPH mahupun RPT. Audit `pi_t6_juz25_sequence_gap_audit.py` memeriksa bilangan, tiada pertindihan dan keseluruhan julat supaya regresi dapat dikesan.

### Juzuk 29: Lesson 117 dan dua jirannya

RPT yang sama menunjukkan **PdP 113 → PdP 117 → PdP 121** sebagai berikut:
- PdP 113: al-Ma'arij 70:1–39.
- PdP 117 (ditahan): al-Ma'arij 70:40–44, Nuh 71:1–28, al-Jinn 72:1–13.
- PdP 121: al-Jinn 72:14–28.

Sumber MYQURAN/KDN dan Quran.com mengesahkan bilangan ayat surah 70/71/72 ialah **44+28+28=100**. Gabungan tiga PdP itu **menutup tepat 100/100 ayat** pada ketiga-tiga surah, tanpa bertindih atau jurang **pada segmen yang disemak**. Ini **tidak** mengesahkan keseluruhan Juzuk 29. Surah az-Zumar tidak termasuk dalam Juzuk 29 dan tidak dimasukkan semula. Audit `pi_t6_juz29_l117_continuity_review.py` mengunci semakan segmen ini.

### Empat draf RPH tasmi' untuk semakan editor sahaja

Fail baharu `pi_t6_held_quran_editor_candidates.json` menyediakan **empat draf Bahasa Melayu Rumi (belum Jawi)** bagi **T6-L006, T6-L014, T6-L018, T6-L117**. Setiap draf mengandungi hasil pembelajaran, set induksi, **empat langkah PdP** dengan tindakan guru dan murid, pengukuhan, PBD tasmi' individu, penutup serta bahan. Julat ayat asal disimpan sebagai **rujukan RPT**, dengan rekod surah dan julat bacaan **sebenar** setiap murid perlu diluluskan guru.

Semua calon ialah **editor sahaja**, belum sesuai untuk guru menggunakan sebagai RPH rasmi. Kekurangan 67 ayat Juzuk 25 **tidak** diselesaikan oleh kewujudan empat calon ini. Reviu tajwid, alokasi ayat sebenar, tempoh PdP, ejaan Jawi dan bukti Word/PDF generator Web/Telegram juga masih tertangguh. Rekod asal katalog `year6.json` bagi **keempat-empat Lesson itu kekal `withheld=true`, tanpa `fields`**. Daripada lima Year 6 yang ditahan, T6-L060 ialah calon amali solat berasingan yang juga masih HOLD. T2-L035 ialah rekod keenam seluruh katalog yang ditahan.

Ujian baharu `test_pi_t6_juz25_sequence_gap_audit.py`, `test_pi_t6_juz29_l117_continuity_review.py`, dan `test_pi_t6_held_quran_editor_candidate_review.py` serta lejar CI JSON/CSV menolak dakwaan FULL READY. **Liputan 690/690 tiga langkah hanyalah mekanikal; tiada skor kualiti akademik ≥80% yang diperakui.** Database produksi, Web, Telegram dan `main` tidak disentuh; PR #443 kekal **DRAFT/HOLD/NO_GO**.


### Punca sebenar Juzuk 25 — dibandingkan dengan RPT asal Tahun 6 (2026)

Perbandingan langsung dengan Word RPT asal `Rozayus_RPT_Pendidikan_Islam_Tahun_6_SK_2026.docx` (Google Drive ID `1WJTT7wm3aiN4F7YHMf1v_Qj6tuWu597a`; SHA-256 `6b0cb9ac986be8cc0350b66db341e2fefc9a698b0c78be0406020149107b1b14`) melibatkan jadual 0 baris 3 serta jadual 1–6 baris 2 (tujuh slot tasmi' Juz25 yang kemudian dipetakan ke PdP002/006/010/014/018/022/026 dalam RPT 2027).

**RPT 2026 mempunyai satu kesalahan yang lebih jelas daripada RPT 2027**:
- Slot yang sepadan dengan **PdP006** dahulu menyatakan **asy-Syura 42:33–77**. Sedangkan surah asy-Syura **tamat pada ayat 53**; ini menyebabkan **24 nombor ayat tidak wujud (54–77)** dalam rujukan sumber.
- Slot berikutnya mengandungi **asy-Syura 42:52–53** semula: **dua ayat pertindihan**.
- RPT 2027 telah membetulkan julat PdP006 kepada **42:33–51** supaya PdP010 bermula pada **42:52–53**, membuang kesalahan 24 ayat tidak wujud serta pertindihan 2 ayat.
- Walau bagaimanapun, **empat kelompok ayat yang tertinggal (67 ayat)**—Fussilat 41:47–54, az-Zukhruf 43:74–89, ad-Dukhan 44:1–39, al-Jathiyah 45:34–37—juga **tidak disenaraikan dalam sumber 2026**. Dalam sumber 2026 pun bilangan ayat Juz25 yang *sah dan unik* dipetakan ialah **179/246** selepas mengasingkan julat mustahil/berulang.

Kesimpulan sumber: isu 67 ayat bukan timbul daripada pembetulan 2027 tetapi **diwarisi daripada RPT 2026 asal**. Penyelesaian sebenar memerlukan pengagihan semula PdP secara editorial, bukan sekadar pembaikan ejaan atau pengujian Word/PDF. Data asal tidak ditimpa dan tiada ayat palsu dimasukkan. Fail `pi_t6_juz25_rpt2026_source_provenance.py` dan ujian memastikan kesalahan lama kekal boleh dikesan sehingga RPT serta RPH pengganti diluluskan.


## Sambungan 7 Nov 2026 — 13 sebutan Buku Aktiviti Jawi Tahun 5 belum diketahui jenis sumber (STAGING)

Audit tanpa meminda sumber RPH menjumpai **13 Lesson Tahun 5** yang secara nyata menyebut `بوكو اكتيۏيتي` (“Buku Aktiviti”) walaupun bahan khusus, edisi, muka surat bercetak dan latihan tidak dapat disahkan dalam rekod projek. Sebutan itu boleh merujuk **buku latihan murid secara umum** atau **buku aktiviti terbitan tertentu**; **jangan membuat andaian buku rasmi KPM atau memasukkan pautan fail secara automatik**.

- **9 rujukan pada medan pentaksiran:** T5-L092, L096, L100, L104, L111, L115, L119, L123, L127.
- **4 rujukan pada aktiviti utama:** T5-L131, L135, L139, L143.
- Buku sokongan dengan judul mirip tersedia dalam katalog penerbit DBP: [*Siri Mantap Bestari: Pendidikan Islam Tahun 5 Buku Aktiviti*](https://jendeladbp.my/ujana/siri-mantap-bestari-pendidikan-islam-tahun-5-buku-aktiviti/). **Buku komersial ini tidak semestinya sumber yang digunakan RPH**, dan pautan jualan/penstriman tidak memberikan hak untuk mengedarkannya atau mengesahkan halaman latihannya. Jangan kelirukan buku KSSR arus perdana dengan terbitan KSSRPK pendidikan khas.
- Modul `pi_y5_activity_book_wording_review.py` mengesan ID, medan asal, petikan dan SHA-256 **tanpa menulis semula Jawi**; `test_pi_y5_activity_book_wording_review.py` menolak jumlah tidak sepadan, pautan/halaman rekaan atau status publish. Audit kualiti, senarai P2 dan pagar NO_GO turut merangkumi 13 sebutan tersebut.
- Pemadanan Buku Aktiviti **Tahun 2/3 (174 calon)** masih masalah berasingan; dapatan 13 Tahun 5 **tidak** bermaksud 13 latihan baharu sudah disahkan.

**Keputusan penerbitan: NO_GO.** `690` draf, `6` tahan penuh, `3` sumber kritikal, `687` pratonton editorial, **0 RPH baharu dibuka**. Semua data asal kekal, tiada Word/PDF rasmi, muat turun bahan, `main`, DB, Web atau Telegram produksi disentuh. Sumber/aktiviti/penilaian sebenar perlu semakan Jawi pakar dan buku sebelum kelulusan.

## Sambungan 8 Nov 2026 — 49 pembetulan noktah RPH al-Quran + kertas keputusan 67 ayat Juzuk 25 (STAGING)

- **49 RPH Tahun 2–6** dibetulkan pada satu rentetan `برتجويد..` → `برتجويد.` dalam medan `aktiviti_utama` sahaja (T2=5, T3=8, T4=12, T5=12, T6=12). Teks aktiviti asal disimpan **penuh** dalam `staging_copyedit.original_activity` bagi setiap rekod, bersama `expert_content_approved=false`, `jawi_orthography_approved=false`, `publication=HOLD`. Ayat al-Quran, SK/SP, objektif, isi dan bidang tidak diubah.
- **8 contoh imbuhan Jawi Tahun 3** yang menggunakan tiga hingga lima noktah sebagai pola apitan kekal seperti asal (L084/088/092/096/100/104/108/115); elipsis petikan hadis juga tidak disentuh. Ujian `pi_tajwid_double_period_copyedit_review.py` menyemak pembetulan aksara tepat, 49 asal tersimpan dan status bukan READY.
- **Jurang Juzuk 25: 67 ayat** tetap tidak disenaraikan dalam RPT Tahun 6. Fail baharu `pi_t6_juz25_gap_resolution_editor_plan.py` menjana daftar **empat keputusan pengagihan untuk penyemak**, dengan petunjuk lokasi: (1) Fussilat 41:47–54 sebelum PdP002; (2) az-Zukhruf 43:74–89 antara PdP014 dan 018; (3) ad-Dukhan 44:1–39 juga di antara slot itu; (4) al-Jathiyah 45:34–37 perlu dipertimbang pada **sempadan dalaman PdP026** antara 45:23–33 dan 46:1–14 (yang terakhir sudah Juz26). Ini **petunjuk urutan sahaja, bukan alokasi PdP yang diluluskan**.
- Daftar keputusan menyimpan `teacher_allocated_lesson=null`, `exact_student_ayah_assignment=null`, `teacher_quran_sequence_approved=false`, `rpt_changed=false`, `rph_changed=false`, `release=NO_GO`; kod SP rasmi tidak direka. Artefak JSON/CSV dijana dalam GitHub Actions untuk semakan editor.

**Tiada merge, deployment, perubahan produksi, DB atau fail RPT asal.** `690` draf kekal, `6` rekod held, `3` source-critical holds, `0` kelulusan akademik/Jawi, skor akademik kekal `null`, keputusan pelepasan **NO_GO**.

## Sambungan 8 Nov 2026 — draf penuh 696 untuk editor, semua sumber asal tidak ditimpa

**Enam slot yang asalnya kosong** sekarang mempunyai RPH **khusus untuk penyemak** berasingan daripada katalog sumber: T2-L035, T6-L006/L014/L018/L060/L117. Fail T2-L035 baharu merujuk terus RPT Tahun 2 2027 (Drive `1R2FNyT0CYb_WTMiw99lnZW9GuPaatz8w`, PdP 032=al-Baqarah 216–224, PdP035=224–245 dan PdP038=246–259); ayat **224 ialah pengulangan tidak diputuskan**. Cadangan A kekalkan ayat 224 sebagai pemantapan, B mula 225 selepas persetujuan guru. Kedua-duanya masih HOLD dan RPT sumber tidak berubah.

`pi_held_six_editor_candidate_packet.py` mengumpulkan enam calon dengan 4 aktiviti utama lengkap, objektif, PBD dan bahan; gabungan **690 draf asal tidak-held + 6 calon editor = 696 entri berkandungan untuk editor**; sifar READY/approved. Ujian `pi_held_six_word_pdf_print_audit.py` menggunakan Word/PDF A4 sementara dengan fon Amiri; **tiada** binari dokumen latihan dimuat naik ke pengguna atau produksi, cuma laporan QA.

**Jurang 67 ayat Juzuk 25** mempunyai **dua pemetaan lengkap 246/246 untuk dipilih oleh penyemak**, tanpa duplikasi: Pilihan A kekalkan semua julat 179 ayat dalam tujuh PdP asal dan tambah 67 ayat yang tidak disebut; beban PdP014=56 dan PdP018=59 ayat menuntut pembahagian masa/tasmi. Pilihan B agih 246 ayat sebanyak 35/35/35/35/35/35/36, tetapi mengubah banyak batas sesi asal. Ayat al-Ahqaf 46:1–14 (Juz26) yang asalnya bersama PdP026 **tidak dibuang senyap** dan mesti ditetapkan jadual berasingan. Kedua-duanya **calon editor sahaja**, tidak diluluskan guru; lihat `pi_t6_juz25_complete_alternative_rpt_plan.py`.

**690 penutup Rumi** kini mempunyai overlay pratonton Jawi semuka bersumberkan **78 calon teks Jawi unik** melalui `pi_editor_jawi_closing_projection.py`, dengan Rumi asal dan SHA-256 kekal untuk perbandingan. **0/78 diluluskan ejaan Jawi oleh pakar**; tidak digunakan oleh bot atau laman web rasmi.

**Sumber Buku Aktiviti KSSR Tahun 2/3** dikenal pasti dalam e-Katalog KPM (BA102001 dan BA103001; DBP) serta portal Panitia Pendidikan Islam SK Pangkalan TLDM Kota Kinabalu. URL portal untuk setiap tahun disimpan dalam `pi_ba_source_integrity.py` bagi memudahkan semakan **naskhah asal**. **0/174 latihan/halaman khusus SP disahkan** dalam audit ini dan hak pengedaran PDF tidak dibuktikan; jangan sediakan PDF buku untuk muat turun automatik.

**Status pelepasan tetap NO_GO:** Kandungan draf lebih lengkap, bukan bukti 80% kualiti akademik. Semua 696 kekal tidak diluluskan pakar; enam sumber utama asal ditahan; tiga draf sumber kritikal turut ditahan. Pemadanan latihan, bacaan al-Quran/tajwid, ejaan Jawi, semakan fiqh/pedagogi dan ujian native Telegram/Web belum disahkan. PR mesti kekal `DRAFT`; jangan merge ke `main`, deploy, ganti DB atau melabel FINAL READY.


## 8 Nov 2026 — Pembetulan silang surah, objektif, induksi dan pentaksiran

**11 PdP dibaiki pada draf RPH, dengan 14 medan berubah** (T3=5, T4=5, T5=1). Tujuh daripadanya memerlukan tanda pembetulan sumber RPT kerana label surah yang salah turut muncul dalam PDF RPT 2027. Bukti dibandingkan dengan PDF RPT Tahun 3 Drive `1ceqdKRKYP2MHpkPe4KbIOVpCooq37NVE` dan Tahun 4 Drive `1O7Jvuvs7B7CF1tomvJdBTo7khSnu2haX`; **RPT asal belum diubah**.

| PdP | Pembetulan kandungan staging |
|---|---|
| T3-L086 | Objektif "سورة المائدة" → "سورة الأنفال", sepadan SP, aktiviti tasmi', pentaksiran dan RPT julat 53–75 |
| T3-L089, T3-L093 | Set induksi "سورة الكافرون" → "سورة العصر", sepadan SP hafazan al-Asr |
| T4-L009, T4-L013 | Set induksi dan PBD "سورة الكافرون" → "سورة التكاثر", sepadan SK/SP hafazan at-Takathur |
| T4-L081, T4-L085 | Set induksi "سورة العصر" → "سورة القارعة", sepadan SP tilawah al-Qari'ah |
| T4-L085, T4-L093 | PBD julat al-Qari'ah ayat 1–5 → ayat 6–11 mengikut objektif PdP sebenar |
| T3-L011 | "Murid membuat aktiviti (gallery walk)" diganti latihan kad situasi untuk akidah al-'Alim dan al-Hakim, berdasarkan SP 3.1.4 |
| T3-L023 | "Murid membuat aktiviti (hot seat)" diganti susunan kad langkah mandi wajib secara sesuai tahap, berdasarkan SP 4.1.5–4.1.7 |
| T5-L069 | Betulkan sela perkataan "سورة القدردري" → "سورة القدر دري" tanpa menukar isi |

**Penting:** Sesetengah ralat yang dibaiki ialah salinan terus daripada RPT asal. Draf RPH dibuat lebih konsisten tetapi dokumen RPT Tahun 3/4 yang sudah diedarkan masih perlu **pembetulan sumber berasingan**. Semua bahan asal dan cap SHA-256 provenance dikekalkan; setiap rekod baharu menyimpan `staging_cross_field_source_correction.original_fields` dan `revised_fields` untuk pemulihan. Semakan `pi_surah_pbd_alignment_audit.py` memeriksa nama surah yang disebut secara nyata serta julat ayat PBD terhadap objektif pada semua entri, bukan mensahkan keseluruhan kandungan hadis/tajwid/Jawi. **Kelulusan pakar 0; status HOLD/NO_GO; main, produksi dan DB tidak diubah.**



### Tambahan — urutan T3 PdP051/055/059 perkara membatalkan solat

Perbandingan bersebelahan PdP051, PdP055, PdP059 dalam katalog dan PDF RPT PI Tahun 3 2027 (Drive `1ceqdKRKYP2MHpkPe4KbIOVpCooq37NVE`) membuktikan ralat penyalinan lain pada objektif PdP059: RPT asal menyebut senarai **7–12** tetapi aktivitinya mengajar **13–18**, selepas PdP051 mengajar 1–6 dan PdP055 mengajar 7–12.

Objektif RPH **T3-L059** diperbetulkan daripada 7–12 kepada **13–18**, sejajar aktivitinya, menghasilkan pembahagian berturutan 1–6 → 7–12 → 13–18 tanpa pertindihan. Butiran asal dan kedua-dua versi objektif disimpan dalam metadata `staging_t3_solat_18_case_objective_correction`, dan `pi_t3_solat_case_sequence_audit.py` memaksa ujian yang gagal jika urutan berubah. **Ini bukan pengesahan oleh pakar terhadap senarai 18 perkara tersebut**; buku/DSKP asal serta fiqh masih perlu disemak. Kesilapan sumber RPT telah dimaklumkan pada PR #441. Tidak mengubah RPT Drive, `main` atau produksi.
