# Sains Tahun 2–3 — Audit kandungan latihan Buku Aktiviti (staging)

Tarikh: 7 November 2026. PR #442 (DRAF/HOLD). **Bukan kelulusan pengguna LIVE.**

## Apa yang diperiksa

Dua Buku Aktiviti Sains SK asal (imbasan, bukan teks OCR):
- Tahun 2 — https://drive.google.com/file/d/1j0qoRWHcaAzHVgbb6uua7k_3i2-qVm0v/view
- Tahun 3 — https://drive.google.com/file/d/1kVL3PT-VjQiITqmfNXlURQA8gLYvCrI5/view

Audit terdahulu sudah membuat padanan **96 nombor halaman dan kod SP tercetak**, dengan **94 kod SP sama** dan **2 berkaitan sahaja**. Audit baharu ini membaca **isi 11 halaman latihan tertentu secara visual** dan menyediakan arahan pelaksanaan yang lebih tepat serta selamat. Ia **tidak mengesahkan kesesuaian akademik penuh baki 85 halaman** walaupun kod SP bercetak sepadan.

## 11 semakan isi latihan khusus

| Tahun | SP | Halaman bercetak | Semakan dan tindakan |
|---|---|---:|---|
| 2 | 3.1.3 | 16 | Buku meminta berat/tinggi/saiz kasut rakan. Dalam RPH guna **data rekaan** supaya tiada pendedahan maklumat tubuh peribadi murid. Ini adaptasi keselamatan, bukan salinan literal buku. |
| 2 | 4.1.7 | 27 | Halaman buku berlabel 4.1.5, jadi **bukan PBD langsung untuk SP4.1.7**. Murid menghasilkan lakaran dan penerangan sendiri daripada aktiviti RPH. |
| 2 | 5.1.6 | 36 | *Pokok Timun Saya*: bezakan keperluan biji benih bercambah dengan anak pokok membesar. |
| 2 | 6.1.6 | 44 | Halaman bayang tangan berlabel 6.1.5, **bukan PBD langsung SP6.1.6**. Guna lakaran/penerangan pemerhatian asal RPH sebagai PBD. |
| 2 | 7.1.7 | 54 | *Memasang Permainan Buzzer*: murid melakar litar; pemasangan sebenar hanya kit **sel kering voltan rendah** dengan pengawasan guru. |
| 2 | 8.1.5 | 62 | *Yang Manakah Cepat Larut?*: jawapan daripada gambar suhu, saiz gula, kacauan. **Tiada air panas untuk kendalian murid**. |
| 2 | 9.2.3 | 73 | *Kesan Angin*: padankan gambar dan kesan angin menggunakan bank kata sebenar. |
| 2 | 9.2.6 | 72 | *Mencipta Model Kapal Layar*: lakaran dahulu; jika membina, gunting hujung bulat dan pengawasan guru. |
| 3 | 3.2.3 | 30 | *Menu Makanan Pilihan Saya*: bina menu seimbang daripada gambar dan berikan sebab; elakkan membuat penilaian terhadap diet peribadi murid. |
| 3 | 6.1.6 | 61 | *Mengukur Isi Padu Pepejal Tidak Sekata*: bacaan air awal/akhir dan beza isi padu melalui sesaran air. |
| 3 | 6.1.7 | 59 | *Mengukur Isi Padu Cecair*: pemilihan alat dan cara membaca aras mata/meniskus. |

Bukti penerangan dan arahan cadangan disimpan dalam `audits/sains_y2_y3_ba_page_content_safety_review_20261107.json`. Fail mengandungi halaman, SP, tajuk latihan, jenis keputusan dan bukti yang boleh disemak semula.

## Integrasi tanpa merosakkan RPH asal

- `tools/sains_buku_aktiviti_mapping_20261107.py` memeriksa keserasian kod SP, halaman bercetak, tajuk asal **dan** 11 nota kandungan; jika nombor halaman/tajuk berubah, penjana gagal daripada memaparkan tugasan salah.
- Tambahan bahan di baris Buku Aktiviti dalam Word/PDF Tahun 2 dan 3 memberi peringatan yang boleh digunakan terus oleh guru; **Aktiviti 1/2 dan sumber SP asal tidak diganti**.
- Dua aktiviti yang tidak sepadan kod SP dilabel **BA (rujukan sahaja)** dan **RUJUKAN SAHAJA, bukan tugasan PBD**. Guru menggunakan PBD asli RPH bagi dua SP tersebut.
- `tools/check_sains_ba_96_document_content_20261107.py` membaca **96 fail DOCX dan 96 fail PDF yang benar-benar dijana** dan menyemak tajuk latihan, halaman, 11 arahan keselamatan, dua amaran bukan-PBD, manifest, dan PDF satu halaman A4. Semakan halaman Word fizikal diteruskan melalui LibreOffice dalam CI.
- Semua maklumat dibuat pada cabang staging, tanpa menyunting SQLite, akaun, peranan, langganan atau Web/Telegram produksi; sumber buku hanya dipautkan, **tidak dihos semula**.

## Baki sebelum READY

**85 latihan** belum menerima nota semakan isi khusus; semua **96** kekal belum diluluskan oleh guru/panitia. Semakan kandungan buku teks, objektif/KPS/PBD sebenar, aliran muat turun Web/Telegram staging dan rubrik akademik 80% masih belum lengkap. Nilai kod SP yang sama **bukan** bukti kualiti akademik ≥80%.

**Status keseluruhan:** STAGING / HOLD, tanpa auto-merge atau deployment produksi.

---

## Susulan 7 November 2026 — lengkap 85 nota isi tambahan (bukan kelulusan akademik)

Pemeriksaan visual semua halaman yang dipaut dalam rekod baki telah menghasilkan **43 nota Tahun 2 dan 42 nota Tahun 3** yang khusus kepada soalan/gambar latihan asal, disimpan secara berasingan sebagai `audits/sains_y2_43_remaining_page_content_20261107.json` dan `audits/sains_y3_42_remaining_page_content_20261107.json`. Bersama 11 nota terdahulu, liputan editorial kandungan sumber kini **96/96**. Seluruh 96 memerlukan pengesahan guru/panitia; keadaan `teacher_academic_approved=false` dan `STAGING_HOLD` dikekalkan.

Contoh perkara yang dibetulkan dalam panduan baharu:
- **Y2 SP9.1.2 m/s65:** petunjuk imbasan mencadangkan memotong botol dengan pisau. Bahan dipotong oleh guru sahaja; murid menganalisis arah aliran air pada gambar.
- **Y2 SP8.1.4 m/s62:** pilihan air panas ditafsir melalui gambar sahaja.
- **Y3 SP8.1.2 m/s72:** buku mempunyai arahan rasa/sentuh bahan berasid/beralkali. RPH melarang murid menguji rasa/sentuhan; guna kertas litmus atau data selamat.
- **Y3 SP8.1.4 m/s76:** situasi sengatan tidak digunakan untuk menyuruh rawatan kulit DIY.
- **Y3 SP5.1.3 m/s50:** pemotongan ubi/keratan dengan pisau hanya dilakukan guru.

Laporan versi ini mengatasi angka lama **11/96** untuk liputan nota kandungan; angka lama ialah checkpoint audit terdahulu, bukan status akhir. Ujian baharu `tools/check_sains_ba_96_document_content_20261107.py` menuntut kesemua 96 nota dipaparkan dalam fail Word/PDF sebenar serta format satu halaman A4.
