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
