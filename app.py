import os
import html
import requests
import time
import random
import tempfile
import re
import secrets
from flask import Flask, request, jsonify
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Flowable
from reportlab.lib.units import mm
from reportlab.lib import colors
from xml.sax.saxutils import escape

app = Flask(__name__)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.getenv(
    'GEMINI_FALLBACK_MODELS',
    'gemini-3.7-flash,gemini-3.6-flash,gemini-3.5-flash'
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

def _is_heading_line(line):
    u = line.strip().upper()
    return (
        u.startswith('BAHAGIAN ') or
        u.startswith('SECTION ') or
        u.startswith('ARAHAN') or
        u.startswith('SKEMA JAWAPAN') or
        u.startswith('JAWAPAN') or
        u.startswith('AKTIVITI ') or
        u.startswith('OBJEKTIF PEMBELAJARAN') or
        u.startswith('KRITERIA KEJAYAAN') or
        u.startswith('SET INDUKSI') or
        u.startswith('LANGKAH PENGAJARAN') or
        u.startswith('PENTAKSIRAN') or
        u.startswith('REFLEKSI')
    )

def _is_question_line(line):
    return bool(re.match(r'^\s*(?:SOALAN\s*)?\d+[\.\)]\s+', line, flags=re.I))

def _is_option_line(line):
    return bool(re.match(r'^\s*[A-D][\.\)]\s+', line))

def _is_answer_line(line):
    return bool(re.match(r'^\s*(?:JAWAPAN|ANSWER)\s*(?:\d+)?\s*[:\-]', line, flags=re.I))

def _is_titleish(line):
    u = line.strip().upper()
    return (
        u.startswith('TAJUK:') or
        u.startswith('LEMBARAN KERJA') or
        u.startswith('SET SOALAN') or
        u.startswith('LATIHAN ') or
        u.startswith('RANCANGAN PENGAJARAN HARIAN')
    )

def _word_set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        if edge in kwargs:
            edge_data = kwargs.get(edge)
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key in ['val', 'sz', 'space', 'color']:
                if key in edge_data:
                    element.set(qn('w:{}'.format(key)), str(edge_data[key]))

def _word_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' PAGE '
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)

def _word_add_answer_lines(doc, count=2):
    for _ in range(count):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.add_run('_' * 82)


def _worksheet_split(ai_text):
    """Parse AI text into student sections/questions and a separate answer scheme."""
    lines = [x.strip() for x in clean_doc_text(ai_text).splitlines() if x.strip()]
    student = []
    scheme = []
    in_scheme = False

    for line in lines:
        u = line.upper().strip()

        # Template already provides the main instruction/header.
        if u == 'ARAHAN:' or u.startswith('ARAHAN:'):
            continue

        if u.startswith('SKEMA JAWAPAN') or u == 'JAWAPAN':
            in_scheme = True
            continue

        if in_scheme:
            scheme.append(line)
        else:
            student.append(line)

    return student, scheme


def _worksheet_blocks(student_lines):
    """
    Group a question together with its A-D options and nearby supporting lines.
    Section headings/instructions are returned as their own block.
    """
    blocks = []
    current = None

    for line in student_lines:
        u = line.upper()

        if u.startswith('HELAIAN ') or u.startswith('WORKSHEET '):
            if current:
                blocks.append(current)
                current = None
            blocks.append({'type':'sheet', 'lines':[line]})
            continue

        if u.startswith('BAHAGIAN ') or u.startswith('SECTION '):
            if current:
                blocks.append(current)
                current = None
            blocks.append({'type':'section', 'lines':[line]})
            continue

        if _is_question_line(line):
            if current:
                blocks.append(current)
            current = {'type':'question', 'lines':[line]}
            continue

        if current and (_is_option_line(line) or not _is_heading_line(line)):
            current['lines'].append(line)
        else:
            if current:
                blocks.append(current)
                current = None
            blocks.append({'type':'instruction', 'lines':[line]})

    if current:
        blocks.append(current)

    return blocks


def _worksheet_question_kind(lines):
    """Decide how much answer space a student needs."""
    joined = ' '.join(lines).lower()

    if any(_is_option_line(x) for x in lines):
        return 'objective'

    if '____' in joined or 'tempat kosong' in joined:
        return 'fill'

    # Word problems and explicit working/calculation requests get working space.
    keywords = [
        'berapakah', 'berapa', 'hitung', 'kirakan', 'kira', 'cari hasil',
        'selesaikan', 'tunjukkan jalan kerja', 'show your working',
        'explain', 'jelaskan', 'huraikan', 'nyatakan sebab'
    ]
    if any(k in joined for k in keywords):
        return 'structured'

    return 'short'


def _extract_scheme_rows(scheme_lines):
    """Turn answer scheme lines into compact (number, answer) rows."""
    rows = []
    current_section = None
    for line in scheme_lines:
        u = line.upper().strip()
        if u.startswith('BAHAGIAN ') or u.startswith('SECTION '):
            current_section = line
            rows.append(('__SECTION__', current_section))
            continue

        m = re.match(r'^\s*(\d+)[\.\)]\s*(.+)$', line)
        if m:
            rows.append((m.group(1), m.group(2).strip()))
        elif line:
            # Keep any meaningful note, but don't lose it.
            rows.append(('', line))
    return rows


def _visual_symbol_for_question(text):
    """Simple printable visual cues without external image downloads."""
    t = text.lower()
    mapping = [
        (['epal','apple'], '●'),
        (['bola','ball'], '●'),
        (['bintang','star'], '★'),
        (['bunga','flower'], '✿'),
        (['pensel','pencil'], '✎'),
        (['buku','book'], '▭'),
        (['duit','wang','money','syiling'], '◉'),
        (['jam','clock'], '◷'),
        (['segi tiga','triangle'], '△'),
        (['segi empat','square'], '□'),
        (['bulatan','circle'], '○'),
    ]
    for keys, symbol in mapping:
        if any(k in t for k in keys):
            return symbol
    return None


