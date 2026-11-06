# Audit silang buku teks BM Tingkatan 4–5 — 7 November 2026

## Hasil yang boleh disahkan
- Buku teks sebenar dalam Drive telah dibaca secara tempatan (PDF teks, dan contoh halaman diperiksa melalui render imej).
- **Tingkatan 4:** 54/54 kod SP DSKP muncul dalam buku teks yang tersedia; 108 RPH draf (dua variasi/SP) kini berpadanan dengan kod, tajuk dan **nombor halaman bercetak**.
- **Tingkatan 5:** 48/48 kod SP DSKP muncul dalam buku teks yang tersedia; 96 RPH draf (dua variasi/SP) kini berpadanan dengan kod, tajuk dan nombor halaman bercetak.
- T4 indeks PDF mempunyai **offset +22** terhadap halaman bercetak (contoh SP 1.1.1, tajuk *Kitalah Juara!*, m/s 3 = PDF halaman 25).
- T5 indeks PDF mempunyai **offset +24**, **bukan +26** (contoh SP 1.1.1, tajuk *Cergaskan Dirimu* dengan bahan *Bersenam di Alam Hijau*, m/s 3 = PDF halaman 27). Versi awal tersasar dua halaman dan telah dibetulkan dalam indeks dan kesemua 96 RPH Tingkatan 5.
- Tiga ralat bacaan kod panjang bukan SP DSKP (T4 `2.3.12`, `4.2.14`; T5 `2.3.22`) dikecualikan.
- Nota ketepatan tajuk: beberapa tajuk berbilang baris/kolum di dalam isi kandungan menyebabkan padanan teks tidak bersebelahan; tajuk seperti *Bulat Air kerana Pembetung*, *Tiada Tercicir, Tiada Terpinggir*, *Indahnya Bimasakti*, dan *Dari Kopitiam ke Kafe Hipster* disemak dengan muka surat kiri (permulaan bahan) dan muka surat kanan (kod SP). Beberapa butiran jenis aktiviti asal masih belum diaudit manual satu demi satu.

## Rujukan fail staging
- `data/bm_t4_t5_textbook_sp_102_anchor_index.json` — kod SP, tajuk dan m/s disemak dari buku; tiada salinan isi buku disertakan.
- `data/bm_t4_dskp_54sp_108rph_draft.json` — 108 RPH dengan `source_book` dan aktiviti berasaskan topik sebenar.
- `data/bm_t5_dskp_48sp_96rph_draft.json` — 96 RPH dengan `source_book` dan aktiviti berasaskan topik sebenar.
- `tests/test_bm_textbook_quality.py` — semak 102 indeks dan 204 rekod secara automatik.
- `data/bm_full_460_master_manifest_20261107.json` — empat pek calon import; **jangan** tambah pek lama 5/60/120/180.

## Masih belum READY
1. **Padanan halaman dan kewujudan kod SP BUKAN pengesahan RPH secara penuh**. Semak arahan setiap aktiviti asal, rangsangan sebenar dan ketepatan objektif.
2. RPH Tingkatan 4–5 adalah **dua contoh bagi setiap SP**. Ini **bukan susunan PdP/RPT 2027**. Susunan RPT/sesi/cuti Kumpulan A dan B mesti dipetakan secara berasingan.
3. Semak PBD dan kebolehlaksanaan bagi guru (masa, bahan, tahap, pemulihan/pengayaan) dan preview PDF/Word A4.
4. Jangan mengaktifkan Telegram/Web atau main, jangan memuat naik buku teks PDF ke repo, dan jangan menjana pautan muat turun buku berhak cipta secara sewenang-wenang.
5. T2/T3 masih perlukan audit terhadap buku teks Tingkatan 2/3 yang sepadan, bukan buku Tahun 2/3.
6. Tingkatan 1 2027 menggunakan **KP2027**; jangan mewarisi SK/SP KSSM atau templat tema terdahulu.

## Sumber asal dalam Drive
- Buku BM Tingkatan 4 KSSM: `1kXLu1ndQeE4BHvp1AWxnBpEIUI0oQjkY`
- Buku BM Tingkatan 5 KSSM: `1vHicn5bs9xAIcETkearILtLo9-VIpZyj`
- DSKP BM Tingkatan 4–5 KSSM: `1j0hOd_RQYd4w3p8fj3yCmxc-UyabDQO5`
