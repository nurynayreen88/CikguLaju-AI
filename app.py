import os
import html
import requests
import time
import random
import tempfile
import re
from flask import Flask, request, jsonify
from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import mm
from xml.sax.saxutils import escape

app = Flask(__name__)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.7-flash')
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.getenv(
    'GEMINI_FALLBACK_MODELS',
    'gemini-3.6-flash,gemini-3.5-flash-lite'
).split(',') if m.strip()]
API = f'https://api.telegram.org/bot{BOT_TOKEN}'
state = {}

# Senarai topik pilihan mengikut tahap/subjek.
# Direka untuk kegunaan menu bot dan boleh dikemas kini kemudian jika cikgu mahu
# nama unit yang sama 100% seperti buku teks/DSKP sekolah masing-masing.
TOPICS = {
    'Tahun 1': {
        'Bahasa Melayu': ['Kemahiran Mendengar dan Bertutur','Kemahiran Membaca','Kemahiran Menulis','Huruf, Suku Kata dan Perkataan','Ayat Mudah','Kata Nama','Kata Kerja','Kata Adjektif','Kata Tanya','Kata Perintah','Penjodoh Bilangan','Simpulan Bahasa Mudah'],
        'Bahasa Inggeris': ['Greetings and Introductions','Myself and Family','School and Classroom','Numbers and Colours','Food and Drinks','Animals','Body Parts','Daily Routines','Listening and Speaking','Reading','Writing','Basic Grammar and Vocabulary'],
        'Matematik': ['Nombor hingga 100','Tambah','Tolak','Pecahan Asas','Wang','Masa dan Waktu','Panjang','Jisim','Isi Padu Cecair','Bentuk 2D dan 3D','Kedudukan','Pengurusan Data'],
        'Sains': ['Kemahiran Saintifik','Benda Hidup dan Benda Bukan Hidup','Manusia','Haiwan','Tumbuhan','Deria Manusia','Magnet','Penyerapan','Bumi','Teknologi dan Kehidupan'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Ibadah','Sirah','Adab','Jawi'],
    },
    'Tahun 2': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca','Menulis','Perkataan dan Frasa','Ayat Tunggal','Kata Nama','Kata Kerja','Kata Adjektif','Kata Hubung','Kata Tanya','Penjodoh Bilangan','Peribahasa Mudah'],
        'Bahasa Inggeris': ['My World','At School','Food','Animals','Home','Free Time','Health and Hygiene','Listening and Speaking','Reading','Writing','Grammar','Vocabulary'],
        'Matematik': ['Nombor hingga 1000','Tambah','Tolak','Darab','Bahagi','Pecahan','Wang','Masa dan Waktu','Panjang','Jisim','Isi Padu Cecair','Bentuk','Data'],
        'Sains': ['Kemahiran Saintifik','Manusia','Haiwan','Tumbuhan','Pembiakan dan Pertumbuhan','Cahaya dan Bayang-bayang','Elektrik Asas','Campuran','Bumi dan Angkasa','Teknologi'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Ibadah','Sirah','Adab','Jawi'],
    },
    'Tahun 3': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca','Menulis','Ayat Tunggal dan Ayat Majmuk','Kata Nama','Kata Kerja','Kata Adjektif','Kata Sendi Nama','Kata Hubung','Imbuhan Asas','Penjodoh Bilangan','Peribahasa'],
        'Bahasa Inggeris': ['People and Family','School Life','Food and Health','Nature and Animals','Places','Hobbies','Daily Activities','Listening','Speaking','Reading','Writing','Grammar and Vocabulary'],
        'Matematik': ['Nombor hingga 10 000','Tambah','Tolak','Darab','Bahagi','Pecahan','Perpuluhan Asas','Wang','Masa dan Waktu','Panjang, Jisim dan Isi Padu','Bentuk dan Ruang','Data'],
        'Sains': ['Kemahiran Saintifik','Manusia','Haiwan','Tumbuhan','Gigi','Makanan dan Pencernaan','Magnet','Ketumpatan','Asid dan Alkali Asas','Sistem Suria','Teknologi'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Ibadah','Sirah','Adab','Jawi'],
    },
    'Tahun 4': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca dan Memahami','Penulisan','Kata Nama','Kata Kerja','Kata Adjektif','Kata Ganda','Kata Majmuk','Imbuhan','Ayat Aktif dan Pasif','Peribahasa','Seni Bahasa'],
        'Bahasa Inggeris': ['Where Are You From?','My Week','In the Past','Celebrations','Eating Right','Getting Around','Helping Out','Amazing Animals','Listening','Speaking','Reading','Writing','Grammar and Vocabulary'],
        'Matematik': ['Nombor Bulat dan Operasi Asas','Pecahan','Perpuluhan','Wang','Masa dan Waktu','Panjang, Jisim dan Isi Padu Cecair','Ruang','Koordinat','Nisbah dan Kadaran Asas','Pengurusan Data'],
        'Sains': ['Kemahiran Saintifik','Manusia','Haiwan','Tumbuhan','Sifat Bahan','Tenaga','Cahaya','Bunyi','Bumi','Sistem Suria','Teknologi'],
        'Sejarah': ['Mari Belajar Sejarah','Saya dan Keluarga','Sejarah Sekolah','Tempat Tinggal Saya','Zaman Prasejarah','Kerajaan Melayu Awal','Tokoh Terbilang Kesultanan Melayu Melaka','Warisan Kesultanan Melayu Melaka'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Ibadah','Sirah','Adab','Jawi'],
    },
    'Tahun 5': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca','Penulisan','Tatabahasa','Kata Terbitan','Kata Ganda','Kata Majmuk','Ayat Aktif dan Pasif','Ayat Majmuk','Peribahasa','Seni Bahasa','Ulasan dan Karangan'],
        'Bahasa Inggeris': ['Town and Community','Days and Activities','Past Events','Culture and Celebrations','Health','Travel','Helping Others','Nature','Listening','Speaking','Reading','Writing','Grammar and Vocabulary'],
        'Matematik': ['Nombor Bulat dan Operasi','Pecahan','Perpuluhan','Peratus','Wang','Masa dan Waktu','Panjang, Jisim dan Isi Padu','Ruang','Koordinat','Nisbah dan Kadaran','Pengurusan Data'],
        'Sains': ['Kemahiran Saintifik','Manusia','Haiwan','Tumbuhan','Elektrik','Haba','Pengaratan','Jirim','Fasa Bulan dan Buruj','Mesin','Teknologi'],
        'Sejarah': ['Institusi Raja','Agama Islam di Malaysia','Bahasa Melayu','Kedaulatan Negara','Identiti Negara','Rukun Negara','Yang di-Pertuan Agong','Jata Negara','Bendera Kebangsaan','Lagu Kebangsaan'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Ibadah','Sirah','Adab','Jawi'],
    },
    'Tahun 6': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca','Penulisan','Tatabahasa','Morfologi','Sintaksis','Peribahasa','Seni Bahasa','Ringkasan','Ulasan','Karangan Berformat','Karangan Tidak Berformat'],
        'Bahasa Inggeris': ['Personal Life','School and Learning','Health and Lifestyle','Technology','Environment','Travel','Culture','Community','Listening','Speaking','Reading','Writing','Grammar and Vocabulary'],
        'Matematik': ['Nombor dan Operasi','Pecahan','Perpuluhan','Peratus','Wang','Masa dan Waktu','Ukuran dan Sukatan','Ruang','Koordinat','Nisbah dan Kadaran','Pengurusan Data','Penyelesaian Masalah'],
        'Sains': ['Kemahiran Saintifik','Manusia','Mikroorganisma','Interaksi antara Hidupan','Pemeliharaan dan Pemuliharaan','Daya','Kelajuan','Teknologi Makanan','Bahan Buangan','Gerhana','Galaksi','Teknologi'],
        'Sejarah': ['Pembentukan Malaysia','Negeri-negeri di Malaysia','Rukun Negara dan Perpaduan','Kaum dan Etnik','Agama dan Kepercayaan','Perayaan Masyarakat Malaysia','Pemimpin Negara','Kemajuan Ekonomi','Sukan Kebanggaan Negara','Malaysia di Persada Dunia'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Ibadah','Sirah','Adab','Jawi'],
    },
    'Tingkatan 1': {
        'Bahasa Melayu': ['Kemahiran Mendengar dan Bertutur','Membaca','Menulis','Tatabahasa','Komsas','Ringkasan','Ulasan','Karangan','Peribahasa','Seni Bahasa'],
        'Bahasa Inggeris': ['People and Culture','School and Education','Health','Environment','Technology','Travel','Listening','Speaking','Reading','Writing','Grammar','Literature'],
        'Matematik': ['Nombor Nisbah','Faktor dan Gandaan','Kuasa Dua, Punca Kuasa Dua, Kuasa Tiga dan Punca Kuasa Tiga','Nisbah, Kadar dan Kadaran','Ungkapan Algebra','Persamaan Linear','Ketaksamaan Linear','Garis dan Sudut','Poligon Asas','Perimeter dan Luas','Pengenalan Set','Pengendalian Data'],
        'Sains': ['Pengenalan kepada Penyiasatan Saintifik','Sel sebagai Unit Asas Hidupan','Koordinasi dan Gerak Balas','Pembiakan','Jirim','Jadual Berkala Asas','Udara','Cahaya dan Optik','Bumi'],
        'Sejarah': ['Mengenali Sejarah','Zaman Air Batu','Zaman Prasejarah','Tamadun Awal Dunia','Peningkatan Tamadun Yunani dan Rom','Peningkatan Tamadun India dan China','Tamadun Islam dan Sumbangannya','Seni Bina Tamadun'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Fikah','Sirah dan Tamadun Islam','Akhlak Islamiah'],
    },
    'Tingkatan 2': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca','Menulis','Tatabahasa','Komsas','Ringkasan','Ulasan','Karangan','Peribahasa','Seni Bahasa'],
        'Bahasa Inggeris': ['Family and Society','Health','Science and Technology','Environment','Consumerism','Travel','Listening','Speaking','Reading','Writing','Grammar','Literature'],
        'Matematik': ['Pola dan Jujukan','Pemfaktoran dan Pecahan Algebra','Rumus Algebra','Poligon','Bulatan','Bentuk Geometri Tiga Dimensi','Koordinat','Graf Fungsi','Laju dan Pecutan','Kecerunan Garis Lurus','Transformasi Isometri','Sukatan Kecenderungan Memusat','Kebarangkalian Mudah'],
        'Sains': ['Biodiversiti','Ekosistem','Nutrisi','Kesihatan Manusia','Air dan Larutan','Asid dan Alkali','Keelektrikan dan Kemagnetan','Daya dan Gerakan','Haba','Gelombang Bunyi','Bintang dan Galaksi','Sistem Suria','Meteoroid, Asteroid dan Komet'],
        'Sejarah': ['Kerajaan Alam Melayu','Sistem Pemerintahan dan Kegiatan Ekonomi','Sosiobudaya Masyarakat Kerajaan Alam Melayu','Agama, Kepercayaan dan Keunikan Warisan','Kesultanan Melayu Melaka','Kesultanan Johor Riau','Kesultanan Melayu Pahang, Perak, Terengganu dan Selangor','Kerajaan Kedah, Kelantan, Negeri Sembilan dan Perlis','Warisan Kerajaan Kedah, Kelantan, Negeri Sembilan dan Perlis','Sarawak dan Sabah'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Fikah','Sirah dan Tamadun Islam','Akhlak Islamiah'],
    },
    'Tingkatan 3': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca','Menulis','Tatabahasa','Komsas','Rumusan','Ulasan','Karangan','Peribahasa','Seni Bahasa'],
        'Bahasa Inggeris': ['People and Culture','Health','Science and Technology','Environment','Money and Consumerism','Travel','Listening','Speaking','Reading','Writing','Grammar','Literature'],
        'Matematik': ['Indeks','Bentuk Piawai','Matematik Pengguna: Simpanan dan Pelaburan, Kredit dan Hutang','Lukisan Berskala','Nisbah Trigonometri','Sudut dan Tangen bagi Bulatan','Pelan dan Dongakan','Lokus dalam Dua Dimensi','Garis Lurus'],
        'Sains': ['Rangsangan dan Gerak Balas','Respirasi','Pengangkutan','Kereaktifan Logam','Termokimia','Elektrik dan Kemagnetan','Tenaga dan Kuasa','Keradioaktifan','Cuaca Angkasa Lepas','Penerokaan Angkasa Lepas'],
        'Sejarah': ['Kedatangan Kuasa Barat','Pentadbiran Negeri-negeri Selat','Pentadbiran Negeri-negeri Melayu Bersekutu','Pentadbiran Negeri-negeri Melayu Tidak Bersekutu','Pentadbiran Barat di Sarawak dan Sabah','Kesan Pentadbiran Barat terhadap Ekonomi dan Sosial','Penentangan Masyarakat Tempatan','Kebijaksanaan Raja dan Pembesar Melayu Menangani Cabaran Barat'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Fikah','Sirah dan Tamadun Islam','Akhlak Islamiah'],
    },
    'Tingkatan 4': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca','Menulis','Tatabahasa','Komsas','Rumusan','Karangan Respons Terhad','Karangan Respons Terbuka','Peribahasa','Seni Bahasa'],
        'Bahasa Inggeris': ['People and Culture','Health','Science and Technology','Environment','Consumerism','Travel','Listening','Speaking','Reading','Writing','Grammar','Literature'],
        'Matematik': ['Fungsi dan Persamaan Kuadratik dalam Satu Pemboleh Ubah','Asas Nombor','Penaakulan Logik','Operasi Set','Rangkaian dalam Teori Graf','Ketaksamaan Linear dalam Dua Pemboleh Ubah','Graf Gerakan','Sukatan Serakan Data Tak Terkumpul','Kebarangkalian Peristiwa Bergabung','Matematik Pengguna: Pengurusan Kewangan'],
        'Sains': ['Langkah Keselamatan di dalam Makmal','Bantuan Kecemasan','Teknik Mengukur Parameter Kesihatan Badan','Teknologi Hijau dalam Melestarikan Alam','Genetik','Sokongan, Pergerakan dan Pertumbuhan','Koordinasi Badan','Unsur dan Bahan','Kimia Industri','Kimia dalam Perubatan dan Kesihatan','Daya dan Gerakan','Tenaga Nuklear'],
        'Sejarah': ['Warisan Negara Bangsa','Kebangkitan Nasionalisme','Konflik Dunia dan Pendudukan Jepun di Negara Kita','Era Peralihan Kuasa British di Negara Kita','Persekutuan Tanah Melayu 1948','Ancaman Komunis dan Perisytiharan Darurat','Usaha ke Arah Kemerdekaan','Pilihan Raya','Perlembagaan Persekutuan Tanah Melayu 1957','Pemasyhuran Kemerdekaan'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Fikah','Sirah dan Tamadun Islam','Akhlak Islamiah'],
    },
    'Tingkatan 5': {
        'Bahasa Melayu': ['Mendengar dan Bertutur','Membaca','Menulis','Tatabahasa','Komsas','Rumusan','Karangan Respons Terhad','Karangan Respons Terbuka','Peribahasa','Seni Bahasa'],
        'Bahasa Inggeris': ['People and Culture','Health','Science and Technology','Environment','Consumerism','Travel','Listening','Speaking','Reading','Writing','Grammar','Literature'],
        'Matematik': ['Ubahan','Matriks','Matematik Pengguna: Insurans','Matematik Pengguna: Percukaian','Kongruen, Pembesaran dan Gabungan Transformasi','Nisbah dan Graf Fungsi Trigonometri','Sukatan Serakan Data Terkumpul','Pemodelan Matematik'],
        'Sains': ['Mikroorganisma','Nutrisi dan Teknologi Makanan','Kelestarian Alam Sekitar','Kadar Tindak Balas','Sebatian Karbon','Elektrokimia','Cahaya dan Optik','Daya dan Tekanan','Teknologi Angkasa Lepas'],
        'Sejarah': ['Kedaulatan Negara','Perlembagaan Persekutuan','Raja Berperlembagaan dan Demokrasi Berparlimen','Sistem Persekutuan','Pembentukan Malaysia','Cabaran Selepas Pembentukan Malaysia','Membina Kesejahteraan Negara','Membina Kemakmuran Negara','Dasar Luar Malaysia','Kecemerlangan Malaysia di Persada Dunia'],
        'Pendidikan Islam': ['Al-Quran','Hadis','Akidah','Fikah','Sirah dan Tamadun Islam','Akhlak Islamiah'],
    },
}


# =========================
# SUBTOPIK TETAP
# =========================
# Tidak dijana oleh Gemini. Pilihan yang sama akan sentiasa menghasilkan
# senarai subtopik yang sama.

SCIENCE_FIXED = {
    'Sistem Suria': ['Matahari sebagai pusat Sistem Suria','Planet dalam Sistem Suria','Urutan planet','Putaran dan peredaran','Kepentingan Sistem Suria'],
    'Fasa Bulan dan Buruj': ['Pergerakan Bulan','Fasa-fasa Bulan','Buruj','Kegunaan buruj','Pemerhatian langit'],
    'Gerhana': ['Gerhana Matahari','Gerhana Bulan','Kedudukan Matahari-Bumi-Bulan','Keselamatan pemerhatian'],
    'Galaksi': ['Bima Sakti','Kedudukan Sistem Suria','Bintang dan galaksi','Saiz dan skala angkasa'],
    'Elektrik': ['Litar elektrik','Komponen litar','Konduktor dan penebat','Litar bersiri dan selari','Keselamatan elektrik'],
    'Haba': ['Sumber haba','Pengaliran haba','Pengembangan dan pengecutan','Aplikasi haba'],
    'Cahaya': ['Sumber cahaya','Cahaya bergerak lurus','Pantulan cahaya','Bayang-bayang','Aplikasi cahaya'],
    'Bunyi': ['Sumber bunyi','Getaran','Perambatan bunyi','Kekuatan dan kelangsingan','Kegunaan bunyi'],
    'Magnet': ['Kutub magnet','Tarikan dan tolakan','Bahan magnet dan bukan magnet','Kegunaan magnet'],
    'Manusia': ['Struktur dan fungsi tubuh','Keperluan asas manusia','Pertumbuhan dan perkembangan','Kesihatan dan penjagaan diri'],
    'Haiwan': ['Ciri haiwan','Habitat','Pemakanan','Pembiakan','Penyesuaian'],
    'Tumbuhan': ['Bahagian tumbuhan','Keperluan tumbuhan','Pertumbuhan','Pembiakan','Penyesuaian'],
    'Jirim': ['Pepejal, cecair dan gas','Ciri keadaan jirim','Perubahan keadaan jirim','Kitaran perubahan jirim'],
    'Daya': ['Jenis daya','Kesan daya','Geseran','Aplikasi daya'],
    'Kelajuan': ['Maksud kelajuan','Jarak dan masa','Pengiraan kelajuan','Faktor mempengaruhi pergerakan'],
    'Mikroorganisma': ['Jenis mikroorganisma','Keperluan hidup','Kegunaan','Kesan berbahaya','Pencegahan penyakit'],
    'Biodiversiti': ['Kepelbagaian organisma','Pengelasan organisma','Habitat','Kepentingan biodiversiti','Pemuliharaan'],
    'Ekosistem': ['Habitat','Rantai makanan','Siratan makanan','Interaksi organisma','Keseimbangan ekosistem'],
    'Nutrisi': ['Kelas makanan','Diet seimbang','Sistem pencernaan','Penyerapan nutrien','Amalan pemakanan sihat'],
    'Asid dan Alkali': ['Sifat asid','Sifat alkali','Penunjuk','Nilai pH','Peneutralan'],
    'Keelektrikan dan Kemagnetan': ['Cas elektrik','Arus dan voltan','Litar elektrik','Magnet dan elektromagnet','Aplikasi harian'],
    'Daya dan Gerakan': ['Jenis daya','Gerakan','Halaju dan pecutan','Graf gerakan','Aplikasi daya'],
    'Keradioaktifan': ['Sinaran mengion','Jenis sinaran','Kegunaan radioisotop','Risiko dan keselamatan'],
    'Genetik': ['DNA dan gen','Kromosom','Pewarisan','Variasi','Mutasi'],
    'Tenaga Nuklear': ['Tenaga nuklear','Pembelahan nukleus','Kegunaan','Risiko','Pengurusan sisa'],
    'Elektrokimia': ['Elektrolit','Elektrolisis','Sel kimia','Aplikasi elektrokimia','Keselamatan'],
}

MATH_FIXED = {
    'Tambah': ['Fakta asas tambah','Tambah tanpa mengumpul semula','Tambah dengan mengumpul semula','Penyelesaian masalah'],
    'Tolak': ['Fakta asas tolak','Tolak tanpa mengumpul semula','Tolak dengan mengumpul semula','Penyelesaian masalah'],
    'Darab': ['Konsep darab','Sifir','Darab nombor','Penyelesaian masalah'],
    'Bahagi': ['Konsep bahagi','Fakta asas bahagi','Bahagi nombor','Penyelesaian masalah'],
    'Pecahan': ['Pecahan wajar','Pecahan setara','Banding pecahan','Operasi pecahan','Penyelesaian masalah'],
    'Perpuluhan': ['Nilai tempat','Banding perpuluhan','Tambah dan tolak','Darab dan bahagi','Penyelesaian masalah'],
    'Peratus': ['Konsep peratus','Tukar pecahan/perpuluhan/peratus','Peratus daripada kuantiti','Penyelesaian masalah'],
    'Wang': ['Nilai wang','Tambah dan tolak wang','Darab dan bahagi wang','Diskaun / baki','Penyelesaian masalah'],
    'Masa dan Waktu': ['Jam dan minit','Tempoh masa','Kalendar','Penukaran unit masa','Penyelesaian masalah'],
    'Pengurusan Data': ['Kumpul data','Jadual','Carta / graf','Tafsir data','Penyelesaian masalah'],
    'Nombor Nisbah': ['Integer','Pecahan','Perpuluhan','Nombor positif dan negatif','Operasi gabungan'],
    'Ungkapan Algebra': ['Pemboleh ubah','Sebutan algebra','Pekali','Permudahkan ungkapan','Nilai ungkapan'],
    'Persamaan Linear': ['Maksud persamaan','Persamaan satu pemboleh ubah','Kaedah penyelesaian','Masalah berayat'],
    'Indeks': ['Hukum indeks','Pendaraban indeks','Pembahagian indeks','Kuasa sifar dan negatif','Penyelesaian masalah'],
    'Bentuk Piawai': ['Nombor dalam bentuk piawai','Penukaran bentuk','Operasi bentuk piawai','Aplikasi'],
    'Matriks': ['Pengenalan matriks','Peringkat matriks','Tambah dan tolak','Darab skalar','Aplikasi matriks'],
    'Ubahan': ['Ubahan langsung','Ubahan songsang','Ubahan bergabung','Persamaan ubahan','Penyelesaian masalah'],
}

HISTORY_FIXED = {
    'Zaman Prasejarah': ['Maksud Zaman Prasejarah','Lokasi dan tempoh','Cara hidup','Peralatan','Sumbangan dan warisan'],
    'Kesultanan Melayu Melaka': ['Pengasasan','Sistem pentadbiran','Kegiatan ekonomi','Hubungan luar','Warisan'],
    'Pembentukan Malaysia': ['Idea pembentukan','Faktor pembentukan','Langkah pembentukan','Reaksi wilayah dan negara jiran','Pengisytiharan Malaysia'],
    'Kedatangan Kuasa Barat': ['Faktor kedatangan','Kuasa Barat terlibat','Strategi penguasaan','Kesan kepada negeri Melayu','Reaksi masyarakat'],
    'Kedaulatan Negara': ['Konsep kedaulatan','Ciri negara berdaulat','Kepentingan kedaulatan','Langkah mempertahankan kedaulatan'],
    'Perlembagaan Persekutuan': ['Latar belakang','Ciri utama','Keluhuran Perlembagaan','Hak dan tanggungjawab','Kepentingan'],
}

def get_subtopics(year_label, subject, topic):
    if subject == 'Sains':
        return SCIENCE_FIXED.get(topic, [
            f'Konsep asas {topic}', f'Ciri-ciri {topic}', f'Proses / hubungan dalam {topic}',
            f'Aplikasi {topic}', f'Kepentingan {topic}'
        ])
    if subject == 'Matematik':
        return MATH_FIXED.get(topic, [
            f'Konsep asas {topic}', f'Istilah dan simbol {topic}', f'Kaedah / langkah {topic}',
            f'Latihan pengiraan {topic}', f'Penyelesaian masalah {topic}'
        ])
    if subject == 'Sejarah':
        return HISTORY_FIXED.get(topic, [
            f'Latar belakang {topic}', 'Tokoh / pihak berkaitan', 'Peristiwa penting',
            'Kesan dan perubahan', 'Kepentingan / iktibar'
        ])
    if subject == 'Bahasa Melayu':
        return [f'Pengenalan {topic}', f'Mengenal pasti {topic}', f'Penggunaan {topic} dalam ayat',
                'Latihan pemahaman', 'Latihan penulisan / aplikasi']
    if subject == 'Bahasa Inggeris':
        return [f'Introduction to {topic}', 'Key vocabulary', 'Grammar / language focus',
                'Reading / comprehension', 'Writing / application']
    if subject == 'Pendidikan Islam':
        return [f'Pengenalan {topic}', 'Pengertian dan konsep', 'Dalil / contoh berkaitan',
                'Amalan dalam kehidupan', 'Pengajaran dan penghayatan']
    return [f'Pengenalan {topic}', 'Konsep utama', 'Contoh dan aplikasi', 'Latihan', 'Pengukuhan']


SUBJECTS = [
    ('🇲🇾 Bahasa Melayu','Bahasa Melayu'),('🇬🇧 Bahasa Inggeris','Bahasa Inggeris'),
    ('➗ Matematik','Matematik'),('🔬 Sains','Sains'),('🏛️ Sejarah','Sejarah'),
    ('☪️ Pendidikan Islam','Pendidikan Islam'),('✏️ Subjek Lain','Subjek Lain')
]

def send(cid, text, kb=None, parse_html=True, reply_keyboard=None):
    p = {'chat_id': cid, 'text': text}
    if parse_html:
        p['parse_mode'] = 'HTML'
    if kb:
        p['reply_markup'] = {'inline_keyboard': kb}
    elif reply_keyboard:
        p['reply_markup'] = {
            'keyboard': reply_keyboard,
            'resize_keyboard': True,
            'is_persistent': True
        }
    r = requests.post(f'{API}/sendMessage', json=p, timeout=20)
    return r


def install_menu_button(cid):
    """Paparkan butang ☰ Menu secara kekal di bawah ruang menaip Telegram."""
    send(cid, '☰ <b>Menu CikguLaju tersedia di bawah.</b>',
         reply_keyboard=[[{'text':'☰ Menu'}]])


def send_long_plain(cid, text):
    """Hantar output AI tanpa HTML dan pecahkan ikut had Telegram."""
    text = (text or '').strip()
    if not text:
        send(cid, '⚠️ Gemini tidak memulangkan jawapan. Cuba sekali lagi.')
        return
    limit = 3900
    while len(text) > limit:
        cut = text.rfind('\n', 0, limit)
        if cut < 1000:
            cut = limit
        send(cid, text[:cut], parse_html=False)
        text = text[cut:].lstrip()
    if text:
        send(cid, text, parse_html=False)



def safe_filename(value):
    clean = re.sub(r'[^A-Za-z0-9_-]+', '_', value or 'Bahan')
    return clean.strip('_')[:60] or 'Bahan'

def send_document(cid, path, caption=''):
    with open(path, 'rb') as f:
        data = {'chat_id': str(cid), 'caption': caption}
        return requests.post(
            f'{API}/sendDocument',
            data=data,
            files={'document': (os.path.basename(path), f)},
            timeout=60
        )

def clean_doc_text(value):
    return re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u00A0-\u024F]', '', value or '')

def create_word_file(s, ai_text, cid):
    filename = f"CikguLaju_{safe_filename(s.get('subject'))}_{safe_filename(s.get('topic'))}.docx"
    path = os.path.join(tempfile.gettempdir(), f"{cid}_{filename}")
    doc = Document()
    doc.styles['Normal'].font.name = 'Arial'
    doc.styles['Normal'].font.size = Pt(11)

    p = doc.add_paragraph()
    r = p.add_run('CIKGULAJU AI')
    r.bold = True
    r.font.size = Pt(16)

    fields = [
        ('Tahap', s.get('year','-')),
        ('Subjek', s.get('subject','-')),
        ('Tajuk', s.get('topic','-')),
        ('Subtopik', s.get('subtopic','Semua Subtopik')),
    ]
    if s.get('qtype'):
        fields.append(('Jenis', s.get('qtype')))
    if s.get('amount'):
        fields.append(('Bilangan', f"{s.get('amount')} soalan"))

    for k, v in fields:
        p = doc.add_paragraph()
        a = p.add_run(f'{k}: ')
        a.bold = True
        p.add_run(str(v))

    doc.add_paragraph('')
    for line in clean_doc_text(ai_text).splitlines():
        p = doc.add_paragraph()
        rr = p.add_run(line)
        if line.strip().upper().startswith('SKEMA'):
            rr.bold = True

    p = doc.add_paragraph()
    rr = p.add_run('Dijana menggunakan CikguLaju AI - semak semula sebelum digunakan dalam PdP.')
    rr.italic = True
    rr.font.size = Pt(8)

    doc.save(path)
    return path

def create_pdf_file(s, ai_text, cid):
    filename = f"CikguLaju_{safe_filename(s.get('subject'))}_{safe_filename(s.get('topic'))}.pdf"
    path = os.path.join(tempfile.gettempdir(), f"{cid}_{filename}")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CLTitle', parent=styles['Title'], fontName='Helvetica-Bold',
                                 fontSize=16, leading=20, alignment=TA_CENTER, spaceAfter=8)
    meta_style = ParagraphStyle('CLMeta', parent=styles['Normal'], fontName='Helvetica',
                                fontSize=9.5, leading=13, spaceAfter=2)
    body_style = ParagraphStyle('CLBody', parent=styles['Normal'], fontName='Helvetica',
                                fontSize=10.5, leading=15, spaceAfter=4)

    pdf = SimpleDocTemplate(path, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=16*mm, bottomMargin=16*mm)
    story = [Paragraph('CIKGULAJU AI', title_style)]

    fields = [
        ('Tahap', s.get('year','-')),
        ('Subjek', s.get('subject','-')),
        ('Tajuk', s.get('topic','-')),
        ('Subtopik', s.get('subtopic','Semua Subtopik')),
    ]
    if s.get('qtype'):
        fields.append(('Jenis', s.get('qtype')))
    if s.get('amount'):
        fields.append(('Bilangan', f"{s.get('amount')} soalan"))

    for k, v in fields:
        story.append(Paragraph(f'<b>{escape(str(k))}:</b> {escape(clean_doc_text(str(v)))}', meta_style))

    story.append(Spacer(1, 5*mm))
    for line in clean_doc_text(ai_text).splitlines():
        line = line.strip()
        if not line:
            story.append(Spacer(1, 3*mm))
        elif line.upper().startswith('SKEMA'):
            story.append(Paragraph(f'<b>{escape(line)}</b>', body_style))
        else:
            story.append(Paragraph(escape(line), body_style))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph('<i>Dijana menggunakan CikguLaju AI - semak semula sebelum digunakan dalam PdP.</i>',
                           ParagraphStyle('small', parent=body_style, fontSize=7.5, leading=10)))
    pdf.build(story)
    return path