def _worksheet_level(s):
    y = str(s.get('year','')).lower()
    if any(x in y for x in ['tahun 1','tahun 2','tahun 3']):
        return 'lower_primary'
    if any(x in y for x in ['tahun 4','tahun 5','tahun 6']):
        return 'upper_primary'
    return 'secondary'


def _worksheet_pages(s):
    try:
        return max(1, min(5, int(s.get('worksheet_pages', 1))))
    except Exception:
        return 1

def _difficulty_label(code):
    return {
        'easy': 'Mudah',
        'medium': 'Sederhana',
        'hard': 'Sukar',
        'mixed': 'Campuran'
    }.get(str(code), 'Campuran')


def _difficulty_instruction(s):
    level = _worksheet_level(s)
    diff = str(s.get('difficulty', 'mixed'))

    if level == 'lower_primary':
        mapping = {
            'easy': (
                'Aras MUDAH untuk Tahun 1-3: gunakan nombor kecil, arahan sangat ringkas, '
                'gambar objek sebenar dalam worksheet, kiraan objek, padanan, pilihan mudah dan satu langkah sahaja.'
            ),
            'medium': (
                'Aras SEDERHANA untuk Tahun 1-3: gunakan gabungan visual dan simbol, '
                'dua langkah mudah apabila sesuai, isi tempat kosong, aplikasi situasi harian ringkas.'
            ),
            'hard': (
                'Aras SUKAR untuk Tahun 1-3 tetapi masih sesuai umur: gunakan penyelesaian masalah ringkas, '
                'pilih strategi, bandingkan, cari nilai hilang, dan penaakulan asas. Jangan melebihi silibus tahap.'
            ),
            'mixed': (
                'Aras CAMPURAN untuk Tahun 1-3: susun progresif kira-kira 40% mudah, 40% sederhana, 20% mencabar; '
                'mulakan visual/asas dan akhiri dengan aplikasi ringkas.'
            )
        }
    elif level == 'upper_primary':
        mapping = {
            'easy': (
                'Aras MUDAH untuk Tahun 4-6: fokus penguasaan konsep asas, satu langkah, istilah jelas, '
                'contoh langsung, jadual/rajah mudah jika membantu.'
            ),
            'medium': (
                'Aras SEDERHANA untuk Tahun 4-6: gabungkan pengiraan, aplikasi, tafsiran jadual/rajah, '
                'dan masalah dua langkah yang munasabah.'
            ),
            'hard': (
                'Aras SUKAR untuk Tahun 4-6 tetapi masih dalam tahap murid: gunakan aplikasi bukan rutin, '
                'penyelesaian masalah pelbagai langkah, penaakulan dan KBAT yang sesuai silibus.'
            ),
            'mixed': (
                'Aras CAMPURAN untuk Tahun 4-6: susun progresif kira-kira 30% mudah, 50% sederhana, 20% sukar; '
                'pastikan perubahan aras jelas tetapi tidak melangkaui tahap.'
            )
        }
    else:
        mapping = {
            'easy': (
                'Aras MUDAH sekolah menengah: fokus kefahaman asas konsep, prosedur langsung dan soalan satu langkah.'
            ),
            'medium': (
                'Aras SEDERHANA sekolah menengah: gunakan aplikasi konsep, interpretasi maklumat dan penyelesaian masalah sederhana.'
            ),
            'hard': (
                'Aras SUKAR sekolah menengah: gunakan penaakulan, aplikasi bukan rutin, analisis dan KBAT yang relevan dengan tahap.'
            ),
            'mixed': (
                'Aras CAMPURAN sekolah menengah: susun kira-kira 25% mudah, 50% sederhana, 25% sukar secara progresif.'
            )
        }

    return mapping.get(diff, mapping['mixed'])




class WorksheetVisual(Flowable):
    """Printable black/white vector illustrations drawn directly into the PDF."""
    def __init__(self, obj='objek', count=5, width=150*mm, height=28*mm):
        Flowable.__init__(self)
        self.obj = (obj or 'objek').lower()
        self.count = max(1, min(20, int(count or 1)))
        self.width = width
        rows = 1 if self.count <= 10 else 2
        self.height = height * rows

    def _star(self, c, x, y, r):
        import math
        pts = []
        for i in range(10):
            a = -math.pi/2 + i*math.pi/5
            rr = r if i % 2 == 0 else r*0.42
            pts.append((x + rr*math.cos(a), y + rr*math.sin(a)))
        p = c.beginPath()
        p.moveTo(*pts[0])
        for pt in pts[1:]:
            p.lineTo(*pt)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    def _draw_one(self, c, x, y, size):
        o = self.obj
        c.setLineWidth(1)

        if any(k in o for k in ['epal','apple']):
            c.circle(x, y, size*0.34, stroke=1, fill=0)
            c.line(x, y+size*0.32, x+size*0.05, y+size*0.52)
            c.ellipse(x+size*0.03, y+size*0.38, x+size*0.25, y+size*0.53, stroke=1, fill=0)
        elif any(k in o for k in ['bintang','star']):
            self._star(c, x, y, size*0.42)
        elif any(k in o for k in ['bola','ball']):
            c.circle(x, y, size*0.38, stroke=1, fill=0)
            c.arc(x-size*.28, y-size*.35, x+size*.28, y+size*.35, 70, 40)
            c.arc(x-size*.35, y-size*.22, x+size*.35, y+size*.22, 180, 180)
        elif any(k in o for k in ['bunga','flower']):
            for dx,dy in [(0,size*.24),(size*.24,0),(0,-size*.24),(-size*.24,0)]:
                c.circle(x+dx, y+dy, size*.18, stroke=1, fill=0)
            c.circle(x, y, size*.12, stroke=1, fill=0)
        elif any(k in o for k in ['pensel','pencil']):
            c.saveState()
            c.translate(x-size*.34, y-size*.08)
            c.rect(0, 0, size*.58, size*.16, stroke=1, fill=0)
            p = c.beginPath()
            p.moveTo(size*.58, 0)
            p.lineTo(size*.78, size*.08)
            p.lineTo(size*.58, size*.16)
            p.close()
            c.drawPath(p, stroke=1, fill=0)
            c.restoreState()
        elif any(k in o for k in ['buku','book']):
            c.rect(x-size*.38, y-size*.28, size*.76, size*.56, stroke=1, fill=0)
            c.line(x, y-size*.28, x, y+size*.28)
        elif any(k in o for k in ['syiling','coin','wang','duit']):
            c.circle(x, y, size*.38, stroke=1, fill=0)
            c.setFont('Helvetica-Bold', max(6, size*.22))
            c.drawCentredString(x, y-size*.08, 'RM')
        elif any(k in o for k in ['segi tiga','triangle']):
            p = c.beginPath()
            p.moveTo(x, y+size*.4); p.lineTo(x-size*.4, y-size*.35)
            p.lineTo(x+size*.4, y-size*.35); p.close()
            c.drawPath(p, stroke=1, fill=0)
        elif any(k in o for k in ['segi empat','square']):
            c.rect(x-size*.35, y-size*.35, size*.7, size*.7, stroke=1, fill=0)
        else:
            # Generic countable object: simple outlined circle, never the word "VISUAL".
            c.circle(x, y, size*.34, stroke=1, fill=0)

    def draw(self):
        c = self.canv
        cols = min(10, self.count)
        rows = 1 if self.count <= 10 else 2
        cell_w = self.width / max(cols, 1)
        cell_h = self.height / rows
        size = min(cell_w, cell_h) * 0.72
        for i in range(self.count):
            row = i // 10
            col = i % 10
            x = col*cell_w + cell_w/2
            y = self.height - (row*cell_h + cell_h/2)
            self._draw_one(c, x, y, size)


