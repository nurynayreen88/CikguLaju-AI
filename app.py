import os
import html
import requests
import time
import random
import tempfile
import re
import secrets
import threading
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
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
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')
GEMINI_TIMEOUT = int(os.getenv('GEMINI_TIMEOUT', '90'))
GEMINI_RETRIES = int(os.getenv('GEMINI_RETRIES', '1'))
HYBRID_LOW_COST = os.getenv('HYBRID_LOW_COST', '1').strip().lower() not in ('0','false','no','off')
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.getenv(
    'GEMINI_FALLBACK_MODELS',
    'gemini-2.5-flash'
).split(',') if m.strip()]
API = f'https://api.telegram.org/bot{BOT_TOKEN}'
state = {}
_processing_chats = set()
_seen_updates = set()
_runtime_lock = threading.Lock()

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
        if u.startswith('HELAIAN ') or u.startswith('WORKSHEET '):
            current_section = line
            rows.append(('__SHEET__', current_section))
            continue
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


def _worksheet_question_count(s):
    try:
        return max(4, min(12, int(s.get('worksheet_questions', 8))))
    except Exception:
        return 8


def _worksheet_blueprint_instruction(s):
    """Concrete worksheet composition rules so difficulty and page density stay consistent."""
    year = str(s.get('year','')).lower()
    subject = str(s.get('subject','')).lower()
    topic = str(s.get('topic','')).lower()
    diff = str(s.get('difficulty','mixed')).lower()
    qcount = _worksheet_question_count(s)

    if 'tahun 2' in year and 'matematik' in subject:
        if 'tambah' in topic:
            if diff == 'easy':
                return (
                    f'PELAN WORKSHEET MATEMATIK TAHUN 2 (MUDAH): hasilkan tepat {qcount} soalan pada SATU halaman A4. '
                    'Maksimum 2 item fakta asas satu digit. Selebihnya gunakan nombor 2 digit yang sesuai, '
                    'ayat matematik, nilai hilang, representasi visual puluh dan sa, dan 1-2 masalah harian satu langkah. '
                    'Jangan gunakan item seperti 2+3, 4+1, 5+2 berulang kali.'
                )
            if diff == 'hard':
                return (
                    f'PELAN WORKSHEET MATEMATIK TAHUN 2 (SUKAR): hasilkan tepat {qcount} soalan pada SATU halaman A4. '
                    'Gunakan nombor 2 digit, tambah dengan/ tanpa mengumpul semula mengikut subtopik, nombor hilang, '
                    'banding strategi, kesan kesilapan, bina ayat matematik daripada situasi dan sekurang-kurangnya 2 masalah berayat. '
                    'Masih kekal dalam silibus Tahun 2; jangan bawa konsep Tahun 3.'
                )
            return (
                f'PELAN WORKSHEET MATEMATIK TAHUN 2: hasilkan tepat {qcount} soalan pada SATU halaman A4 dengan progres jelas. '
                'Cadangan komposisi: 1-2 item pemanasan, 3-4 item nombor dua digit/algoritma sesuai subtopik, '
                '2 item nilai hilang atau pelbagai representasi, 1-2 item visual bermakna, dan 1-2 masalah berayat/aplikasi. '
                'Sekurang-kurangnya 60% item mesti jelas melebihi aras Tahun 1.'
            )

    if any(x in year for x in ['tahun 1','tahun 2','tahun 3']):
        return (
            f'PELAN WORKSHEET TAHAP I: hasilkan tepat {qcount} soalan pada SATU halaman A4, 2-4 bentuk aktiviti, '
            'sekurang-kurangnya 2 item visual yang benar-benar digunakan untuk menjawab, dan 1-2 item aplikasi. '
            'Pastikan kepadatan sesuai satu halaman A4 dan elakkan latihan berulang mekanikal.'
        )
    if any(x in year for x in ['tahun 4','tahun 5','tahun 6']):
        return (
            f'PELAN WORKSHEET TAHAP II: hasilkan tepat {qcount} soalan pada SATU halaman A4, gabungkan prosedur, aplikasi, '
            'tafsiran maklumat/rajah dan sekurang-kurangnya satu item penaakulan.'
        )
    return (
        f'PELAN WORKSHEET MENENGAH: hasilkan tepat {qcount} soalan pada SATU halaman A4 dengan campuran prosedur, aplikasi, '
        'analisis dan penaakulan; jangan penuhkan helaian dengan item rutin yang sama.'
    )

def _difficulty_label(code):
    return {
        'easy': 'Mudah',
        'medium': 'Sederhana',
        'hard': 'Sukar',
        'mixed': 'Campuran',
        'kbat': 'KBAT'
    }.get(str(code), 'Campuran')



def _curriculum_depth_instruction(s):
    """Guardrails so the selected year/form does not collapse to a lower grade."""
    year = str(s.get('year','')).lower()
    subject = str(s.get('subject','')).lower()
    topic = str(s.get('topic','')).lower()
    subtopic = str(s.get('subtopic','')).lower()

    # Important specific fix from live QA: Year 2 Mathematics was too Year-1-like.
    if 'tahun 2' in year and 'matematik' in subject:
        if 'tambah' in topic or 'tambah' in subtopic:
            return (
                'KHUSUS MATEMATIK TAHUN 2 - TAMBAH: jangan dominasi latihan dengan fakta satu digit seperti 3+4 atau 6+2. '
                'Gunakan perkembangan yang sesuai Tahun 2: fakta asas sebagai pemanasan sahaja, kemudian nombor dua digit '
                'yang sesuai dengan tajuk/subtopik, nilai hilang, bina ayat matematik daripada situasi, soalan berayat, '
                'pemilihan strategi dan aplikasi harian. Jika subtopik benar-benar "Fakta asas tambah", kekalkan fakta asas '
                'tetapi tingkatkan kognitif melalui keluarga fakta, nombor hilang, pelbagai representasi, benar/salah, '
                'padanan representasi dan masalah ringkas; jangan menjadikannya seperti latihan Tahun 1 semata-mata. '
                'Untuk aras Sederhana/Sukar, sekurang-kurangnya separuh item mesti memerlukan lebih daripada sekadar mengira objek.'
            )

    if 'tahun 3' in year and 'matematik' in subject and ('darab' in topic or 'darab' in subtopic):
        if 'konsep' in subtopic:
            return (
                'KHUSUS MATEMATIK TAHUN 3 - KONSEP DARAB: ajar darab sebagai KUMPULAN SAMA BANYAK dan tambah berulang. '
                'Jika soalan menyatakan A kumpulan, B objek setiap kumpulan, representasi utama ialah A × B dan visual MESTI '
                'menunjukkan tepat A kumpulan yang berasingan, setiap kumpulan mengandungi tepat B objek. Jangan lukis A×B objek '
                'sebagai satu longgokan tanpa sempadan kumpulan. Gunakan token [VISUAL_GROUPS: objek, A, B]. '
                'Contoh: 3 kumpulan 4 bola -> [VISUAL_GROUPS: bola, 3, 4], tambah berulang 4 + 4 + 4, ayat darab 3 × 4 = 12. '
                'Jangan jadikan 4 × 3 sebagai representasi konsep yang sama dalam soalan yang sedang menguji bilangan kumpulan, '
                'walaupun hasil darabnya sama; bezakan bilangan kumpulan daripada bilangan objek setiap kumpulan. '
                'Semak sendiri setiap visual: bilangan kotak/kumpulan, objek dalam setiap kotak, tambah berulang dan ayat darab mesti konsisten.'
            )

    if any(x in year for x in ['tahun 1','tahun 2','tahun 3']):
        return (
            'Pastikan kandungan tepat pada TAHUN yang dipilih. Tahap I bukan satu aras yang sama. '
            'Tahun 2 mesti jelas lebih berkembang daripada Tahun 1, dan Tahun 3 lebih berkembang daripada Tahun 2. '
            'Visual digunakan sebagai representasi matematik/pembelajaran, bukan menggantikan semua pemikiran simbolik.'
        )

    return (
        'Pastikan aras kandungan tepat pada Tahun/Tingkatan yang dipilih dan jangan turunkan soalan ke tahap kelas lebih rendah. '
        'Gunakan variasi representasi, aplikasi dan penaakulan yang selari dengan tahap murid.'
    )

