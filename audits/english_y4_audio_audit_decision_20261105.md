# CikguLaju English Year 4 — Keputusan audit keselamatan audio
**Tarikh:** 5 November 2026  
**Skop:** semua 160 Lesson English Year 4; KPM Primary Year 4 SK SOW PDF asal; peta legacy sebenar `app.py` v25.257–259; lima folder Google Drive asal (CD1/CD2/CD3 MP3 dan CD1/CD2 WMA).  
**Status:** AUDIT STAGING SAHAJA. **BUKAN** kelulusan semua RPH/audio atau bukti audio berjaya dihantar Telegram.

## Apa yang telah diperiksa
- **160/160** Lesson dikenal pasti daripada SOW asal; tiada Lesson tercicir daripada indeks.
- **65** Lesson menyebut nombor Track dalam SOW. Ini **tidak** bermaksud semua Lesson lain langsung tiada audio dalam Teacher's Book.
- Peta audio legacy terakhir mengandungi **56 Lesson** dengan **69 rujukan media**, bukan 55/68. Ralat pengiraan awal diatasi selepas CI menangkap item pertama `Lesson 1`.
- **69/69** ID sumber legacy dijumpai dalam **lima folder asal** yang diperiksa: **45 MP3, 24 WMA**. Kewujudan fail hanya mengesahkan ID, nama, format dan folder—**bukan** kesesuaian perkataan audio dengan aktiviti.
- Untuk kesemua **24** rujukan WMA, terdapat fail MP3 pada nombor CD/Track yang sama. Semua hanya **CALON PADANAN**, kerana fail WMA pernah dihantar sebagai `.mp3` tanpa penukaran format sebenar oleh pengirim lama. Jangan hidupkan audio berdasarkan persamaan nama sahaja.

## Ralat sumber yang terbukti / mesti ditahan
| Lesson | Peta lama | Sumber atau tugasan yang disemak | Keputusan |
|---|---|---|---|
| **29** | CD1 Track 35, 36 (**WMA**) | TB **p.193**, SB **p.129**: CLIL Social Studies, **CD3 Track 35, 36** | **SALAH CAKERA**. Jangan hantar CD1. Calon CD3 MP3 ditemui; audio Telegram sebenar belum diuji. |
| **30** | CD2 Track 29 | TB **p.39**, SB **p.20 Activity 2**: **CD1 Track 29**, disahkan pengguna | **SALAH CAKERA** dalam SOW dan peta. Guard sedia ada menahan CD2, PR #275 membaiki rujukan tepat tetapi masih staging. |
| **103** | CD2 Track 26, **27, 28** (**WMA**) | SOW L103 hanya Track **26**. SOW L104 memerlukan Track **27, 28**. | Track **27, 28 SALAH LESSON**. Guard sedia ada memadam lebihan daripada L103 semasa runtime, tetapi L104 masih tidak ada laluan yang disahkan. |

**Penting:** Perbezaan nombor dan urutan CD antara Lesson **tidak** semestinya salah. Bahan CLIL/Phonics di bahagian belakang SB boleh menggunakan **CD3 lebih awal**; semakan mesti ikut Teacher's Book + aktiviti, bukannya menukar CD mengikut formula.

## 9 Lesson menyebut audio dalam SOW tetapi peta terakhir tiada media
**Lesson 13, 20, 65, 66, 68, 70, 76, 104, 139**. Audio bagi Lesson ini tidak boleh diteka dan tidak boleh diisytihar siap. Lesson **1 sebenarnya ADA dalam peta**; pembetulan parser telah disimpan dan dilindungi ujian automatik.

## Risiko penghantaran
Pengirim media lama `_send_verified_media_rows_v2594` menyalin fail sumber sebagai fail sementara dengan sambungan `.mp3` lalu menghantarnya melalui `sendAudio` sebagai `audio/mpeg`. **24 fail sumber tersebut sebenarnya WMA**. Ini risiko format/penyampaian yang tidak boleh dianggap lulus hanya kerana nama fail dan ID sepadan. CI yang dijalankan ialah audit sumber dan kod **offline**, bukan penghantaran sebenar.

## Keputusan & kawalan keluaran
1. **Jangan tandakan 160 Lesson atau 69 media FINAL READY** daripada audit ini sahaja. Tiada bukti audio spoken-content/playback penuh bagi kesemua laluan.
2. Kekalkan Lesson 29 dan 30 dalam **HOLD AUDIO** sehingga CD3/CD1 masing-masing dihantar dan diuji pada akaun guru sebenar. RPH Word/PDF yang sepatutnya digunakan **tidak patut disekat** kerana audio.
3. Jangan terus menukar 24 WMA menjadi ID MP3 secara automatik. Fail calon perlu disemak terhadap halaman TB/SB, perkataan audio dan penghantaran melalui Telegram.
4. Semak 9 Lesson tanpa peta media, khususnya L104, serta **semua** rujukan audio dalam 160 Lesson secara individu mengikut TB/SB.
5. Semak selepas PR lengkap tanpa meminda `app.py`, Supabase, pengguna, quota, langganan, pembayaran, referral atau subjek lain. PR #279 audit-only; PR #275 pembetulan L30 (draft); PR #277 pembetulan sumber & hold audio L29 (draft).
6. Selepas lulus ujian offline, semak laluan Telegram sebenar untuk **pilih bahan**, butang lama, Word satu halaman, PDF satu halaman dan audio yang betul sebelum merge/release.

## Bukti
- `audits/english_y4_sow_160_audio_index_20261105.json` — 160 sumber SOW asal.
- `audits/english_y4_160_audio_drive_crosscheck_20261105.json` — 160 Lesson, semua 69 laluan lama dan status setiap satu.
- `audits/english_y4_legacy_wma_to_mp3_candidates_20261105.json` — 24 padanan calon tanpa kelulusan.
- `tests/test_english_y4_160_audio_crosscheck_20261105.py` — audit automatik offline dan pencegahan angka/status palsu.
- <https://github.com/nurynayreen88/CikguLaju-AI/pull/279>.

**Klasifikasi terkini:** Inventori sumber/peta = diaudit. Semua audio / pedagogi / penghantaran Telegram = **belum FINAL READY secara menyeluruh**.
