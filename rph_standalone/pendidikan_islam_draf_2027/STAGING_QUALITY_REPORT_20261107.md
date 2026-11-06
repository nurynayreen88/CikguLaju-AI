# Pendidikan Islam 2027 — Audit kedua terendah dalam giliran RPH ≥80%

**Tarikh:** 7 November 2026  
**Subjek:** Pendidikan Islam Tahun 2–6  
**Cabang:** `staging/rph80-pendidikan-islam-second-20261107`  
**Status:** STAGING / DRAF / **HOLD — BELUM MENCAPAI 80% KUALITI KANDUNGAN TERBUKTI**

## Asas dan ketepatan peratus

Ranking editorial terdahulu ialah **51%** untuk Pendidikan Islam, kedua terendah selepas Sains (45%). Skor ini bukan hasil semakan guru secara individu dan **tidak boleh dinaikkan secara automatik** hanya kerana format diperbaiki. Rubrik yang perlu dibuktikan: ketepatan SK/SP/sumber (25), pedagogi spesifik (25), pentaksiran/PBD (25), format Word/PDF (15), serta padanan Telegram–Web (10).

## Perubahan nyata dalam batch ini

- **696/696** rekod kekal (T2 112; T3 147; T4 151; T5 143; T6 143); **690 draf, enam ditahan**.
- **685** RPH asalnya memulakan penomboran di `2.` dalam seksyen Aktiviti Utama; pembetulan bermula `1.` pada salinan staging, **tanpa mengubah teks langkah Jawi**.
- **Lima** RPH Tahun 4 (L087, L091, L095, L099, L134) mempunyai perenggan aktiviti panjang tanpa nombor. Perenggan tersebut dipecah menjadi 3–5 langkah berdasarkan frasa sedia ada, tanpa membuang perkataan.
- **690/690** draf kini bermula dengan `1.` dalam Aktiviti Utama. **Enam tahanan tidak disentuh**.
- Skrip audit konservatif `pi_quality_audit.py` menjana lejar per-Lesson 696 rekod dan meninggalkan `quality_score_percent=null`, `quality_80_certified=false`, `release=NO_GO`.
- Skrip `pi_pedagogy_review.py` menghasilkan **690 cadangan semakan pedagogi** menurut tujuh bidang (al-Quran, Jawi, Akidah, Ibadah, Sirah, Adab, Hadis), beserta SP, objektif dan aktiviti asal setiap Lesson. Cadangan ialah nota editor berbahasa Melayu Rumi, **belum diterjemah/semak Jawi** dan **tidak disalurkan kepada guru**.
- CI baharu menguji integriti 696 rekod, tiada bahan tahanan terpapar, tiada READY palsu, penomboran lengkap, dan keluaran lejar audit serta cadangan editor sebagai artefak.

## Jurang yang masih nyata

| Semakan berdasarkan data katalog | Bilangan | Status |
|---|---:|---|
| RPH lengkap dalam katalog | 696/696 | DRAF / bukan kelulusan kandungan |
| Draf yang penomboran Aktiviti Utama bermula 1 | 690/690 tidak ditahan | Pembaikan format disediakan |
| Aktiviti Utama hanya satu atau dua baris | **563/690** | Perlu pemurnian kandungan satu persatu |
| Rujukan buku teks dengan penanda tidak diperakui yang dikesan | **77/690** | Perlu semakan halaman asal; angka ini bukan keseluruhan rujukan belum disahkan |
| Rekod ditahan | **6** | Kekal HOLD |
| Persetujuan guru pakar dan pemeriksaan semantik setiap Lesson | **Belum dibuktikan** | HOLD |
| Ujian render Word/PDF berdasarkan data yang baru diubah | **Belum dilaksanakan** | HOLD |
| Pengujian parity Telegram–Web untuk bahan terkini | **Belum dilaksanakan** | HOLD |

**Enam rekod tahanan:** T2 L035; T6 L006, L014, L018, L060, L117. Jangan meneka julat tasmi' atau menaikkan status.

## Syarat memuktamadkan skor 80%

1. Edit aktiviti dan PBD **secara khusus bagi Lesson**, bukan salin templat pelbagai bidang ke RPH. Semak 563 rekod ringkas dan gunakan cadangan editor hanya sebagai senarai kerja.
2. Buktikan padanan SK/SP terhadap DSKP dan halaman buku teks sebenar atau mushaf. Tanda pemeriksaan khusus bagi ayat al-Quran, Jawi dan pelajaran tasmi' berisiko.
3. Semak visual dan kelegaan cetakan Word/PDF A4 untuk pembaikan terkini, kemudian uji pilihan Lesson sebenar melalui Telegram dan Web di staging.
4. Skor rubrik berdasarkan bukti individu; capai **≥80/100** tanpa isu kritikal sebelum mempertimbangkan READY, dan kekalkan keputusan NO-GO untuk semua yang belum diluluskan.

Tiada `main`, database, `app.py`, kuota, langganan atau laluan produksi diubah. Semua pembetulan disimpan di branch staging dan PR perlu kekal **DRAFT** sehingga QA kandungan selesai.