def _difficulty_instruction(s):
    level = _worksheet_level(s)
    diff = str(s.get('difficulty', 'mixed'))

    if level == 'lower_primary':
        mapping = {
            'easy': (
                'Aras MUDAH mengikut tahun sebenar dalam Tahap I: mudahkan proses berfikir, bukan turunkan kandungan ke Tahun 1. '
                'Gunakan representasi visual yang sesuai, padanan, melengkapkan, satu langkah dan konteks ringkas, '
                'tetapi julat nombor serta kemahiran mesti tetap sesuai dengan Tahun yang dipilih.'
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

    if diff == 'kbat':
        return (
            'Aras KBAT: bina item yang memerlukan murid mengaplikasikan pengetahuan, menganalisis maklumat, '
            'membuat pertimbangan/keputusan atau mencipta strategi/penyelesaian. Elakkan hafalan dan soalan rutin semata-mata. '
            'Kekalkan kandungan dalam silibus serta tahap Tahun/Tingkatan yang dipilih.'
        )
    return mapping.get(diff, mapping['mixed'])




class WorksheetVisual(Flowable):
    """Printable black/white vector illustrations drawn directly into the PDF.

    Supports ordinary countable visuals and explicit equal-group visuals for
    multiplication concepts. Equal groups are separated visually so the
    picture represents 'number of groups × objects in each group' correctly.
    """
    def __init__(self, obj='objek', count=5, width=150*mm, height=28*mm, groups=1, per_group=None):
        Flowable.__init__(self)
        self.obj = (obj or 'objek').lower()
        self.groups = max(1, min(10, int(groups or 1)))
        self.per_group = max(1, min(10, int(per_group or count or 1)))
        self.count = max(1, min(40, self.groups * self.per_group if self.groups > 1 else int(count or 1)))
        self.width = width
        rows = self.groups if self.groups > 1 else (1 if self.count <= 10 else 2)
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

        if any(k in o for k in ['blok puluh','base ten','puluh']):
            # tens rod
            c.rect(x-size*.12, y-size*.42, size*.24, size*.84, stroke=1, fill=0)
            for j in range(1,10):
                yy = y-size*.42 + j*(size*.84/10)
                c.line(x-size*.12, yy, x+size*.12, yy)
        elif any(k in o for k in ['kad nombor','number card']):
            c.roundRect(x-size*.42, y-size*.30, size*.84, size*.60, size*.08, stroke=1, fill=0)
            c.setFont('Helvetica-Bold', max(7, size*.25))
            c.drawCentredString(x, y-size*.08, '?')
        elif any(k in o for k in ['epal','apple']):
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
        if self.groups > 1:
            # One clearly bounded row per equal group. This prevents a multiplication
            # visual from becoming one undifferentiated pile of objects.
            row_h = self.height / self.groups
            left_pad = 8*mm
            usable_w = self.width - left_pad - 3*mm
            cell_w = usable_w / max(self.per_group, 1)
            size = min(cell_w, row_h) * 0.60
            for g in range(self.groups):
                y0 = self.height - (g+1)*row_h + 1.5*mm
                c.roundRect(1.5*mm, y0, self.width-3*mm, row_h-3*mm, 2*mm, stroke=1, fill=0)
                c.setFont('Helvetica-Bold', 8)
                c.drawString(3*mm, y0 + row_h/2 - 3, str(g+1))
                for j in range(self.per_group):
                    x = left_pad + j*cell_w + cell_w/2
                    y = y0 + (row_h-3*mm)/2
                    self._draw_one(c, x, y, size)
            return

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


def _find_fraction_visual_token(lines):
    """Mathematically structured fraction visuals only.

    [FRACTION_BAR: 3, 5] -> bar split into 5 equal parts, 3 hatched.
    [FRACTION_SET: 12, 8] -> 12 equal objects, 8 hatched/selected.
    """
    text = ' '.join(lines)
    m = re.search(r'\[FRACTION_BAR:\s*(\d+)\s*,\s*(\d+)\s*\]', text, re.I)
    if m:
        num, den = int(m.group(1)), int(m.group(2))
        den = max(2, min(20, den)); num = max(0, min(den, num))
        return ('bar', num, den)
    m = re.search(r'\[FRACTION_SET:\s*(\d+)\s*,\s*(\d+)\s*\]', text, re.I)
    if m:
        total, selected = int(m.group(1)), int(m.group(2))
        total = max(2, min(30, total)); selected = max(0, min(total, selected))
        return ('set', selected, total)
    return None


class FractionVisual(Flowable):
    def __init__(self, mode='bar', selected=1, total=2, width=150*mm, height=18*mm):
        Flowable.__init__(self)
        self.mode=mode; self.selected=selected; self.total=total; self.width=width; self.height=height
    def draw(self):
        c=self.canv; c.setLineWidth(0.8)
        if self.mode=='bar':
            x0=5*mm; y0=4*mm; w=self.width-10*mm; h=9*mm; cw=w/self.total
            for i in range(self.total):
                c.rect(x0+i*cw,y0,cw,h,stroke=1,fill=0)
                if i < self.selected:
                    # hatch rather than colour, so meaning survives B&W printing
                    step=3*mm; xx=x0+i*cw-h
                    while xx < x0+(i+1)*cw:
                        c.line(max(x0+i*cw,xx), y0, min(x0+(i+1)*cw,xx+h), y0+h)
                        xx += step
            return
        cols=min(10,self.total); rows=(self.total+cols-1)//cols
        cw=self.width/cols; ch=self.height/max(rows,1); r=min(cw,ch)*0.28
        for i in range(self.total):
            row=i//cols; col=i%cols; x=col*cw+cw/2; y=self.height-(row*ch+ch/2)
            c.circle(x,y,r,stroke=1,fill=0)
            if i < self.selected:
                # cross-hatch selection, no colour dependency
                c.line(x-r*.7,y-r*.7,x+r*.7,y+r*.7)
                c.line(x-r*.7,y+r*.7,x+r*.7,y-r*.7)


def _word_fraction_image(mode, selected, total):
    W,H=1100,180
    img=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(img)
    if mode=='bar':
        x0,y0,x1,y1=60,45,W-60,130; cw=(x1-x0)/total
        for i in range(total):
            a=x0+i*cw; b=x0+(i+1)*cw
            d.rectangle((a,y0,b,y1), outline='black', width=3)
            if i < selected:
                t=a-(y1-y0)
                while t < b:
                    d.line((max(a,t),y0,min(b,t+(y1-y0)),y1), fill='black', width=2)
                    t += 24
    else:
        cols=min(10,total); rows=(total+cols-1)//cols; cellw=(W-80)/cols; cellh=(H-30)/max(rows,1); r=min(cellw,cellh)*.24
        for i in range(total):
            row=i//cols; col=i%cols; cx=40+col*cellw+cellw/2; cy=15+row*cellh+cellh/2
            d.ellipse((cx-r,cy-r,cx+r,cy+r), outline='black', width=3)
            if i < selected:
                d.line((cx-r*.7,cy-r*.7,cx+r*.7,cy+r*.7), fill='black', width=2)
                d.line((cx-r*.7,cy+r*.7,cx+r*.7,cy-r*.7), fill='black', width=2)
    bio=BytesIO(); img.save(bio,format='PNG'); bio.seek(0); return bio


def _find_visual_token(lines):
    """Find an ordinary visual or an explicit equal-groups visual.

    Returns (object, total_count, groups, per_group).
    [VISUAL: epal, 5] -> 5 ordinary objects.
    [VISUAL_GROUPS: bola, 3, 4] -> 3 clearly separated groups of 4 balls.
    """
    joined = ' '.join(lines)
    mg = re.search(r'\[VISUAL_GROUPS:\s*([^,\]]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', joined, flags=re.I)
    if not mg:
        mg = re.search(r'\bVISUAL_GROUPS:\s*([^,\n]+?)\s*,\s*(\d+)\s*,\s*(\d+)\b', joined, flags=re.I)
    if mg:
        obj = mg.group(1).strip()
        groups = max(1, min(10, int(mg.group(2))))
        per_group = max(1, min(10, int(mg.group(3))))
        return obj, min(40, groups * per_group), groups, per_group

    m = re.search(r'\[VISUAL:\s*([^,\]]+)\s*,\s*(\d+)\s*\]', joined, flags=re.I)
    if not m:
        m = re.search(r'\bVISUAL:\s*([^,\n]+?)\s*,\s*(\d+)\b', joined, flags=re.I)
    if m:
        count = max(1, min(20, int(m.group(2))))
        return m.group(1).strip(), count, 1, count
    return None


def _strip_visual_tokens(value):
    value = re.sub(r'\[(?:VISUAL_GROUPS|VISUAL|DIAGRAM|FRACTION_BAR|FRACTION_SET):[^\]]+\]', '', value, flags=re.I)
    value = re.sub(r'\b(?:VISUAL_GROUPS|VISUAL|DIAGRAM|FRACTION_BAR|FRACTION_SET):[^\n]+', '', value, flags=re.I)
    return value.strip()


def _find_layout_token(lines):
    """Return a reusable answer-layout specification embedded in a question.

    Supported tokens:
      [FORM_LAZIM: rows, cols]  blank arithmetic grid, e.g. 3 x 3
      [WORKLINES: n]            ruled response lines (language/essay only)
      [ANSWERSPACE: n]           blank unruled working space, n is relative height units
      [ANSWERBOX: n]            blank bordered answer box, n is relative height units
    """
    text = ' '.join(lines)
    m = re.search(r'\[FORM_LAZIM\s*:\s*(\d+)\s*[,xX]\s*(\d+)\s*\]', text, re.I)
    if m:
        return ('form_lazim', max(2, min(8, int(m.group(1)))), max(2, min(10, int(m.group(2)))))
    m = re.search(r'\[WORKLINES\s*:\s*(\d+)\s*\]', text, re.I)
    if m:
        return ('worklines', max(1, min(8, int(m.group(1)))), None)
    m = re.search(r'\[ANSWERSPACE\s*:\s*(\d+)\s*\]', text, re.I)
    if m:
        return ('answerspace', max(1, min(8, int(m.group(1)))), None)
    m = re.search(r'\[ANSWERBOX\s*:\s*(\d+)\s*\]', text, re.I)
    if m:
        return ('answerbox', max(1, min(6, int(m.group(1)))), None)
    return None


def _strip_layout_tokens(value):
    return re.sub(r'\[(?:FORM_LAZIM|WORKLINES|ANSWERSPACE|ANSWERBOX)\s*:[^\]]+\]', '', value, flags=re.I).strip()


def _clean_worksheet_text(value):
    return _strip_layout_tokens(_strip_visual_tokens(value))

def _word_visual_image(obj, count, groups=1, per_group=None):
    """Create a clean black-and-white PNG pictogram grid for Word worksheets."""
    obj = (obj or 'objek').lower()
    groups = max(1, min(10, int(groups or 1)))
    per_group = max(1, min(10, int(per_group or count or 1)))
    count = max(1, min(40, groups * per_group if groups > 1 else int(count or 1)))
    cols = per_group if groups > 1 else min(8, count)
    rows = groups if groups > 1 else (count + cols - 1) // cols
    cell = 72
    pad = 12
    group_gap = 16 if groups > 1 else 0
    img = Image.new('RGB', (cols*cell + pad*2, rows*cell + pad*2 + max(0, rows-1)*group_gap), 'white')
    d = ImageDraw.Draw(img)

    def star(cx, cy, r):
        import math
        pts=[]
        for i in range(10):
            a=-math.pi/2+i*math.pi/5
            rr=r if i%2==0 else r*.42
            pts.append((cx+rr*math.cos(a), cy+rr*math.sin(a)))
        d.polygon(pts, outline='black')

    if groups > 1:
        for g in range(groups):
            gy = pad + g*(cell + group_gap)
            d.rounded_rectangle((4, gy-5, cols*cell + pad*2-4, gy+cell+5), radius=10, outline='black', width=2)

    for i in range(count):
        row, col = divmod(i, cols)
        x0 = pad + col*cell
        y0 = pad + row*(cell + group_gap)
        cx, cy = x0+cell//2, y0+cell//2
        r = 22
        if any(k in obj for k in ['epal','apple']):
            d.ellipse((cx-r,cy-r+4,cx+r,cy+r+4), outline='black', width=2)
            d.line((cx,cy-r+5,cx+3,cy-r-9), fill='black', width=2)
            d.ellipse((cx+2,cy-r-10,cx+16,cy-r+1), outline='black', width=2)
        elif any(k in obj for k in ['bola','ball']):
            d.ellipse((cx-r,cy-r,cx+r,cy+r), outline='black', width=2)
            d.arc((cx-r+5,cy-r,cx+r-5,cy+r), 65, 115, fill='black', width=2)
            d.arc((cx-r,cy-10,cx+r,cy+10), 0, 180, fill='black', width=2)
        elif any(k in obj for k in ['bintang','star']):
            star(cx,cy,r+2)
        elif any(k in obj for k in ['bunga','flower']):
            for dx,dy in [(0,-12),(12,0),(0,12),(-12,0)]:
                d.ellipse((cx+dx-9,cy+dy-9,cx+dx+9,cy+dy+9), outline='black', width=2)
            d.ellipse((cx-6,cy-6,cx+6,cy+6), outline='black', width=2)
        elif any(k in obj for k in ['pensel','pencil']):
            d.rectangle((cx-24,cy-7,cx+15,cy+7), outline='black', width=2)
            d.polygon([(cx+15,cy-7),(cx+29,cy),(cx+15,cy+7)], outline='black')
        elif any(k in obj for k in ['buku','book']):
            d.rectangle((cx-25,cy-18,cx+25,cy+18), outline='black', width=2)
            d.line((cx,cy-18,cx,cy+18), fill='black', width=2)
        elif any(k in obj for k in ['syiling','coin','wang','duit']):
            d.ellipse((cx-r,cy-r,cx+r,cy+r), outline='black', width=2)
            d.text((cx-11,cy-7),'RM', fill='black')
        elif any(k in obj for k in ['segi tiga','triangle']):
            d.polygon([(cx,cy-r),(cx-r,cy+r),(cx+r,cy+r)], outline='black')
        elif any(k in obj for k in ['segi empat','square']):
            d.rectangle((cx-r,cy-r,cx+r,cy+r), outline='black', width=2)
        elif any(k in obj for k in ['blok puluh','base ten','puluh']):
            d.rectangle((cx-9,cy-27,cx+9,cy+27), outline='black', width=2)
            for j in range(1,10):
                yy=cy-27+j*5.4
                d.line((cx-9,yy,cx+9,yy), fill='black', width=1)
        else:
            d.ellipse((cx-r,cy-r,cx+r,cy+r), outline='black', width=2)

    stream=BytesIO()
    img.save(stream, format='PNG', dpi=(150,150))
    stream.seek(0)
    return stream


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
            fraction_visual = _find_fraction_visual_token(lines)
            visual_info = _find_visual_token(lines)
            layout_info = _find_layout_token(lines)
            clean_q = _clean_worksheet_text(raw_q)
            p.clear()
            rr = p.add_run(clean_q)
            rr.bold = True
            if fraction_visual:
                mode, selected, total = fraction_visual
                vp = cell.add_paragraph(); vp.alignment = WD_ALIGN_PARAGRAPH.CENTER; vp.paragraph_format.space_after = Pt(3)
                vp.add_run().add_picture(_word_fraction_image(mode, selected, total), width=Cm(14.5))
            elif visual_info:
                obj, count, groups, per_group = visual_info
                # Insert a real generated black-and-white pictogram image instead of Unicode symbols.
                vp = cell.add_paragraph()
                vp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                vp.paragraph_format.space_after = Pt(3)
                vr = vp.add_run()
                img_stream = _word_visual_image(obj, count, groups=groups, per_group=per_group)
                width_cm = min(15.0, max(5.0, min(8, per_group if groups > 1 else count) * 1.45))
                vr.add_picture(img_stream, width=Cm(width_cm))

            # Options/supporting lines
            options = [x for x in lines[1:] if _is_option_line(x)]
            other = [_clean_worksheet_text(x) for x in lines[1:]
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

            # Reusable exam/workbook answer formats. The AI selects the template;
            # Python renders it consistently so only question content changes.
            if layout_info and layout_info[0] == 'form_lazim':
                rows, cols = layout_info[1], layout_info[2]
                gp = cell.add_paragraph(); gp.paragraph_format.space_before = Pt(2); gp.paragraph_format.space_after = Pt(1)
                grid = cell.add_table(rows=rows, cols=cols)
                grid.alignment = WD_TABLE_ALIGNMENT.CENTER
                for grow in grid.rows:
                    grow.height = Cm(0.72)
                    for gc in grow.cells:
                        gc.width = Cm(0.85)
                        gc.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                        _word_set_cell_border(
                            gc,
                            top={'val':'single','sz':'8','color':'555555'},
                            bottom={'val':'single','sz':'8','color':'555555'},
                            left={'val':'single','sz':'8','color':'555555'},
                            right={'val':'single','sz':'8','color':'555555'}
                        )
            elif layout_info and layout_info[0] == 'worklines':
                if 'matematik' in str(s.get('subject','')).lower():
                    for _ in range(layout_info[1]):
                        pp = cell.add_paragraph(''); pp.paragraph_format.space_after = Pt(7)
                else:
                    for _ in range(layout_info[1]):
                        pp = cell.add_paragraph('____________________________________________________________'); pp.paragraph_format.space_after = Pt(1)
            elif layout_info and layout_info[0] == 'answerspace':
                for _ in range(layout_info[1]):
                    pp = cell.add_paragraph(''); pp.paragraph_format.space_after = Pt(7)
            elif layout_info and layout_info[0] == 'answerbox':
                bx = cell.add_table(rows=1, cols=1)
                bx.rows[0].height = Cm(0.65 * layout_info[1])
                bc = bx.cell(0,0)
                _word_set_cell_border(
                    bc,
                    top={'val':'single','sz':'8','color':'555555'},
                    bottom={'val':'single','sz':'8','color':'555555'},
                    left={'val':'single','sz':'8','color':'555555'},
                    right={'val':'single','sz':'8','color':'555555'}
                )

            # Answer/work area only when pedagogically useful and no explicit template was requested.
            if not layout_info and kind == 'structured':
                if 'matematik' in str(s.get('subject','')).lower():
                    for _ in range(3):
                        pp = cell.add_paragraph(''); pp.paragraph_format.space_after = Pt(7)
                else:
                    for _ in range(2):
                        pp = cell.add_paragraph('____________________________________________________________'); pp.paragraph_format.space_after = Pt(1)
            elif not layout_info and kind == 'short':
                if 'matematik' in str(s.get('subject','')).lower():
                    pp = cell.add_paragraph(''); pp.paragraph_format.space_after = Pt(8)
                else:
                    pp = cell.add_paragraph('Jawapan: _________________________________________________'); pp.paragraph_format.space_before = Pt(4); pp.paragraph_format.space_after = Pt(1)
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
                if no in ('__SECTION__','__SHEET__'):
                    p = doc.add_paragraph()
                    if no == '__SHEET__':
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    r = p.add_run(ans)
                    r.bold = True
                    r.font.size = Pt(12 if no == '__SHEET__' else 10.5)
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
        fraction_visual = _find_fraction_visual_token(lines)
        visual_info = _find_visual_token(lines)
        layout_info = _find_layout_token(lines)
        question_clean = _clean_worksheet_text(question)
        options = [x for x in lines[1:] if _is_option_line(x)]
        other = [_clean_worksheet_text(x) for x in lines[1:]
                 if not _is_option_line(x) and not _is_answer_line(x)]
        other = [x for x in other if x]

        cell_flow = [Paragraph(escape(question_clean), question_style)]
        if fraction_visual:
            mode, selected, total = fraction_visual
            cell_flow.append(Spacer(1,1.5*mm))
            cell_flow.append(FractionVisual(mode=mode, selected=selected, total=total, width=155*mm, height=18*mm))
            cell_flow.append(Spacer(1,1.5*mm))
        elif visual_info:
            obj, count, groups, per_group = visual_info
            # Real vector illustration drawn into the worksheet PDF.
            cell_flow.append(Spacer(1,1.5*mm))
            cell_flow.append(WorksheetVisual(obj=obj, count=count, width=155*mm, height=18*mm, groups=groups, per_group=per_group))
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

        if layout_info and layout_info[0] == 'form_lazim':
            rows, cols = layout_info[1], layout_info[2]
            cell_flow.append(Spacer(1,1*mm))
            grid_data = [['' for _ in range(cols)] for _ in range(rows)]
            cell_w = min(12*mm, 72*mm/cols)
            grid = Table(grid_data, colWidths=[cell_w]*cols, rowHeights=[9*mm]*rows)
            grid.setStyle(TableStyle([
                ('GRID',(0,0),(-1,-1),0.65,colors.black),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ]))
            cell_flow.append(grid)
        elif layout_info and layout_info[0] == 'worklines':
            cell_flow.append(Spacer(1,1.5*mm))
            if 'matematik' in str(s.get('subject','')).lower():
                cell_flow.append(Spacer(1, 5*mm*layout_info[1]))
            else:
                for _ in range(layout_info[1]):
                    cell_flow.append(Paragraph('_______________________________________________________________', body_style))
        elif layout_info and layout_info[0] == 'answerspace':
            cell_flow.append(Spacer(1, 5*mm*layout_info[1]))
        elif layout_info and layout_info[0] == 'answerbox':
            h = 8*mm*layout_info[1]
            bx = Table([['']], colWidths=[160*mm], rowHeights=[h])
            bx.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.65,colors.black)]))
            cell_flow.append(Spacer(1,1.5*mm))
            cell_flow.append(bx)
        elif kind == 'structured':
            cell_flow.append(Spacer(1, 12*mm if 'matematik' in str(s.get('subject','')).lower() else 2*mm))
            if 'matematik' not in str(s.get('subject','')).lower():
                cell_flow.append(Paragraph('_______________________________________________________________', body_style))
                cell_flow.append(Paragraph('_______________________________________________________________', body_style))
        elif not layout_info and kind == 'short':
            if 'matematik' in str(s.get('subject','')).lower():
                cell_flow.append(Spacer(1,5*mm))
            else:
                cell_flow.append(Spacer(1,1.5*mm)); cell_flow.append(Paragraph('Jawapan: _________________________________________________', body_style))
        # No extra answer line for objective/fill-in items.

        card = Table([[cell_flow]], colWidths=[172*mm])
        card.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.65,colors.black),
            ('LEFTPADDING',(0,0),(-1,-1),6),
            ('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),4),
            ('BOTTOMPADDING',(0,0),(-1,-1),4),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        story.append(KeepTogether([card, Spacer(1,1.8*mm)]))

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
            if no in ('__SECTION__','__SHEET__'):
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
                if no == '__SHEET__':
                    story.append(Spacer(1,2*mm))
                    story.append(Paragraph(escape(ans), title_style))
                    table_rows = []
                else:
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


def _gemini_request(prompt, model, max_output_tokens=4096):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    payload = {
        'contents': [{'role':'user','parts':[{'text':prompt}]}],
        'generationConfig': {
            'temperature': 0.55,
            'maxOutputTokens': max(1200, min(5000, int(max_output_tokens or 4096)))
        }
    }
    headers = {
        'Content-Type':'application/json',
        'x-goog-api-key': GEMINI_API_KEY
    }
    # Worksheet generation can take longer during peak load; use a configurable timeout.
    return requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=(15, GEMINI_TIMEOUT)
    )