def _find_visual_token(lines):
    """Find VISUAL token anywhere in a question block, not only on the first line."""
    joined = ' '.join(lines)
    m = re.search(r'\[VISUAL:\s*([^,\]]+)\s*,\s*(\d+)\s*\]', joined, flags=re.I)
    if not m:
        # tolerate Gemini omitting brackets
        m = re.search(r'\bVISUAL:\s*([^,\n]+?)\s*,\s*(\d+)\b', joined, flags=re.I)
    if m:
        return m.group(1).strip(), max(1, min(20, int(m.group(2))))
    return None


def _strip_visual_tokens(value):
    value = re.sub(r'\[(?:VISUAL|DIAGRAM):[^\]]+\]', '', value, flags=re.I)
    value = re.sub(r'\b(?:VISUAL|DIAGRAM):[^\n]+', '', value, flags=re.I)
    return value.strip()

def create_word_file(s, ai_text, cid):
    filename = f"CikguLaju_{safe_filename(s.get('subject'))}_{safe_filename(s.get('topic'))}.docx"
    path = os.path.join(tempfile.gettempdir(), f"{cid}_{filename}")

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.35)
    section.bottom_margin = Cm(1.4)
    section.left_margin = Cm(1.55)
    section.right_margin = Cm(1.55)

    normal = doc.styles['Normal']
    normal.font.name = 'Arial'
    normal.font.size = Pt(10.5)

    # -------- WORKSHEET PROFESSIONAL TEMPLATE --------
    if s.get('task') == 'worksheet':
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run('LEMBARAN KERJA')
        r.bold = True
        r.font.size = Pt(14)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(str(s.get('subject','')).upper())
        r.bold = True
        r.font.size = Pt(16)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(f"{s.get('year','')}  |  Tajuk: {s.get('topic','')}  |  Aras: {_difficulty_label(s.get('difficulty','mixed'))}")
        r.bold = True
        r.font.size = Pt(10.5)

        if s.get('subtopic'):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(7)
            r = p.add_run(f"Subtopik: {s.get('subtopic')}")
            r.italic = True
            r.font.size = Pt(9)

        # Student info, compact two-row grid
        info = doc.add_table(rows=2, cols=4)
        info.alignment = WD_TABLE_ALIGNMENT.CENTER
        labels = [
            ('Nama', '__________________________________', 'Kelas', '____________'),
            ('Tarikh', '__________________________________', 'Markah', '________ / ________')
        ]
        for ri, row in enumerate(labels):
            for ci, value in enumerate(row):
                cell = info.cell(ri, ci)
                p = cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                rr = p.add_run(value)
                rr.bold = ci in (0,2)
                _word_set_cell_border(
                    cell,
                    top={'val':'single','sz':'5','color':'777777'},
                    bottom={'val':'single','sz':'5','color':'777777'},
                    left={'val':'single','sz':'5','color':'777777'},
                    right={'val':'single','sz':'5','color':'777777'}
                )

        doc.add_paragraph()

        # One main instruction only; AI instructions are removed by parser.
        box = doc.add_table(rows=1, cols=1)
        box.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = box.cell(0,0)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        rr = p.add_run('ARAHAN: ')
        rr.bold = True
        p.add_run('Jawab semua soalan dengan teliti. Tulis jawapan pada ruang yang disediakan.')
        _word_set_cell_border(
            c,
            top={'val':'single','sz':'8','color':'444444'},
            bottom={'val':'single','sz':'8','color':'444444'},
            left={'val':'single','sz':'8','color':'444444'},
            right={'val':'single','sz':'8','color':'444444'}
        )
        doc.add_paragraph()

        student_lines, scheme_lines = _worksheet_split(ai_text)
        blocks = _worksheet_blocks(student_lines)

        sheet_seen = 0
        for block in blocks:
            if block['type'] == 'sheet':
                sheet_seen += 1
                if sheet_seen > 1:
                    doc.add_page_break()
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(block['lines'][0])
                r.bold = True
                r.font.size = Pt(13)
                continue

            if block['type'] == 'section':
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(7)
                p.paragraph_format.space_after = Pt(2)
                rr = p.add_run(block['lines'][0])
                rr.bold = True
                rr.font.size = Pt(11.5)
                continue

            if block['type'] == 'instruction':
                for line in block['lines']:
                    if _is_titleish(line) or line.upper().startswith('ARAHAN'):
                        continue
                    p = doc.add_paragraph()
                    p.paragraph_format.space_after = Pt(5)
                    rr = p.add_run(line)
                    rr.italic = True
                continue

            lines = block['lines']
            kind = _worksheet_question_kind(lines)

            qtbl = doc.add_table(rows=1, cols=1)
            qtbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell = qtbl.cell(0,0)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP

            # Question line
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(4)
            raw_q = lines[0]
            visual_info = _find_visual_token(lines)
            clean_q = _strip_visual_tokens(raw_q)
            p.clear()
            rr = p.add_run(clean_q)
            rr.bold = True
            if visual_info:
                obj, count = visual_info
                symbol = _visual_symbol_for_question(obj) or '○'
                # Word fallback uses printable pictograms only; never exposes VISUAL/DIAGRAM tokens.
                per_row = 8
                for start_i in range(0, count, per_row):
                    vp = cell.add_paragraph('     '.join([symbol] * min(per_row, count-start_i)))
                    vp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    vp.paragraph_format.space_after = Pt(2)
                    for run in vp.runs:
                        run.font.size = Pt(18)

            # Options/supporting lines
            options = [x for x in lines[1:] if _is_option_line(x)]
            other = [_strip_visual_tokens(x) for x in lines[1:]
                     if not _is_option_line(x) and not _is_answer_line(x)]
            other = [x for x in other if x]

            if options:
                # A-D in two columns when possible
                ot = cell.add_table(rows=2, cols=2)
                ot.alignment = WD_TABLE_ALIGNMENT.CENTER
                vals = options[:4] + [''] * max(0, 4-len(options))
                for i, val in enumerate(vals[:4]):
                    pp = ot.cell(i//2, i%2).paragraphs[0]
                    pp.paragraph_format.space_after = Pt(1)
                    pp.add_run(val)
            for extra in other:
                pp = cell.add_paragraph()
                pp.paragraph_format.space_after = Pt(2)
                pp.add_run(extra)

            # Answer/work area only when pedagogically useful.
            if kind == 'structured':
                pp = cell.add_paragraph()
                pp.paragraph_format.space_before = Pt(5)
                rr = pp.add_run('Jalan kerja:')
                rr.italic = True
                for _ in range(2):
                    pp = cell.add_paragraph('____________________________________________________________')
                    pp.paragraph_format.space_after = Pt(1)
                pp = cell.add_paragraph('Jawapan: _________________________________________________')
                pp.paragraph_format.space_after = Pt(1)
            elif kind == 'short':
                pp = cell.add_paragraph('Jawapan: _________________________________________________')
                pp.paragraph_format.space_before = Pt(4)
                pp.paragraph_format.space_after = Pt(1)
            # objective and fill-in get no redundant "Jawapan" line.

            _word_set_cell_border(
                cell,
                top={'val':'single','sz':'7','color':'777777'},
                bottom={'val':'single','sz':'7','color':'777777'},
                left={'val':'single','sz':'7','color':'777777'},
                right={'val':'single','sz':'7','color':'777777'}
            )

            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(3)

        # Answer scheme on a fresh page.
        rows = _extract_scheme_rows(scheme_lines)
        if rows:
            doc.add_page_break()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run('SKEMA JAWAPAN')
            r.bold = True
            r.font.size = Pt(14)

            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(f"{s.get('subject','')} • {s.get('year','')} • {s.get('topic','')}")
            r.font.size = Pt(9)

            table = None
            for no, ans in rows:
                if no == '__SECTION__':
                    p = doc.add_paragraph()
                    r = p.add_run(ans)
                    r.bold = True
                    r.font.size = Pt(10.5)
                    table = None
                    continue

                if table is None:
                    table = doc.add_table(rows=1, cols=2)
                    table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    h = table.rows[0].cells
                    h[0].paragraphs[0].add_run('No.').bold = True
                    h[1].paragraphs[0].add_run('Jawapan').bold = True

                cells = table.add_row().cells
                cells[0].text = no
                cells[1].text = ans

            for t in doc.tables[3:]:
                for row in t.rows:
                    for cell in row.cells:
                        _word_set_cell_border(
                            cell,
                            top={'val':'single','sz':'5','color':'888888'},
                            bottom={'val':'single','sz':'5','color':'888888'},
                            left={'val':'single','sz':'5','color':'888888'},
                            right={'val':'single','sz':'5','color':'888888'}
                        )

        footer = section.footer
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr = p.add_run('CikguLaju AI  •  ')
        rr.font.size = Pt(7.5)
        _word_page_number(p)

        doc.save(path)
        return path

    # -------- NON-WORKSHEET: retain exam-style behaviour --------
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('CIKGULAJU AI')
    r.bold = True
    r.font.size = Pt(15)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(str(s.get('subject','')).upper())
    r.bold = True
    r.font.size = Pt(13)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"{s.get('year','')}  •  {s.get('topic','')}")
    r.bold = True
    r.font.size = Pt(11)

    for raw in clean_doc_text(ai_text).splitlines():
        line = raw.strip()
        if not line:
            continue
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        rr = p.add_run(line)
        if _is_heading_line(line):
            rr.bold = True

    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = p.add_run('CikguLaju AI  •  ')
    rr.font.size = Pt(7.5)
    _word_page_number(p)

    doc.save(path)
    return path


