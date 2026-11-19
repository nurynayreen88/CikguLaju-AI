"""Reviewed two-number subtraction focus for SK Year 2 PdP 017.

DPK Edisi 3, hlm. 24, lists SK 2.2 and SP 2.2.1. The two-number
lesson is one part of that standard. MOBIM Matematik Tahun 2 (KPM,
2024), hlm. 62–63, maps regrouping to Buku Teks Jilid 1, hlm. 66–72,
and Buku Aktiviti, hlm. 44–48. This lesson uses textbook hlm. 66–69.
The assessment retains the two exercises and answers in the approved RPT.
"""


def document(heading, details):
    details = [details[0], ("PdP / Tempoh", "PdP 017 · 60 minit"), *details[2:4]] + [
        ("Standard Kandungan", "2.2 Tolak dalam lingkungan 1000."),
        ("Standard Pembelajaran", "SP 2.2.1 Menolak hingga tiga nombor dalam lingkungan 1000. "
         "Fokus sesi ini ialah penolakan dua nombor dengan mengumpul semula."),
        ("Rujukan", "DPK Edisi 3, hlm. 24 · Buku Teks Jilid 1, hlm. 66–69 · Buku Aktiviti, hlm. 44–48"),
        ("Objektif Pembelajaran", "Murid menolak dua nombor dalam lingkungan 1000 dengan mengumpul semula "
         "dan menyelesaikan kedua-dua soalan pentaksiran dalam bentuk lazim."),
        ("Kriteria Kejayaan", "2 daripada 2 hasil tolak betul. Murid menyusun digit mengikut lajur dan "
         "menanda sekurang-kurangnya satu pertukaran yang betul."),
        ("Pengetahuan Sedia Ada", "Murid mengenal nilai tempat ratus, puluh dan sa serta boleh menolak tanpa mengumpul semula."),
        ("Bahan Bantu Mengajar", "Blok asas sepuluh, carta nilai tempat, papan putih mini dan buku murid."),
    ]
    activities = [
        ("Fasa / Masa", "Tindakan Guru", "Tindakan Murid"),
        ("Set Induksi\n5 minit",
         "Paparkan 452 pada carta nilai tempat. Tanya sama ada 8 sa boleh diambil daripada 2 sa dan bagaimana "
         "bilangan sa boleh ditambah tanpa mengubah nilai 452.",
         "Bina 452 dengan blok. Tukar 1 puluh kepada 10 sa dan jelaskan bahawa jumlah keseluruhan kekal sama."),
        ("Aktiviti 1\nDemonstrasi\n15 minit",
         "Modelkan 452 − 178. Tunjukkan pertukaran pada lajur sa, kemudian lajur puluh. Pindahkan setiap "
         "perubahan daripada blok ke bentuk lazim dan bincangkan contoh dalam Buku Teks hlm. 66–69.",
         "Rekod 452 sebagai 3 ratus, 14 puluh dan 12 sa selepas dua pertukaran. Tolak mengikut lajur. "
         "Terangkan bagaimana baki 2 ratus, 7 puluh dan 4 sa membentuk 274."),
        ("Aktiviti 2\nLatihan Berpandu\n15 minit",
         "Beri 416 − 128 dan 673 − 248. Semak penjajaran digit. Minta pasangan bandingkan lajur yang memerlukan "
         "pertukaran. Gunakan satu latihan sesuai daripada Buku Aktiviti hlm. 44–48 jika pasangan sudah bersedia.",
         "Bergilir membina model dan merekod bentuk lazim. Bandingkan jawapan 288 dan 425. Terangkan mengapa "
         "soalan pertama memerlukan dua pertukaran dan soalan kedua hanya satu."),
        ("Aktiviti 3\nPBD Individu\n20 minit",
         "Beri 531 − 247 dan 620 − 156. Periksa jawapan, penjajaran digit dan bukti pertukaran. Catat murid "
         "yang masih keliru apabila digit sa ialah sifar.",
         "Selesaikan kedua-dua soalan secara individu. Tanda lajur yang ditukar dan semak satu jawapan dengan "
         "menambah baki kepada nombor yang ditolak."),
        ("Penutup\n5 minit",
         "Bincangkan satu kesilapan pada lajur sa atau puluh. Tunjuk hubungan antara ayat tolak dan ayat tambah.",
         "Gunakan 284 + 247 = 531 untuk menerangkan semakan. Sebut pertukaran 1 puluh kepada 10 sa."),
    ]
    reflection = [
        ("Evidens PBD", "Hasil 284 dan 464, penjajaran tiga lajur dan bukti pertukaran pada kerja individu."),
        ("Pemulihan", "Bimbing 352 − 126 dengan blok dan carta. Murid ulang satu pertukaran sebelum merekod bentuk lazim."),
        ("Pengayaan", "Murid cari nombor yang hilang dalam 620 − □ = 464 dan sahkan dengan operasi tambah."),
        ("Refleksi", "___ / ___ murid mencapai kedua-dua kriteria.\n"
         "___ murid memerlukan bimbingan. Fokus susulan ________________________________"),
    ]
    return heading, details, activities, reflection