def _gemini_error_detail(response):
    try:
        return response.json().get('error',{}).get('message') or response.text
    except Exception:
        return response.text


def gemini_generate(prompt, max_output_tokens=4096):
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
    retries_per_model = max(1, GEMINI_RETRIES)

    for model_index, model in enumerate(models):
        for attempt in range(retries_per_model):
            try:
                r = _gemini_request(prompt, model, max_output_tokens=max_output_tokens)
            except requests.RequestException as e:
                last_error = f'Ralat rangkaian Gemini ({model}): {e}'

                if attempt < retries_per_model - 1:
                    delay = min(8.0, (1.5 * (2 ** attempt)) + random.uniform(0.25, 0.9))
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
                    retry_after = r.headers.get('Retry-After')
                    try:
                        retry_after = float(retry_after) if retry_after else 0.0
                    except (TypeError, ValueError):
                        retry_after = 0.0
                    delay = max(
                        retry_after,
                        min(10.0, (1.5 * (2 ** attempt)) + random.uniform(0.3, 1.0))
                    )
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

            # A model can be unavailable for a specific API key/project even when it exists.
            # In that case, switch model instead of killing the whole generation.
            if r.status_code in (404,):
                print(
                    f'Gemini model {model} unavailable for this project (HTTP {r.status_code}); '
                    'switching fallback model.',
                    flush=True
                )
                break

            # Auth/key errors are global and will not be fixed by changing model.
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



