# Matematik v57 — 34 pasangan Lesson Tahun 4 (RPH sahaja)
**7 November 2026 — DRAF STAGING — QA ZIP sebenar 15/15 PASS — GitHub CI PASS — BELUM FINAL READY AKADEMIK.**

## Penemuan dan pembetulan
- Daripada **34 pasangan Lesson Tahun 4**, **32 pasangan** mempunyai set induksi yang sama walaupun Aktiviti 1, Aktiviti 2 dan PBD masing-masing berbeza. Dua pasangan (T4-L022/L023 dan T4-L056/L057) sudah mempunyai set induksi berbeza dan **tidak diubah**.
- **32 set induksi lesson kedua** ditulis semula daripada **Aktiviti 1 sedia ada** agar meneruskan kemahiran lesson pertama, bukan mengulangi pembuka yang serupa.
- **Satu set induksi lesson pertama (T4-L014)** juga dibetulkan kerana intro asal meminta murid menghitung **60 + 20 − 10** untuk SP **1.7.2 operasi bergabung darab/bahagi**. Intro baharu meminta murid menyusun operasi **24 × 15 ÷ 6**. T4-L015 pula menggunakan **48 × 25 ÷ 10** sebagai tugasan susulan.
- Selepas pembetulan **34/34 pasangan mempunyai dua set induksi berbeza**; **33 RPH/33 seksyen berubah**, **552 RPH lain byte-identical** dalam Word/PDF/Markdown. SK/SP, objektif, Aktiviti 1/2, PBD, rujukan buku dan tempoh **tidak diubah**.
- Audit before/after: `AUDIT/V57_33_SET_INDUKSI_PASANGAN_T4.csv` dalam ZIP v57. Matriks 34 pasangan: `AUDIT/V57_34_PASANGAN_T4_TOPIC_ONLY.csv` dalam ZIP.

## Sumber dan sempadan pengesahan
- Kod SP 34 pasangan dipadankan dengan bukti **DSKP Matematik Tahun 4** sedia ada (`audits/matematik_v48_34_pasangan_T4_DSKP_20261107.csv`).
- Buku Teks Matematik Tahun 4 SK (DBP, 2019) mempunyai teks rujukan yang boleh diakses di https://anyflip.com/coll/xosm/basic ; contohnya SP1.7.2 ditunjukkan dalam bahagian operasi bergabung **hlm. bercetak 45–47**. **Sumber ini digunakan sebagai rujukan topik/unit. Tidak ada dakwaan 34 pasangan sudah disahkan latihan satu persatu.**
- Buku Teks Tahun 4 dalam Google Drive asal sekitar 306MB sebelum ini melebihi had muat turun connector; perkongsian teks awam tidak semestinya menggantikan salinan asal atau menjamin padanan latihan item yang sama.
- **Status item latihan 34 pasangan: NOT VERIFIED; signoff formal guru 0**. Nombor SP sama, aktiviti berbeza dan intro berbeza **tidak menyamai kelulusan akademik penuh**.

## Arkib dan QA
- Input `CIKGULAJU_MATEMATIK_v56_585_RPH_SET_INDUKSI_T5_T6_KONKRIT_STAGING.zip`: SHA256 `f6c50114698826060bac92355ca1e476e9bf6ca921785cd0b2138e935b773695`.
- Output `CIKGULAJU_MATEMATIK_v57_585_RPH_PASANGAN_T4_INDUKSI_STAGING.zip`, **48,927,660 bait**, SHA256 `07bada94723bde54d958c11fcdfc3e46b06e59aefbcf63e26926144365331332`.
- **585 Word, 585 PDF individu A4 satu halaman, 585 Markdown**, lima PDF gabungan (masing-masing 117 halaman). Hanya PDF gabungan Tahun 4 dibina semula, empat tahun lain kekal.
- **15/15 ujian terhadap ZIP sebenar PASS** menggunakan `test_v57_actual_archive.py`: SHA sumber/hasil, ZIP CRC, tepat 33 perubahan, 552 unchanged, 34 pasangan pembuka berbeza, 33 Word/Markdown/PDF mengandungi ayat baharu, semua 585 PDF A4, lima PDF gabungan, matriks 34 pending signoff, tiada fail RPT, `final_ready=false`.
- Kesemua **33 Word** yang diubah dirender dengan LibreOffice; tidak melebihi satu halaman dan tiada teks di luar sempadan. Enam contoh visual diperiksa: **T4-L014, L015, L044, L071, L100, L117**.
- GitHub evidence CI menguji kod/metadata staging; **ZIP besar tidak dikomit ke GitHub awam**. ZIP sebenar diuji setempat, bukan di runner GitHub.
- Loader SHA-locked `rph_standalone/matematik/staging_preview_v57.py` adalah opt-in staging; jangan aktifkan sebagai sumber runtime produksi.

## Syarat HOLD
- **RPH sahaja.** RPT 2027 diurus dalam chat lain; **tiada RPT dibaca/diubah/dijana** dalam proses build v57.
- **0 signoff formal latihan**, **34 pasangan item BT belum lulus semakan akademik**, Telegram–Web real staging E2E belum dilakukan.
- **Tiada PR merge, deploy Render, edit database, kuota, pembayaran, akaun atau langganan.**
- `final_ready=false`, `rpt_changed=false`, `production_modified=false`. PR #444 kekal DRAFT STAGING.
