# Audit sambungan Bahasa Melayu SK — RPT 2027 (Batch 3, 3 November 2026)

**Status: DRAF TERKAWAL, bukan READY.** Pembetulan hanya pada branch `staging/bm-rpt-2027-20261103`. Tidak mengubah `main`, database, Telegram, Web atau RPH standalone.

## Semakan struktur selepas pembetulan

| Tahun | Lesson calon | Unit | Minggu M01–M44 | Padanan Markdown–HTML (ID, tema/tajuk, SK, SP) |
|---|---:|---:|---:|---|
| 2 | 164 | 24 | 44 | 164/164 |
| 3 | 165 | 24 | 44 | 165/165 |
| 4 | 165 | 27 | 44 | 165/165 |
| 5 | 166 | 27 | 44 | 166/166 |
| 6 | 165 | 27 | 44 | 165/165 |
| **Jumlah** | **825** | **129** | **220 slot minggu** | **825/825** |

Padanan diuji pada ID Lesson, tajuk aktiviti, SK dan SP bagi setiap baris fail `.md` dan `.html`. Ini ialah pemeriksaan keselarasan dua format, **bukan pengesahan akademik semua 825 lesson**.

## Perubahan kandungan daripada RPT BM SK 2026 (mengekalkan Lesson asal)

| Tahun | Rekod dibetulkan | Keterangan |
|---|---:|---|
| 2 | 4 | SP 3.3.1 (i), konteks penulisan separa terkawal |
| 3 | 6 + 1 pembetulan ejaan | SP 3.2.1 (i)/(ii), ayat/perenggan; ejaan `Bacaan Luaas` → `Bacaan Luas` pada BM3-P047 |
| 4 | 12 | SP 2.2.1 (6) dan 3.3.1 (6) dilengkapkan daripada teks RPT sumber |
| 5 | 12 | SP 2.2.1 (6) dan 3.3.1 (6) dilengkapkan daripada teks RPT sumber |
| 6 | 20 + 2 tajuk | SP 1.1.3 (3), 2.2.1 (7), 3.3.1 (7), 4.4.1 (3); BM6-P020 bertajuk `Nasihat Pakar Pemakanan`, BM6-P100 dibersihkan daripada catatan editorial `Tambah rph` |

**Jumlah: 54 pembetulan SP + 3 tajuk/ejaan = 57 rekod pembetulan.** Setiap pembetulan dibuat serentak pada Markdown dan HTML. Bilangan Lesson asal tidak berubah.

Sumber silang RPT 2026: [Tahun 2](https://docs.google.com/document/d/1qFUGCNH672R4QYBSxzSCYUbTiVmTQQU0/edit), [Tahun 3](https://docs.google.com/document/d/1wlrI120RKhZh85oSPIZPPgJwj7CKChsT/edit), [Tahun 4](https://docs.google.com/document/d/103e8N7kZvR_tPr9TLy8TaM8Yz6VMeoQ-/edit), [Tahun 5](https://docs.google.com/document/d/1q0vWe8ydZonJsAohVEe121u-0A2xMrg7/edit), [Tahun 6](https://docs.google.com/document/d/1g0HR5PGuW9CMQFJZLcDbXUD0qZwlMJK1/edit). Dokumen asal mungkin mengandungi ralat ejaan/catatan editorial. Ayat SP yang diperoleh daripada RPT 2026 **belum menggantikan audit perbandingan dengan DSKP primer**.

## Baki kualiti sebelum READY

1. **12 calon ulangan** dalam `AUDIT_PENGULANGAN_19_BM_2027.md` masih perlu rujuk halaman BT dan niat aktiviti sebenar. Jangan padam/dinombor semula secara automatik.
2. **Tahun 2, tiga baris Penilaian Tema** (BM2-P023, P047, P094) tidak mempunyai SP baharu dalam RPT sumber; ini bukan ralat kod kosong yang boleh diisi secara andaian. Tetapkan sasaran pentaksiran berasaskan SK/SP terdahulu apabila reka RPH.
3. **Buku Aktiviti Tahun 2–3**: belum ada naskhah penuh yang disahkan dalam sumber projek. Halaman BA calon tidak boleh dijadikan arahan latihan yang disahkan.
4. Semak setiap ayat SK/SP dan subkod roman terhadap DSKP primer; sebahagian entri sumber mempunyai teks terpotong atau variasi akibat pemindahan 2026. Semakan regex pendek di atas tidak membuktikan semua ayat lengkap.
5. Peruntukan waktu, hari PdP, cuti negeri/gantian, aktiviti sekolah serta minggu BELUM AGIH belum dimuktamadkan; minggu ordinal bukan tarikh Lesson sebenar.
6. Tahun 1 adalah kohort **KP2027** berasingan, bukan salinan RPT KSSR 2026. Word DOCX bermuka depan dan RPH BM standalone belum diterbitkan.

**Kesimpulan:** Draf Tahun 2–6 lengkap dari segi struktur 825 Lesson dan mempunyai fail HTML cetak A4 landscape + Markdown, namun belum layak READY sehingga audit primer, buku, takwim dan RPH selesai.
