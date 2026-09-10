import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
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

SUBJECTS = [
    ('🇲🇾 Bahasa Melayu','Bahasa Melayu'),('🇬🇧 Bahasa Inggeris','Bahasa Inggeris'),
    ('➗ Matematik','Matematik'),('🔬 Sains','Sains'),('🏛️ Sejarah','Sejarah'),
    ('☪️ Pendidikan Islam','Pendidikan Islam'),('✏️ Subjek Lain','Subjek Lain')
]

def send(cid, text, kb=None):
    p = {'chat_id': cid, 'text': text, 'parse_mode': 'HTML'}
    if kb:
        p['reply_markup'] = {'inline_keyboard': kb}
    requests.post(f'{API}/sendMessage', json=p, timeout=20)

def menu(cid):
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

def choose_topic(cid, idx):
    s = state.setdefault(cid,{})
    topics = s.get('topic_list',[])
    if idx < 0 or idx >= len(topics):
        return show_topics(cid,0)
    s['topic'] = topics[idx]
    s.pop('waiting',None)
    after_topic(cid)

def after_topic(cid):
    s = state.setdefault(cid,{})
    if s.get('task') in ('questions','kbat'):
        qtype(cid)
    else:
        send(cid,
             f"✅ <b>Tajuk dipilih</b>\n\n🎓 {s.get('year','-')}\n📚 {s.get('subject','-')}\n📖 {s.get('topic','-')}\n\n🤖 Sedia untuk dijana dengan AI.",
             [[{'text':'✨ Jana Dengan AI','callback_data':'generate'}],[{'text':'🏠 Menu Utama','callback_data':'home'}]])

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
    elif d == 'quick': quick(cid)
    elif d == 'material':
        state.setdefault(cid,{})['waiting'] = 'material'
        send(cid,'📚 <b>GUNA BAHAN CIKGU</b>\n\nHantar 📄 PDF atau 📸 gambar nota.\n\nPembacaan AI akan disambungkan pada langkah seterusnya.')
    elif d == 'pro':
        send(cid,'⭐ <b>CIKGU PRO</b>\n\n💳 <b>RM9.90/bulan</b> — harga pengenalan\n\n📝 Soalan & skema\n📋 Worksheet\n📚 RPH\n🧠 KBAT\n📥 Word/PDF\n⚡ Had lebih tinggi')
    elif d == 'account':
        send(cid,'👤 <b>AKAUN SAYA</b>\n\nPelan: 🎁 Percubaan\nStatus: Aktif')
    elif d.startswith('task_'): level(cid,d[5:])
    elif d == 'level_primary': year(cid,'primary')
    elif d == 'level_secondary': year(cid,'secondary')
    elif d.startswith('year_'): subjects(cid,'Tahun '+d[5:])
    elif d.startswith('form_'): subjects(cid,'Tingkatan '+d[5:])
    elif d.startswith('sub_'):
        s = state.setdefault(cid,{})
        s['subject'] = d[4:]
        show_topics(cid,0)
    elif d.startswith('tpage_'):
        show_topics(cid,int(d[6:]))
    elif d.startswith('topic_'):
        if d == 'topic_custom':
            state.setdefault(cid,{})['waiting'] = 'topic'
            send(cid,'✏️ <b>Taip tajuk/topik sendiri:</b>')
        else:
            choose_topic(cid,int(d[6:]))
    elif d.startswith('qt_'): amount(cid,d[3:])
    elif d.startswith('amt_'):
        s = state.setdefault(cid,{})
        s['amount'] = d[4:]
        send(cid,
             f"✅ <b>Pilihan Cikgu</b>\n\n🎓 {s.get('year','-')}\n📚 {s.get('subject','-')}\n📖 {s.get('topic','-')}\n📝 {s.get('qtype','-')}\n🔢 {s['amount']} soalan\n\n🤖 Sedia untuk dijana dengan AI.",
             [[{'text':'✨ Jana Dengan AI','callback_data':'generate'}],[{'text':'🏠 Menu Utama','callback_data':'home'}]])
    elif d == 'generate':
        send(cid,'🤖 <b>Asas bot sudah siap.</b>\n\nLangkah seterusnya kita sambungkan Gemini untuk jana bahan sebenar berdasarkan pilihan cikgu.')

@app.route('/')
def index():
    return jsonify({'status':'ok','app':'CikguLaju AI'})

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
        if m.get('text') == '/start':
            state[cid] = {}
            menu(cid)
        elif 'text' in m and state.get(cid,{}).get('waiting') == 'topic':
            state[cid]['topic'] = m['text'].strip()
            state[cid].pop('waiting',None)
            after_topic(cid)
        elif 'document' in m or 'photo' in m:
            send(cid,'✅ Bahan diterima. Pembacaan PDF/gambar oleh AI akan disambungkan seterusnya.')
    return jsonify({'ok':True})

@app.route('/setup-webhook')
def setup_webhook():
    if not BOT_TOKEN or not WEBHOOK_URL:
        return jsonify({'ok':False,'error':'Tetapkan BOT_TOKEN dan WEBHOOK_URL dahulu'}),500
    url = WEBHOOK_URL.rstrip('/') + '/webhook'
    r = requests.post(f'{API}/setWebhook',json={'url':url},timeout=20)
    return jsonify({'webhook':url,'telegram':r.json()})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','10000')))