def _pdf_header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFont('Helvetica', 7.5)
    canvas.drawCentredString(width/2, 8*mm, f"CikguLaju AI  •  Halaman {doc.page}")
    canvas.restoreState()

def create_pdf_file(s, ai_text, cid):
    filename = f"CikguLaju_{safe_filename(s.get('subject'))}_{safe_filename(s.get('topic'))}.pdf"
    path = os.path.join(tempfile.gettempdir(), f"{cid}_{filename}")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('WSTitle', parent=styles['Title'], fontName='Helvetica-Bold',
                                 fontSize=14, leading=16, alignment=TA_CENTER, spaceAfter=1)
    subject_style = ParagraphStyle('WSSubject', parent=styles['Normal'], fontName='Helvetica-Bold',
                                   fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=2)
    sub_style = ParagraphStyle('WSSub', parent=styles['Normal'], fontName='Helvetica',
                               fontSize=9, leading=11, alignment=TA_CENTER, spaceAfter=5)
    section_style = ParagraphStyle('WSSection', parent=styles['Normal'], fontName='Helvetica-Bold',
                                   fontSize=11, leading=14, spaceBefore=5, spaceAfter=2)
    instruction_style = ParagraphStyle('WSInst', parent=styles['Normal'], fontName='Helvetica-Oblique',
                                       fontSize=9.2, leading=12, spaceAfter=4)
    question_style = ParagraphStyle('WSQuestion', parent=styles['Normal'], fontName='Helvetica-Bold',
                                    fontSize=10.2, leading=13.5, spaceAfter=3)
    option_style = ParagraphStyle('WSOption', parent=styles['Normal'], fontName='Helvetica',
                                  fontSize=9.6, leading=12, spaceAfter=1)
    body_style = ParagraphStyle('WSBody', parent=styles['Normal'], fontName='Helvetica',
                                fontSize=9.5, leading=12.5, spaceAfter=2)

    pdf = SimpleDocTemplate(
        path, pagesize=A4,
        rightMargin=14*mm, leftMargin=14*mm,
        topMargin=12*mm, bottomMargin=14*mm
    )

    # Non-worksheet falls back to a simple clean document.
    if s.get('task') != 'worksheet':
        story = [
            Paragraph('CIKGULAJU AI', title_style),
            Paragraph(escape(clean_doc_text(str(s.get('subject',''))).upper()), subject_style),
            Paragraph(escape(clean_doc_text(f"{s.get('year','')} | {s.get('topic','')}")), sub_style),
        ]
        for raw in clean_doc_text(ai_text).splitlines():
            line = raw.strip()
            if not line:
                continue
            story.append(Paragraph(escape(line), body_style))
        pdf.build(story, onFirstPage=_pdf_header_footer, onLaterPages=_pdf_header_footer)
        return path

    story = [
        Paragraph('LEMBARAN KERJA', title_style),
        Paragraph(escape(clean_doc_text(str(s.get('subject',''))).upper()), subject_style),
        Paragraph(
            escape(clean_doc_text(f"{s.get('year','')}  |  Tajuk: {s.get('topic','')}  |  Subtopik: {s.get('subtopic','Semua Subtopik')}  |  Aras: {_difficulty_label(s.get('difficulty','mixed'))}")),
            sub_style
        ),
    ]

    # Compact pupil details
    info_data = [
        [Paragraph('<b>Nama</b>', body_style), '________________________________',
         Paragraph('<b>Kelas</b>', body_style), '____________'],
        [Paragraph('<b>Tarikh</b>', body_style), '________________________________',
         Paragraph('<b>Markah</b>', body_style), '______ / ______']
    ]
    info = Table(info_data, colWidths=[15*mm, 72*mm, 15*mm, 70*mm], rowHeights=[8*mm,8*mm])
    info.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.35,colors.grey),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),4),
        ('RIGHTPADDING',(0,0),(-1,-1),4),
        ('FONTSIZE',(0,0),(-1,-1),8.8),
    ]))
    story.extend([info, Spacer(1,3*mm)])

    instruction = Table(
        [[Paragraph('<b>ARAHAN:</b> Jawab semua soalan dengan teliti. Tulis jawapan pada ruang yang disediakan.', body_style)]],
        colWidths=[172*mm]
    )
    instruction.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.7,colors.black),
        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    story.extend([instruction, Spacer(1,3*mm)])

    student_lines, scheme_lines = _worksheet_split(ai_text)
    blocks = _worksheet_blocks(student_lines)

    sheet_seen = 0
    for block in blocks:
        if block['type'] == 'sheet':
            sheet_seen += 1
            if sheet_seen > 1:
                story.append(PageBreak())
            story.append(Paragraph(escape(block['lines'][0]), title_style))
            story.append(Spacer(1,2*mm))
            continue

        if block['type'] == 'section':
            story.append(Paragraph(escape(block['lines'][0]), section_style))
            continue

        if block['type'] == 'instruction':
            for line in block['lines']:
                if _is_titleish(line) or line.upper().startswith('ARAHAN'):
                    continue
                story.append(Paragraph(escape(line), instruction_style))
            continue

        lines = block['lines']
        kind = _worksheet_question_kind(lines)
        question = lines[0]
        visual_info = _find_visual_token(lines)
        question_clean = _strip_visual_tokens(question)
        options = [x for x in lines[1:] if _is_option_line(x)]
        other = [_strip_visual_tokens(x) for x in lines[1:]
                 if not _is_option_line(x) and not _is_answer_line(x)]
        other = [x for x in other if x]

        cell_flow = [Paragraph(escape(question_clean), question_style)]
        if visual_info:
            obj, count = visual_info
            # Real vector illustration drawn into the worksheet PDF.
            cell_flow.append(Spacer(1,1.5*mm))
            cell_flow.append(WorksheetVisual(obj=obj, count=count, width=155*mm, height=18*mm))
            cell_flow.append(Spacer(1,1.5*mm))

        # Objective choices in a neat 2 x 2 grid.
        if options:
            vals = options[:4] + [''] * max(0, 4-len(options))
            opt_data = [
                [Paragraph(escape(vals[0]), option_style), Paragraph(escape(vals[1]), option_style)],
                [Paragraph(escape(vals[2]), option_style), Paragraph(escape(vals[3]), option_style)]
            ]
            ot = Table(opt_data, colWidths=[81*mm,81*mm])
            ot.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),2),
                ('RIGHTPADDING',(0,0),(-1,-1),2),
                ('TOPPADDING',(0,0),(-1,-1),1),
                ('BOTTOMPADDING',(0,0),(-1,-1),1),
            ]))
            cell_flow.append(ot)

        for extra in other:
            cell_flow.append(Paragraph(escape(extra), body_style))

        if kind == 'structured':
            cell_flow.append(Spacer(1,2*mm))
            cell_flow.append(Paragraph('<i>Jalan kerja:</i>', body_style))
            cell_flow.append(Paragraph('_______________________________________________________________', body_style))
            cell_flow.append(Paragraph('_______________________________________________________________', body_style))
            cell_flow.append(Paragraph('Jawapan: _________________________________________________', body_style))
        elif kind == 'short':
            cell_flow.append(Spacer(1,1.5*mm))
            cell_flow.append(Paragraph('Jawapan: _________________________________________________', body_style))
        # No extra answer line for objective/fill-in items.

        card = Table([[cell_flow]], colWidths=[172*mm])
        card.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.65,colors.black),
            ('LEFTPADDING',(0,0),(-1,-1),6),
            ('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),5),
            ('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        story.append(KeepTogether([card, Spacer(1,2.5*mm)]))

    # Separate compact answer scheme.
    rows = _extract_scheme_rows(scheme_lines)
    if rows:
        story.append(PageBreak())
        story.append(Paragraph('SKEMA JAWAPAN', title_style))
        story.append(Paragraph(
            escape(clean_doc_text(f"{s.get('subject','')} | {s.get('year','')} | {s.get('topic','')}")),
            sub_style
        ))

        table_rows = []
        for no, ans in rows:
            if no == '__SECTION__':
                if table_rows:
                    at = Table(table_rows, colWidths=[20*mm,145*mm], repeatRows=1)
                    at.setStyle(TableStyle([
                        ('GRID',(0,0),(-1,-1),0.45,colors.grey),
                        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
                        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                        ('VALIGN',(0,0),(-1,-1),'TOP'),
                        ('LEFTPADDING',(0,0),(-1,-1),5),
                        ('RIGHTPADDING',(0,0),(-1,-1),5),
                        ('TOPPADDING',(0,0),(-1,-1),4),
                        ('BOTTOMPADDING',(0,0),(-1,-1),4),
                    ]))
                    story.extend([at, Spacer(1,3*mm)])
                    table_rows = []
                story.append(Paragraph(escape(ans), section_style))
                table_rows = [[Paragraph('<b>No.</b>', body_style), Paragraph('<b>Jawapan</b>', body_style)]]
            else:
                if not table_rows:
                    table_rows = [[Paragraph('<b>No.</b>', body_style), Paragraph('<b>Jawapan</b>', body_style)]]
                table_rows.append([Paragraph(escape(no), body_style), Paragraph(escape(ans), body_style)])

        if table_rows:
            at = Table(table_rows, colWidths=[20*mm,145*mm], repeatRows=1)
            at.setStyle(TableStyle([
                ('GRID',(0,0),(-1,-1),0.45,colors.grey),
                ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),5),
                ('RIGHTPADDING',(0,0),(-1,-1),5),
                ('TOPPADDING',(0,0),(-1,-1),4),
                ('BOTTOMPADDING',(0,0),(-1,-1),4),
            ]))
            story.append(at)

    pdf.build(story, onFirstPage=_pdf_header_footer, onLaterPages=_pdf_header_footer)
    return path


