# Matematik Tahun 2–6 — audit v41, 5 November 2026

**STATUS: 585/585 lulus QA teknikal, BUKAN FINAL READY akademik.** Tiada perubahan ke `main`, DB pengguna, Render atau Telegram produksi.

## Keluaran dan pembetulan yang telah dibuat

- **v40: 32 RPH** dengan aksara terselit dalam teks SP/objektif diperbetulkan berpandukan DSKP rasmi: T3 = 21, T4 = 8, T5 = 3. Word/Markdown dan PDF A4 dikemaskini.
- **v41: 11 RPH tambahan** dimurnikan dengan sumber DSKP: T6 Lesson 017–020 meliputi skop penuh SP 1.4.1 (nombor perdana/gubahan, pecahan juta, perpuluhan juta, kurungan dan anu); T5 Lesson 044–045 mematuhi SP3.1.3 dan nilai RM1 juta; T3 Lesson 109 diperbetulkan frasa koordinat; T4 Lesson 101 asalan (O); T4 Lesson 097 dan T5 Lesson 100,104 menggunakan istilah segi empat sama yang betul. Pengiraan baharu diperiksa.
- **Buku Aktiviti T2/T3:** dua PDF adalah imbasan. Empat halaman PDF diperiksa secara visual untuk bukti topik enam Lesson: T2 001,023,024; T3 016,051,052. Ini **tidak** membuktikan semua latihan/halaman BA.
- **QA penuh 585:** 585 DOCX, 585 PDF individu satu halaman A4, 585 Markdown; lima PDF tahunan masing-masing 117 halaman disemak terhadap 585 PDF individu — tidak ada halaman/teks hilang. 585 SHA-256 PDF individu berbeza, 585 SHA-256 Word individu berbeza. Semua Lesson dan medan wajib lengkap. **574 RPH** luar skop perubahan v41 kekal byte-for-byte daripada v40.
- **Pratonton staging:** adapter opt-in diuji terhadap ZIP v41 sebenar: **12/12 unittest PASS**, termasuk SHA-256, 585 bacaan PDF, entitlement dan fail-closed. **Ujian simulasi, bukan penghantaran Telegram API LIVE.**

## Bukti aset tempatan
- ZIP: `CIKGULAJU_MATEMATIK_v41_585_RPH_KANDUNGAN_DSKP_STAGING.zip` (48,935,715 bytes), SHA-256 `58e9f50701e26f318829f4730b38b20ae8eb4dbffb0e8b44987c315eab36bc89`.
- Matriks 585 Lesson: `math_v41_review/CIKGULAJU_MATEMATIK_V41_MATRIKS_585.csv` (semuanya `FINAL_READY=TIDAK`), SHA-256 `cd6fc310675dedca86a76fe9cc2d57122f0266408beb5955eb13f8788c3a2a18`.
- QA individu: `math_v41_review/V41_585_PDF_AND_RPH_INTEGRITY.csv`, QA JSON: `math_v41_review/V41_FULL_585_TECHNICAL_QA.json`.
- Audit perubahan SP: `math_v40_audit/V40_SP_TEXT_CORRECTIONS_32_LESSONS.csv`; perubahan semantik `math_v41_review/V41_11_CORRECTIONS.csv`.
- Adapter simulasi: `CIKGULAJU_MATEMATIK_v41_STAGING_PREVIEW_ADAPTER.zip`.

## Baki gate akademik dan release (tiada bukti untuk mengisytiharkan lulus)

1. **Audit individu 585 Lesson** secara semantik: objektif, aktiviti guru/murid, contoh pengiraan, PBD dan halaman Buku Teks/Buku Aktiviti yang benar-benar sepadan. Kod SP hadir dalam naskhah bukan bukti aktiviti sepadan.
2. Tahun 2–3 BA PDF bergambar memerlukan semakan visual halaman yang berkaitan; tidak mengada-adakan rujukan yang tidak disahkan.
3. Tahun 4 83 ID RPH sumber →117 Lesson: 34 sesi pecahan tambahan perlu dibanding naskhah asal v15 dan signoff kandungan; 68 Lesson telah dipetakan secara asas dalam v39 tetapi belum diluluskan mendalam.
4. Takwim 2027 negeri/cuti gantian/jadual guru yang digunakan oleh RPT/RPH belum disahkan menyeluruh.
5. Uji **end-to-end Telegram staging** dengan DB kanonik, fail Word/PDF, entitlement, 10 janaan percuma, dan regresi subjek lain; **bukan** ujian mock sahaja.

**Keputusan: STAGING, `FINAL_READY=false`; tiada merge, deploy atau perubahan pangkalan data.** Arkib hampir 49 MB sengaja tidak dimuat naik ke repository GitHub awam.

Rujukan audit sebelumnya: [v39 Year4 SP 2.1.3](./matematik_v39_68_year4_source_review_sp213_20261105.md), [v38](./matematik_v38_split_session_gate_20261105.md).