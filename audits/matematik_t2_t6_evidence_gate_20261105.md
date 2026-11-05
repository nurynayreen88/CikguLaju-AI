# Matematik Tahun 2–6 — evidence gate (5 November 2026)

**Keputusan: RPT v28 lulus struktur / belum FINAL READY kandungan dan RPH.**

## Bukti yang diperiksa

- Sumber: 5 PDF RPT Matematik 2027 v28 dalam folder Drive, 5 DSKP Matematik Tahun 2–6, RPT Matematik Tahun 4 83 PdP v20, Buku Teks Matematik Tahun 4 SK, dan adapter Telegram GitHub.
- Semua lima RPT mengandungi tepat 117 ID Lesson (001–117) dan 44 minggu (01–44): jumlah **585/585 Lesson**. PDF sumber Drive: A4 landscape, tiada halaman kosong atau blok teks di luar sempadan.
- Setiap 585 entri mempunyai kod SP, kandungan aktiviti/cadangan PdP, dan PBD dalam PDF sumber Drive. Ini ialah kewujudan unsur, bukan pengesahan pedagogi.
- Kod SP unik setiap tahun dalam RPT: T2=70, T3=102, T4=85, T5=72, T6=38. Semua kod wujud dalam DSKP tahun berkenaan. T2 kod 4.1.1 diekstrak sebagai `4. 1.1` pada PDF DSKP dan telah disemak sebagai kod sah.
- RPT T4 83 PdP v20 menggunakan **set 85 kod SP yang sama** seperti RPT T4 v28 yang mempunyai 117 Lesson. Kesemua 85 kod ditemui pada halaman kandungan Buku Teks T4 SK; setiap 83 PdP mempunyai kod yang wujud dalam buku. Contoh: 2.1.3 hlm 75–79; 2.1.4 hlm 80–82; 2.1.5 hlm 83–85. Padanan ini ialah **lokasi kod SP**, bukan semakan aktiviti penuh bagi setiap RPH.

## Gate yang belum lulus

1. 117 Lesson tidak sama dengan 117 RPH diluluskan. T4 mempunyai 83 RPH sumber dan 34 Lesson cadangan pecahan; T2 mempunyai 72 sesi/RPH dalam laporan v28, dengan 47/117 Lesson belum dipaut automatik kepada RPH sumber. Bukti 117 RPH lengkap bagi T3/T5/T6 belum dikemukakan.
2. Buku Aktiviti T2 (164 halaman) dan T3 (158 halaman) ditemui tetapi sumbernya imbasan imej tanpa lapisan teks pada halaman diperiksa; perlu semakan visual untuk padanan halaman. Padanan Buku Aktiviti T4–T6 belum dibuktikan.
3. Semakan aktiviti/pentaksiran khusus terhadap halaman Buku Teks dan DSKP untuk setiap 585 Lesson belum selesai. Kod SP sahaja bukan tanda kelulusan RPH.
4. Fail PDF v28 sumber Drive berbeza saiz berbanding PDF semasa dalam GitHub `main` (T2 432980 vs 423969; T3 469436 vs 462291; T4 535262 vs 560146; T5 472523 vs 465086; T6 469316 vs 462072). PR #200 membersihkan PDF untuk guru. Audit teks/render perlu dibuat semula pada bit sebenar `main` sebelum pengesahan penerbitan.
5. Kalendar 2027, cuti umum/cuti gantian mengikut negeri, dan agihan 117 Lesson kepada masa/jadual sekolah perlu disahkan.
6. PR #168 sudah digabung dan ujian GitHub `isolated-math-rpt` lulus, tetapi mock Telegram bukan bukti live sendDocument/menu→RPH/DB aktif. Issue #250 masih membuka keperluan muka depan seperti English.

## Status rasmi audit

| Komponen | Keputusan |
|---|---|
| RPT: ID, 44 minggu, kod SP, aktiviti dan PBD hadir | **LULUS STRUKTUR** (sumber Drive v28) |
| Kod SP dalam DSKP T2–T6 | **LULUS kewujudan kod** |
| Kod SP dalam Buku Teks T4 | **LULUS lokasi kod** untuk 83 PdP |
| Ketepatan aktiviti, pentaksiran dan halaman semua RPH | **HOLD** |
| PDF yang sedang diterbitkan pada `main` | **HOLD** sehingga audit bit akhir |
| Integrasi Telegram/Web LIVE | **BELUM DISAHKAN** |
| FINAL READY keseluruhan | **TIDAK DILULUSKAN** |

**Kawalan:** report ini pada branch audit sahaja. Tiada perubahan `main`, DB, Telegram/Web, fail PDF, status pengguna atau langganan. Jangan gabung ke produksi sehingga gate di atas lulus.

## Sumber
- [Folder PDF v28 Drive](https://drive.google.com/drive/folders/1UARWx990NzWRJQnPNBJiBYhpfKbZmyOr)
- [RPT T4 83 PdP v20](https://docs.google.com/document/d/1EGrtBGrdYl8DtuMT3MuOpyaTNd0eyeJOFjOZp0_WxW8/edit)
- [Buku Teks T4 SK](https://drive.google.com/file/d/14YFkZnDxLQA_OpFMpI_eJQCTjUfQRDtZ/view)
- [GitHub RPT Matematik main](https://github.com/nurynayreen88/CikguLaju-AI/tree/main/rpt_2027/matematik)
- [PR #168](https://github.com/nurynayreen88/CikguLaju-AI/pull/168), [PR #200](https://github.com/nurynayreen88/CikguLaju-AI/pull/200), [issue #250](https://github.com/nurynayreen88/CikguLaju-AI/issues/250)