def _gemini_request(prompt, model):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    payload = {
        'contents': [{'role':'user','parts':[{'text':prompt}]}],
        'generationConfig': {
            'temperature': 0.55,
            'maxOutputTokens': 8192
        }
    }
    headers = {
        'Content-Type':'application/json',
        'x-goog-api-key': GEMINI_API_KEY
    }
    return requests.post(url, headers=headers, json=payload, timeout=30)


def _gemini_error_detail(response):
    try:
        return response.json().get('error',{}).get('message') or response.text
    except Exception:
        return response.text


def gemini_generate(prompt):
    """Generate with retry + fallback for transient Gemini API failures.

    - Preferred model: Gemini 3.8 Flash
    - Fallback: 3.7 Flash -> 3.6 Flash -> 3.5 Flash
    - Retry transient 408/429/5xx with short exponential backoff + jitter
    - Do not retry auth/config errors such as 400/401/403
    """
    if not GEMINI_API_KEY:
        raise RuntimeError('GEMINI_API_KEY belum ditetapkan di Render.')

    models = []
    for model in [GEMINI_MODEL] + GEMINI_FALLBACK_MODELS:
        if model and model not in models:
            models.append(model)

    transient_statuses = {408, 429, 500, 502, 503, 504}
    last_error = None
    retries_per_model = 2

    for model_index, model in enumerate(models):
        for attempt in range(retries_per_model):
            try:
                r = _gemini_request(prompt, model)
            except requests.RequestException as e:
                last_error = f'Ralat rangkaian Gemini ({model}): {e}'

                if attempt < retries_per_model - 1:
                    delay = 1.0 + random.uniform(0.15, 0.6)
                    print(
                        f'Gemini network retry {attempt + 1}/{retries_per_model} '
                        f'for {model} after {delay:.1f}s',
                        flush=True
                    )
                    time.sleep(delay)
                    continue

                break

            if r.ok:
                try:
                    data = r.json()
                except Exception:
                    last_error = f'Gemini {model} memulangkan respons yang tidak sah.'
                    break

                parts = (
                    (((data.get('candidates') or [{}])[0].get('content') or {})
                     .get('parts') or [])
                )
                out = ''.join(
                    p.get('text', '') for p in parts if isinstance(p, dict)
                )

                if out.strip():
                    print(f'Gemini success: {model}', flush=True)
                    return out.strip()

                last_error = f'Gemini {model} tidak memulangkan teks.'
                break

            detail = _gemini_error_detail(r)
            last_error = f'Gemini API {r.status_code} ({model}): {detail[:500]}'

            if r.status_code in transient_statuses:
                if attempt < retries_per_model - 1:
                    delay = (1.0 * (2 ** attempt)) + random.uniform(0.2, 0.8)
                    print(
                        f'Gemini transient {r.status_code} on {model}; '
                        f'retry {attempt + 1}/{retries_per_model} after {delay:.1f}s',
                        flush=True
                    )
                    time.sleep(delay)
                    continue

                print(
                    f'Gemini transient {r.status_code} persists on {model}; '
                    'switching fallback model.',
                    flush=True
                )
                break

            # 400/401/403 etc. are usually request/key/configuration issues.
            print(
                f'Gemini non-transient error {r.status_code} on {model}; '
                'stopping without repeated retries.',
                flush=True
            )
            raise RuntimeError(last_error)

        if model_index < len(models) - 1:
            print(
                f'Gemini fallback: {model} -> {models[model_index + 1]}',
                flush=True
            )

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
- Gunakan format seperti kertas soalan sekolah / buku latihan, bukan gaya artikel atau chat.
- Gunakan teks biasa sahaja: jangan gunakan Markdown seperti **, ##, ``` atau jadual Markdown.
- Gunakan tajuk bahagian yang jelas seperti BAHAGIAN A, BAHAGIAN B, ARAHAN dan SKEMA JAWAPAN apabila sesuai.
- Nomborkan soalan sebagai 1. 2. 3. dan pilihan objektif sebagai A. B. C. D.
- Jangan tulis mukadimah, ucapan, nota AI atau penerangan tambahan di luar bahan.
- Jangan masukkan penerangan tentang proses AI.
"""

    if task == 'questions':
        return common + f"""
