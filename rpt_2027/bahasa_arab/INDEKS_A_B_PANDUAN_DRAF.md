# Indeks RPT 2027 Bahasa Arab Tahun 2–6 (DRAF)

Kumpulan A/B masing-masing mempunyai **298 baris calon PdP** berdasarkan 16 CSV sumber yang disimpan sebelum ini. Tahun2=60, Tahun3=60, Tahun4=58, Tahun5=60, Tahun6=60. Pemeriksaan tidak mendapati ID berulang dalam sumber.

**Tarikh PdP, waktu dan negeri kosong secara sengaja.** Kalendar asas A/B (mula 4 Jan 2027; kumpulan A tamat 2 Dis, B tamat 3 Dis) sahaja diturunkan daripada dokumen induk tersambung di Drive. Semakan KPM terkini, cuti negeri/gantian, penjadualan kelas, jumlah waktu subjek dan kelulusan guru belum selesai. Jangan keluarkan sebagai RPT tahunan akhir.

Semua entri `DRAF_TARIKH_BELUM_DISAHKAN`, `ready=FALSE`. Gunakan `python scripts/check_bahasa_arab_rpt2027_crosswalk_stage.py` untuk audit silang. **0 FINAL READY**, DB dan produksi tidak disentuh.

## Ujian teknikal 298 A4
- [298 DOCX + 298 PDF satu halaman A4 lulus](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42147097355). Ujian struktur 298 lulus (42147137049). **0 FINAL READY**; penilaian pedagogi, cuti negeri, tarikh PdP dan Telegram/Web masih belum diuji/disahkan.

## QA tambahan untuk calon FINAL READY (6 November 2026)
- [Semakan struktur setiap 298 RPH dan 596 indeks A/B](https://github.com/nurynayreen88/CikguLaju-AI/pull/378): **0 ralat struktur, 0 amaran halaman sumber** (GitHub Actions PR #378); ini membuktikan keutuhan pemetaan sahaja, bukan padanan pedagogi/DSKP muktamad.
- Mula sesi **4 Januari 2027**, tamat A **2 Disember 2027**, tamat B **3 Disember 2027** sepadan pengumuman KPM, dirujuk melalui [portal kalendar rasmi](https://www.moe.gov.my/index.php/kalendar-akademik-semasa) dan [RTM](https://berita.rtm.gov.my/nasional/senarai-berita-nasional/senarai-artikel/kpm-umum-sesi-persekolahan-2027-bermula-4-januari/).
- **Masih belum final:** semua cuti umum/gantian dan cuti tambahan negeri, jumlah waktu Bahasa Arab, tarikh setiap PdP, kelulusan guru individu dan ujian runtime Telegram/Web. Tiada tarikh PdP direka, tiada rekod READY diubah.

## Semakan agihan masa DSKP
Dokumen DSKP Bahasa Arab KSSR Semakan 2017 Tahun 5/6 merujuk kepada **sekurang-kurangnya 48 jam setahun** bagi sekolah kebangsaan, berdasarkan SPI Bil. 8 Tahun 2016 (contoh rujukan DSKP Tahun 6: https://asiemodel.net/wp-content/uploads/2022/08/DSKP-KSSR-Semakan-2017-Bahasa-Arab-Tahun-6.pdf). Jumlah **60/58 calon PdP** dalam indeks ini ialah pengagihan kerja CikguLaju, **bukan pengesahan cukup waktu rasmi** kerana durasi setiap PdP belum diisi. Semak kesepadanan jam tahunan, RPT 2026 dan jadual sekolah sebelum READY.
