# Pendidikan Moral Tahun 2–6 — laporan release gate 4 November 2026

**Keputusan: TIDAK LULUS UNTUK PRODUKSI.** Pemilik meminta merge ke main dan Telegram hanya SELEPAS semua ujian lulus. Jangan gabungkan PR #179 atau tandakan 210 draf ini READY.

## Bukti yang telah lulus
- 210 RPH standalone, 70 kad aktiviti, 210 baris CSV RPT, 350 kod SP dalam DSKP crosswalk.
- CI struktur GitHub run 41782399623 lulus.
- 210 RPH mempunyai tempoh cadangan 60 minit dengan fasa 5 + 20 + 20 + 10 + 5.
- Indeks halaman permulaan 70 unit buku teks selaras dengan RPT.
- Lima PdP 001 (Y2–6) diperkemas dengan contoh visual buku teks dan evidens PBD.

## Punca gagal (dikesan melalui DB v26.00 sebenar, bukan tekaan)
- CI DB parity run 41783143891 FAIL. Padanan nombor PdP, kod SP dan teks untuk 210 rekod dibandingkan dengan database v26.00 yang direkonstruksi kepada direktori sementara.
- Tahun 2 PdP 008, SP 3.3: sumber draf DSKP mengandungi artifak OCR `keluarga 3.` yang tiada dalam dokumen rasmi. Kini dibetulkan di crosswalk, RPH dan kad unit 3.
- Tahun 2 PdP 011, SP 4.4: DB produksi v26.00 tersimpan `Mengamalkan sikap berterima kasih terhadap keluarga.` (teks SP 4.5), sedangkan DSKP asal memerlukan `Melahirkan perasaan apabila berterima kasih terhadap keluarga.`. DB produksi TIDAK diubah. `scripts/preview_pm_y2_sp44_v2600_safe_patch.py` hanya membetulkan salinan sementara dengan precondition exact-match.
- Selagi DB produksi tidak dibetulkan dalam versi baharu yang diluluskan, paparan SP 4.4 Telegram tidak selaras dengan DSKP sebenar.

## Jadual waktu dan RPT
- KPM Panduan Pelaksanaan Jadual Waktu PdPR (2021), Lampiran 1 KSSR Semakan 2017 SK Tahap 1 dan Tahap 2, menyenaraikan peruntukan masa **180 minit seminggu** untuk Pendidikan Islam/Pendidikan Moral (120 PdP + 60 tutorial sewaktu PdPR). Ini rujukan sejarah untuk pembandingan; perlu sahkan peruntukan kurikulum/takwim 2027 yang terpakai.
- **42 RPH × 60 minit = 2520 minit** sahaja bagi setahun. Jika 180 minit seminggu dan ~38–42 minggu, rancangan perlu menerangkan baki waktu/pengukuhan/tutorial atau pecahan 3 slot. Jangan anggap 42 draf RPH merangkumi keseluruhan peruntukan masa.
- RPT masih CSV DRAF, Kumpulan A/B kosong, belum ada Word/PDF landscape, cuti tambahan KPM 2027 dan negeri/kelas belum dipadankan. Tarikh per kelas tidak boleh diandaikan.
- Kalendar 2027 rasmi KPM: https://www.moe.gov.my/index.php/kalendar-akademik-semasa ; pemetaan berdasarkan lampiran sahaja.

## Keperluan sebelum merge
1. Sahkan semua 210 RPH terhadap aktiviti buku teks sebenar per SP dan semak pedagogi, bukan TOC sahaja.
2. Tentukan liputan 180 minit mingguan / sebenar, bilangan sesi, padanan minggu A/B dan cuti negeri.
3. Sediakan 5×2 RPT Word/PDF landscape dengan tarikh dan semakan A4.
4. Betulkan DB SP 4.4 pada versi copy-based, dengan parity dan regresi DB serta tiada overwrite.
5. Uji RPH dalam Word/PDF sebenar dan laluan Telegram termasuk akses RPT berbayar, butang kembali, dokumen, kuota, dan subjek lain.
6. Semak PR berbanding main terkini, CI semua, baru deploy; Render bot auto deploy dari main.

**Semua kerja terkini berada di staging; main/DB aktif/Telegram tidak disentuh.**