def _can_generate_zero_cost(s):
    """Topics we can generate correctly without spending any Gemini quota."""
    if not HYBRID_LOW_COST or s.get('task') != 'worksheet':
        return False
    subject = str(s.get('subject','')).strip().lower()
    topic = str(s.get('topic','')).strip().lower()
    subtopic = str(s.get('subtopic','')).strip().lower()
    return ('matematik' in subject and 'darab' in topic and 'konsep darab' in subtopic)


def _local_concept_darab_worksheet(s):
    """Zero-cost one-page generator for Tahun 3 Konsep Darab.

    Generates exactly the requested number of questions. Equal-group visuals are
    deterministic mathematical diagrams, never decorative pictures.
    """
    qcount = _worksheet_question_count(s)
    diff = str(s.get('difficulty','mixed')).lower()
    seed = str(s.get('variation_seed') or secrets.token_hex(4))
    rng = random.Random(seed)
    objects = ['bola','epal','bintang','bunga','pensel','buku']
    contexts = [('pinggan','epal'),('kotak','pensel'),('bakul','bola'),('pasu','bunga'),('rak','buku'),('kad','bintang')]
    if diff == 'easy': gvals,pvals=list(range(2,5)),list(range(2,6))
    elif diff == 'hard': gvals,pvals=list(range(3,8)),list(range(3,10))
    else: gvals,pvals=list(range(2,7)),list(range(2,9))
    used=set()
    def pair():
        for _ in range(60):
            a,b=rng.choice(gvals),rng.choice(pvals)
            if (a,b) not in used: used.add((a,b)); return a,b
        return rng.choice(gvals),rng.choice(pvals)

    student=[]; ans=[]
    n_obj=max(1, round(qcount*.35)); n_fill=max(1, round(qcount*.30)); n_struct=qcount-n_obj-n_fill
    if n_struct < 1: n_struct=1; n_obj=max(1,n_obj-1)
    q=1
    student += ['BAHAGIAN A','Pilih jawapan yang betul.']
    for _ in range(n_obj):
        a,b=pair(); obj=rng.choice(objects); correct=f'{a} x {b}'
        choices=[correct,f'{b} x {a}',f'{a} + {b}',f'{a+b} x 1']; rng.shuffle(choices)
        student.append(f'{q}. Rajah menunjukkan {a} kumpulan sama banyak. Setiap kumpulan mempunyai {b} {obj}. [VISUAL_GROUPS: {obj}, {a}, {b}]')
        student.append(' '.join(f'{L}. {v}' for L,v in zip('ABCD',choices)))
        ans.append((q,'ABCD'[choices.index(correct)])); q+=1
    student += ['BAHAGIAN B','Lengkapkan ayat matematik.']
    for _ in range(n_fill):
        a,b=pair(); rep=' + '.join([str(b)]*a)
        if q%2: student.append(f'{q}. {rep} = ______ x {b}'); atext=str(a)
        else: student.append(f'{q}. {a} x {b} = {rep} = ______'); atext=str(a*b)
        ans.append((q,atext)); q+=1
    if n_struct:
        student += ['BAHAGIAN C','Selesaikan soalan.']
    for i in range(n_struct):
        a,b=pair(); container_name,obj=rng.choice(contexts)
        token=f' [VISUAL_GROUPS: {obj}, {a}, {b}]' if i==0 and qcount<=10 else ''
        student.append(f'{q}. Terdapat {a} {container_name}. Setiap {container_name} mempunyai {b} {obj}. Berapakah jumlah {obj} kesemuanya?{token} [ANSWERSPACE: 2]')
        ans.append((q,f'{a} x {b} = {a*b}')); q+=1
    schemes=['BAHAGIAN A']+[f'{no}. {a}' for no,a in ans[:n_obj]]+['BAHAGIAN B']+[f'{no}. {a}' for no,a in ans[n_obj:n_obj+n_fill]]
    if n_struct: schemes += ['BAHAGIAN C']+[f'{no}. {a}' for no,a in ans[n_obj+n_fill:]]
    return '\n'.join(student+['SKEMA JAWAPAN']+schemes)

