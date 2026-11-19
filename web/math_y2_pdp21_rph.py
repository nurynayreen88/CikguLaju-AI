"""Source-backed RPH for the Year 2 two- and three-number addition lessons."""
from web.math_rph_delivery_quality_20261110 import _slot_minutes


def install(runtime):
    previous = runtime._rph_rows

    def render_rows(state, *args, **kwargs):
        rows = previous(state, *args, **kwargs)
        if state.get("subject") != "Matematik" or state.get("sk_code") != "2.1":
            return rows
        addition_lesson = state.get("pdp_sequence_code"), state.get("sp_code")
        if addition_lesson not in (("MT2-PDP-020", "2.1.1"), ("MT2-PDP-021", "2.1.2")):
            return rows

        duration = _slot_minutes(state.get("rph_time")) or 60
        induction = max(1, duration // 12)
        guided = max(1, duration * 3 // 10)
        assessment = max(1, duration // 4)
        closing = induction
        practice = duration - induction - guided - assessment - closing
        # A slot shorter than the five planned phases is still an invalid plan.
        if practice < 1:
            return rows

        if addition_lesson[0] == "MT2-PDP-020":
            return {
                **rows,
                "STANDARD KANDUNGAN": "2.1 Tambah dalam lingkungan 1000.",
                "STANDARD PEMBELAJARAN": "2.1.1 Menambah dua nombor hasil tambah dalam lingkungan 1000.",
                "OBJEKTIF PEMBELAJARAN": "Murid menambah dua nombor dalam lingkungan 1000 dan menjawab sekurang-kurangnya 3 daripada 4 soalan dengan tepat.",
                "KRITERIA KEJAYAAN": "Sekurang-kurangnya 3 hasil tambah betul. Murid menyusun digit mengikut nilai tempat dan menunjukkan pertukaran apabila perlu.",
                "PENGETAHUAN SEDIA ADA": "Murid tahu nilai tempat sa, puluh dan ratus.",
                "BAHAN BANTU MENGAJAR": "Buku Teks Matematik Tahun 2 Jilid 1, ms. 48–57, blok asas 10 dan carta nilai tempat.",
                "EMK / NILAI": "Teliti menyusun digit dan menyemak hasil tambah.",
                "KBAT / PAK21": "Jelaskan mengapa 10 sa ditukar kepada 1 puluh.",
                "PENTAKSIRAN": "Guru semak empat hasil tambah dan catat murid yang masih tersilap pada langkah pertukaran.",
                "SET INDUKSI": (
                    f"{induction} minit\n"
                    "Guru tambah tujuh blok sa kepada lapan blok sa. Murid kumpulkan semula sebagai 1 puluh dan 5 sa."
                ),
                "AKTIVITI UTAMA": (
                    f"Aktiviti 1 – Tambah dalam bentuk lazim ({guided} minit)\n"
                    "Guru modelkan 248 + 137 pada carta sa, puluh dan ratus. Murid rekod pertukaran 15 sa kepada 1 puluh 5 sa.\n\n"
                    f"Aktiviti 2 – Latihan pasangan ({practice} minit)\n"
                    "Murid selesaikan 156 + 273 dan 278 + 146. Guru semak lajur digit dan minta murid terangkan pertukaran pada setiap lajur.\n\n"
                    f"Aktiviti 3 – Pentaksiran individu ({assessment} minit)\n"
                    "Murid jawab 213 + 145, 326 + 158, 248 + 175 dan 507 + 286. Guru semak hasil 358, 484, 423 dan 793."
                ),
                "PENUTUP": f"{closing} minit\nMurid tunjuk satu tanda pertukaran dalam jawapan. Guru betulkan satu kesilapan lajur.",
                "PEMULIHAN / PENGAYAAN": "Bimbing pertukaran berpandukan blok. Murid yang menguasai mencari nombor yang perlu ditambah kepada 248 supaya jumlahnya 385.",
            }

        return {
            **rows,
            "STANDARD KANDUNGAN": "2.1 Tambah dalam lingkungan 1000.",
            "STANDARD PEMBELAJARAN": "2.1.2 Menambah tiga nombor dengan hasil tambah dalam lingkungan 1000.",
            "OBJEKTIF PEMBELAJARAN": "Murid menambah tiga nombor dalam lingkungan 1000 dengan tepat bagi sekurang-kurangnya 3 daripada 4 soalan.",
            "KRITERIA KEJAYAAN": "3 daripada 4 jawapan tepat. Digit disusun mengikut nilai tempat dalam bentuk lazim.",
            "PENGETAHUAN SEDIA ADA": "Murid boleh menambah dua nombor dan mengenal nilai tempat sa, puluh dan ratus.",
            "BAHAN BANTU MENGAJAR": "Buku Teks Matematik Tahun 2 Jilid 1, ms. 58–61, kad nombor, carta nilai tempat dan papan putih mini.",
            "EMK / NILAI": "Ketelitian dan kerjasama.",
            "KBAT / PAK21": "Membandingkan dua cara menambah dan menerangkan kesilapan susunan digit.",
            "PENTAKSIRAN": "Semak empat jawapan individu dan catat murid yang masih tersalah menyusun digit atau mengumpul semula.",
            "SET INDUKSI": f"{induction} minit\nGuru tunjuk tiga kad skor 20, 35 dan 45. Murid tulis ayat matematik untuk jumlah skor.",
            "AKTIVITI UTAMA": (
                f"Aktiviti 1 – Tambah dalam Bentuk Lazim ({guided} minit)\n"
                "Guru modelkan 46 + 128 + 205. Murid tambah dua nombor dahulu, kemudian cuba semula dengan menyusun ketiga-tiganya dalam bentuk lazim.\n\n"
                f"Aktiviti 2 – Semak Nilai Tempat ({practice} minit)\n"
                "Guru beri 83 + 216 + 147. Murid berpasangan membetulkan digit yang tersalah lajur dan menerangkan cara mengumpul semula.\n\n"
                f"Aktiviti 3 – Pentaksiran Individu ({assessment} minit)\n"
                "Murid jawab 4 soalan: 23 + 104 + 210, 38 + 46 + 125, 146 + 217 + 318 dan 265 + 178 + 124. Guru semak hasil dan susunan digit."
            ),
            "PENUTUP": f"{closing} minit\nMurid terangkan cara menyusun digit sa, puluh dan ratus. Guru ulas satu kesilapan lazim.",
            "PEMULIHAN / PENGAYAAN": "Pemulihan dengan carta nilai tempat dan tiga nombor tanpa mengumpul semula. Pengayaan dengan menentukan satu skor yang hilang apabila jumlah diberi.",
        }

    runtime._rph_rows = render_rows
