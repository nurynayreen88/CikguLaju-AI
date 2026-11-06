# Matematik Tahun 2–6 — Buku Aktiviti evidence ledger, 7 Nov 2026

**Status: STAGING ONLY; 0/585 RPH diluluskan untuk padanan Buku Aktiviti v41.** Fail ini bukan perubahan kandungan Telegram/Web, DB atau penjanaan pengguna.

## Bukti ditemui
- Arkib Matematik v41: 585 RPH teknikal (117 Lesson setiap Tahun 2–6) dilaporkan dalam audit 5 November. Ini **tidak** bermaksud 585 padanan BA sudah disahkan.
- Drive mempunyai imbasan Buku Aktiviti Matematik **Tahun 2** dan **Tahun 3**. Belum ada padanan halaman dan aktiviti yang disahkan secara individu kepada *Lesson v41*.
- Salinan guru **Tahun 2 v27** merekod **72 sesi cadangan / 71 RPH asal** (36A/36B); semua 72 mempunyai **calon nombor halaman BA**. Audit v27 sendiri menyatakan PRA-READY, semakan BT, RPT dan SK/SP belum selesai.
- Audit visual v41 pernah menyampel topik **6 Lesson** (T2 001,023,024; T3 016,051,052); ia bukan pengesahan halaman, latihan dan semantik individu.
- Carian sumber Drive semasa belum menemukan BA terverifikasi untuk Tahun 4–6. **Jangan anggap buku tersebut tiada dalam pasaran; sumber belum dijumpai/disahkan dalam simpanan yang diperiksa.**

## Fail
- `matematik_ba_legacy_t2_v27_candidates_20261107.csv`: **72 calon**, hanya rujukan halaman bercetak dan nama sesi; **bukan** pemetaan v41. Sumber Drive asal kekal persendirian; tiada fail PDF, kandungan latihan atau ID dokumen peribadi dimuat naik ke GitHub awam.
- `matematik_ba_v41_585_ledger_20261107.csv`: **585 identiti v41**, status PENDING, tiada nombor halaman rekaan.
- `tools/matematik_ba_stage_gate_20261107.py`: fungsi opt-in untuk membina rujukan BA **hanya** apabila semua semakan diluluskan. Tidak diimport ke runtime.
- `tests/test_matematik_ba_stage_gate_20261107.py`: ujian untuk kekangan fail-closed.

## Peraturan sebelum sebarang integrasi
1. Baca kandungan lesson v41 sebenar dan padankan tajuk, semua SP, objektif, aktiviti serta PBD dengan Buku Teks **dan** Buku Aktiviti sebenar. Jangan padankan hanya berdasarkan nombor `RPH 01` atau persamaan tajuk.
2. Semak halaman **bercetak**, nombor latihan, naskhah/edisi dan halaman PDF; rekod bukti serta penyemak. Jika BA tidak sesuai untuk lesson, tandakan `NOT_APPLICABLE` beralasan, bukan cipta rujukan.
3. Hanya entri `APPROVED` boleh digunakan oleh fungsi opt-in. Kekalkan RPH asal jika bukti tidak lengkap; jangan sisip rujukan BA palsu.
4. Semak perubahan A4 Word/PDF, pengiraan, penilaian, 34 sesi pecahan Tahun 4, serta aliran Telegram/Web di staging. Pentadbir mesti meluluskan satu per satu sebelum penerbitan.

**Tiada merge/deploy dan tiada perubahan data produksi dilakukan oleh kerja ini.**

Sumber teknikal v41: https://github.com/nurynayreen88/CikguLaju-AI/blob/audit/matematik-evidence-gate-20261105/audits/matematik_v41_585_rph_release_gate_20261105.md
