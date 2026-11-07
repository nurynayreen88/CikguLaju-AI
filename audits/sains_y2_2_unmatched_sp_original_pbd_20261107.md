# Bukti PBD alternatif untuk dua SP Sains Tahun 2 tanpa padanan Buku Aktiviti langsung

**Tarikh:** 7 November 2026  
**Skop:** STAGING sahaja / PR #442 / status **DRAF/HOLD**  
**Larangan:** Jangan jadikan latihan ini halaman rasmi Buku Aktiviti KPM; jangan deploy ke Telegram/Web produksi atau mengubah DB sebelum pengesahan akademik.

## Dapatan sumber utama

DSKP Sains Tahun 2 KSSR Semakan 2017 asal (KPM), tersedia di: https://drive.google.com/file/d/1rr4CjNvhtI13ioiVSTZi65cvap7j1U6Z/view

- **SP 4.1.7:** *Menjelaskan pemerhatian tentang pembiakan dan tumbesaran melalui lakaran, TMK, penulisan atau lisan.* Buku Aktiviti Tahun 2 m/s 27 (*Ceritakan tentang Kitar Hidup Rama-rama*) **berlabel SP 4.1.5**, bukannya 4.1.7.
- **SP 6.1.6:** *Menjelaskan pemerhatian tentang terang dan gelap melalui lakaran, TMK, penulisan atau lisan.* Buku Aktiviti Tahun 2 m/s 44 (*Mencipta Bayang-bayang Tangan*) **berlabel SP 6.1.5**, bukannya 6.1.6.

Buku Aktiviti sumber: https://drive.google.com/file/d/1j0qoRWHcaAzHVgbb6uua7k_3i2-qVm0v/view. Muka surat 27 dan 44 diperiksa sebagai imej imbasan; nombor SP bercetak telah dibaca daripada footer halaman. Kedua-duanya kekal dalam data rujukan sebagai **RELATED_DIFFERENT_SP__DO_NOT_ASSIGN_AS_SP_PBD**, bukan bahan pengukuhan langsung untuk SP lain.

## Tugasan PBD alternatif yang telah ditulis

| PdP | SP | Tajuk lembaran asli | Bukti PBD individu |
|---|---|---|---|
| T2 PdP 010 | 4.1.7 | *Kitar Hidup dan Tumbesaran Haiwan — Saya Boleh Menjelaskan* | Empat peringkat rama-rama dilakar dan dilabel; dua perubahan diperhatikan; satu penerangan berdasarkan bukti |
| T2 PdP 022 | 6.1.6 | *Terang, Gelap dan Bayang-bayang — Pemerhatian Saya* | Dua lakaran lampu menyala/padam; dua pemerhatian perbezaan; penerangan hubungan sumber cahaya, objek legap dan bayang |

Kedua-duanya menyokong bukti **lakaran, penulisan atau lisan** sebagaimana DSKP, tetapi guru mesti menilai setiap murid dan boleh menyesuaikan masa dan tahap kebolehan. Arahan keselamatan: jangan meminta murid mendedahkan maklumat peribadi, memegang haiwan hidup, menghalakan lampu suluh ke mata, atau menggunakan elektrik soket rumah.

Penjana fail: `tools/render_sains_y2_2_sp_alternative_pbd_20261107.py` mengeluarkan dua Word dan dua PDF cetakan A4. Fail menggunakan label **BUKAN LATIHAN BUKU AKTIVITI RASMI** dan mempunyai tiga kriteria PBD bagi setiap SP. Ini ialah tugasan asli yang disediakan untuk menangani jurang sumber, **bukan halaman buku teks/buku aktiviti KPM yang direka**.

## Keserasian dan fail disimpan

- `tools/render_sains_y2_51_rph_draf_20261107.py` memasukkan medan lampiran PBD alternatif pada dua RPH sahaja; 49 PdP T2 yang lain tidak diubah menjadi ada lampiran palsu.
- `web/sains_buku_aktiviti_resources_20261107.py` menyediakan metadata **`PBD_ALTERNATIF_CIKGULAJU`** dengan nama fail staging sahaja, bukan URL muat turun LIVE yang direka. `ready_for_runtime=False` dan `teacher_academic_approved=False`.
- `tests/test_sains_y2_2_sp_alternative_pbd_20261107.py` memeriksa dua SP asal, identiti PdP, kriteria dan larangan dakwaan buku rasmi.
- `tools/check_sains_ba_96_document_content_20261107.py` menyemak dua RPH mengandungi arahan menggunakan lampiran alternatif dan dua Word/PDF asal benar-benar dihasilkan, berlabel bukan Buku Aktiviti rasmi.
- GitHub CI staging menjalankan cetakan Word melalui LibreOffice; PDF mesti tepat **satu halaman A4**, teks SP/kriteria/eviden tidak hilang. Baki semua 96 RPH Word/PDF terus melalui ujian semula.

## Had pengesahan

**Kedua-dua lembaran masih DRAF/HOLD.** Kod SP dan tugasan per murid berasaskan DSKP, namun **guru/panitia belum mengesahkan** keberkesanan tugas, tahap kesukaran, kecukupan pentaksiran dan kebolehlaksanaan kelas. PBD alternatif tidak menjadikan dua halaman BA yang berlainan SP sebagai 'padan', dan tidak mengubah statistik **94 padanan kod SP Buku Aktiviti + 2 rujukan berkaitan sahaja**. Keseluruhan 96 RPH Sains T2–T3 masih dalam senarai semakan panitia.

Tiada suntingan SQLite, data lama, kuota, pembayaran, bot Telegram atau Render Web.
