# Matematik Tahun 1–6 — titik semakan Buku Aktiviti / RPH, 7 November 2026

## Keputusan semasa
**Audit sumber dan indeks selesai dalam skop yang tersedia; pelepasan RPH Matematik belum selesai.**
**Tiada RPH v41 yang dapat ditanda FINAL READY.** Jangan merge PR ini atau terbit kepada pengguna.
Tahun 1 perlu diproses berasingan menurut sumber rasmi KP2027 baharu; 585 RPH yang direkodkan adalah **Tahun 2–6 sahaja**.

## Kerja yang benar-benar diselesaikan
1. Disahkan melalui imbasan PDF asal: Buku Aktiviti Matematik SK Tahun 2 (164 halaman PDF; bercetak 1–156; PDF = bercetak +6) dan Tahun 3 (158 halaman; bercetak 1–155; PDF = bercetak +3). Dua TOC dan halaman awal/akhir dilihat secara visual.
2. **190** entri isi kandungan BA (T2:84, T3:106), dengan peta nombor halaman bercetak↔PDF: `matematik_ba_t2_t3_visual_toc_20261107.csv`. Julat akhir per topik berasal daripada permulaan topik seterusnya; setiap latihan di halaman tersebut **belum** disemak satu per satu.
3. **72/72** rujukan halaman dalam RPH salinan guru Tahun 2 v27 berada dalam julat topik TOC yang betul; **0** merentasi topik dan **0** di luar julat. Ini hanya pengesahan isi kandungan, **bukan** padanan semantik v41.
4. **9** sampel aktiviti BA telah diperiksa pada halaman asal dan dihubungkan kepada calon Lesson RPT v28 (T2:3, T3:6). Tiada sampel diluluskan untuk v41 kerana RPH kandungan v41 tidak tersedia untuk dibaca.
5. Semua **585** lesson RPT Matematik v28 Tahun 2–6 mempunyai kod SP yang dapat diindeks. 72 rekod lama Tahun 2 → 64 mempunyai calon SP RPT v28 (21 satu calon, 43 berbilang), 8 tiada calon. Keputusan SP ini **bukan kelulusan** dan tidak boleh membenarkan pindahan halaman automatik.
6. Katalog rasmi **KPM E-Katalog Buku Teks 2023** mengesahkan **BA Matematik SK Tahun 2 (BA082001)** dan **Tahun 3 (BA083001)**. Untuk Tahun 4–6, katalog menyenaraikan buku teks SK (T4 BT084002; T5 BT085002; T6 BT08001) dan tiada entri BA Matematik SK pada bahagian yang diperiksa. Ini tidak menafikan kewujudan buku kerja komersial; jangan mereka-reka muka surat BA. Gunakan aktiviti buku teks yang sah dan sumber PBD bersesuaian.
7. Semua fail dan ujian disimpan di cabang staging sahaja. Gate `verified_ba_reference` hanya mengeluarkan teks BA jika mempunyai bukti halaman, latihan, naskhah, semantik, penyemak dan `APPROVED`; semua rekod sedia ada **NOT_APPROVED**.

## Halangan pelepasan yang tidak boleh diabaikan
- ZIP `CIKGULAJU_MATEMATIK_v41_585_RPH_KANDUNGAN_DSKP_STAGING.zip` (SHA256 `58e9f50701e26f318829f4730b38b20ae8eb4dbffb0e8b44987c315eab36bc89`), 585 sumber RPH, **belum ditemui dalam GitHub, Drive dan Library yang dapat dicapai pada semakan ini**. Rekod lama menyatakan arkib kekal tempatan dan tidak dimuat naik ke GitHub public. Tidak wajar membuat semula kandungan daripada andaian.
- Tiada pengesahan individu 585 RPH terhadap halaman Buku Teks/Buku Aktiviti, pengiraan/PBD, atau 34 sesi pecahan Tahun 4. Tiada QA satu-halaman terhadap *RPH yang diubah*, dan ujian end-to-end Telegram/Web staging selepas integrasi.
- Tahun 1 KP2027 memerlukan DK/penjajaran kurikulum terkini; **tiada BA atau RPH Tahun 1 KP2027 diluluskan dalam kerja ini**.
- Fail Buku Teks/BA yang besar dan hak cipta tidak dipindahkan ke repositori GitHub awam.

## Release gate
**HOLD / STAGING; 0/585 RPH v41 cleared.** Dapatkan semula arkib v41 sah, semak semantik setiap lesson terhadap sumber (BA untuk T2–3, Buku Teks/PBD untuk T4–6), kelulusan manual, ujian PDF/Word A4 dan aliran Telegram/Web staging. Jangan menganggap integriti indeks membuktikan kesiapsiagaan pengguna.

## Rujukan
- KPM: https://www.moe.gov.my/storage/files/shares/Banner/E-Katalog%20Buku%20Teks%20KPM.pdf
- Audit v41: https://github.com/nurynayreen88/CikguLaju-AI/blob/audit/matematik-evidence-gate-20261105/audits/matematik_v41_585_rph_release_gate_20261105.md
- PR staging: https://github.com/nurynayreen88/CikguLaju-AI/pull/444