Tugasan: Jana {amount} soalan jenis {qtype}.
Sediakan:
1. Mulakan terus dengan ARAHAN atau BAHAGIAN A; jangan ulang tajuk dokumen.
2. Tepat {amount} soalan, bernombor dengan kemas.
4. Jika objektif, berikan 4 pilihan A-D dan hanya satu jawapan terbaik.
5. Jika campuran, seimbangkan objektif dan struktur mengikut jumlah soalan.
6. Selepas semua soalan, tulis SKEMA JAWAPAN pada baris berasingan dan senaraikan jawapan mengikut nombor soalan.
"""
    if task == 'kbat':
        return common + f"""
Tugasan: Jana tepat {amount} soalan KBAT.
Jenis pilihan guru: {qtype}.
Soalan mesti menguji aplikasi, analisis, penilaian atau penciptaan, bukan hafalan semata-mata.
Sediakan cadangan jawapan / skema ringkas bagi setiap soalan.
"""
    if task == 'worksheet':
        worksheet_pages = _worksheet_pages(s)
        student_level = _worksheet_level(s)
        difficulty_label = _difficulty_label(s.get('difficulty', 'mixed'))
        difficulty_instruction = _difficulty_instruction(s)
        variation_seed = s.get('variation_seed') or secrets.token_hex(4)
        return common + f"""
