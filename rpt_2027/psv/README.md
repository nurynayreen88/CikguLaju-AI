# PSV Tahun 2–6 — RPT/RPH CikguLaju 2027

Status: DRAF SEMAK, BELUM LIVE TELEGRAM.

Dokumen merangkumi 42 PdP setahun bagi Tahun 2–6, termasuk sesi projek pameran selepas Unit 5 dan Unit 10, 210 RPH Markdown dan 5+5 RPT CSV/HTML landskap. 10 unit setiap tahun telah dipadankan dengan Buku Teks dan RPT 2026 pada peringkat tajuk/teknik; Tahun 4 Unit 10 mengutamakan Buku Teks dan DSKP berbanding ralat salin contoh RPT. Aktiviti RPH masih perlu audit kandungan akhir. Minggu PdP berurutan, dan tarikh Kumpulan A/B masih kosong sehingga kalendar negeri disahkan. Jangan ubah DB produksi atau app.py semata-mata daripada bahan staging ini.

Sumber DSKP: Tahun 2: https://drive.google.com/file/d/1RA2bw9IGU9MFakT33HhgAdnjY-7H3DW8/view; Tahun 3: https://drive.google.com/file/d/1asgoqHa5EPOTzhcDz9k5G4WzdGSAg8tY/view; Tahun 4: https://drive.google.com/file/d/1CpSVz8txeDqSnKM7OfOmrjnYH9HBmGy1/view; Tahun 5: https://drive.google.com/file/d/19zvNNKKbn6mIwF7ES9I87yqNaj1xW2Fx/view; Tahun 6: https://drive.google.com/file/d/1-EmxKXK_Fn3tK-wY42ST4TNOIO0CHBHy/view
RPT 2026 awam: https://sites.google.com/moe-dl.edu.my/sekolah-kebangsaan-haji-mahmud/kurikulum/panitia-pendidikan-seni-visual/rpt-psv

## Status disahkan — 5 November 2026 (staging sahaja)

- **210/210 RPH** disediakan, 42 PdP setiap tahun (Tahun 2–6). Setiap RPH kekal berlabel DRAF dan tiada pemasangan ke Telegram LIVE.
- **66/66 ujian PSV CI lulus** pada run [41982846379](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41982846379), termasuk **210/210 Word A4 satu halaman**, preview PDF, sumber SK/SP, dan 84 ujian adapter RPH staging tanpa mengubah metadata native.
- Rekod semakan individu sedia ada: **126 PASSED kandungan dan 84 BELUM_READY penerbitan** bagi Tahun 3 dan 6. 84 RPH telah lulus semakan kandungan dan silang kod DSKP; ini **bukan** sijil pengesahan visual seluruh halaman dan bukan kelulusan siaran.
- Tahun 3: kekalkan kod rasmi bercetak **SK 5.1 bersama SP 3.3.1–3.3.5** untuk PdP projek 020, 021, 041 dan 042. Jangan menggantikan SK dengan 3.3 hanya kerana awalan SP berbeza.
- Tahun 6: Padanan asal karya telah dibetulkan untuk PdP 001 (kaktus Kampungku, ms 8–9), 018 (sisik ikan Susunan Kreatif, ms 50–51), 020 (Dompet Lemon, ms 54–55), 027 (loket dan pending, ms 62–63), dan 019 menggunakan tajuk buku teks **Gerak Beritma**. Rujukan khusus PdP 010–017 dan 021 juga diselaraskan: 26–27, 28–29, 30–31, 32–33, 34–35, 36–37, 38–43, 44–45, 56–57.

### Pintu kawalan sebelum READY / penerbitan

1. Lengkapkan bukti semakan visual dan pengesahan setiap halaman aktiviti bagi semua PdP belum diluluskan; jangan tukar `BELUM_READY` berdasarkan ujian automatik sahaja.
2. Lulus ujian **native Telegram pada servis staging PSV berasingan**. Semakan Render semasa menemui servis LIVE `CikguLaju-AI` pada `main`, sementara servis ujian web berada pada branch berlainan. Belum ada servis staging PSV khusus.
3. Sahkan kesemua 210 rekod audit, status RPH dan RPT, cap jari kandungan serta audit, kemudian sediakan `psv_release_approval.json` yang lengkap **hanya setelah** dua prasyarat di atas lulus.
4. Jangan aktifkan `CIKGULAJU_PSV_RPH_RELEASE_ENABLED` atau menggabungkan ke `main` secara pintas. Adapter mesti **fail-closed** bagi DRAF; kekalkan database dan fungsi subjek lain.

Rekod: `rph_standalone/psv/audits/psv_individual_210_review_20261105.csv` dan `rph_standalone/psv/audits/psv_84_pdp_source_followup_20261105.md`.

Nota: Ini pelan RPH Pendidikan Seni Visual semasa untuk Tahun 2–6. Ia tidak menandakan kurikulum Tahun 1 KP2027 telah disahkan.