def _gemini_request(prompt, model):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    payload = {
        'contents': [{'role':'user','parts':[{'text':prompt}]}],
        'generationConfig': {
            'temperature': 0.35,
            'maxOutputTokens': 8192
        }
    }
    headers = {
        'Content-Type':'application/json',
        'x-goog-api-key': GEMINI_API_KEY
    }
    return requests.post(url, headers=headers, json=payload, timeout=18)


def _gemini_error_detail(response):
    try:
        return response.json().get('error',{}).get('message') or response.text
    except Exception:
        return response.text


def gemini_generate(prompt):
    """Generate with retry + fallback for temporary Gemini congestion.

    Retry only transient errors (408, 429, 5xx). Client/auth errors are not
    retried. After retries on the main model, try configured fallback models.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError('GEMINI_API_KEY belum ditetapkan di Render.')

    models = []
    for model in [GEMINI_MODEL] + GEMINI_FALLBACK_MODELS:
        if model and model not in models:
            models.append(model)

    transient_statuses = {408, 429, 500, 502, 503, 504}
    last_error = None

    # Mod pantas: hanya 1 percubaan bagi setiap model.
    # Jika model pertama sibuk/timeout, terus lompat ke fallback.
    for model_index, model in enumerate(models):
        try:
            r = _gemini_request(prompt, model)
        except requests.RequestException as e:
            last_error = f'Ralat rangkaian Gemini: {e}'
            if model_index < len(models) - 1:
                print(f'Gemini timeout/network; switching fallback: {model} -> {models[model_index + 1]}', flush=True)
                continue
            break

        if r.ok:
            data = r.json()
            parts = (((data.get('candidates') or [{}])[0].get('content') or {}).get('parts') or [])
            out = ''.join(p.get('text','') for p in parts if isinstance(p,dict))
            if out.strip():
                if model != GEMINI_MODEL:
                    print(f'Gemini fallback success: {model}', flush=True)
                return out.strip()
            last_error = f'Gemini {model} tidak memulangkan teks.'
        else:
            detail = _gemini_error_detail(r)
            last_error = f'Gemini API {r.status_code} ({model}): {detail[:500]}'

            # Untuk 503/429/timeout sementara, terus tukar model tanpa tunggu retry.
            if r.status_code in transient_statuses and model_index < len(models) - 1:
                print(f'Gemini transient {r.status_code}; switching fallback immediately.', flush=True)
                continue

            # Ralat auth/config jangan cuba model lain berulang kali.
            if r.status_code not in transient_statuses:
                break

    raise RuntimeError(last_error or 'Gemini belum berjaya menjana bahan.')


def build_ai_prompt(s):
    task = s.get('task','questions')
    year = s.get('year','-')
    subject = s.get('subject','-')
    topic = s.get('topic','-')
    subtopic = s.get('subtopic','Semua Subtopik')
    qtype = s.get('qtype','Campuran')
    amount = s.get('amount','5')

    common = f"""Anda ialah pembantu guru Malaysia untuk CikguLaju AI.
