# Matematik T2–T6 v39 — audit akademik sumber Tahun 4 (2026-11-05)

**Keputusan: STAGING. FINAL READY = FALSE. Telegram production = NOT VERIFIED.**

## Bukti semakan terkini
- **68 Lesson Tahun 4** (34 pasangan yang berkongsi 34 ID RPH asal) diperiksa secara individu bagi identiti Lesson, kod SP dalam DSKP, lokasi SP di Buku Teks Tahun 4 SK, petunjuk topik buku, perbezaan PBD kedua-dua sesi, struktur RPH dan SHA-256 fail. **34/34** pasangan mempunyai kod SP yang wujud dalam DSKP dan lokasi halaman buku teks; PBD sesi kedua berbeza daripada PBD pertama. Semakan topik/kod ini **BUKAN** kelulusan semua aktiviti berdasarkan halaman buku.
- Pemeriksaan konservatif **40 persamaan nombor bulat/perpuluhan** daripada pasangan tersebut: 40/40 betul. Ungkapan pecahan bercampur tidak dimasukkan jika berisiko salah tafsir parser.
- **Isu akademik sebenar dikesan dan diperbaiki:** Tahun 4 Lesson **022–023**, SP **2.1.3**. DSKP Matematik Tahun 4 halaman PDF 52 membezakan **(i) menolak dua nombor** daripada **(ii) menolak dua nombor daripada satu nombor**. Pakej v38 mengulang penolakan satu langkah dalam kedua-dua Lesson.
- **v39 Lesson 022** khusus 2.1.3(i); **v39 Lesson 023** khusus 2.1.3(ii) dengan penolakan berturutan. Kedua-duanya mempunyai empat item PBD berbeza dengan jawapan disemak **8/8 tepat**, contoh, langkah guru-murid dan rujukan **Buku Teks Tahun 4 bercetak halaman 75–78 (PDF 81–84)**. Kedua-dua DOCX dirender dan ditinjau secara visual: **1 halaman A4** setiap satu.
- PDF gabungan Tahun 4 dikemaskini pada halaman 22–23; **115 RPH Tahun 4 lain dan 468 RPH Tahun 2,3,5,6 dikekalkan**. Arkib v39 lulus ZIP CRC dan 585/585 PDF individu 1 halaman A4; lima PDF tahunan 117 halaman.
- Arkib pengguna: `CIKGULAJU_MATEMATIK_v39_585_RPH_PEMBETULAN_SP213_STAGING.zip`, **48,093,070 bytes**, SHA-256 `f24d054211c0dd6ca89e8e043ae3142b85fb6ad2413f078898c7075dba116bee`.
- Matriks 585 baris versi v39: `CIKGULAJU_MATEMATIK_V39_585_RPH_RELEASE_MATRIX.csv`, **442,977 bytes**, SHA-256 `95ed6385da079a100f6353e9b9b68fa3dd4888e1bb1b70c0ed9c075aa27db344`.
- Bukti CSV dalam arkib: `AUDIT/MATEMATIK_T4_v39_AUDIT_68_LESSON_BUKU_TEKS.csv` dan `AUDIT/MATEMATIK_T4_v39_AUDIT_34_PASANGAN_BUKU_TEKS.csv`.

## Pembetulan syarat Buku Aktiviti
[E-Katalog Buku Teks rasmi KPM](https://www.moe.gov.my/storage/files/shares/Banner/E-Katalog%20Buku%20Teks%20KPM.pdf) secara jelas menyenaraikan Matematik Tahun 2–3 SK dengan **Buku Aktiviti** (BA082001 / BA083001) tetapi tidak menyenaraikan BA Matematik SK berasingan untuk Tahun 4–6 pada senarai yang sama. **Jangan tahan kelulusan Tahun 4–6 semata-mata kerana tiada BA berasingan**. Rujukan utama Tahun 4–6 ialah DSKP dan Buku Teks; latihan tambahan guru boleh digunakan jika sesuai. Penemuan ini tidak membuktikan tidak wujud sebarang buku kerja komersial.

## Yang masih belum FINAL
- **583 RPH lain** belum melalui semakan mendalam aktiviti dan PBD terhadap halaman buku yang tepat; semua 585 belum diuji dalam Telegram LIVE.
- Untuk Tahun 2 dan 3, BA perlu dipadankan dengan latihan individu; Tahun 4–6 fokus Buku Teks dan DSKP.
- Hubungan Tahun 4 daripada **83 sumber kepada 117 Lesson** masih memerlukan naskhah 83 RPH asal v15 dan bukti kesesuaian setiap pecahan sesi, bukan sekadar kod SP.
- Kalendar negeri/cuti 2027 dan ujian enjin runtime, akses, DB staging serta regresi subjek lain belum lulus.
- **Jangan merge, deploy atau paparkan FINAL READY**. Semua artefak v39 hanya di working staging; tiada perubahan ke `main`, DB pengguna, Telegram production atau Render.

Laporan terdahulu: [audit v38](./matematik_v38_split_session_gate_20261105.md).