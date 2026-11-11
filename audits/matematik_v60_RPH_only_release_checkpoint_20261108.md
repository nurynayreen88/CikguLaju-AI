# Matematik v60 — skema guru 68 lesson pasangan Tahun 4 (RPH sahaja)
**Tarikh:** 8 November 2026 • **DRAF STAGING** • **14/14 ujian ZIP sebenar PASS** • **FINAL READY AKADEMIK = NO**

## Arahan skop
- **RPH Matematik Tahun 2–6 sahaja.** RPT 2027 diurus dalam chat lain; **tidak dibaca, disunting, dijana atau dipasang** dalam v60.
- Sumber v59: `CIKGULAJU_MATEMATIK_v59_585_RPH_PBD_30_PASANGAN_T4_STAGING.zip`, SHA256 `79a759be40fd8aadebbf3318d784e042239d290e8cc36b4136380c8fb5c215eb`.
- Arkib v60: `CIKGULAJU_MATEMATIK_v60_585_RPH_OBJEKTIF_PBD_T4_STAGING.zip`, **49,194,607 bait**, SHA256 `a641d7aff88b375f4786807a10eed384d9b6b22fea632d11ad9f2bc97fec5271`.

## Dapatan sebenar dan keputusan pembetulan
- **34 lesson kedua** bagi 34 pasangan Tahun 4 telah pun mempunyai PBD yang khusus. Jangan ganti dengan soalan generik atau duplikasi.
- Skema v59 meliputi **30 lesson pertama sahaja** (120 soalan asal). Empat lesson pertama **L022, L039, L056, L060** sudah ada PBD khusus tetapi belum termasuk skema v59.
- v60 menyediakan **144 entri jawapan/kriteria baharu untuk 38 RPH** (34 lesson kedua + 4 lesson pertama tadi). Gabungan liputan skema ialah **68 daripada 68 RPH** dalam 34 pasangan Year4.
- Daripada 144 entri v60: **124 pengiraan disemak menggunakan aritmetik pecahan rasional tepat**, **14 memerlukan input/semakan guru** (ukuran objek, titik koordinat tidak diberi, atau kadar mata wang BNM bertarikh), dan **6 ialah jawapan konsep/model/kategori**. Bagi kes dinamik, **TIADA nombor/kadar rekaan dimasukkan**.
- **8 RPH Tahun 4 mempunyai objektif yang tidak selaras dengan item PBD sebenar**. Hanya medan **Objektif** diubah: T4-L019 (2/3), L039 (2/2), L040 (2/3), L060 (2/2), L061 (2/3), L073 (2/3), L092 (2/3), L103 (4/5). PBD, SK/SP, Aktiviti 1/2, rujukan, unit, nombor Lesson dan masa tidak diubah.
- **577 daripada 585 RPH kekal byte-identical** pada DOCX, PDF dan Markdown berbanding v59. Tiada RPH subjek atau tahun lain diubah.

## Artifak guru
- Fail **`CIKGULAJU_MATEMATIK_v60_SKEMA_GURU_68_RPH_PASANGAN_T4_STAGING.pdf`** ialah skema gabungan v59 (30 lesson) dan v60 (38 lesson), **24 halaman**, SHA256 `660aa65152cc5b8ebf46dde73ce5685c8ff5278bf2b6b81ce5ebb0361f16f0ec`.
- Fail ZIP v60 mengandungi `AUDIT/V60_38_RPH_PBD_SKEMA_GURU.csv` (144 entri, teks PBD sumber v59 pada setiap baris), `AUDIT/V60_8_OBJEKTIF_PBD_T4.csv` (before/after lapan objektif), `AUDIT/V60_RELEASE_GATE.json`. PDF skema disediakan secara berasingan kerana bahan guru, bukan item Word murid.

## QA sebenar, bukan sekadar metadata
- **14/14 ujian arkib ZIP v60 sebenar PASS** oleh `/mnt/data/math_ready_audit/test_v60_actual_archive.py`, termasuk SHA/CRC, 585 DOCX + 585 Markdown + **585 PDF A4 satu halaman**, hanya 8 RPH berubah (24 fail), 577 kekal bait demi bait, satu perenggan Word sahaja diubah pada lapan RPH, bukti PBD tidak disentuh, 144 baris skema bersumberkan RPH, **124 pengiraan disemak semula bebas**, liputan 68/68, lima PDF gabungan 117 halaman dan **tidak mengubah RPT**.
- Lapan Word dirender ke PDF menggunakan LibreOffice; semuanya satu muka A4 dan margin teks dalam sempadan. Contact sheet visual lapan Word dan lima halaman contoh skema telah dilihat. Skema tambahan disusun **KeepTogether** untuk mengelakkan tajuk Lesson terpisah daripada jadual jawapan; jumlah halaman skema gabungan **24**.
- PDF gabungan Tahun 4 v60 dijana semula (117 halaman). Empat PDF gabungan Tahun 2, 3, 5, 6 dikekalkan byte-identical.
- GitHub CI v60 metadata/loader berasingan; **ZIP 49MB tidak dimuat naik ke GitHub awam**.
- Fail GitHub: `audits/matematik_v60_release_gate_RPH_only_20261108.json`, `rph_standalone/matematik/staging_preview_v60.py`, `tests/test_matematik_ba_v60_preview_20261108.py`, `tests/test_matematik_ba_v60_pbd_key_RPH_only_20261108.py`.

## HOLD akademik dan sistem
- Skema ialah jawapan/kriteria yang disediakan berdasarkan **soalan RPH sedia ada**, **bukan bukti bahawa setiap soalan sudah dipadankan dengan latihan Buku Teks asal**. **34 pasangan Tahun 4 masih belum mendapat signoff item Buku Teks pada aras soalan**, dan 585 RPH keseluruhan tidak boleh diisytiharkan FINAL READY akademik.
- **Ujian sebenar Telegram–Web staging E2E pada DB kanonik belum dilaksanakan**. Ujian ZIP/mock tidak membuktikan pengguna live menerima dokumen yang betul.
- `final_ready=false`, `rpt_changed=false`, `production_modified=false`; **PR #444 kekal DRAFT, jangan merge/deploy**. Tiada kemas kini database, akaun, kuota, bayaran atau langganan.