Gunakan Bahasa Melayu Malaysia yang jelas, profesional dan sesuai dengan tahap murid.
Tahap: {year}
Subjek: {subject}
Topik: {topic}
Subtopik: {subtopic}

Arahan penting:
- Pastikan kandungan sesuai dengan tahap murid dan topik yang dipilih.
- Jangan reka fakta yang meragukan. Jika topik memerlukan maklumat khusus yang tidak diberi, kekalkan pada fakta asas yang kukuh.
- Formatkan jawapan supaya mudah terus disalin oleh guru.
- Jangan masukkan penerangan tentang proses AI.
"""

    if task == 'questions':
        return common + f"""
Tugasan: Jana {amount} soalan jenis {qtype}.
Sediakan:
1. Tajuk set soalan.
2. Arahan kepada murid.
3. Tepat {amount} soalan, bernombor dengan kemas.
4. Jika objektif, berikan 4 pilihan A-D dan hanya satu jawapan terbaik.
5. Jika campuran, seimbangkan objektif dan struktur mengikut jumlah soalan.
6. Selepas semua soalan, sediakan bahagian SKEMA JAWAPAN yang jelas dan sepadan nombor soalan.
"""
    if task == 'kbat':
        return common + f"""
Tugasan: Jana tepat {amount} soalan KBAT.
Jenis pilihan guru: {qtype}.
Soalan mesti menguji aplikasi, analisis, penilaian atau penciptaan, bukan hafalan semata-mata.
Sediakan cadangan jawapan / skema ringkas bagi setiap soalan.
"""
    if task == 'worksheet':
        return common + """