def _hybrid_postprocess_worksheet(text, s):
    """Keep AI as a content writer; all countable artwork is rendered by Python.

    Also repairs omitted equal-group visual tokens for the current Year 3 multiplication
    concept so the picture can never be a decorative or mathematically ambiguous pile.
    """
    if not text or s.get('task') != 'worksheet':
        return text
    subject=str(s.get('subject','')).lower(); topic=str(s.get('topic','')).lower(); sub=str(s.get('subtopic','')).lower()
    if 'matematik' in subject and 'pecahan' in (topic + ' ' + sub):
        # Generic object pictures cannot faithfully encode shaded/coloured fraction categories.
        # Keep only mathematically structured fraction diagrams.
        text = re.sub(r'\[VISUAL:\s*[^\]]+\]', '', text, flags=re.I)
    if not ('matematik' in subject and 'darab' in topic and 'konsep' in sub):
        return text

    out=[]
    obj_words='bola|epal|bintang|bunga|pensel|buku'
    pat=re.compile(rf'(?P<a>\d+)\s+kumpulan[^\n]*?(?P<b>\d+)\s+(?P<obj>{obj_words})', re.I)
    for line in text.splitlines():
        if 'SKEMA JAWAPAN' in line.upper():
            out.append(line); out.extend(text.splitlines()[len(out):]); break
        if '[VISUAL_GROUPS:' not in line.upper():
            m=pat.search(line)
            if m and re.match(r'^\s*\d+[\.)]', line):
                line += f" [VISUAL_GROUPS: {m.group('obj').lower()}, {m.group('a')}, {m.group('b')}]"
        out.append(line)
    else:
        return '\n'.join(out)
    return '\n'.join(out)