Tugasan: Hasilkan satu worksheet yang boleh terus digunakan di kelas.
Mulakan dengan ARAHAN, kemudian bahagikan aktiviti kepada BAHAGIAN A, BAHAGIAN B dan seterusnya jika sesuai. Jangan ulang ruang Nama/Kelas/Tarikh kerana dokumen akan menyediakannya.

KHUSUS UNTUK WORKSHEET:
- Hasilkan {worksheet_pages} HELAIAN LATIHAN yang berbeza tetapi masih pada tajuk dan subtopik yang sama.
- ID variasi set ini: {variation_seed}. Gunakan ID ini hanya untuk mempelbagaikan pemilihan nombor, konteks, susunan dan bentuk aktiviti; jangan paparkan ID ini dalam hasil.
- Setiap penjanaan baharu mesti menggunakan variasi soalan, nombor, objek, situasi dan susunan yang berbeza.
- Elakkan mengulang set contoh lazim yang sama apabila terdapat banyak kemungkinan soalan.
- Labelkan setiap helaian sebagai HELAIAN 1, HELAIAN 2 dan seterusnya.
- Jangan ulang soalan yang sama antara helaian.
- Aras mesti sesuai dengan {student_level}.
- Pilihan aras cikgu: {difficulty_label}.
- {difficulty_instruction}
- Untuk Tahun 1-3, utamakan aktiviti visual, mengira objek, memadan, melengkapkan, memilih, mewarna/menanda secara munasabah, dan situasi harian yang sangat ringkas.
- Untuk Tahun 4-6, gunakan gabungan visual, aplikasi, jadual/rajah ringkas, objektif, struktur dan penyelesaian masalah.
- Untuk sekolah menengah, gunakan visual/rajah hanya apabila membantu kandungan; utamakan aplikasi konsep dan penaakulan.
- Untuk sekurang-kurangnya 30% soalan Tahun 1-3, gunakan visual yang benar-benar diperlukan untuk menjawab soalan.
- Untuk visual objek boleh kira, letakkan token teknikal tepat seperti [VISUAL: epal, 5]. Sistem akan menukarnya kepada GAMBAR sebenar; jangan tulis perkataan "visual", "gambar di sini", atau penerangan placeholder kepada murid.
- Gunakan hanya objek mudah yang sesuai dilukis/cetak: epal, bola, bintang, bunga, pensel, buku, syiling, bulatan, segi tiga atau segi empat.
- Jangan gunakan token [DIAGRAM] buat masa ini.
- Visual mesti menjadi sebahagian daripada tugasan, contohnya "Kira objek di bawah", "Bulatkan kumpulan yang betul", atau "Tulis ayat matematik berdasarkan gambar".
- Helaian murid mesti mengandungi SOALAN sahaja.
- Jangan tulis tajuk dokumen, Nama/Kelas/Tarikh/Markah atau ARAHAN umum kerana templat dokumen akan menyediakannya.
- Bahagikan latihan kepada BAHAGIAN A, BAHAGIAN B dan seterusnya jika sesuai.
- Selepas tajuk BAHAGIAN, beri arahan ringkas khusus bahagian sahaja, contohnya: Pilih jawapan yang betul.
- Soalan objektif mesti mempunyai pilihan A. B. C. D. dan JANGAN beri ruang "Jawapan:".
- Soalan isi tempat kosong mesti mempunyai ruang kosong terus dalam ayat, contohnya 7 + 5 = ______.
- Soalan subjektif / penyelesaian masalah boleh meminta jalan kerja dan jawapan.
- Jangan tulis "Jawapan:" selepas setiap soalan objektif atau isi tempat kosong.
- Selepas semua soalan, tulis SKEMA JAWAPAN pada bahagian berasingan.
- Skema hendaklah ringkas mengikut nombor soalan.
- Gaya keseluruhan seperti lembaran kerja / kertas latihan sekolah Malaysia, bukan artikel atau chat.
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
         f"📖 <b>{s['topic']}</b>\n\nPilih subtopik dengan menekan butang di bawah:\n<i>Tidak perlu taip sendiri. Senarai ini tetap.</i>",
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
    detail = (f"📄 {s.get('worksheet_pages',1)} helaian worksheet\n\n🤖 Sedia untuk dijana dengan AI."
              if s.get('task') == 'worksheet'
              else f"📝 {s.get('qtype','-')}\n🔢 {s.get('amount','-')} soalan\n\n🤖 Sedia untuk dijana dengan AI.")
    msg = (f"✅ <b>Pilihan Cikgu</b>\n\n🎓 {s.get('year','-')}\n📚 {s.get('subject','-')}\n"
           f"📖 {s.get('topic','-')}\n▫️ {s.get('subtopic','Semua Subtopik')}\n{detail}")
    send(cid, msg,
         [[{'text':'✨ Jana Dengan AI','callback_data':gen_cb}],
          [{'text':'🏠 Menu Utama','callback_data':'home'}]])

