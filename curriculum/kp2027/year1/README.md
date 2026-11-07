# CikguLaju — KP2027 TAHUN 1 sahaja

**Status: DRAF/HOLD (7 November 2026). Untuk semakan editorial guru, bukan untuk penerbitan RPH/RPT KP2027.**

Sasaran kerja ialah kohort **Tahun 1 pada 2027**. Kelas Tingkatan 1 tidak dipadam daripada inventori asal tetapi **ditangguhkan** dan tidak terkandung dalam pakej ini.

## Pakej kerja semasa

| Subjek calon | RPH contoh Tahun 1 | Peringkat pembuktian | Status |
|---|---:|---|---|
| Alam dan Manusia | 3 | Portal penataran menyenaraikan DK, PDF asal belum diaudit | DRAF/HOLD |
| Bahasa Melayu SK | 3 | Bahan penataran ada, dokumen DK SK belum diambil | DRAF/HOLD |
| Matematik | 3 | Penataran Tahun 1, DK belum disahkan | DRAF/HOLD |
| Pendidikan Islam | 3 | Pautan DK di PPD Saratok, akses fail 403 | DRAF/HOLD |
| Bahasa Arab | 3 | Pautan DK Tahun 1 di penataran, akses fail 403 | DRAF/HOLD |
| Bahasa Inggeris | 3 | Laporan penataran sahaja | DRAF/HOLD |
| Pendidikan Moral | 3 | Laporan penataran sahaja | DRAF/HOLD |
| Pendidikan Jasmani dan Kesihatan | 3 | Laporan penataran sahaja | DRAF/HOLD |
| **Jumlah** | **24** | **0 standard rasmi disahkan** | **0 READY** |

Data 24 contoh: [`candidate_rph_year1_24_20261107.json`](candidate_rph_year1_24_20261107.json). 15 contoh diambil semula daripada batch asal dan 9 draf baharu ialah Bahasa Inggeris, Pendidikan Moral dan PJPK. **Tidak mendakwa 8 subjek ini satu senarai tawaran rasmi lengkap.** Semakan struktur boleh dilaksanakan melalui ujian yang disertakan.

## Keutamaan audit sumber

1. **Alam dan Manusia** — peroleh PDF `DKP2027 ... TAHUN 1_PENATARAN2`, sahkan versi dan semak struktur pengetahuan/kemahiran pembelajaran bersepadu serta model pengajaran bersesuaian.
2. **Bahasa Melayu SK** — asingkan SK daripada SJK; semak kemahiran mendengar, bertutur, membaca dan menulis dengan nombor SP/SPi sebenar.
3. **Pendidikan Islam & Bahasa Arab** — dapatkan salinan dokumen rasmi Tahun 1 yang boleh dibaca (pautan Drive PPD Saratok belum dapat diakses). Semak jawi dan tulisan Arab secara visual sebelum diaktifkan.
4. **Matematik** — sahkan DK Tahun 1, unit, bilangan PdP dan peruntukan masa; pendekatan konkrit–bergambar–simbol dalam draf ini bukan pengganti standard sebenar.
5. **Bahasa Inggeris, Pendidikan Moral, PJPK** — penghasilan contoh editorial dibenarkan tetapi penyusunan RPT rasmi ditahan sehingga DK Tahun 1 diperoleh dan disahkan.

## Pagar keselamatan

- Kandungan 24 contoh ialah bahan asal CikguLaju sebagai **cadangan pengajaran**, bukan transkripsi SP/SPi KPM; semua `official_sk`, `official_sp`, `official_spi`, `official_page` mesti `null` sehingga audit dokumen asal.
- Nombor `C01–C03` ialah bilangan **contoh editorial**, bukan nombor PdP rasmi; semua tempoh 60 minit adalah **andaian contoh** yang perlu diselaraskan kemudian.
- Jangan gunakan buku teks/aktiviti KSSR lama sebagai buku rasmi KP2027; tiada muka surat baharu direka.
- Jangan ubah `app.py`, DB SQLite utama, API pengguna, kuota, pembayaran atau menu Telegram/Web kerana hasil ini.
- Setelah audit versi PDF, halaman standard dan urutan mata pelajaran, hasilkan RPT Kumpulan A/B dan RPH Word/PDF 1 halaman satu demi satu; semak kualiti kandungan dan muat turun sebenar.
- Program Pembentukan Karakter wujud sebagai program berasingan dan nilai karakter disepadukan dalam RPH; jangan cipta mata pelajaran baharu dengan kod standard palsu.

**Status release: 0/24 READY. Tanggungjawab semakan akademik dan penerbitan masih terbuka.**
