# Pendidikan Muzik 2027 — Quality Gate dan Bukti Sumber
**Tarikh:** 5 November 2026  
**Branch:** `staging/pendidikan-muzik-dskp-rph-audit-20261105`  
**PR:** #335 (DRAFT, JANGAN MERGE)

## Hasil semasa
| Tahun | RPT 2027 draf | RPH PdP draf | DSKP SP diinventori |
|---|---:|---:|---:|
| 2 | 1 | 35 | 20 |
| 3 | 1 | 35 | 22 |
| 4 | 1 | 35 | 19 |
| 5 | 1 | 35 | 20 |
| 6 | 1 | 35 | 18 |
| **Jumlah** | **5** | **175** | **99** |

Fail RPT (.md/.csv), RPH setiap PdP (.md), manifest JSON di `staging/pendidikan_muzik/rpt_rph_2027/year{2..6}/`. Terdapat 190 fail kandungan berkenaan, semuanya **DRAF**. Sumber aktiviti RPH disusun mengikut domain kemahiran dan SP, **belum cukup bukti mengesahkan aktiviti buku teks setiap PdP**. Tidak boleh diterbitkan secara automatik.

## Pemeriksaan buku teks Tahun 4 — masalah sumber yang disahkan

`GuruBesar_BukuTeks_Pendidikan_Muzik_T4_SK.pdf` dalam folder Pendidikan Muzik Google Drive:
- Boleh dibuka dan diperiksa secara visual; PDF mempunyai **41 halaman, kebanyakannya imbasan muka surat bercantum dua halaman**.
- Halaman judul memaparkan **Pendidikan Muzik Tahun 4 Sekolah Kebangsaan**, edisi lama. Halaman awal menunjukkan topik **Terokai Muzik / Tinggi Rendah Bunyi Pic**, bukannya unit pembuka **Senja Nan Indah** daripada RPT 2025/26 yang dijadikan sumber.
- Oleh itu, buku tersebut **tidak boleh digunakan sebagai bukti pengesahan halaman buku teks bagi RPT Semakan 2017 ini**. Semua nombor halaman pada manifest masih label rujukan RPT lama; belum verified.
- Perlu mendapatkan buku teks Tahun 4 yang sepadan dengan RPT KSSR Semakan yang menggunakan *Senja Nan Indah, Warna-Warni Kek Cawan, Beg Cantik Menawan, Bunga Gergasi* dan seterusnya. Contoh daftar unit daripada koleksi rujukan [RPT 2024](https://app.testpaper.com.my/list_detail/gJ76/rph-dan-rpt-2024-pendidikan-muzik-tahun-4) / [RPT 2020](https://anyflip.com/edoh/qmnx/basic) ialah rujukan nama sahaja, bukan pengesahan keseluruhan buku teks.

## Konflik DSKP Tahun 4 — diperiksa pada PDF visual, bukan OCR
`GuruBesar_DSKP_Pendidikan_Muzik_Tahun_4.pdf`:
- PDF halaman ke-**38** (nombor bercetak **26**): SK **3.1 Pengkaryaan Muzik**, tetapi SP dicetak **3.2.1, 3.2.2 dan 3.2.3**.
- PDF halaman ke-**40** (nombor bercetak **28**): SK **4.1 Penghayatan Karya Muzik**, tetapi SP dicetak **4.2.1**.
- RPT rujukan menggunakan **3.1.x / 4.1.1**. Jangan normalisasi atau menimpa kod dalam DB tanpa semakan versi DSKP/DPK berkuasa. Manifest T4 merekodkan SP sumber RPT dan tanda konflik. Draf RPH yang ada bukan kelulusan kod.

## Isu kandungan lain
- Tahun 3: sebahagian tajuk/unit atau SP diulang dalam slot bersebelahan. Semak sama ada pengulangan PdP dirancang guru atau salinan berganda.
- Tahun 4: Unit *Harum Mewangi* pada hujung RPT merujuk halaman 50/52 selepas Unit *Kota Ceria* halaman 90/94. Ini mencurigakan dan belum boleh disahkan.
- Tahun 5: tajuk Unit 5 dan Unit 9 serta sebahagian besar rujukan buku/audio belum disahkan.
- Tahun 6: salinan RPT lama menyebut **Baroque** sedangkan DSKP Tahun 6 **Classical**; julat rekoder DSKP meliputi C-D'.
- Tahun 2–3: rujukan Audio pada RPT tidak sama dengan bukti fail audio sebenar.
- Semua tahun: semak cuti negeri/cuti gantian Kumpulan A/B secara khusus; slot 2027 hanyalah cadangan.

## Ujian dan hasil
- GitHub tree readback: **175** fail RPH `rph_pdp_??.md`, **5** CSV RPT, **5** MD RPT dan **5** manifest unik.
- 5 manifest mempunyai **35 PdP** setahun, setiap satu dengan ID unik `MZ-Yn-xx`.
- Pakej Word/PDF untuk semakan guru telah dijana sebagai artifak perbualan ini (tidak dimasukkan ke GitHub): **5 RPT landscape** dan **5 buku RPH A4** yang masing-masing mengandungi **35 halaman untuk 35 PdP**. Dokumen diedarkan berlabel **DRAF**. Fail Word individu untuk 175 PdP turut dijana.
- Ujian `tests/test_pendidikan_muzik_rpt_rph_2027_staging.py` ditambahkan pada branch. **Keputusan GitHub Actions masih perlu disahkan; ujian daripada repository belum disahkan lulus**.

## Release gates
[ ] Buku teks sepadan dan nombor halaman disahkan PdP demi PdP  
[ ] Audio, skor atau muzik sebenar disahkan; jangan reka track  
[ ] Konflik DSKP/RPT Year 4 diselesaikan dengan sumber autoritatif  
[ ] RPT 2027 lengkap serta tarikh cuti negeri Kumpulan A/B disahkan  
[ ] 175 RPH dinilai kandungan satu persatu dengan evidens, bukan sekadar format satu halaman  
[ ] Ujian staging / pembaca Word-PDF / format Telegram sebenar lulus  
[ ] Selaraskan satu sumber generator antara Web dan Telegram  
[ ] Kelulusan penerbitan, checksum dan audit non-destructive sebelum `main`

**TIADA kemas kini** kepada `main`, SQLite produksi, Supabase pengguna, Telegram/Web runtime, akses pelanggan atau referral.
