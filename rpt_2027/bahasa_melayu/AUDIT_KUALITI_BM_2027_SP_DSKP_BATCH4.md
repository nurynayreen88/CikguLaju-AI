# CikguLaju AI — Audit kualiti RPT Bahasa Melayu 2027, pembetulan subkemahiran B4

**3 November 2026 · KELUARAN STAGING · BELUM READY**

## Skop

Mengikut arahan pemilik projek, draf BM Tahun 2–6 diselaraskan sebagai **satu dokumen bagi setiap tahun, gabungan tarikh A/B, Minggu → Lesson bernombor → baris berasingan**, seperti RPT English. RPT BM 2026 digunakan untuk urutan/tajuk, DSKP sebagai sumber kod standard, Buku Teks sebagai rujukan utama halaman dan aktiviti. Semua pembetulan terhad kepada `staging/bm-rpt-2027-20261103`.

## Kerja batch ini

1. **Audit global 825 Lesson** mengesan 37 pasangan yang berkongsi unit, tajuk asas, SP dan rujukan buku; 6 ialah varian dengan penanda +PKJR dan 31 berkongsi tajuk yang sama. Kesemua tajuk asas muncul dua kali dalam RPT 2026. Lihat [audit global 37 pasangan](AUDIT_ULANGAN_GLOBAL_825_20261103.md). Tiada rekod digabung/dipadam.
2. **Tahun 2 — sembilan rekod fokus sumber primer:** BM2-P005/P017 dipulihkan penanda +PKJR; BM2-P016/P017 BA1 18–20 berpandukan nota Buku Teks m/s 14 (RPT 2026 18–19); BM2-P021/P022 subkod 5.1.1 (i)/(ii)/(iii); BM2-P065/P066 tajuk penuh `Berkemas sambil Bersenam`; BM2-P067/P068 tajuk penuh `Menjaga Kebersihan Almari Baju` dan SP **5.1.4 (iii) kata arah** berdasarkan Buku Teks Tahun 2 Jilid 1 halaman 59 — RPT 2026 mengandungi kesilapan (ii).
3. **Lima tajuk terpotong tambahan:** BM2-P074/P079 (`Sedapnya Amplang + PKJR`), BM2-P088/P093 (`Seronoknya Menonton Teater + PKJR`) dan BM3-P120 (`Jagalah Bumi Kita + PKJR`) dipadankan dengan teks RPT 2026.
4. **34 rekod SP terpotong** disiapkan menggunakan teks RPT 2026: Tahun 3 (1), Tahun 4 (3), Tahun 5 (7), Tahun 6 (23). Contoh pemotongan `lag`, `mempersembahkann`, `sesua`, `susuna`, `per`, `pelb`, `yang`.
5. **36 rekod subkemahiran** diselaraskan kepada DSKP: Tahun 2 (14) dan Tahun 3 (22), termasuk BM3-P095 yang kehilangan subkod (i). Tahun 2: SP 1.1.2 (i) soalan, (ii) suruhan, (iii) pesanan, (iv) permintaan; SP 1.1.3 (i) soalan bercapah, (ii) pesanan. Tahun 3: SP 1.1.2 (i) suruhan dan permintaan, (ii) silaan dan larangan; SP 1.1.3 (i) soalan bertumpu, (ii) soalan bercapah; SP 3.3.1 (i) berpandu, (ii) separa berpandu.

**Penting:** Bilangan 34 + 36 merujuk pembetulan SP batch ini, tidak termasuk empat pembetulan subkod SP Tahun 2 dalam senarai fokus sebelumnya dan pembetulan lama batch B3. Ini bukan 70 Lesson baharu.

## Pengesahan struktur pasca pembetulan

| Tahun | Lesson/ID unik | Markdown–HTML sepadan pada ID, tajuk, SP, rujukan dan catatan | Minggu |
|---|---:|---|---:|
| 2 | 164 | 164/164 | 44 |
| 3 | 165 | 165/165 | 44 |
| 4 | 165 | 165/165 | 44 |
| 5 | 166 | 166/166 | 44 |
| 6 | 165 | 165/165 | 44 |
| **Jumlah** | **825** | **825/825** | **220 baris minggu** |

Perbandingan HTML–Markdown menormal entiti teks HTML (contohnya `&#39;`). Tiada ID Lesson berganda, nombor Lesson tidak lompat, dan tiada contoh SP dengan hujung jelas terpotong daripada corak yang diuji. **Pemeriksaan automatik tidak menggantikan audit ayat setiap SP terhadap DSKP.**

## Sumber yang digunakan

- [RPT BM Tahun 2 2026](https://docs.google.com/document/d/1qFUGCNH672R4QYBSxzSCYUbTiVmTQQU0/edit) dan [DSKP BM Tahun 2](https://drive.google.com/file/d/1uxmBLWILcferhst8FSsZLn8WCIrr1Nx1/view), [Buku Teks BM Tahun 2 Jilid 1](https://drive.google.com/file/d/1f6CJ87NbI7uNS_GKIh483-8DsiOr0Lr0/view)
- [RPT BM Tahun 3 2026](https://docs.google.com/document/d/1wlrI120RKhZh85oSPIZPPgJwj7CKChsT/edit) dan [DSKP BM Tahun 3](https://drive.google.com/file/d/1q-Mdq8kIZGui7-IccvSGJx1dfMjIOAQN/view)
- [RPT BM Tahun 4 2026](https://docs.google.com/document/d/103e8N7kZvR_tPr9TLy8TaM8Yz6VMeoQ-/edit), [Tahun 5 2026](https://docs.google.com/document/d/1q0vWe8ydZonJsAohVEe121u-0A2xMrg7/edit) dan [Tahun 6 2026](https://docs.google.com/document/d/1g0HR5PGuW9CMQFJZLcDbXUD0qZwlMJK1/edit)
- [RPT induk 2027](https://docs.google.com/document/d/1MO37hjLMT5Afzlnq2--rf3jJQKX9BlTdyejZvU6Yau4/edit), [Kalendar negeri/cuti 2027](https://docs.google.com/spreadsheets/d/1tf6-B6hmA4U6E0fCROcKpxh-B5uLUQOYBt6TZft_7_k/edit)

## Baki sebelum status READY

1. Audit akademik sepenuhnya **825 baris SK/SP, unit, sumber buku dan aktiviti**, bukan sekadar kesamaan format dan kod. Semak khusus SP berganda dan PKJR.
2. **37 pasangan** ulangan dalam inventori global (dan tujuh aktiviti berlainan tajuk tetapi berkongsi halaman/kod dalam audit lama) belum diputuskan untuk sesi susulan, gabungan atau pemetaan semula.
3. Buku Aktiviti Tahun 2–3 belum dapat disahkan sepenuhnya; nombor BA dalam Buku Teks ialah petunjuk rujukan, bukan bukti kandungan dan arahan latihan.
4. Projek Tahun 6 **BM6-P147/P148** mempunyai konflik sumber SK 3.2 dengan SP 5.3.4; jangan jana RPH READY daripada padanan itu tanpa DSKP primer.
5. Jadual negeri A/B, cuti negeri dan gantian, peruntukan masa BM, minggu `BELUM AGIH`, dan hari PdP sebenar belum disahkan. Kalendar minggu bukan identiti Lesson.
6. Word landscape bermuka depan dan RPH standalone BM belum siap/diterbitkan. **Tahun 1 KP2027** kekal berasingan daripada DSKP KSSR Semakan.

**Kawalan:** DRAF TERKAWAL; `main`, database asal, Telegram, Web, dan RPH sedia ada tidak disentuh.