def generate_v3(cid, s, regen_cb):
    # Fresh seed on every generation, including Jana Semula.
    if s.get('task') == 'worksheet':
        s['variation_seed'] = secrets.token_hex(4)
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
            send(cid,'📚 Sila pilih tajuk daripada senarai yang disediakan.',
                 [[{'text':'🏠 Menu Utama','callback_data':'home'}]])
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
        elif s['task'] == 'worksheet':
            send(cid,'📄 <b>Berapa helaian worksheet cikgu mahu?</b>\n\nSetiap helaian akan mempunyai latihan yang berbeza.',
                 [[{'text':'1 Helaian','callback_data':f'wp3|1|{tc}|{yc}|{si}|{ti}|{sti}'},
                   {'text':'2 Helaian','callback_data':f'wp3|2|{tc}|{yc}|{si}|{ti}|{sti}'}],
                  [{'text':'3 Helaian','callback_data':f'wp3|3|{tc}|{yc}|{si}|{ti}|{sti}'},
                   {'text':'5 Helaian','callback_data':f'wp3|5|{tc}|{yc}|{si}|{ti}|{sti}'}],
                  [{'text':'🏠 Menu Utama','callback_data':'home'}]])
        else:
            gen_cb = f"gn3|{tc}|{yc}|{si}|{ti}|{sti}|-|-"
            preview_v3(cid, s, gen_cb)

    elif d.startswith('wp3|'):
        parts = d.split('|')
        if len(parts) == 7:
            _, pages_n, tc, yc, si, ti, sti = parts
            s = rebuild_state(tc, yc, si, ti, sti)
            if s:
                send(cid,
                     '🎯 <b>Pilih aras soalan</b>\n\n'
                     'Aras akan disesuaikan dengan Tahun/Tingkatan murid.',
                     [[
                         {'text':'🟢 Mudah','callback_data':f'lv3|easy|{pages_n}|{tc}|{yc}|{si}|{ti}|{sti}'},
                         {'text':'🟡 Sederhana','callback_data':f'lv3|medium|{pages_n}|{tc}|{yc}|{si}|{ti}|{sti}'}
                      ],
                      [
                         {'text':'🔴 Sukar','callback_data':f'lv3|hard|{pages_n}|{tc}|{yc}|{si}|{ti}|{sti}'},
                         {'text':'🌈 Campuran','callback_data':f'lv3|mixed|{pages_n}|{tc}|{yc}|{si}|{ti}|{sti}'}
                      ],
                      [{'text':'🏠 Menu Utama','callback_data':'home'}]])

    elif d.startswith('lv3|'):
        parts = d.split('|')
        if len(parts) == 8:
            _, diff, pages_n, tc, yc, si, ti, sti = parts
            s = rebuild_state(tc, yc, si, ti, sti)
            if s:
                s['worksheet_pages'] = int(pages_n)
                s['difficulty'] = diff
                s['variation_seed'] = secrets.token_hex(4)
                gen_cb = f'gw3|{diff}|{pages_n}|{tc}|{yc}|{si}|{ti}|{sti}'
                send(cid,
                     f"✅ <b>Pilihan Cikgu</b>\n\n"
                     f"🎓 {s.get('year','-')}\n📚 {s.get('subject','-')}\n"
                     f"📖 {s.get('topic','-')}\n▫️ {s.get('subtopic','Semua Subtopik')}\n"
                     f"📄 {pages_n} helaian worksheet\n"
                     f"🎯 Aras: {_difficulty_label(diff)}\n\n"
                     f"🤖 Soalan akan disesuaikan dengan tahap murid dan tidak melangkaui aras yang dipilih.",
                     [[{'text':'✨ Jana Worksheet','callback_data':gen_cb}],
                      [{'text':'🏠 Menu Utama','callback_data':'home'}]])

    elif d.startswith('gw3|'):
        parts = d.split('|')
        if len(parts) == 8:
            _, diff, pages_n, tc, yc, si, ti, sti = parts
            s = rebuild_state(tc, yc, si, ti, sti)
            if s:
                s['worksheet_pages'] = int(pages_n)
                s['difficulty'] = diff
                s['variation_seed'] = secrets.token_hex(4)
                generate_v3(cid, s, d)

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
