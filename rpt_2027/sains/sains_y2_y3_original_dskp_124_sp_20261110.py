"""Extracted-and-normalized SP statement candidates from owner's original DSKP PDFs.

Source PDF identity is SHA256 pinned, with source 1-based PDF page numbers.
KPM documents: Sains Tahun 2 (2016) and Sains Tahun 3 (2017).
Each entry is an original DSKP code and its wording, not an authored lesson.
Text spelling and unusual original source wording are NOT silently revised;
final independent visual and teacher review remain mandatory.
"""

from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib

SOURCE_SHA256 = {
  2: "55af6dad33970f6e32aea17d1bb750ce59af24872a97661374a5ecd3bee94985",
  3: "83711fabd4ddb70423f51a24dac62b1754c50719613a1bfd0cfb9127e0893ce1",
}
PDF_PAGES = {2: 80, 3: 88}
SOURCE_SP_COUNTS = {2:64, 3:60}
SK_TEXT = {
  2: {
  "1.1": "Kemahiran Proses Sains", "1.2": "Kemahiran Manipulatif",
  "2.1": "Peraturan Bilik Sains", "3.1": "Pembiakan dan Tumbesaran Manusia",
  "4.1": "Pembiakan dan Tumbesaran Haiwan", "5.1": "Tumbesaran Tumbuhan",
  "6.1": "Terang dan Gelap", "7.1": "Litar Elektrik",
  "8.1": "Campuran", "9.1": "Air", "9.2": "Udara", "10.1": "Teknologi",
  },
  3: {
  "1.1": "Kemahiran Proses Sains", "1.2": "Kemahiran Manipulatif",
  "2.1": "Peraturan Bilik Sains", "3.1": "Gigi",
  "3.2": "Kelas Makanan", "3.3": "Pencernaan",
  "4.1": "Tabiat Pemakanan Haiwan", "5.1": "Pembiakan Tumbuhan",
  "6.1": "Pengukuran", "7.1": "Ketumpatan",
  "8.1": "Asid dan Alkali", "9.1": "Sistem Suria", "10.1": "Mesin",
  },
}
# Original DSKP codes, 1-based PDF pages and text. Some Year2 lines are
# especially source-odd (10.1.6 references "campuran"); retain exactly as
# printed pending editorial review, don't replace with guessed lesson wording.
Y2 = """
1.1.1|49|Memerhati
1.1.2|51|Mengelas
1.1.3|52|Mengukur dan menggunakan nombor
1.1.4|53|Berkomunikasi
1.2.1|54|Menggunakan dan mengendalikan peralatan dan bahan sains dengan betul.
1.2.2|54|Mengendalikan spesimen dengan betul dan cermat.
1.2.3|54|Melakar spesimen, peralatan dan bahan sains dengan betul.
1.2.4|54|Membersihkan peralatan sains dengan cara yang betul.
1.2.5|54|Menyimpan peralatan dan bahan sains dengan betul dan selamat.
2.1.1|56|Mematuhi peraturan bilik sains
3.1.1|58|Menyatakan cara manusia membiak.
3.1.2|58|Memerihalkan perubahan yang berlaku pada diri sejak dilahirkan dari aspek saiz, tinggi dan berat.
3.1.3|58|Mengitlak tumbesaran adalah berbeza antara individu dengan menjalankan aktiviti.
3.1.4|58|Memerihalkan bahawa anak mewarisi ciri daripada ibu, bapa atau keturunan.
3.1.5|58|Memberi contoh ciri yang diwarisi oleh anak daripada ibu bapa atau keturunan seperti warna kulit, warna mata dan jenis rambut.
3.1.6|59|Menjelaskan pemerhatian tentang tumbesaran dan pewarisan melalui lakaran, TMK, penulisan atau lisan.
4.1.1|60|Menyatakan cara haiwan membiak.
4.1.2|60|Mengelaskan haiwan berdasarkan cara pembiakan.
4.1.3|60|Menjelaskan dengan contoh haiwan bertelur banyak dan bertelur sedikit.
4.1.4|60|Menjelaskan dengan contoh haiwan melahirkan anak yang banyak dan anak yang sedikit.
4.1.5|60|Merekod perubahan tumbesaran haiwan dengan memerhati kitar hidup haiwan.
4.1.6|61|Menjelas dengan contoh anak haiwan yang menyerupai induknya dan yang tidak menyerupai induknya.
4.1.7|61|Menjelaskan pemerhatian tentang pembiakan dan tumbesaran melalui lakaran, TMK, penulisan atau lisan.
5.1.1|62|Menyatakan kepentingan tumbuhan kepada manusia dan haiwan.
5.1.2|62|Menyatakan keperluan asas untuk biji benih bercambah.
5.1.3|62|Merekod perubahan tumbesaran tumbuhan bermula daripada percambahan biji benih dengan memerhati biji benih sebenar.
5.1.4|62|Menyusun mengikut urutan peringkat tumbesaran tumbuhan.
5.1.5|62|Membuat kesimpulan keperluan asas untuk tumbesaran tumbuhan dengan menjalankan penyiasatan.
5.1.6|63|Menjelaskan pemerhatian tentang proses hidup tumbuhan melalui lakaran, TMK, penulisan atau lisan.
6.1.1|64|Menyatakan sumber cahaya.
6.1.2|64|Membanding beza aktiviti yang dijalankan dalam keadaan terang dan gelap.
6.1.3|64|Menerangkan bagaimana bayang-bayang dihasilkan melalui aktiviti.
6.1.4|64|Membanding dan membezakan kejelasan bayang-bayang apabila cahaya dihalang oleh objek yang berlainan dengan menjalankan penyiasatan.
6.1.5|64|Mencipta permainan bayang-bayang
6.1.6|65|Menjelaskan pemerhatian tentang terang dan gelap melalui lakaran, TMK, penulisan atau lisan.
7.1.1|66|Mengenal pasti komponen dalam litar elektrik iaitu sel kering, mentol dan suis.
7.1.2|66|Menerangkan fungsi komponen dalam litar elektrik lengkap.
7.1.3|66|Membina litar elektrik lengkap dengan menggunakan sel kering, mentol, suis dan wayar penyambung.
7.1.4|66|Meramal sebab mentol tidak menyala dalam litar yang dibina.
7.1.5|66|Merekod nyalaan mentol dengan mengantikan suis dengan objek atau bahan dengan menjalankan penyiasatan.
7.1.6|67|Mengitlak objek yang boleh menyalakan mentol dalam litar adalah konduktor dan yang tidak menyalakan mentol adalah penebat.
7.1.7|67|Menjelaskan pemerhatian tentang litar elektrik melalui lakaran, TMK, penulisan atau lisan.
8.1.1|68|Memerihalkan kaedah untuk mengasingkan campuran pelbagai bahan atau objek.
8.1.2|68|Menaakul cara yang digunakan untuk mengasingkan campuran pelbagai bahan atau objek.
8.1.3|68|Mengenal pasti bahan yang boleh larut dan tidak boleh larut di dalam air dengan menjalankan penyiasatan.
8.1.4|68|Merumuskan cara bahan boleh dilarutkan dengan lebih cepat dengan menjalankan penyiasatan.
8.1.5|69|Menjelaskan pemerhatian tentang campuran melalui lakaran, TMK, penulisan atau lisan.
9.1.1|70|Menyatakan sumber air semulajadi seperti hujan, sungai, tasik, laut dan mata air.
9.1.2|70|Menyatakan arah aliran air dengan menjalankan aktiviti.
9.1.3|70|Mengitlak arah aliran air secara semulajadi seperti aliran air sungai, air terjun melalui pemerhatian menerusi pelbagai media.
9.1.4|70|Membuat urutan kitar air semulajadi.
9.1.5|70|Menjelaskan pemerhatian tentang kitaran air melalui lakaran, TMK, penulisan atau lisan.
9.2.1|71|Menyatakan udara berada di sekeliling kita.
9.2.2|71|Menyatakan udara terdiri daripada beberapa jenis gas seperti oksigen dan karbon dioksida.
9.2.3|71|Memerihalkan udara yang bergerak adalah angin.
9.2.4|71|Menjana idea kesan udara yang bergerak dalam kehidupan manusia.
9.2.5|71|Mencipta alat atau model dengan mengaplikasikan pengetahuan yang menunjukkan kegunaan udara yang bergerak.
9.2.6|71|Menjelaskan pemerhatian tentang udara melalui lakaran, TMK, penulisan atau lisan.
10.1.1|72|Memilih binaan yang hendak dibina daripada set binaan.
10.1.2|72|Mengenal pasti komponen binaan berpandukan manual bergambar.
10.1.3|72|Memasang komponen binaan berpandukan manual bergambar.
10.1.4|72|Mencipta satu binaan baru yang tidak terdapat dalam manual bergambar.
10.1.5|72|Membuka hasil binaan mengikut urutan dan menyimpan komponen yang telah dibuka ke dalam bekas penyimpanan.
10.1.6|73|Menjelaskan pemerhatian tentang campuran melalui lakaran, TMK, penulisan atau lisan.
"""
Y3 = """
1.1.1|50|Memerhati
1.1.2|52|Mengelas
1.1.3|54|Mengukur dan menggunakan nombor
1.1.4|56|Membuat inferens
1.1.5|58|Meramal
1.1.6|60|Berkomunikasi
1.2.1|62|Menggunakan dan mengendalikan peralatan dan bahan sains dengan betul.
1.2.2|62|Mengendalikan spesimen dengan betul dan cermat.
1.2.3|62|Melakar spesimen, peralatan dan bahan sains dengan betul.
1.2.4|62|Membersihkan peralatan sains dengan cara yang betul.
1.2.5|62|Menyimpan peralatan dan bahan sains dengan betul dan selamat.
2.1.1|64|Mematuhi peraturan bilik sains.
3.1.1|66|Memerihalkan jenis gigi dan fungsinya.
3.1.2|66|Melabelkan struktur gigi.
3.1.3|66|Membanding dan membezakan set gigi susu dan set gigi kekal.
3.1.4|66|Menghubung kait penjagaan kesihatan gigi dengan struktur gigi.
3.1.5|66|Menjelaskan pemerhatian tentang gigi melalui lakaran, TMK, penulisan atau lisan secara kreatif.
3.2.1|67|Memberi contoh makanan bagi setiap kelas makanan.
3.2.2|67|Mengitlak kepentingan makanan mengikut kelasnya kepada tubuh manusia.
3.2.3|67|Menjelas dengan contoh makanan seimbang berdasarkan piramid makanan.
3.2.4|67|Menaakul kesan pengambilan makanan yang tidak seimbang.
3.2.5|67|Menjelaskan pemerhatian tentang kelas makanan menerusi lakaran, TMK, penulisan atau lisan secara kreatif.
3.3.1|68|Memerihalkan proses pencernaan.
3.3.2|68|Membuat urutan aliran makanan semasa pencernaan.
3.3.3|68|Merumus tentang makanan tercerna yang tidak diperlukan oleh badan.
3.3.4|68|Menjelaskan pemerhatian tentang pencernaan menerusi lakaran, TMK, penulisan atau lisan secara kreatif.
4.1.1|70|Mengelas haiwan mengikut tabiat pemakanan.
4.1.2|70|Menjelaskan dengan contoh tabiat pemakanan haiwan herbivor, karnivor dan omnivor.
4.1.3|70|Membuat inferens tentang kumpulan haiwan berdasarkan tabiat pemakanan.
4.1.4|70|Membanding dan membezakan kegigian haiwan herbivor, karnivor, dan omnivor.
4.1.5|70|Menjelaskan pemerhatian tentang tabiat pemakanan haiwan melalui lakaran, TMK, penulisan atau lisan secara kreatif.
5.1.1|71|Memberi contoh tumbuhan bagi setiap cara pembiakan.
5.1.2|71|Menaakul kepentingan pembiakan tumbuhan kepada hidupan.
5.1.3|71|Mengitlak satu tumbuhan boleh membiak melalui pelbagai cara dengan menjalankan projek.
5.1.4|71|Menjelaskan pemerhatian tentang pembiakan tumbuhan melalui lakaran, TMK, penulisan atau lisan secara kreatif.
6.1.1|74|Menyatakan unit yang digunakan untuk mengukur luas dan isi padu.
6.1.2|74|Mengukur luas permukaan sekata menggunakan petak yang berukuran 1cm x 1cm.
6.1.3|74|Menyelesaikan masalah untuk menganggar luas permukaan yang tidak sekata.
6.1.4|74|Mengukur isi padu kotak lohong dengan menggunakan kubus yang berukuran 1cm x 1cm x 1cm.
6.1.5|74|Mengukur isi padu cecair menggunakan alat dan teknik yang betul.
6.1.6|74|Menyelesaikan masalah untuk menentukan isi padu pepejal tidak sekata melalui kaedah sesaran air.
6.1.7|75|Menjelaskan pemerhatian tentang pengukuran luas dan isi padu melalui lakaran, TMK, penulisan atau lisan secara kreatif.
7.1.1|76|Membuat inferens tentang objek atau bahan yang timbul dan objek atau bahan yang tenggelam dengan menjalankan aktiviti.
7.1.2|76|Menghubung kait objek atau bahan yang timbul dan objek atau bahan yang tenggelam dengan ketumpatan.
7.1.3|76|Menyelesaikan masalah bagi mengenal pasti kaedah untuk menjadikan air lebih tumpat.
7.1.4|76|Menjelaskan pemerhatian tentang objek atau bahan yang lebih tumpat dan kurang tumpat daripada air melalui lakaran, TMK, penulisan atau lisan secara kreatif.
8.1.1|78|Menguji bahan yang berasid, beralkali dan neutral dari segi perubahan warna kertas litmus dengan menjalankan penyiasatan.
8.1.2|78|Mengitlak bahan yang berasid, beralkali dan neutral dari aspek rasa dan sentuhan dengan menguji beberapa contoh bahan.
8.1.3|78|Meneroka bahan lain yang boleh menguji bahan berasid, beralkali dan neutral.
8.1.4|78|Menjelaskan pemerhatian tentang asid dan alkali melalui lakaran, TMK, penulisan atau lisan secara kreatif.
9.1.1|80|Menyenaraikan ahli dalam Sistem Suria melalui pemerhatian menerusi pelbagai media.
9.1.2|80|Mengitlak suhu planet berdasarkan urutan dalam Sistem Suria.
9.1.3|80|Memerihalkan planet beredar mengelilingi Matahari mengikut orbit.
9.1.4|80|Menghubung kait kedudukan planet dari Matahari dengan masa planet beredar mengelilingi Matahari.
9.1.5|80|Menjelaskan pemerhatian tentang sistem suria melalui lakaran, TMK, penulisan atau lisan secara kreatif.
10.1.1|82|Menyatakan maksud dan kegunaan takal.
10.1.2|82|Memerihalkan cara takal tetap berfungsi dengan menggunakan model.
10.1.3|82|Memberi contoh aplikasi takal dalam kehidupan.
10.1.4|82|Mereka cipta model takal yang berfungsi.
10.1.5|82|Menjelaskan pemerhatian tentang takal melalui lakaran, TMK, penulisan atau lisan secara kreatif.
"""

def source_records(year: int):
    if type(year) is not int or year not in (2,3):
        raise ValueError("Only source-grounded Year2/3 available here")
    text = Y2 if year == 2 else Y3
    rows = []
    seen = set()
    for line in text.strip().splitlines():
        parts=line.strip().split("|",2)
        if len(parts)!=3:
            raise ValueError("Source malformed")
        code,page,text=parts
        sk=".".join(code.split(".")[:2])
        if not text or code in seen or sk not in SK_TEXT[year]:
            raise ValueError("Source DSKP code/statement mismatch")
        seen.add(code)
        page=int(page)
        if not 1 <= page <= PDF_PAGES[year]:
            raise ValueError("Source DSKP pdf page invalid")
        rows.append(dict(
            sp_code=code, sk_code=sk, sp_text=text.strip(),
            sk_text=SK_TEXT[year][sk], original_pdf_page=page,
            source_curriculum="KSSR SAINS TAHUN "+str(year),
            source_pdf_sha256=SOURCE_SHA256[year],
            source_visual_signoff=False,
        ))
    if len(rows)!=SOURCE_SP_COUNTS[year]:
        raise ValueError("Expected all 64/60 original official DSKP SP rows")
    return rows
