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
