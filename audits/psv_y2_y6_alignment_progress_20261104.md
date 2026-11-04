# Audit sambungan PSV Tahun 2–6 | 4 Nov 2026

## Hasil yang telah dimasukkan ke staging
| Tahun | RPH aktif (draf) | Bilangan unit/rujukan RPT 2026 | Status |
|---|---:|---:|---|
| 2 | 42 | 10 | 40 PdP seni disusun semula + 2 pameran belum dijadualkan |
| 3 | 42 | 10 | 40 PdP seni disusun semula + 2 pameran belum dijadualkan |
| 4 | 42 | 9 + 1 pengayaan DSKP | 40 PdP seni + 2 pameran; konflik ukiran/diorama perlu keputusan rasmi |
| 5 | 42 | 10 | 40 PdP seni disusun semula + 2 pameran belum dijadualkan |
| 6 | 42 | 10 | RPH dibina semula mengikut 10 unit RPT 2026; pameran pertengahan & akhir ditambah |
| **Jumlah** | **210** | **50 unit/rujukan** | Semua belum READY |

- RPT 2027 lima CSV dan lima HTML dibina sepadan mengikut nombor PdP dan path fail RPH.
- Lima crosswalk RPT 2026 mengandungi nama unit, padanan teknik asal, pautan sumber; halaman disalin daripada RPT 2026, belum disemak terhadap buku teks sebenar.
- 42 RPH Tahun 6 dan RPT asal Tahun 2–6 disimpan sebagai sandaran, bukan dihapus tanpa rekod.
- Ujian struktur automatik tambahan di `tests/test_psv_rpt_rph_alignment.py`, meliputi bilangan, penomboran, SK/SP dalam CSV vs RPH dan pautan fail. **Belum ada keputusan larian CI yang disahkan**.

## Baki semakan sebelum READY
1. Padanan penuh SP DSKP dengan teks asli setiap teknik dan tahap (terutama ralat cetakan Tahun 2, dan projek Tahun 2–4).
2. Tahun 4: RPT 2026 Unit 10 mengulangi diorama, sedangkan DSKP memasukkan ukiran; bahagian pengayaan CikguLaju tidak boleh dianggap unit rasmi.
3. Tahun 2–5: tempatkan dan agihkan slot pameran pertengahan tahun dan akhir tahun mengikut bilangan PdP sekolah sebenar.
4. Kalendar sesi persekolahan 2027, kumpulan A/B, cuti sekolah, cuti gantian negeri dan PdP yang terjejas belum dipadankan. Tarikh CSV sengaja kosong.
5. Semak halaman buku teks asal, media, teknik, nilai estetik, keselamatan murid dan sama ada langkah 60 minit boleh dilaksanakan; pemeriksaan visual PDF RPH A4 dan RPT landskap belum dibuat.
6. Uji integrasi database/Telegram pada staging sahaja. `main` dan data produksi tidak diubah.

**Kesimpulan:** Susunan dan kandungan draf kini lebih hampir kepada rujukan 2026, tetapi tidak boleh dianggap selesai/lulus sehingga semakan di atas dibuat. PR #196 kekal draf.
