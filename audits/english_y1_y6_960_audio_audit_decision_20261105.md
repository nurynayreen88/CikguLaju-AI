# CikguLaju English Year 1–6 — Audit SOW dan sumber audio (5 November 2026)

**Skop:** 960 Lesson rasmi (160 setiap Year 1–6).  
**Tahap pemeriksaan:** indeks asal SOW bagi kesemua 960 Lesson, padanan sumber Drive untuk kes kritikal, semakan rujukan RPH terpilih, pemeriksaan statik peta Telegram Year 4 terdahulu. **Ini bukan pengesahan audio penuh 960 Lesson atau kelulusan guru.**

| English | Lesson SOW direkodkan | Lesson SOW menyatakan ID CD/Track/Audio secara eksplisit | Catatan |
|---|---:|---:|---|
| Year 1 | 160 | **0** | SOW lama tidak mencetak ID audio; gunakan Super Minds/TB dan peta v15. Kurikulum KP2027 **belum** disahkan oleh indeks lama ini |
| Year 2 | 160 | **0** | SOW lama tidak mencetak ID audio; contoh RPH L26 menggunakan CD2 Tracks35/36 menurut nota buku teks tetapi TB asal dan audio Telegram belum disemak |
| Year 3 | 160 | **0** | SOW tidak mencetak ID audio; contoh L93 RPH menyebut CD1 Track97. Perlu semakan buku teks dan fail asal secara terus |
| Year 4 | 160 | **65** | Audit khusus 69 laluan lama dalam PR #279; isu salah cakera, salah Lesson dan **24 fail sumber daripada buku Super Minds 1** |
| Year 5 | 160 | **62** | SOW format seperti CD3.02/03; tiga calon MP3 L29–30 ditemui dalam folder English Plus 1 Year5 tetapi belum diuji melalui Telegram |
| Year 6 | 160 | **7** | SOW hanya sebahagian menyatakan nombor seperti Audio 1.28. Folder Drive bernama Year6 mengandungi bahan **AS5**, bukannya pengenalan jelas AS6 |

**Penting:** Angka 0, 65, 62 atau 7 hanya menyatakan berapa Lesson mempunyai **ID audio yang dicetak dalam SOW**. Ia tidak menyatakan berapa Lesson sebenar menggunakan audio. Untuk setiap tahun, sumber audio per aktiviti mesti merujuk Teacher's Book dan Student's/Pupil's Book.

## Masalah utama ditemui

1. **Year 4, 24 rujukan WMA — risiko silang buku teks.** ID lama berada dalam `Super Minds 1 Audio Unzipped`, bukan dalam Get Smart Plus 4. Ini **bukan sekadar isu format WMA**. Jangan hantar atau tukar secara pukal hanya berdasarkan CD dan Track. Ujian pemetaan 24 ini ada dalam audit khusus PR #279.
2. **Year 4 L29** — TB p193/SB p129 menetapkan CD3 Tracks35/36, sedangkan kod lama memetakan CD1 WMA. Sumber pembetulan serta cadangan sekatan audio sahaja disimpan dalam PR #277; RPH Word/PDF perlu kekal.
3. **Year 4 L30** — TB p39/SB p20 CD1 Track29, disahkan pengguna, sedangkan SOW dan peta lama menyatakan CD2. Kes berasingan dalam PR #275.
4. **Year 4 L103–104** — dua Track 27/28 tersalah berada bersama Lesson103 dalam peta lama; SOW merujuknya pada Lesson104.
5. **Year 6 sumber audio** — folder `Academy_Stars_Year6_Audio` dalam Drive mengandungi `Academy_Stars_5_Audio_www.frenglish.ru` dengan **49 fail MP3 `AS5_Uxx...` serta 2 fail bukan audio** (51 entri keseluruhan). Kena sahkan sama ada terdapat folder Year6 yang lain dan sama ada kod bot memang menggunakan fail tersebut. **Label yang salah bukan bukti bahawa bot menghantar audio yang salah.**
6. **Year 5 sumber audio** — folder `English Plus 1 Audio Year 5` memaparkan hanya 100 fail pertama. SOW L29 CD3.02/03 dan L30 CD3.04 mempunyai fail MP3 dengan nombor yang sepadan dalam sampel ini; kandungan rakaman belum dibandingkan dengan skrip TB.

## Larangan automatik

- Jangan anggap CD1 sentiasa mendahului CD2 dalam **semua** Lesson; CLIL dan Phonics boleh guna CD3 lebih awal.
- Jangan samakan nombor track dari buku yang berlainan.
- Jangan tandakan semua audio `FINAL READY` hanya kerana fail wujud dalam Drive, PDF RPH satu halaman atau lulus GitHub CI.
- Jangan kemas kini database pengguna, kuota 10 janaan, langganan, pembayaran, referral atau RPH subjek lain semasa semakan audio.
- Jangan anggap Year1 SOW lama sudah mematuhi KP2027.

## Fail semakan

- `audits/english_y1_y6_960_sow_audio_index_20261105.json` — **960 rekod** dengan asal SOW, tajuk Lesson dan ID audio SOW jika dinyatakan.
- `audits/english_y1_y6_audio_source_risk_register_20261105.json` — **8 isu / semakan berkeutamaan**, klasifikasi bukti dan tindakan.
- `tests/test_english_y1_y6_960_sow_audio_provenance_20261105.py` — regression 960 Lesson, format berbeza setiap tahun dan perlindungan daripada status siap palsu.
- `.github/workflows/english-y1-y6-audio-provenance-20261105.yml` — ulang semakan sumber dalam PR.
- PR Year4 audio penuh: https://github.com/nurynayreen88/CikguLaju-AI/pull/279.

**Kekal dalam staging:** Semua tahun SOW diindeks; **bukan** semua audio/TB/SB/MP3 dan penghantaran Telegram disahkan. Kelulusan individu hanya boleh diberi selepas membaca arahan TB/SB, mendengar rakaman sebenar, menguji ID fail yang dihantar serta meneliti PBD dan satu halaman RPH.