def _worksheet_output_token_budget(s):
    """Keep Gemini output compact: enough for questions + short answer scheme only."""
    q = _worksheet_question_count(s) if s.get('task') == 'worksheet' else int(s.get('amount', 5) or 5)
    # Most worksheets need far less than the previous fixed 8192-token ceiling.
    return min(5000, max(1600, 900 + (q * 220)))


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
        worksheet_questions = _worksheet_question_count(s)
        student_level = _worksheet_level(s)
        difficulty_label = _difficulty_label(s.get('difficulty', 'mixed'))
        difficulty_instruction = _difficulty_instruction(s)
        curriculum_depth = _curriculum_depth_instruction(s)
        worksheet_blueprint = _worksheet_blueprint_instruction(s)
        variation_seed = s.get('variation_seed') or secrets.token_hex(4)
        return common + f"""
Tugasan: Hasilkan satu worksheet yang boleh terus digunakan di kelas.
MOD HIBRID KOS RENDAH: Anda hanya menjana kandungan teks soalan dan token visual. Jangan cuba melukis gambar, ASCII art atau menerangkan rupa gambar; enjin Python CikguLaju akan membina semua visual dan PDF secara tempatan. Gunakan ayat pendek dan elakkan penerangan tambahan supaya token output rendah.
Mulakan dengan ARAHAN, kemudian bahagikan aktiviti kepada BAHAGIAN A, BAHAGIAN B dan seterusnya jika sesuai. Jangan ulang ruang Nama/Kelas/Tarikh kerana dokumen akan menyediakannya.

KHUSUS UNTUK WORKSHEET:
- Hasilkan TEPAT {worksheet_questions} SOALAN dalam SATU worksheet sahaja.
- ID variasi set ini: {variation_seed}. Gunakan ID ini hanya untuk mempelbagaikan pemilihan nombor, konteks, susunan dan bentuk aktiviti; jangan paparkan ID ini dalam hasil.
- Setiap penjanaan baharu mesti menggunakan variasi soalan, nombor, objek, situasi dan susunan yang berbeza.
- Elakkan mengulang set contoh lazim yang sama apabila terdapat banyak kemungkinan soalan.
- JANGAN tulis HELAIAN 1, HELAIAN 2 atau label helaian lain.
- Bilangan halaman TIDAK ditetapkan. Gunakan sebanyak halaman yang perlu mengikut panjang soalan, visual dan ruang menjawab/pengiraan.
- Aras mesti sesuai dengan {student_level}.
- Pilihan aras cikgu: {difficulty_label}.
- {difficulty_instruction}
- {curriculum_depth}
- {worksheet_blueprint}
- Gunakan 2 hingga 4 jenis aktiviti yang berbeza dalam worksheet yang sama jika sesuai.
- Elakkan lebih daripada 3 soalan berturut-turut dengan struktur ayat yang sama.
- Ruang jawapan/pengiraan mesti mengikut keperluan sebenar. 10 soalan boleh menjadi 1, 2 atau 3 halaman. Jangan paksa kandungan muat dalam satu halaman.
- Untuk objektif, pilihan jawapan mesti munasabah dan pengecoh mesti berdasarkan kesilapan lazim murid.
- Untuk soalan visual, visual mesti mengandungi maklumat yang diperlukan untuk menyelesaikan soalan DAN mesti sepadan tepat dengan semua nombor/kuantiti dalam teks.
- Visual bukan hiasan. Sebelum keluarkan jawapan, semak bahawa murid boleh mendapatkan maklumat matematik yang dimaksudkan terus daripada visual.
- Jangan cipta ungkapan rosak seperti "+ = ____". Semua operand/nombor penting mesti kekal dalam teks atau divisualkan dengan jelas.
- Untuk Tahun 1-3, utamakan aktiviti visual, mengira objek, memadan, melengkapkan, memilih, mewarna/menanda secara munasabah, dan situasi harian yang sangat ringkas.
- Untuk Tahun 4-6, gunakan gabungan visual, aplikasi, jadual/rajah ringkas, objektif, struktur dan penyelesaian masalah.
- Untuk sekolah menengah, gunakan visual/rajah hanya apabila membantu kandungan; utamakan aplikasi konsep dan penaakulan.
- Untuk Tahun 1-3, sasarkan 25%-40% item menggunakan visual yang benar-benar diperlukan untuk menjawab; jangan jadikan semua soalan visual.
- Untuk visual objek boleh kira biasa, gunakan token [VISUAL: epal, 5].
- Untuk konsep KUMPULAN SAMA BANYAK/darab, WAJIB gunakan [VISUAL_GROUPS: bola, 3, 4] yang bermaksud 3 kumpulan berasingan, 4 bola setiap kumpulan. Jangan gunakan [VISUAL: bola, 12] untuk soalan konsep 3 × 4 kerana itu menghilangkan struktur kumpulan.
- Sistem akan menukar token kepada GAMBAR sebenar; jangan tulis perkataan "visual", "gambar di sini", atau penerangan placeholder kepada murid.
- GUNAKAN FORMAT ASAS SEPERTI BUKU LATIHAN/KERTAS PEPERIKSAAN: pilih ruang jawapan mengikut jenis tugasan, bukan satu bentuk ruang untuk semua soalan.
- Untuk operasi Matematik yang sesuai dibuat secara bentuk lazim, tambah token [FORM_LAZIM: baris, lajur]. Contoh asas [FORM_LAZIM: 3, 3] untuk pengiraan ringkas. Besarkan grid secara munasabah bagi nombor lebih panjang/lebih banyak langkah, contohnya 4x4 atau 4x5. Jangan gunakan grid jika soalan hanya objektif atau isi tempat kosong mudah.
- Untuk MATEMATIK, JANGAN gunakan garisan bergaris untuk pengiraan. Gunakan [ANSWERSPACE: n] sebagai ruang kosong tanpa garisan, atau [FORM_LAZIM: baris, lajur] jika operasi memang sesuai dibuat secara bentuk lazim.
- Untuk subjek bahasa/esei yang benar-benar memerlukan tulisan beberapa ayat, [WORKLINES: n] boleh digunakan dengan n antara 2 hingga 6.
- Untuk jawapan yang memerlukan ruang melukis, melabel, membina ayat, peta ringkas atau respons terbuka, gunakan [ANSWERBOX: n] dengan n antara 1 hingga 5 mengikut ruang yang diperlukan.
- Prinsip semua subjek: ruang mesti sepadan dengan jawapan yang dijangka. Jawapan satu perkataan/nombor tidak boleh diberi ruang besar; huraian beberapa ayat tidak boleh diberi satu garisan pendek.
- Anggap format ini sebagai TEMPLATE TETAP CikguLaju. Ubah kandungan soalan, nombor, konteks dan imej antara penjanaan, tetapi kekalkan struktur lembaran yang konsisten dan kemas seperti buku latihan/kertas peperiksaan.
- Visual mesti dipilih kerana KONSEP, bukan kerana hiasan. Jika enjin tidak mempunyai token rajah yang boleh mewakili konsep dengan tepat, JANGAN gunakan visual pada soalan itu. Lebih baik tiada gambar daripada gambar yang mengelirukan.
- Untuk PECAHAN, jangan gunakan sekumpulan bunga/epal biasa untuk mewakili pecahan berlorek atau warna. Gunakan [FRACTION_BAR: pengangka, penyebut] untuk bar pecahan atau [FRACTION_SET: jumlah, dipilih] untuk set pecahan tunggal. Rajah dipilih ditanda dengan corak hitam-putih, bukan warna. Untuk lebih daripada satu kategori pecahan/warna dalam soalan yang sama, gunakan teks/jadual sahaja buat masa ini.
- Gunakan visual cetak hitam-putih yang sesuai dengan umur hanya apabila tepat: epal, bola, bintang, bunga, pensel, buku, syiling, bentuk, kad nombor dan blok puluh/base-ten.
- Untuk Matematik Tahun 2 ke atas, jangan terlalu bergantung pada gambar objek comel. Campurkan representasi matematik seperti blok puluh, kad nombor, nilai hilang, jadual kecil dan situasi sebenar.
- Jangan gunakan token [DIAGRAM] buat masa ini.
- Visual mesti menjadi sebahagian daripada tugasan, contohnya "Kira objek di bawah", "Bulatkan kumpulan yang betul", atau "Tulis ayat matematik berdasarkan gambar".
- VALIDASI WAJIB VISUAL: jika teks menyebut N kumpulan dengan M objek setiap kumpulan, gambar mesti ada tepat N kumpulan dan tepat M objek dalam setiap kumpulan; jumlah mestilah N×M. Jika tidak konsisten, betulkan sebelum memberikan output.
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
        result = (_local_concept_darab_worksheet(s) if _can_generate_zero_cost(s) else gemini_generate(build_ai_prompt(s), max_output_tokens=_worksheet_output_token_budget(s)))
        result = _hybrid_postprocess_worksheet(result, s)
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
        [{'text':'📋 Jana Worksheet','callback_data':'task_worksheet'}],
        [{'text':'📚 RPH','callback_data':'task_rph'}],
        [{'text':'⬅️ Menu Utama','callback_data':'home'}]])

def level(cid, task):
    state.setdefault(cid,{})['task'] = task
    send(cid,'🏫 <b>Pilih tahap:</b>',[
        [{'text':'🎒 Sekolah Rendah','callback_data':'level_primary'}],
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
    detail = (f"🔢 {s.get('worksheet_questions',8)} soalan • 1 halaman worksheet\n\n🤖 Sedia untuk dijana dengan AI."
              if s.get('task') == 'worksheet'
              else f"📝 {s.get('qtype','-')}\n🔢 {s.get('amount','-')} soalan\n\n🤖 Sedia untuk dijana dengan AI.")
    msg = (f"✅ <b>Pilihan Cikgu</b>\n\n🎓 {s.get('year','-')}\n📚 {s.get('subject','-')}\n"
           f"📖 {s.get('topic','-')}\n▫️ {s.get('subtopic','Semua Subtopik')}\n{detail}")
    send(cid, msg,
         [[{'text':'✨ Jana Dengan AI','callback_data':gen_cb}],
          [{'text':'🏠 Menu Utama','callback_data':'home'}]])

def generate_v3(cid, s, regen_cb):
    # Prevent Telegram webhook retries / double taps from launching duplicate AI jobs.
    with _runtime_lock:
        if cid in _processing_chats:
            send(cid, '⏳ <b>Worksheet masih sedang dijana.</b>\n\nCikgu tak perlu tekan lagi. Tunggu sehingga proses siap.')
            return
        _processing_chats.add(cid)

    try:
        # Fresh seed on every generation, including Jana Semula.
        if s.get('task') == 'worksheet':
            s['variation_seed'] = secrets.token_hex(4)
        send(cid,'⚡ <b>Sedang jana bahan...</b>\n<i>Cikgu tunggu beberapa saat.</i>')
        try:
            if _can_generate_zero_cost(s):
                print('Hybrid zero-cost local generator: Matematik > Darab > Konsep darab', flush=True)
                result = _local_concept_darab_worksheet(s)
            else:
                result = gemini_generate(build_ai_prompt(s), max_output_tokens=_worksheet_output_token_budget(s))
            result = _hybrid_postprocess_worksheet(result, s)
            state.setdefault(cid,{})['last_result'] = result
            state[cid]['last_result_context'] = s

            # Worksheet tidak dipaparkan sebagai teks dalam Telegram; terus tawarkan fail siap.
            send(cid,'✅ <b>Worksheet siap!</b>\n\nPilih format fail:',
                 [[{'text':'📄 PDF','callback_data':'file_pdf'},
                   {'text':'📝 Word','callback_data':'file_word'}],
                  [{'text':'📦 Kedua-dua','callback_data':'file_both'}],
                  [{'text':'🔄 Jana Semula','callback_data':regen_cb}],
                  [{'text':'🏠 Menu Utama','callback_data':'home'}]])
        except Exception as e:
            err = str(e)
            print('Gemini error:', repr(e), flush=True)
            # Show a safe, short technical reason so failures are diagnosable from Telegram too.
            safe = html.escape(err[:220])
            send(cid,
                 '⚠️ <b>Janaan AI belum berjaya.</b>\n\n'
                 f'<code>{safe}</code>\n\n'
                 'Tekan <b>Cuba Lagi</b>. Sistem akan menggunakan model alternatif secara automatik.',
                 [[{'text':'🔄 Cuba Lagi','callback_data':regen_cb}],
                  [{'text':'🏠 Menu Utama','callback_data':'home'}]])
    finally:
        with _runtime_lock:
            _processing_chats.discard(cid)


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
            send(cid,'🔢 <b>Berapa soalan cikgu mahu?</b>\n\nBilangan halaman akan disesuaikan secara automatik mengikut soalan dan ruang jawapan.',
                 [[{'text':'5 Soalan','callback_data':f'wp3|5|{tc}|{yc}|{si}|{ti}|{sti}'},
                   {'text':'8 Soalan','callback_data':f'wp3|8|{tc}|{yc}|{si}|{ti}|{sti}'}],
                  [{'text':'10 Soalan','callback_data':f'wp3|10|{tc}|{yc}|{si}|{ti}|{sti}'},
                   {'text':'12 Soalan','callback_data':f'wp3|12|{tc}|{yc}|{si}|{ti}|{sti}'}],
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
                      [
                         {'text':'🧠 KBAT','callback_data':f'lv3|kbat|{pages_n}|{tc}|{yc}|{si}|{ti}|{sti}'}
                      ],
                      [{'text':'🏠 Menu Utama','callback_data':'home'}]])

    elif d.startswith('lv3|'):
        parts = d.split('|')
        if len(parts) == 8:
            _, diff, pages_n, tc, yc, si, ti, sti = parts
            s = rebuild_state(tc, yc, si, ti, sti)
            if s:
                s['worksheet_questions'] = int(pages_n)
                s['difficulty'] = diff
                s['variation_seed'] = secrets.token_hex(4)
                gen_cb = f'gw3|{diff}|{pages_n}|{tc}|{yc}|{si}|{ti}|{sti}'
                send(cid,
                     f"✅ <b>Pilihan Cikgu</b>\n\n"
                     f"🎓 {s.get('year','-')}\n📚 {s.get('subject','-')}\n"
                     f"📖 {s.get('topic','-')}\n▫️ {s.get('subtopic','Semua Subtopik')}\n"
                     f"🔢 {pages_n} soalan • halaman automatik mengikut ruang\n"
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
                s['worksheet_questions'] = int(pages_n)
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
    update_id = u.get('update_id')

    # Telegram retries a webhook if the HTTP response is slow. Ignore duplicate deliveries.
    if update_id is not None:
        with _runtime_lock:
            if update_id in _seen_updates:
                return jsonify({'ok':True, 'duplicate':True})
            _seen_updates.add(update_id)
            if len(_seen_updates) > 5000:
                # Bound memory usage; update IDs are monotonically increasing.
                for old_id in sorted(_seen_updates)[:2500]:
                    _seen_updates.discard(old_id)

    if 'callback_query' in u:
        c = u['callback_query']
        try:
            requests.post(
                f'{API}/answerCallbackQuery',
                json={'callback_query_id':c['id']},
                timeout=5
            )
        except Exception as e:
            print('answerCallbackQuery error:', repr(e), flush=True)

        cid = c['message']['chat']['id']
        data = c.get('data','')
        # Return HTTP 200 immediately; long Gemini/file work continues in background.
        threading.Thread(target=callback, args=(cid, data), daemon=True).start()

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
