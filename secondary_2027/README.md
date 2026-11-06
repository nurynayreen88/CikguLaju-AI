# CikguLaju — Sekolah Menengah 2027 (staging only)

Bahan awal ini **tidak diaktifkan pada Telegram atau Web**. Ia tidak mengubah fail produksi, skema DB atau data sekolah rendah.

## Pemisahan kohort
- Tingkatan 1 sesi 2027: **KP2027**. Jangan import atau papar RPH KSSM sebagai KP2027. Tunggu DK subjek rasmi dan naskhah buku teks 2027 yang disahkan.
- Tingkatan 2–5 sesi 2027: **KSSM** yang berkuat kuasa, dengan sumber DSKP, RPT/SOW dan buku teks yang sepadan.
- Tahun berikutnya: semak kohort pelaksanaan semula sebelum guna katalog ini.

## Batch kandungan yang mula disediakan
- `data/bm_t2_pdp_001_005.json`: **5 RPH Bahasa Melayu Tingkatan 2**, Tema 1, Unit 1, PdP 1–5. Setiap RPH mengandungi standard, objektif boleh ukur, set induksi, **Aktiviti 1**, **Aktiviti 2**, pengukuhan/penilaian, penutup, tindakan guru-murid, pembezaan dan bukti PBD.
- Kod SK/SP disemak terhadap DSKP KSSM BM Tingkatan 2 (BPK, 2016). Tajuk dan rujukan halaman asalnya dicadangkan oleh RPT BM Tingkatan 2 2025 yang tersimpan di Drive. **Padanan halaman dengan buku teks sebenar belum disahkan**; jangan lepaskan ke pengguna sebagai READY.

## Sumber dan rekod audit
- DSKP: https://drive.google.com/file/d/1xtVFZirPVpMV6GMCs2ZNO46dBX0xl4iw/view
- RPT: https://docs.google.com/document/d/19Hb9U6gY_ghzVUF-B6_U-ks6C64v7qEC/edit
- Rujukan English Secondary lama: `ENGLISH_SECONDARY_V25_08_MERGE_PLAN.md` (cadangan 560 lesson, **bukan bukti integrasi live**).
- RPT 2027: urutan kurikulum diselaraskan dengan kalendar sebenar A/B selepas data sekolah/cuti disahkan; RPT tahun lalu tidak dipindah tarikh mentah.

## Pintu READY
1. Semak tiap tajuk/aktiviti dan muka surat terhadap buku teks asal (bukan RPT sahaja).
2. Sahkan SK/SP, unit, nombor PdP, tempoh, bahasa, kelengkapan langkah dan hasil PBD untuk setiap rekod.
3. Uji Word/PDF A4 sebenar, penghasilan tanpa AI runtime, dan dropdown akhir PdP/Lesson pada Telegram/Web yang berkongsi sumber DB.
4. Semak izin distribusi fail buku berhak cipta; jangan menerbitkan salinan buku teks secara automatik.
5. Integrasi secara **additive**, backup/version baharu, audit integrity/FK/orphan/duplicate, uji staging dan barulah mohon kelulusan produksi.

## Keutamaan selepas pilot
BM/English/Matematik/Sains/Sejarah Tingkatan 2–5; diikuti Pendidikan Islam, Pendidikan Moral, Geografi, RBT, PJPK; elektif Tingkatan 4–5 ikut permintaan. Tingkatan 1 berjalan dalam aliran KP2027 berasingan.