Tugasan: Hasilkan satu worksheet yang boleh terus digunakan di kelas.
Sediakan tajuk, objektif ringkas, nama/tarikh, arahan, beberapa aktiviti pelbagai bentuk, ruang jawapan yang sesuai, dan SKEMA JAWAPAN di bahagian akhir.
Elakkan reka bentuk yang memerlukan gambar jika gambar tidak diberikan.
"""
    if task == 'rph':
        return common + """
Tugasan: Hasilkan RPH ringkas dan praktikal untuk satu waktu pengajaran.
Sediakan: Tajuk, Standard/Kandungan pembelajaran secara umum tanpa mereka-reka kod DSKP, objektif pembelajaran yang boleh diukur, kriteria kejayaan, pengetahuan sedia ada, bahan bantu mengajar, set induksi, langkah pengajaran, aktiviti murid, elemen KBAT/PAK21 yang sesuai, pentaksiran, pemulihan/pengayaan dan refleksi guru.
Jika kod Standard Kandungan/Standard Pembelajaran tidak diberi, jangan cipta nombor kod.
"""
    return common + 'Hasilkan bahan pengajaran yang sesuai dengan pilihan guru.'


def generate_ai(cid):
    s = state.setdefault(cid,{})
    if not s.get('topic') and 'selected_topic_index' in s:
        topics = TOPICS.get(s.get('year',''),{}).get(s.get('subject',''),[])
        idx = s.get('selected_topic_index')
        if isinstance(idx, int) and 0 <= idx < len(topics):
            s['topic'] = topics[idx]

    if not s.get('topic'):
        send(cid, '⚠️ Pilihan belum lengkap. Sila pilih tajuk dahulu.',
             [[{'text':'🏠 Menu Utama','callback_data':'home'}]])
        return
    send(cid, '⚡ <b>Sedang jana bahan...</b>\n<i>Cikgu tunggu beberapa saat.</i>')
    try:
        result = gemini_generate(build_ai_prompt(s))
        send_long_plain(cid, result)
        send(cid, '✅ <b>Siap!</b> Cikgu boleh jana bahan lain atau kembali ke menu.',
             [[{'text':'🔄 Jana Semula','callback_data':'generate'}],
              [{'text':'🏠 Menu Utama','callback_data':'home'}]])
    except Exception as e:
        print('Gemini error:', repr(e), flush=True)
        # Elakkan paparkan mesej teknikal panjang kepada pengguna Telegram.
        send(cid, '⚠️ <b>AI sedang sibuk buat sementara waktu.</b>\n\nCikgu boleh tekan <b>Cuba Lagi</b>. Sistem sudah cuba semula dan menukar model secara automatik sebelum mesej ini dipaparkan.',
             [[{'text':'🔄 Cuba Lagi','callback_data':'generate'}],
              [{'text':'🏠 Menu Utama','callback_data':'home'}]])


def menu(cid, show_persistent=False):
    if show_persistent:
        install_menu_button(cid)
    send(cid,
         "👩‍🏫 <b>CIKGULAJU AI</b>\n<i>Bahan mengajar siap dengan lebih pantas ⚡</i>\n\n"
         "Pilih cara cikgu nak mula:\n\n"
         "⚡ <b>Cara Pantas</b> — pilih tahun/tingkatan, subjek dan tajuk.\n"
         "📚 <b>Guna Bahan Cikgu</b> — upload PDF atau gambar nota.",
         [[{'text':'⚡ CARA PANTAS','callback_data':'quick'}],
          [{'text':'📚 GUNA BAHAN CIKGU','callback_data':'material'}],
          [{'text':'⭐ Cikgu PRO','callback_data':'pro'},{'text':'👤 Akaun Saya','callback_data':'account'}]])

def quick(cid):
    send(cid,'⚡ <b>Apa yang cikgu nak hasilkan?</b>',[
        [{'text':'📝 Jana Soalan','callback_data':'task_questions'},{'text':'📋 Worksheet','callback_data':'task_worksheet'}],
        [{'text':'📚 RPH','callback_data':'task_rph'},{'text':'🧠 Soalan KBAT','callback_data':'task_kbat'}],
        [{'text':'⬅️ Menu Utama','callback_data':'home'}]])

def level(cid, task):
    state.setdefault(cid,{})['task'] = task
    send(cid,'🏫 <b>Pilih tahap:</b>',[
        [{'text':'🏫 Sekolah Rendah','callback_data':'level_primary'}],
        [{'text':'🏫 Sekolah Menengah','callback_data':'level_secondary'}],
        [{'text':'⬅️ Kembali','callback_data':'quick'}]])

def year(cid, lv):
    state.setdefault(cid,{})['level'] = lv
    vals = list(range(1,7) if lv == 'primary' else range(1,6))
    prefix = 'year_' if lv == 'primary' else 'form_'
    label = 'Tahun' if lv == 'primary' else 'Tingkatan'
    kb = []
    for i in range(0, len(vals), 2):
        kb.append([{'text':f'{label} {n}','callback_data':f'{prefix}{n}'} for n in vals[i:i+2]])
    kb.append([{'text':'⬅️ Menu Utama','callback_data':'home'}])
    send(cid,'🎓 <b>Pilih Tahun / Tingkatan:</b>',kb)

def subjects(cid, label):
    state.setdefault(cid,{})['year'] = label
    kb = []
    for i in range(0, len(SUBJECTS)-1, 2):
        row=[]
        for text, sub in SUBJECTS[i:i+2]:
            row.append({'text':text,'callback_data':'sub_'+sub})
        kb.append(row)
    kb.append([{'text':'✏️ Subjek Lain','callback_data':'sub_Subjek Lain'}])
    kb.append([{'text':'⬅️ Menu Utama','callback_data':'home'}])
    send(cid,f'📘 <b>{label}</b>\n\nPilih subjek:',kb)

def show_topics(cid, page=0):
    s = state.setdefault(cid,{})
    year_label = s.get('year','')
    sub = s.get('subject','')
    topics = TOPICS.get(year_label,{}).get(sub,[])

    if not topics:
        # Sejarah Tahun 1-3 atau subjek lain: benarkan taip sendiri.
        s['waiting'] = 'topic'
        if sub == 'Sejarah' and year_label in ('Tahun 1','Tahun 2','Tahun 3'):
            send(cid,f'🏛️ <b>{sub} — {year_label}</b>\n\nTiada senarai topik standard disediakan untuk tahap ini.\n\nTaip tajuk sendiri atau kembali ke menu utama.',[[{'text':'⬅️ Menu Utama','callback_data':'home'}]])
        else:
            send(cid,f'📚 <b>{sub}</b>\n\nTaip <b>tajuk / tema</b> yang cikgu mahu.',[[{'text':'⬅️ Menu Utama','callback_data':'home'}]])
        return

    s['topic_list'] = topics
    per_page = 8
    start = page * per_page
    end = min(start + per_page, len(topics))
    kb = []
    for idx in range(start, end):
        kb.append([{'text':f'📖 {topics[idx]}','callback_data':f'topic_{idx}'}])

    nav = []
    if page > 0:
        nav.append({'text':'⬅️ Sebelum','callback_data':f'tpage_{page-1}'})
    if end < len(topics):
        nav.append({'text':'Seterusnya ➡️','callback_data':f'tpage_{page+1}'})
    if nav:
        kb.append(nav)
    kb.append([{'text':'✏️ Tajuk Lain / Taip Sendiri','callback_data':'topic_custom'}])
    kb.append([{'text':'🏠 Menu Utama','callback_data':'home'}])

    pages = (len(topics)+per_page-1)//per_page
    send(cid,f'📚 <b>{sub} — {year_label}</b>\n\nPilih tajuk/topik:\n<i>Halaman {page+1}/{pages}</i>',kb)

def show_subtopics(cid, topic_index):
    s = state.setdefault(cid,{})
    topics = TOPICS.get(s.get('year',''),{}).get(s.get('subject',''),[])
    if topic_index < 0 or topic_index >= len(topics):
        return show_topics(cid,0)

    s['selected_topic_index'] = topic_index
    s['topic'] = topics[topic_index]
    subs = get_subtopics(s.get('year',''), s.get('subject',''), s['topic'])

    kb = [[{'text':'📚 Semua Subtopik','callback_data':f'st3|-1|{topic_index}'}]]
    for i, item in enumerate(subs):
        kb.append([{'text':f'▫️ {item}','callback_data':f'st3|{i}|{topic_index}'}])
    kb.append([{'text':'🏠 Menu Utama','callback_data':'home'}])
    send(cid,
         f"📖 <b>{s['topic']}</b>\n\nPilih subtopik:\n<i>Senarai ini tetap dan tidak berubah setiap kali dijana.</i>",
         kb)

def choose_topic(cid, idx):
    show_subtopics(cid, idx)

TASK_TO_CODE = {'questions':'q','worksheet':'w','rph':'r','kbat':'k'}
CODE_TO_TASK = {v:k for k,v in TASK_TO_CODE.items()}
QTYPE_TO_CODE = {'Objektif':'o','Struktur':'s','KBAT':'k','Campuran':'c'}
CODE_TO_QTYPE = {v:k for k,v in QTYPE_TO_CODE.items()}

def compact_year(label):
    return ('p' if label.startswith('Tahun ') else 's') + label.split()[-1]

def expand_year(code):
    return ('Tahun ' if code.startswith('p') else 'Tingkatan ') + code[1:]

def subject_index(subject):
    for i, (_, sub) in enumerate(SUBJECTS):
        if sub == subject:
            return i
    return -1

def rebuild_state(tc, yc, si, ti, sti, qc='-', amount='-'):
    try:
        si, ti, sti = int(si), int(ti), int(sti)
    except Exception:
        return None
    year_label = expand_year(yc)
    if si < 0 or si >= len(SUBJECTS):
        return None
    subject = SUBJECTS[si][1]
    topics = TOPICS.get(year_label,{}).get(subject,[])
    if ti < 0 or ti >= len(topics):
        return None
    topic = topics[ti]
    subs = get_subtopics(year_label, subject, topic)
    subtopic = 'Semua Subtopik'
    if sti >= 0:
        if sti >= len(subs):
            return None
        subtopic = subs[sti]

    s = {
        'task': CODE_TO_TASK.get(tc,''),
        'year': year_label,
        'subject': subject,
        'topic': topic,
        'subtopic': subtopic,
        'selected_topic_index': ti,
        'selected_subtopic_index': sti,
    }
    if qc != '-':
        s['qtype'] = CODE_TO_QTYPE.get(qc,'')
    if amount != '-':
        s['amount'] = str(amount)
    return s if s['task'] else None

def show_qtype_v3(cid, s, sti):
    tc = TASK_TO_CODE[s['task']]
    yc = compact_year(s['year'])
    si = subject_index(s['subject'])
    ti = s['selected_topic_index']
    send(cid,'📝 <b>Pilih jenis soalan:</b>',[
        [{'text':'🔘 Objektif','callback_data':f'qt3|o|{tc}|{yc}|{si}|{ti}|{sti}'},
         {'text':'✍️ Subjektif / Struktur','callback_data':f'qt3|s|{tc}|{yc}|{si}|{ti}|{sti}'}],
        [{'text':'🧠 KBAT','callback_data':f'qt3|k|{tc}|{yc}|{si}|{ti}|{sti}'},
         {'text':'🔀 Campuran','callback_data':f'qt3|c|{tc}|{yc}|{si}|{ti}|{sti}'}]])

def preview_v3(cid, s, gen_cb):
    send(cid,
         f"✅ <b>Pilihan Cikgu</b>\n\n🎓 {s.get('year','-')}\n📚 {s.get('subject','-')}\n"
         f"📖 {s.get('topic','-')}\n▫️ {s.get('subtopic','Semua Subtopik')}\n"
         f"📝 {s.get('qtype','-')}\n🔢 {s.get('amount','-')} soalan\n\n🤖 Sedia untuk dijana dengan AI.",
         [[{'text':'✨ Jana Dengan AI','callback_data':gen_cb}],
          [{'text':'🏠 Menu Utama','callback_data':'home'}]])

def generate_v3(cid, s, regen_cb):
    send(cid,'⚡ <b>Sedang jana bahan...</b>\n<i>Cikgu tunggu beberapa saat.</i>')
    try:
        result = gemini_generate(build_ai_prompt(s))
        state.setdefault(cid,{})['last_result'] = result
        state[cid]['last_result_context'] = s

        send_long_plain(cid, result)
        send(cid,'✅ <b>Siap!</b>\n\nPilih format fail:',
             [[{'text':'📄 PDF','callback_data':'file_pdf'},
               {'text':'📝 Word','callback_data':'file_word'}],
              [{'text':'📦 Kedua-dua','callback_data':'file_both'}],
              [{'text':'🔄 Jana Semula','callback_data':regen_cb}],
              [{'text':'🏠 Menu Utama','callback_data':'home'}]])
    except Exception as e:
        print('Gemini error:', repr(e), flush=True)
        send(cid,'⚠️ <b>AI sedang sibuk buat sementara waktu.</b>\n\nCuba lagi sebentar.',
             [[{'text':'🔄 Cuba Lagi','callback_data':regen_cb}],
              [{'text':'🏠 Menu Utama','callback_data':'home'}]])


def qtype(cid):
    send(cid,'📝 <b>Pilih jenis soalan:</b>',[
        [{'text':'🔘 Objektif','callback_data':'qt_Objektif'},{'text':'✍️ Subjektif / Struktur','callback_data':'qt_Struktur'}],
        [{'text':'🧠 KBAT','callback_data':'qt_KBAT'},{'text':'🔀 Campuran','callback_data':'qt_Campuran'}]])

def amount(cid, kind):
    state.setdefault(cid,{})['qtype'] = kind
    send(cid,'🔢 <b>Berapa soalan cikgu perlukan?</b>',[[{'text':str(n),'callback_data':f'amt_{n}'} for n in (5,10,20,30)]])

def callback(cid, d):
    if d == 'home':
        state[cid] = {}
        menu(cid)
    elif d == 'quick':
        quick(cid)
    elif d == 'material':
        state.setdefault(cid,{})['waiting'] = 'material'
        send(cid,'📚 <b>GUNA BAHAN CIKGU</b>\n\nHantar 📄 PDF atau 📸 gambar nota.\n\nPembacaan AI akan disambungkan pada langkah seterusnya.')
    elif d == 'pro':
        send(cid,'⭐ <b>CIKGU PRO</b>\n\n💳 <b>RM9.90/bulan</b> — harga pengenalan\n\n📝 Soalan & skema\n📋 Worksheet\n📚 RPH\n🧠 KBAT\n📥 Word/PDF\n⚡ Had lebih tinggi')
    elif d == 'account':
        send(cid,'👤 <b>AKAUN SAYA</b>\n\nPelan: 🎁 Percubaan\nStatus: Aktif')
    elif d.startswith('task_'):
        level(cid,d[5:])
    elif d == 'level_primary':
        year(cid,'primary')
    elif d == 'level_secondary':
        year(cid,'secondary')
    elif d.startswith('year_'):
        subjects(cid,'Tahun '+d[5:])
    elif d.startswith('form_'):
        subjects(cid,'Tingkatan '+d[5:])
    elif d.startswith('sub_'):
        state.setdefault(cid,{})['subject'] = d[4:]
        show_topics(cid,0)
    elif d.startswith('tpage_'):
        show_topics(cid,int(d[6:]))
    elif d.startswith('topic_'):
        if d == 'topic_custom':
            state.setdefault(cid,{})['waiting'] = 'topic'
            send(cid,'✏️ <b>Taip tajuk/topik sendiri:</b>')
        else:
            choose_topic(cid,int(d[6:]))

    elif d.startswith('st3|'):
        _, sti, ti = d.split('|')
        s0 = state.setdefault(cid,{})
        tc = TASK_TO_CODE.get(s0.get('task',''))
        yc = compact_year(s0.get('year',''))
        si = subject_index(s0.get('subject',''))
        if not tc or not yc or si < 0:
            return menu(cid)
        s = rebuild_state(tc, yc, si, ti, sti)
        if not s:
            return menu(cid)
        if s['task'] in ('questions','kbat'):
            show_qtype_v3(cid, s, int(sti))
        else:
            gen_cb = f"gn3|{tc}|{yc}|{si}|{ti}|{sti}|-|-"
            preview_v3(cid, s, gen_cb)

    elif d.startswith('qt3|'):
        parts = d.split('|')
        if len(parts) == 7:
            _, qc, tc, yc, si, ti, sti = parts
            send(cid,'🔢 <b>Berapa soalan cikgu perlukan?</b>',
                 [[{'text':str(n),'callback_data':f'am3|{n}|{qc}|{tc}|{yc}|{si}|{ti}|{sti}'} for n in (5,10,20,30)]])

    elif d.startswith('am3|'):
        parts = d.split('|')
        if len(parts) == 8:
            _, amount_n, qc, tc, yc, si, ti, sti = parts
            s = rebuild_state(tc, yc, si, ti, sti, qc, amount_n)
            if s:
                gen_cb = f'gn3|{tc}|{yc}|{si}|{ti}|{sti}|{qc}|{amount_n}'
                preview_v3(cid, s, gen_cb)

    elif d.startswith('gn3|'):
        parts = d.split('|')
        if len(parts) == 8:
            _, tc, yc, si, ti, sti, qc, amount_n = parts
            s = rebuild_state(tc, yc, si, ti, sti, qc, amount_n)
            if s:
                generate_v3(cid, s, d)

    elif d in ('file_pdf','file_word','file_both'):
        st = state.setdefault(cid,{})
        result = st.get('last_result')
        ctx = st.get('last_result_context')
        if not result or not ctx:
            return send(cid,'⚠️ Fail sementara sudah tiada. Sila jana bahan sekali lagi.',
                        [[{'text':'🏠 Menu Utama','callback_data':'home'}]])

        send(cid,'📦 <b>Sedang menyediakan fail...</b>')
        try:
            paths = []
            if d in ('file_pdf','file_both'):
                p = create_pdf_file(ctx, result, cid)
                paths.append(p)
                send_document(cid, p, '📄 PDF - sedia untuk cetak')
            if d in ('file_word','file_both'):
                p = create_word_file(ctx, result, cid)
                paths.append(p)
                send_document(cid, p, '📝 Word - boleh diedit')
            for p in paths:
                if os.path.exists(p):
                    os.remove(p)
            send(cid,'✅ Fail siap.',[[{'text':'🏠 Menu Utama','callback_data':'home'}]])
        except Exception as e:
            print('File error:', repr(e), flush=True)
            send(cid,'⚠️ Fail belum berjaya disediakan. Cuba semula.',
                 [[{'text':'🏠 Menu Utama','callback_data':'home'}]])


@app.route('/')
def index():
    return jsonify({'status':'ok','app':'CikguLaju AI','gemini_ready':bool(GEMINI_API_KEY),'gemini_model':GEMINI_MODEL})

@app.route('/webhook', methods=['POST'])
def webhook():
    u = request.get_json(silent=True) or {}
    if 'callback_query' in u:
        c = u['callback_query']
        requests.post(f'{API}/answerCallbackQuery',json={'callback_query_id':c['id']},timeout=10)
        callback(c['message']['chat']['id'],c.get('data',''))
    elif 'message' in u:
        m = u['message']
        cid = m['chat']['id']
        if m.get('text') in ('/start','/menu','☰ Menu','Menu'):
            state[cid] = {}
            menu(cid, show_persistent=True)
        elif 'text' in m and state.get(cid,{}).get('waiting') == 'topic':
            state[cid]['topic'] = m['text'].strip()
            state[cid].pop('waiting',None)
            send(cid,'✅ Tajuk sendiri diterima. Buat masa ini fungsi subtopik tetap digunakan untuk tajuk yang tersedia dalam menu.',
                 [[{'text':'🏠 Menu Utama','callback_data':'home'}]])
        elif 'document' in m or 'photo' in m:
            send(cid,'✅ Bahan diterima. Pembacaan PDF/gambar oleh AI akan disambungkan seterusnya.')
    return jsonify({'ok':True})

@app.route('/setup-webhook')
def setup_webhook():
    if not BOT_TOKEN or not WEBHOOK_URL:
        return jsonify({'ok':False,'error':'Tetapkan BOT_TOKEN dan WEBHOOK_URL dahulu'}),500
    url = WEBHOOK_URL.rstrip('/') + '/webhook'
    r = requests.post(f'{API}/setWebhook',json={'url':url},timeout=20)
    requests.post(f'{API}/setMyCommands', json={'commands':[
        {'command':'start','description':'Buka CikguLaju AI'},
        {'command':'menu','description':'Menu utama'}
    ]}, timeout=20)
    requests.post(f'{API}/setChatMenuButton', json={'menu_button':{'type':'commands'}}, timeout=20)
    return jsonify({'webhook':url,'telegram':r.json(),'menu_button':'commands'})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','10000')))
