# Matematik v43 — keputusan QA teknikal dan release gate (7 November 2026)

**Keputusan: 585/585 RPH TECHNICAL QA PASSED; ACADEMIC FINAL READY = NO.**
Semua kerja dalam cabang `staging/matematik-ba-evidence-20261107`. **Jangan merge/deploy produksi** tanpa pengesahan akademik dan integrasi sebenar.

## Bukti asal dan artefak
- Sumber terverifikasi: `CIKGULAJU_MATEMATIK_v42_585_RPH_BA_T2_T3_DRAF_STAGING.zip`, SHA-256 `1a55a2c2f557f6394824f97b4f8f718313d12190636977d28dc2ecc4d3983601`.
- Output baharu: `CIKGULAJU_MATEMATIK_v43_585_RPH_QA_DSKP_BA_STAGING.zip` (49,110,511 bait), SHA-256 `aeb3d9486023832b1e29f7618ec034b95d471d968a566066773b80953f531583`.
- Arkib v43 mengekalkan 585 fail Word, 585 fail PDF individu, 585 Markdown, 5 PDF gabungan, dan fail audit. ZIP `testzip` lulus tanpa ralat CRC.
- **234** RPH Tahun 2–3 menggunakan Buku Aktiviti mengikut **topik dan julat halaman bercetak**, dengan arahan guru memilih latihan mengikut SP. **351** RPH Tahun 4–6 menggunakan Buku Teks/PBD tanpa mencipta rujukan BA palsu.
- **Dua penambahbaikan visual yang disahkan**: T4 Lesson 097, luas segi empat sama dijelaskan sebagai sisi 5 × 5 = 25 unit²; T4 Lesson 117, masa berganda di penghujung Aktiviti 2 dibuang. Word dan PDF satu halaman dirender/semak visual; PDF gabungan Tahun 4 v43 dijana semula.

## Ujian QA 585
Rekod lengkap `audits/matematik_v43_585_technical_qa_20261107.csv`:
- 585/585 PDF satu halaman A4.
- 585/585 tajuk aktiviti bold dalam DOCX.
- 585/585 kod SP terpapar dalam Word dan PDF.
- 585/585 struktur pengukuhan / Aktiviti 3 kelihatan pada PDF.
- 585/585 masa langkah PdP berjumlah 60 minit.
- 234/234 BA Tahun 2–3 hadir dalam RPH; 351/351 Tahun 4–6 tiada BA tidak sah.
- 593 kod SP digunakan; semua mempunyai lokasi DSKP (kod Tahun 2 `4.1.1` bercetak `4. 1.1` pada PDF).
- 360 ungkapan aritmetik dengan tanda sama dengan disaring; 330 pengiraan mudah dikira tepat secara programatik, 30 pengecualian parser berpunca daripada penulisan nombor ribu/pecahan/peratus/multi-persamaan dan disemak pada teks asal. Ini **bukan** semakan setiap dakwaan matematik dalam keseluruhan korpus.
- Tahun 4: 117 Lesson merujuk 83 ID asal termasuk 34 pasangan pengembangan; perbezaan aktiviti pada pasangan diuji secara perbandingan, **belum** diberi kelulusan kandungan sekolah.
- 21/21 ujian Python pada loader pratonton v43 dengan arkib sebenar dan arkib sintetik **lulus** dalam persekitaran terasing (SHA, semua 585 entri, admin/pelanggan, callback fallback, bad delivery, no quota/DB).
- GitHub Actions pada branch staging perlu semak CI sebelum sebarang release.

## Halangan FINAL READY
1. **Semakan akademik setiap latihan Buku Aktiviti/teks mengikut SP dan PBD (585 lesson)** masih belum disahkan satu-persatu. Kandungan sumber TOC 190 topik BA hanyalah bukti topik/halaman, bukan nombor latihan.
2. Pemisahan 83 sumber kepada 117 Lesson Tahun 4 memerlukan signoff manual bagi 34 pasangan pengembangan, walaupun tiada pengulangan penuh automatik.
3. Tarikh 2027 negeri/kumpulan A-B dan keselarasan RPT sebenar memerlukan ujian penjadualan.
4. Telegram/Web API **staging sebenar** belum diuji menggunakan arkib v43. Render mempunyai perkhidmatan web production dan preview lama, tetapi **tiada perkhidmatan staging Matematik v43 yang diaktifkan**. Jangan trigger Render production.
5. Storan **ChatGPT Library telah penuh**. Percubaan memuat naik ZIP v43 ditolak; fail v42 asal dan fail audit v43 yang kecil kekal selamat. ZIP v43 masih tersedia sebagai artifak perbualan / kerja; jangan overwrite/delete arkib untuk melapangkan ruang.

**Release gate:** `TECHNICAL_QA=PASS`; `STAGING_MOCK=PASS`; `ACADEMIC_VERIFIED=NO`; `LIVE_INTEGRATION=NO`; `FINAL_READY=false`.

PR: https://github.com/nurynayreen88/CikguLaju-AI/pull/444
