# RPT 2027 — Semakan Kandungan Sumber Tahun 2 (28 Oktober 2026)

Status: SOURCE_REVIEW / NOT READY. Audit baca sahaja sumber Drive, bukan output RPT 2027.

## Sumber disahkan
- Pendidikan Islam Tahun 2: salinan audit terpelihara DOCX, Drive ID `1A4Xpdv_slwC86L9N90pMSjZut_tDABYP`.
- Pendidikan Jasmani Tahun 2: Rozayus_RPT_PJ_Tahun_2_SK_2026.docx, Drive ID `1iYXEatUbSTbV1B4QqLDJsRx_YrW_KsFF`.

## Dapatan kandungan yang boleh disemak semula
### Pendidikan Islam
- Jadual mengandungi bidang al-Quran, Akidah dan Jawi, serta lajur SK, SP, objektif, aktiviti dan penilaian.
- Contoh sumber awal: Akidah SK `2.1`, SP `2.1.1` dan `2.1.2`; Jawi SK `6.1`, SP `6.1.1` dan `6.1.2`.
- Terdapat rentetan cuti Tahun Baru Cina yang mencampurkan `15.02.2025` dan `19.02.2026`. Jangan tukar tahun secara regex pukal.
- Aksara Jawi asal perlu dipelihara dan diuji secara visual dalam DOCX keluaran.

### Pendidikan Jasmani
- Unit 1 Cabaran Ruang: Teroka Ruang, SK `1.1`, `2.1`, `5.1`; SP `1.1.1`, `2.1.1`, `5.1.5`; buku teks m/s 2–3.
- Unit 1 Cabaran Ruang: Bergerak Ikut Tempo, SP `1.1.2`, `2.1.2`, `2.1.3`, `5.2.2`; buku teks m/s 4–5.
- Unit 2 Mari Bersenam: Senaman Ceria, SP `1.2.1`, `1.3.1`, `2.2.1`, `5.2.1`; buku teks m/s 8–9.
- Unit 2 Mari Bersenam: Mari Melompat, SP `1.2.2`, `2.2.2`, `5.2.2`; buku teks m/s 10 (sumber menggunakan bentuk `1O`, perlu sahkan terhadap buku teks).
- Cuti/orientasi dan baris pentadbiran tidak boleh dihitung sebagai PdP unik.

## Tindakan belum selesai
1. Dapatkan takwim rasmi KPM 2027 untuk Kumpulan A/B dan semak cuti negeri sebelum pemetaan tarikh.
2. Bentuk ID PdP stabil berasingan daripada minggu/tarikh; jangan anggap baris jadual = PdP unik.
3. Bandingkan setiap SK/SP dengan DSKP dan muka surat buku teks; semak PJ dan PK sebagai komponen berbeza sebelum RPT PJPK digabung.
4. Hasilkan salinan DOCX 2027 untuk Kumpulan A/B dan audit jadual, bilangan baris, Jawi, tarikh dan layout.
5. Kekalkan semua fail sumber dan DB produksi; jangan aktifkan READY, merge atau deploy sebelum QA.

## Nota perbezaan metrik
Manifest audit sebelumnya mengira 166 baris PI dan 62 baris PJ pada tahap jadual Word. Laporan pengelasan 163 rekod merujuk set staging yang berbeza dan provisional; jangan gabungkan angka tanpa pemadanan ID baris.
