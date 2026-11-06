# Pendidikan Muzik Tahun 2–6 — STAGING sahaja

**Tarikh semakan:** 5 November 2026  
**Status:** `DRAF / TIDAK UNTUK PRODUKSI`

## Semakan yang sudah dilakukan

| Tahun | SP dikesan dalam DSKP | Draf aktiviti berasaskan SP | Padanan RPT 2026 / buku teks / audio |
|---|---:|---:|---|
| Tahun 2 | 20 | 20 | BELUM DISAHKAN |
| Tahun 3 | 22 | 22 | BELUM DISAHKAN |
| Tahun 4 | 19 | 19 | BELUM DISAHKAN |
| Tahun 5 | 20 | 20 | BELUM DISAHKAN |
| Tahun 6 | 18 | 18 | BELUM DISAHKAN |
| **Jumlah** | **99** | **99** | **BELUM DISAHKAN** |

Lima fail `y{tahun}_dskp_sp_rph_seeds.json` ialah **inventori SP dan draf aktiviti**, bukan 99 RPH PdP yang boleh diterbitkan. Setiap rekod mempunyai objektif draf, set induksi, dua aktiviti utama, penilaian/pengukuhan, penutup dan bahan. Penilaian buku teks, kualiti satu halaman A4 dan urutan RPT belum dibuat.

### Penemuan kritikal — Tahun 4
Dalam DSKP KSSR Semakan 2017 Tahun 4 yang disimpan di Drive, tajuk SK **3.1 Pengkaryaan Muzik** diikuti SP **3.2.1, 3.2.2, 3.2.3**, dan SK **4.1 Penghayatan Karya Muzik** diikuti SP **4.2.1**. Nombor yang tidak selari ini juga terdapat dalam salinan PDF DSKP yang diterbitkan semula. **Jangan menukar kod tersebut secara automatik** kepada 3.1.x atau 4.1.x. Keempat-empat entri ditanda `flag_kod_sk_sp_tidak_sepadan=true` untuk pengesahan manusia terhadap dokumen bercetak/halaman asal.

### Sumber yang telah tersedia
- Google Drive (folder Pendidikan Muzik): `GuruBesar_DSKP_Pendidikan_Muzik_Tahun_2.pdf` hingga `Tahun_6.pdf`.
- Google Drive: `GuruBesar_BukuTeks_Pendidikan_Muzik_T4_SK.pdf` (buku teks Tahun 4 sahaja yang dikenal pasti di folder ini).
- RPT 2026 awam untuk Tahun 1–6: https://www.cikgupress.com/2025/12/rpt-pendidikan-muzik-kssr-semakan-2026.html (rujukan pencarian, fail belum diimport/diuji).
- RPT 2026 Tahun 2 alternatif: https://id.scribd.com/document/991449446/Rpt-Pendidikan-Muzik-Tahun-2-Sk-2026 (belum dianggap bukti siap).

### Batasan pembetulan dan penerbitan
1. **Tahun 1** tidak diisi dengan DSKP lama di sini. Gunakan aliran **KP2027 Tahun 1** yang berasingan; kurikulum lama tidak diubah.
2. Jangan merge branch ini atau aktifkan Telegram/Web berdasarkan draf SP sebelum pemetaan berurutan **Unit/Tajuk → PdP → SK/SP → RPT → Buku Teks/Halaman → Audio** disahkan.
3. Tiada perubahan dilakukan pada `main`, `app.py`, SQLite master, Supabase, akaun pelanggan, referral atau status langganan.
4. Fail draf ini ialah data sandaran untuk penyediaan **RPH PdP sebenar**, bukan pengganti penjana RPH Telegram.

### Baki sebelum FINAL READY
- Semak **RPT 2026 bagi Tahun 2–6** dan tetapkan bilangan PdP mengikut aliran sebenar (jangan ambil bilangan SP sebagai bilangan PdP).
- Padankan semua Unit/Tajuk, aktiviti buku teks, halaman dan audio yang sebenar dengan SP.
- Gantikan setiap draf dengan RPH PdP terperinci, objektif boleh diukur dan penilaian bermakna; hasilkan Word/PDF satu halaman dan audit satu demi satu.
- Sediakan RPT 2027 landscape dengan muka depan dan takwim **Kumpulan A/B**; semak cuti negeri mengikut peraturan yang ditetapkan pengguna.
- Jalankan QA lintas subjek (tiada overwrite/FK orphan/duplicate) serta ujian Telegram dan Web **sebelum** pertimbangan `main`.

## Ujian

Jalankan `python -m unittest tests.test_pendidikan_muzik_staging -v` selepas fail ini tersedia dalam working tree.
