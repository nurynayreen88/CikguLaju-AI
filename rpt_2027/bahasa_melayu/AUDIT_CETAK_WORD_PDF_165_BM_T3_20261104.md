# Audit cetakan RPH dan RPT Bahasa Melayu Tahun 3 2027 — 4 November 2026

**Status: DRAF SEMAKAN, BELUM READY / BELUM LIVE.** Laporan ini merekod ujian fizikal format yang dijalankan terhadap pakej hasil GitHub Actions run [41745205617](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41745205617).

## Keputusan

| Komponen | Semakan | Keputusan |
|---|---|---|
| RPH Tahun 3 Markdown dalam staging | 165/165 fail | Lengkap |
| PDF RPH A4 dalam pakej | 165 fail, 165 satu halaman | Lulus |
| DOCX RPH dibuka melalui LibreOffice dan dicetak PDF untuk pruf | 165 fail, **165 satu halaman A4** | Lulus semakan bilangan halaman |
| RPT Tahun 3 | 44 minggu, 165 Lesson, A/B digabung | Lengkap struktur |
| RPT Word landscape | 16 halaman landscape setelah penukaran melalui LibreOffice | Lulus orientasi |
| RPT PDF landscape yang dihasilkan untuk semakan | 16 halaman landscape, tiada halaman kosong | Lulus semakan asas |
| Ujian GitHub CI pemetaan RPH/RPT/SK/SP/PKJR | 165 Lesson, 28 PKJR, 0 HOLD | Lulus, run 41745205617 |

Keluaran ini disediakan sebagai pakej DRAF (bukan penerbitan READY). Ujian ini memeriksa orientasi, jumlah muka surat, keserasian membuka fail dan struktur, **bukan** pengesahan pakar bagi semua aktiviti, kebenaran takwim negeri atau demonstrasi runtime Telegram.

## Kawalan READY yang kekal belum lulus

1. Padan akademik seluruh 165 RPH kepada Buku Teks/Buku Aktiviti/DSKP — pembetulan terarah telah dijalankan, tetapi belum ada perakuan lengkap satu-persatu.
2. 44 minggu RPT ialah susunan calon. Kalendari negeri, cuti ganti, minggu **BELUM AGIH** dan jadual guru sebenar masih belum disahkan.
3. BPG/BAM PKJR telah dipetakan pada 28 RPH untuk DRAF, tetapi kelulusan guru untuk pengajaran bersepadu dan pentaksiran belum diberikan.
4. CI struktur lulus, tetapi ujian penjanaan runtime Telegram/Web dan pemasangan database utama belum dibuat.
5. Belum diluluskan sebagai bahan produk oleh pemilik projek.

**Syarat penerbitan kekal fail-closed** melalui `rpt_2027/bahasa_melayu/READY_GATE.json` (`DRAFT_NOT_PUBLISHED`, `verified_strict_ready=false`). Semua fail dipelihara dalam branch `staging/bm-rpt-2027-20261103`; `main`/database aktif/Telegram/Web tidak diubah.
