"""Sains Tahun 3 KSSR: PdP asal CikguLaju untuk Unit 1 dan 2.

SK/SP: DSKP Sains Tahun 3 (Semakan 2017), m/s 44–52.
https://c.zoom-a.com/cache/dbp/refpub/1668664909464/DSKP-Sains-3-%28Semakan-2017%29.pdf
Rujukan halaman bercetak: Buku Teks Sains Tahun 3, Dewan Bahasa dan Pustaka.
https://fliphtml5.com/ptqlr/bxbt/D3_BUKU_TEKS_SAINS_-_SAINS_SKDAM/
Aktiviti dan PBD ialah rancangan pengajaran CikguLaju. Nombor PdP baharu
disambung selepas 45 PdP sedia ada supaya identiti lama kekal.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Lesson:
    number: int
    standards: tuple[str, ...]
    title: str
    pages: str
    objective: str
    materials: str
    induction: str
    guided: str
    independent: str
    assessment: str
    closure: str
    follow_up: str

    @property
    def code(self):
        return f"ST3-PDP-{self.number:03d}"

    @property
    def sk(self):
        return self.standards[0].rsplit(".", 1)[0]

    @property
    def unit(self):
        return "Peraturan Bilik Sains" if self.sk == "2.1" else "Kemahiran Saintifik"


SK = {
    "1.1": "Kemahiran Proses Sains",
    "1.2": "Kemahiran Manipulatif",
    "2.1": "Peraturan Bilik Sains",
}
# Ringkasan pernyataan SP bagi ruang RPH. Kod SP mengikut DSKP.
SP = {
    "1.1.1": "Memerhati",
    "1.1.2": "Mengelas",
    "1.1.3": "Mengukur dan menggunakan nombor",
    "1.1.4": "Membuat inferens",
    "1.1.5": "Meramal",
    "1.1.6": "Berkomunikasi",
    "1.2.1": "Menggunakan alatan dan bahan sains dengan betul",
    "1.2.2": "Mengendalikan spesimen secara cermat",
    "1.2.3": "Menghasilkan lakaran spesimen, alatan atau bahan dengan betul",
    "1.2.4": "Membersihkan alatan sains dengan cara yang betul",
    "1.2.5": "Menyimpan alatan dan bahan sains dengan betul dan selamat",
    "2.1.1": "Mematuhi peraturan bilik sains",
}

LESSONS = (
    Lesson(46, ("1.1.1",), "Memerhati menggunakan deria", "2–3",
           "Merekod tiga ciri dua objek dan menyatakan deria bagi setiap pemerhatian.",
           "Kapas, span kering, bekas legap, kad rekod.",
           "Guru menunjukkan dua objek. Murid menyatakan perkara yang boleh diperhatikan dengan mata.",
           "Guru menunjukkan cara memerhati kapas dengan mata dan sentuhan. Murid merekod warna dan tekstur pada kad.",
           "Murid memerhati span secara individu dan menambah satu ciri. Guru meminta murid menyemak padanan ciri dengan deria.",
           "Semak tiga catatan individu dan padanan deria pada kad. Minta murid menunjukkan cara mereka mendapat satu pemerhatian.",
           "Murid menerangkan bagaimana dua deria memberikan maklumat yang berbeza tentang span.",
           "Sediakan kad pilihan deria. Murid yang sudah menguasai kemahiran membandingkan dua objek berdasarkan satu ciri."),
    Lesson(47, ("1.1.2",), "Mengelas berdasarkan ciri sepunya", "4–5",
           "Mengelaskan enam kad objek mengikut satu ciri yang boleh dilihat dan melabel kedua-dua kumpulan.",
           "Kad bentuk pelbagai warna, alas kumpulan, sampul kad individu.",
           "Guru menunjukkan kad dengan warna sama tetapi bentuk berlainan. Murid menyebut satu persamaan dan satu perbezaan.",
           "Guru meminta murid memilih satu ciri untuk pengelasan. Murid mengasingkan kad mengikut ciri pilihan dan menerangkan sebab.",
           "Murid mengelaskan enam kad baharu secara individu dan melabel kedua-dua kumpulan. Guru menyemak kad yang tersalah kumpulan.",
           "Semak enam kad dan dua label. Minta murid menjelaskan ciri sepunya yang digunakan.",
           "Murid menunjukkan bagaimana kad yang sama boleh dikelaskan semula menggunakan ciri lain.",
           "Sediakan dua label ciri untuk dipilih. Murid yang sudah menguasai kemahiran mengelaskan semula kad mengikut bentuk."),
    Lesson(48, ("1.1.3",), "Mengukur panjang dalam sentimeter", "6–8",
           "Mengukur panjang tiga jalur dengan pembaris dan merekod bacaan dalam sentimeter.",
           "Pembaris, jalur kad yang panjangnya dalam sentimeter bulat, jadual rekod.",
           "Guru menunjukkan dua jalur. Murid menganggar jalur yang lebih panjang.",
           "Guru menunjukkan cara menjajarkan hujung jalur dengan tanda sifar dan melihat skala dari atas. Murid mencuba teknik itu secara berpasangan.",
           "Murid mengukur tiga jalur sendiri dan merekod nombor bersama unit. Guru memberi maklum balas tentang kedudukan sifar dan mata.",
           "Perhatikan cara memegang pembaris dan semak ketiga-tiga ukuran dengan nilai yang telah guru ukur.",
           "Murid menerangkan mengapa ukuran perlu bermula pada tanda sifar.",
           "Gunakan pembaris bertanda sifar berwarna. Murid yang sudah menguasai kemahiran membandingkan beza panjang dua jalur."),
    Lesson(49, ("1.1.4",), "Membuat inferens daripada pemerhatian", "9–10",
           "Menulis satu pemerhatian dan dua inferens munasabah tentang situasi yang sama.",
           "Gambar lopak di bawah paip, kad pemerhatian dan inferens.",
           "Guru menunjukkan gambar lopak di bawah paip. Murid menyatakan perkara yang dapat dilihat dalam gambar.",
           "Guru menulis pemerhatian murid. Murid mencadangkan beberapa punca lopak dan menunjuk petunjuk yang menyokong setiap cadangan.",
           "Murid meneliti gambar kedua dan menulis satu pemerhatian serta dua kemungkinan punca. Guru meminta alasan bagi satu inferens.",
           "Semak kad individu. Pemerhatian mestilah dapat dilihat dan kedua-dua inferens mesti menerangkan pemerhatian yang sama.",
           "Murid mencadangkan maklumat tambahan yang boleh membantu mereka membezakan dua kemungkinan punca.",
           "Beri pemula ayat 'Saya lihat…' dan 'Mungkin…'. Murid yang sudah menguasai kemahiran mencadangkan satu cara menyemak inferens."),
    Lesson(50, ("1.1.5",), "Meramal berdasarkan pola", "11–12",
           "Meramal dua kedudukan seterusnya dalam pola dan menerangkan asas ramalan.",
           "Kad pola warna dan bentuk, kad penutup, kad jawapan.",
           "Guru menunjukkan pola warna dengan dua ruang terakhir ditutup. Murid menyebut turutan yang telah diperhatikan.",
           "Guru meminta murid mencari bahagian pola yang berulang. Murid menyatakan ramalan berserta alasan sebelum guru membuka kad penutup.",
           "Murid membuat ramalan individu untuk pola bentuk yang baharu. Guru membuka sambungan pola selepas murid merekod jawapan.",
           "Semak dua bentuk yang diramal dan alasan yang merujuk turutan berulang.",
           "Murid menyebut petunjuk yang digunakan untuk membuat ramalan dan membandingkannya dengan sambungan sebenar.",
           "Tandakan sempadan bahagian yang berulang. Murid yang sudah menguasai kemahiran mencipta pola untuk diuji oleh rakan."),
    Lesson(51, ("1.1.6",), "Berkomunikasi menggunakan carta palang", "13–14",
           "Memindahkan tiga nilai daripada jadual ke carta palang dan menyampaikan satu dapatan.",
           "Jadual undian buah, grid carta, pensel dan pembaris.",
           "Guru menunjukkan jadual undian dan bertanya cara memaparkan buah yang paling digemari.",
           "Guru memodelkan satu palang. Murid membaca kategori, memilih skala satu petak bagi satu undian dan melabel paksi.",
           "Murid melengkapkan tiga palang pada grid sendiri dan menyatakan satu dapatan kepada pasangan. Guru menyemak nilai palang dan kategori.",
           "Semak label, tiga nilai palang dan satu dapatan yang selaras dengan carta setiap murid.",
           "Murid menerangkan bagaimana carta menunjukkan kategori dengan undian tertinggi.",
           "Sediakan paksi berlabel. Murid yang sudah menguasai kemahiran menyatakan beza bilangan undian antara dua buah."),
    Lesson(52, ("1.2.1", "1.2.2", "1.2.3"), "Mengendali dan melakar spesimen", "16–19",
           "Menggunakan kanta tangan dan mengendalikan daun secara cermat serta menghasilkan lakaran dengan dua label tepat.",
           "Kanta tangan, dulang, daun gugur yang bersih, kertas dan pensel.",
           "Guru menunjukkan daun dengan urat yang halus. Murid mencadangkan alat yang membantu melihat perinciannya.",
           "Guru menunjukkan cara meletakkan daun di atas dulang dan melaraskan kanta. Murid bergilir menggunakan kanta tanpa merosakkan daun.",
           "Murid melakar bentuk daun dan urat yang dapat dilihat, kemudian melabel bahagian. Guru meminta murid menyemak lakaran dengan spesimen.",
           "Guna senarai semak individu untuk penggunaan kanta, pengendalian daun dan dua label lakaran yang tepat.",
           "Murid menerangkan satu langkah yang membantu mereka menjaga spesimen semasa pemerhatian.",
           "Sediakan contoh garisan label. Murid yang sudah menguasai kemahiran membandingkan urat dua daun."),
    Lesson(53, ("1.2.4", "1.2.5"), "Membersihkan dan menyimpan alatan sains", "20",
           "Membersihkan dan mengeringkan alatan yang digunakan serta menyimpannya di tempat berlabel.",
           "Bekas plastik, air bersih, kain, dulang dan rak berlabel.",
           "Guru menunjukkan bekas dengan baki air. Murid menyatakan perkara yang perlu dilakukan sebelum menyimpannya.",
           "Guru menunjukkan cara mengosongkan bekas, membilas dan mengeringkannya. Murid melakukan langkah ini mengikut giliran.",
           "Murid menyusun alatan kering pada rak berlabel. Guru menyemak tempat simpan dan mengingatkan murid supaya mengelap tumpahan segera.",
           "Perhatikan setiap murid membilas, mengeringkan dan menyimpan alatan pada tempat yang betul.",
           "Murid menyusun kad urutan dan menerangkan mengapa alatan dikeringkan sebelum disimpan.",
           "Berikan kad urutan bergambar. Murid yang sudah menguasai kemahiran membimbing rakan menyemak rak selepas aktiviti."),
    Lesson(54, ("2.1.1",), "Mematuhi peraturan bilik sains", "24–27",
           "Mengamalkan sekurang-kurangnya satu peraturan pada setiap peringkat sebelum, semasa dan selepas aktiviti.",
           "Kad situasi, dulang, peralatan plastik dan senarai semak guru.",
           "Guru menunjukkan gambar murid berebut mengambil peralatan. Murid mencadangkan tindakan yang lebih selamat.",
           "Guru memodelkan cara masuk dengan tertib dan mengambil alatan selepas arahan. Murid melaksanakan simulasi mengikut giliran.",
           "Murid menjalankan tugasan ringkas, memulangkan peralatan dan mengemas ruang. Guru memberi maklum balas pada setiap peringkat.",
           "Tandakan amalan individu pada ketiga-tiga peringkat. Catat peraturan yang masih memerlukan bimbingan.",
           "Murid memilih satu peraturan dan menjelaskan risiko jika peraturan itu diabaikan.",
           "Guna kad peringatan bergambar. Murid yang sudah menguasai kemahiran mencadangkan tindakan apabila terlihat alatan rosak."),
)

LESSON_BY_CODE = {lesson.code: lesson for lesson in LESSONS}


def add_opening_units(rows):
    """Fill missing opening standards without replacing source rows."""
    if not rows:
        return rows
    source_standards = {
        str(row.get("sk_code") or "").strip() for row in rows
    }
    source_codes = {str(row.get("pdp_sequence_code") or "").strip() for row in rows}
    additions = [
        {
            "unit_code": lesson.sk, "unit_title": lesson.unit,
            "pdp_sequence_code": lesson.code, "source_sequence_no": lesson.number,
            "pdp_title": lesson.title, "theme": "Inkuiri dalam Sains",
            "sk_code": lesson.sk, "sk_text": SK[lesson.sk],
            "sp_code": standard, "sp_text": SP[standard],
            "textbook_ref": f"Buku Teks m/s {lesson.pages}",
            "_sains_y3_opening_lesson": True,
        }
        for lesson in LESSONS
        if lesson.sk not in source_standards and lesson.code not in source_codes
        for standard in lesson.standards
    ]
    return rows + additions


def lesson_text(code):
    lesson = LESSON_BY_CODE[code]
    return "\n".join((
        f"TAJUK: {lesson.title}",
        f"STANDARD KANDUNGAN: {lesson.sk} {SK[lesson.sk]}",
        "STANDARD PEMBELAJARAN: " + "\n".join(
            f"{sp} {SP[sp]}" for sp in lesson.standards),
        f"OBJEKTIF PEMBELAJARAN: {lesson.objective}",
        f"KRITERIA KEJAYAAN: {lesson.objective}",
        f"BAHAN BANTU MENGAJAR: {lesson.materials} Buku Teks m/s {lesson.pages}.",
        f"PENTAKSIRAN: {lesson.assessment}",
        f"SET INDUKSI: {lesson.induction}",
        f"AKTIVITI UTAMA:\nAktiviti 1 — {lesson.guided}\nAktiviti 2 — {lesson.independent}",
        f"PENUTUP: {lesson.closure}",
        f"PEMULIHAN / PENGAYAAN: {lesson.follow_up}",
    ))


def install(runtime):
    """Restore lesson-specific fields after the existing Science layout adapters."""
    previous = runtime._rph_rows

    def rows(state, *args, **kwargs):
        result = previous(state, *args, **kwargs)
        if not state.get("_sains_y3_opening_lesson"):
            return result
        plan = LESSON_BY_CODE[state["pdp_sequence_code"]]
        return {
            **result,
            "STANDARD KANDUNGAN": f"{plan.sk} {SK[plan.sk]}",
            "STANDARD PEMBELAJARAN": "\n".join(f"{sp} {SP[sp]}" for sp in plan.standards),
            "OBJEKTIF PEMBELAJARAN": "Murid dapat " + plan.objective[0].lower() + plan.objective[1:],
            "KRITERIA KEJAYAAN": plan.objective,
            "BAHAN BANTU MENGAJAR": f"{plan.materials} Buku Teks m/s {plan.pages}.",
            "KBAT / PAK21": SK[plan.sk],
            "PENTAKSIRAN": plan.assessment,
            "SET INDUKSI": plan.induction,
            "AKTIVITI UTAMA": f"Aktiviti 1 – {plan.guided}\nAktiviti 2 – {plan.independent}",
            "PENUTUP": plan.closure,
            "PEMULIHAN / PENGAYAAN": plan.follow_up,
        }

    runtime._rph_rows = rows
