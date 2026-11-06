"""Source-locked Sains Tahun 3 RPH activity bank (DRAFT / NOT LIVE).

One distinct pedagogical task per KSSR Semakan 2017 DSKP SP. Read-only overlay
for the Telegram native RPH renderer; no AI API calls, user records or credits.
Not a 2027 KP2027 Year 1 source. Not enabled or released to production.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits/sains_y3_v2582_45_textbook_page_candidates_20261106.json"
FIXES = ROOT / "audits/sains_y3_v2582_12_dskp_title_corrections_20261106.json"

# (Hook, activity 1 teacher action, pupil action, activity 2 teacher action,
# pupil action, observable PBD, specific material)
# Activities are authored for the literal SP and chapter, not generic subject
# prompts. Pages are review cues, never automatically certified as correct.
BANK = {
"3.1.1":(
"Gambar gigi kacip, taring dan geraham",
"menunjukkan kad gambar tiga jenis gigi dan menerangkan lokasi",
"memadankan setiap jenis gigi dengan fungsi menggigit, mengoyak atau mengisar",
"menyediakan gambar makanan dan meminta murid menjelaskan gigi yang digunakan",
"membanding jawapan pasangan dan menyatakan fungsi dengan bukti gambar",
"Padanan tiga jenis gigi dengan tiga fungsi yang tepat",
"Kad gambar gigi, model rahang dan gambar makanan"),
"3.1.2":(
"Keratan rentas sebatang gigi pada poster",
"menunjuk model gigi dan menerangkan bahagian pada gambar keratan",
"melabelkan enamel, dentin, pulpa dan gusi pada rajah",
"mengaburkan label model dan meminta murid membina semula rajah",
"menyemak label berpasangan dan membetulkan lokasi yang tidak tepat",
"Empat bahagian gigi berlabel pada rajah murid",
"Rajah struktur gigi, model gigi dan kad label"),
"3.1.3":(
"Dua gambar set gigi susu dan gigi kekal",
"menyediakan jadual perbandingan bilangan dan ciri gigi",
"mengelaskan maklumat kepada set gigi susu dan gigi kekal",
"membimbing binaan peta Venn berdasarkan persamaan serta perbezaan",
"menyatakan dua perbezaan dan satu persamaan dengan alasan",
"Peta Venn gigi susu/gigi kekal dengan tiga butiran sah",
"Gambar kedua-dua set gigi dan peta Venn"),
"3.1.4":(
"Gambar gigi sihat dan gigi rosak",
"menerangkan hubungan kerosakan enamel dengan cara menjaga gigi",
"mengenal pasti tindakan memberus, flos dan pemeriksaan gigi",
"memberi kad situasi makanan manis dan amalan penjagaan",
"memilih tindakan pencegahan serta mengaitkan dengan bahagian gigi",
"Dua tindakan penjagaan dihuraikan dengan kaitan struktur gigi",
"Poster keratan gigi, berus gigi dan kad situasi"),
"3.1.5":(
"Koleksi lakaran gigi murid",
"meminta kumpulan menerangkan pemerhatian pada model gigi",
"merekod dapatan dalam poster dengan label dan ayat tepat",
"memilih poster contoh dan mengemukakan soalan bukti",
"membentangkan pemerhatian gigi secara lisan dan menerima maklum balas",
"Poster berlabel dan pembentangan satu dapatan tentang gigi",
"Model gigi, kertas poster dan pen warna"),
"3.2.1":(
"Gambar nasi, ikan, telur, buah dan sayur",
"menerangkan kategori karbohidrat, protein, lemak, vitamin, mineral, pelawas dan air",
"mengelaskan kad makanan mengikut kelas yang sesuai",
"memaparkan dua menu dan meminta murid menamakan sumber nutrien",
"menjustifikasi satu pilihan pengelasan dengan contoh makanan",
"Tujuh kelas makanan dipadankan dengan contoh",
"Kad makanan harian dan jadual tujuh kelas makanan"),
"3.2.2":(
"Paparan tujuh kelas makanan",
"menyediakan contoh fungsi tenaga, pembinaan dan perlindungan badan",
"menghubung kait kelas makanan dengan kepentingannya kepada tubuh",
"memberikan situasi pemulihan badan selepas bersukan",
"merumus kelas makanan yang diperlukan dan alasan",
"Rumusan fungsi sekurang-kurangnya empat kelas makanan",
"Kad kelas makanan, carta fungsi nutrien dan kad situasi"),
"3.2.3":(
"Model piramid makanan dan pinggan kosong",
"menunjukkan aras piramid makanan dan saiz hidangan relatif",
"menyusun gambar makanan menjadi menu seimbang",
"membimbing semakan menu berdasarkan kepelbagaian kumpulan",
"menerangkan dua sebab menu itu seimbang",
"Menu seimbang dengan contoh setiap kumpulan dan alasan",
"Piramid makanan dan kad gambar hidangan"),
"3.2.4":(
"Dua menu harian yang berbeza",
"mencabar murid meneliti pengambilan gula, lemak dan sayur",
"mengenal pasti akibat pengambilan makanan tidak seimbang",
"meminta murid mengubah suai satu menu berlebihan",
"menyatakan perubahan, sebab dan kesan yang dijangka",
"Cadangan menu diperbaik dengan sekurang-kurangnya dua sebab",
"Kad menu harian, piramid makanan dan lembaran semak"),
"3.3.1":(
"Rajah sistem pencernaan manusia",
"menunjukkan model laluan makanan dari mulut hingga dubur",
"memerihalkan bagaimana makanan diuraikan sepanjang laluan",
"meminta murid menjelaskan peranan mulut, perut dan usus",
"menyambung anak panah rajah proses dengan penerangan ringkas",
"Penjelasan proses pencernaan dan tiga bahagian terlibat",
"Model salur pencernaan dan kad fungsi organ"),
"3.3.2":(
"Kad organ mulut, esofagus, perut, usus dan dubur",
"mengedarkan kad urutan perjalanan makanan",
"menyusun aliran makanan mengikut urutan yang betul",
"memilih dua titik laluan dan bertanya apa yang berlaku kepada makanan",
"melabel urutan serta menghuraikan perubahan makanan",
"Susunan lima organ pencernaan dalam urutan tepat",
"Kad organ, carta sistem pencernaan dan anak panah"),
"4.1.1":(
"Gambar harimau, kambing dan ayam",
"menerangkan cara mengelaskan haiwan daripada maklumat pemakanan",
"menyusun kad haiwan kepada herbivor, karnivor dan omnivor",
"memaparkan haiwan baharu tanpa label pemakanan",
"mengelaskan haiwan itu dengan menyatakan makanan yang dimakan",
"Pengelasan enam haiwan kepada tiga kumpulan dengan betul",
"Kad haiwan, kad makanan dan tiga carta pengelasan"),
"4.1.2":(
"Gambar haiwan makan tumbuhan dan daging",
"memberikan contoh menu haiwan daripada pelbagai habitat",
"menamakan herbivor, karnivor dan omnivor dengan contoh",
"membina jadual tiga lajur tabiat makan haiwan",
"merekod dua contoh haiwan dan makanan bagi setiap kumpulan",
"Enam contoh haiwan dan sebab pengelasan yang munasabah",
"Gambar haiwan, video tabiat makan dan jadual tiga lajur"),
"4.1.3":(
"Video rusa dan beruang mencari makanan",
"menunjukkan petunjuk bentuk gigi dan jenis makanan",
"membuat inferens kumpulan haiwan daripada bukti",
"memberikan kad haiwan yang belum dikenal pasti",
"menguji inferens melalui perbincangan bukti gambar makanan",
"Satu inferens tabiat makan dengan dua petunjuk",
"Video pemakanan dan kad bukti gambar"),
"4.1.4":(
"Gambar rahang lembu, harimau dan manusia",
"menerangkan kegunaan gigi taring dan geraham haiwan",
"membanding kegigian bagi tiga tabiat pemakanan",
"meminta murid mengisi peta Venn kegigian",
"menyebut dua perbezaan dan satu persamaan",
"Peta Venn dengan ciri kegigian yang tepat",
"Gambar rahang haiwan dan peta Venn"),
"4.1.5":(
"Gambar haiwan dengan makanan semula jadi",
"meminta murid merekod pemerhatian haiwan makan",
"menghasilkan lakaran berlabel tentang tabiat pemakanan",
"mengadakan gallery walk poster haiwan",
"menerangkan dapatan dengan alasan berdasarkan gambar",
"Poster tabiat makanan dengan label dan bukti",
"Kad pemerhatian, gambar dan poster"),
"5.1.1":(
"Benih kacang dan keratan batang",
"menunjukkan biji benih, spora, daun, anak pokok dan batang bawah tanah",
"memadankan gambar tumbuhan dengan cara pembiakan",
"menyediakan sampel tumbuhan yang dikenal pasti",
"mengelaskan setiap sampel mengikut cara pembiakan",
"Lima cara pembiakan dan contohnya dipadankan",
"Sampel benih, keratan batang dan kad gambar"),
"5.1.2":(
"Gambar kawasan tanpa tumbuhan dan kawasan berhijau",
"membimbing murid membincang fungsi pembiakan bagi kesinambungan hidup",
"menyatakan kepentingan pembiakan tumbuhan kepada haiwan dan manusia",
"menyediakan senario satu spesies tidak membiak",
"menaakul kesan terhadap makanan dan habitat",
"Dua sebab kepentingan pembiakan dihuraikan",
"Gambar ekosistem dan kad sebab-akibat"),
"5.1.3":(
"Contoh ubi keledek dan beberapa cara membiak",
"membimbing projek ringkas tumbuhan yang membiak lebih satu cara",
"merancang perbandingan pembiakan melalui biji/keratan batang",
"memberi jadual rekod pertumbuhan berkala",
"melakar prosedur dan mengitlak potensi lebih satu cara pembiakan",
"Jadual projek dengan dua kaedah dan rumusan",
"Biji benih, keratan batang, pasu dan jadual pemerhatian"),
"5.1.4":(
"Gambar pelbagai tumbuhan muda",
"mengarah murid merekod hasil projek pembiakan",
"melakar proses dan mencatat langkah yang diperhatikan",
"menganjurkan pembentangan hasil projek",
"memberi rumusan lisan tentang kaedah dan pemerhatian",
"Lakaran urutan projek dengan dua pemerhatian",
"Jadual projek, foto tumbuhan dan buku rekod"),
"6.1.1":(
"Kad cm², m², mL, L dan cm³",
"menunjuk objek serta bekas dan menyoal unit ukuran sesuai",
"memadankan luas permukaan dengan cm²/m² dan isi padu dengan mL/L/cm³",
"menyediakan contoh objek serta cecair",
"memilih unit dan menerangkan sebab pemilihan",
"Padanan lima unit ukuran dengan kuantiti sebenar",
"Kad unit, bekas bersenggat dan grid persegi"),
"6.1.2":(
"Petak grid 1 cm × 1 cm",
"menunjukkan cara mengira petak bagi bentuk sekata",
"mengukur luas segi empat menggunakan grid",
"menyediakan bentuk kedua tanpa nilai luas",
"mengira petak dan melaporkan luas dalam cm²",
"Dua pengiraan luas sekata dalam cm² yang betul",
"Kertas grid 1 cm, pembaris dan kad bentuk"),
"6.1.3":(
"Bentuk tapak daun pada kertas grid",
"menjelaskan anggaran luas bentuk tidak sekata melalui petak penuh/sebahagian",
"menganggarkan luas bentuk pada grid",
"meminta murid membanding dua kaedah anggaran",
"membina rumusan tentang sebab anggaran berbeza",
"Nilai anggaran luas dan penerangan kaedah",
"Daun, kertas grid 1 cm dan pensel"),
"6.1.4":(
"Model kotak lohong dan kubus 1 cm³",
"menunjuk cara menyusun kubus unit dalam kotak",
"mengisi model dengan kubus dan mengira bilangan kubus",
"menukar dimensi kotak dan meminta perbandingan",
"merekod isi padu kotak kedua dalam cm³",
"Dua nilai isi padu model kotak yang tepat",
"Kotak lohong dan kubus 1 cm³"),
"6.1.5":(
"Silinder penyukat yang mengandungi air",
"menunjukkan cara membaca meniskus pada aras mata",
"mengukur isi padu dua sampel cecair dengan teknik yang betul",
"memaparkan dua gambar bacaan meniskus",
"menentukan bacaan yang tepat dan sebabnya",
"Dua bacaan isi padu cecair dengan unit mL",
"Silinder penyukat, air dan kad meniskus"),
"6.1.6":(
"Batu kecil dan silinder penyukat",
"menunjukkan kaedah sesaran air serta membaca isi padu awal",
"menenggelamkan pepejal selamat dan mencatat bacaan akhir",
"membimbing pengiraan beza dua bacaan",
"mengira isi padu pepejal tidak sekata dalam mL/cm³",
"Beza bacaan awal–akhir dan unit yang betul",
"Silinder penyukat, air dan batu kecil"),
"6.1.7":(
"Rekod luas dan isi padu daripada aktiviti terdahulu",
"mengadakan semakan cara mengambil bacaan ukuran",
"menyediakan rajah berlabel alat dan dapatan",
"menerangkan ketepatan bacaan yang berbeza",
"membentangkan dua bukti pengukuran dengan unit tepat",
"Jadual dan rajah pengukuran dengan alasan",
"Jadual ukuran, kertas grid dan silinder penyukat"),
"7.1.1":(
"Dua objek yang timbul dan tenggelam dalam air",
"menyediakan bekas air untuk ujian objek selamat",
"meramal kemudian memerhati objek timbul atau tenggelam",
"membanding ramalan dan hasil pemerhatian",
"membina inferens menggunakan ketumpatan relatif",
"Jadual ramalan–pemerhatian–inferens bagi empat objek",
"Bekas air, sudu plastik, batu dan gabus"),
"7.1.2":(
"Gabus timbul dan batu tenggelam",
"menunjukkan konsep relatif lebih tumpat atau kurang tumpat daripada air",
"menghubung kait kedudukan objek dalam air dengan ketumpatan",
"memberi gambar objek baharu dan meminta penjelasan",
"memberi alasan mengapa bahan itu timbul atau tenggelam",
"Dua kaitan yang tepat antara ketumpatan dan kedudukan",
"Bekas air, bahan selamat dan gambar perbandingan"),
"7.1.3":(
"Telur dalam air biasa dan air garam",
"menyediakan dua bekas berlabel air dan air garam",
"membanding kedudukan telur dalam dua bekas",
"membimbing rumusan kaedah meningkatkan ketumpatan air",
"menyatakan bahan yang ditambah serta dapatan ujian",
"Kesimpulan satu kaedah peningkatan ketumpatan air",
"Telur, air, garam dan dua bekas telus"),
"7.1.4":(
"Gambar lapisan cecair berlainan ketumpatan",
"membimbing murid melakar kedudukan bahan yang diuji",
"merekod objek lebih/kurang tumpat daripada air",
"mengadakan galeri hasil lakaran",
"menerangkan dapatan dengan bukti pemerhatian",
"Lakaran berlabel dengan penjelasan perbezaan ketumpatan",
"Bekas telus, objek selamat dan kertas lakaran"),
"8.1.1":(
"Kertas litmus merah dan biru",
"menunjuk kertas litmus bagi sampel berlabel dan selamat",
"memerhati perubahan warna litmus tanpa menghidu atau merasa bahan",
"mengarahkan pengelasan tiga sampel berdasarkan rekod warna",
"mengelaskan asid, alkali atau neutral dan memberi bukti",
"Jadual warna litmus dan kelas setiap sampel",
"Kertas litmus, air, sampel makanan berlabel dan sarung tangan"),
"8.1.2":(
"Kad maklumat rasa dan sentuhan bahan makanan",
"menyediakan kad ciri bahan berlabel tanpa ujian rasa atau sentuhan terus",
"mengkaji maklumat ciri asid, alkali dan neutral pada kad",
"membimbing rumusan persamaan serta perbezaan berdasarkan kad",
"membina jadual rumusan daripada maklumat yang diberi",
"Jadual ciri tiga kategori berdasarkan bukti kad",
"Kad ciri bahan makanan, jadual pengelasan dan litmus"),
"8.1.3":(
"Ekstrak kubis ungu sebagai penunjuk semula jadi",
"menunjukkan perubahan warna penunjuk daripada bahan semula jadi",
"meramalkan kemudian memerhati perubahan warna pada sampel berlabel",
"membanding keputusan ekstrak dengan kertas litmus",
"menilai sama ada bahan penunjuk itu boleh digunakan",
"Perbandingan dua penunjuk berdasarkan pemerhatian",
"Ekstrak kubis ungu, litmus dan sampel selamat berlabel"),
"8.1.4":(
"Jadual keputusan penyiasatan litmus",
"meminta murid melakar jadual bukti perubahan warna",
"merekod keputusan ujian asid, alkali dan neutral",
"memimpin perbentangan poster kumpulan",
"menerangkan pemerhatian dengan alasan daripada data",
"Poster jadual litmus dan satu rumusan tepat",
"Kertas litmus, carta data dan poster"),
"9.1.1":(
"Gambar Matahari dan lapan planet",
"menayangkan rajah Sistem Suria daripada bahan media yang sah",
"menyenaraikan Matahari, planet dan ahli lain dalam Sistem Suria",
"meminta murid membina peta susunan planet",
"menyemak susunan serta nama ahli Sistem Suria",
"Susunan lapan planet dan senarai ahli Sistem Suria",
"Rajah Sistem Suria dan kad planet"),
"9.1.2":(
"Jadual planet mengikut kedudukan daripada Matahari",
"menyediakan maklumat suhu planet secara perbandingan",
"mengenal pola umum suhu mengikut kedudukan dengan menyebut pengecualian",
"meminta murid melakar carta suhu menggunakan data diberi",
"mengitlak pola suhu dan menghuraikan satu pengecualian",
"Rumusan berasaskan carta dan data suhu planet",
"Kad suhu planet dan carta data berlabel"),
"9.1.3":(
"Animasi planet bergerak pada orbit",
"menunjukkan laluan orbit planet mengelilingi Matahari",
"melakar orbit dan menandakan arah peredaran",
"menggunakan model bola pada laluan elips ringkas",
"memerihalkan peredaran planet mengikut orbit",
"Lakaran orbit berlabel dan penerangan peredaran",
"Model Matahari–planet dan kad orbit"),
"9.1.4":(
"Kad planet dekat dan jauh daripada Matahari",
"memaparkan jadual tempoh peredaran planet",
"menghubung kait kedudukan planet dengan tempoh mengelilingi Matahari",
"meminta murid menyusun kad tempoh peredaran",
"menyatakan hubungan kedudukan dan tempoh bersama bukti",
"Rumusan tempoh orbit sekurang-kurangnya empat planet",
"Jadual tempoh orbit dan kad planet"),
"9.1.5":(
"Jadual dapatan ahli, suhu dan orbit planet",
"membimbing penyediaan poster ringkasan Sistem Suria",
"melukis susunan dan orbit dengan label",
"memimpin pembentangan dapatan Sistem Suria",
"menerangkan satu pemerhatian tentang suhu atau tempoh orbit",
"Poster Sistem Suria dan dua bukti pemerhatian",
"Kad planet, jadual suhu dan poster"),
"10.1.1":(
"Gambar kren dan telaga bertakal",
"memaparkan takal pada objek kehidupan harian",
"menyatakan maksud takal serta kegunaan menaikkan beban",
"membekalkan model ringkas bertakal untuk diperhatikan",
"melabel roda, tali dan beban serta kegunaannya",
"Rajah takal berlabel dan dua kegunaan takal",
"Model takal, tali dan gambar kren"),
"10.1.2":(
"Takal tetap kecil dengan beban ringan",
"mendemonstrasi takal tetap dengan beban yang selamat",
"menerangkan arah tarikan dan pergerakan beban pada model",
"mengarah murid melakar arah daya dan pergerakan",
"memerihalkan fungsi takal tetap menggunakan model",
"Lakaran arah daya dengan penerangan yang tepat",
"Model takal tetap, tali dan beban ringan"),
"10.1.3":(
"Gambar kren, tiang bendera dan perigi",
"menunjukkan beberapa aplikasi takal dalam kehidupan",
"mengenal pasti lokasi, fungsi dan jenis penggunaan",
"meminta murid memadankan masalah mengangkat beban dengan aplikasi takal",
"memilih dan memberi sebab bagi satu aplikasi",
"Tiga contoh takal serta fungsi masing-masing",
"Gambar kren, tiang bendera dan model takal"),
"10.1.4":(
"Lakaran model takal ringkas",
"membimbing pelan model menggunakan roda, tali dan beban kecil",
"mereka bentuk dan membina model takal yang berfungsi secara berkumpulan",
"meminta kumpulan menguji model dengan beban ringan",
"merekod pembaikan terhadap model berdasarkan ujian",
"Model takal berfungsi dan rekod satu pembaikan",
"Roda kecil, tali, pemegang, beban ringan dan kad ujian"),
"10.1.5":(
"Gambar model takal yang telah dibina",
"meminta murid merakam pemerhatian proses menaikkan beban",
"menghasilkan lakaran model dan catatan bukti",
"menganjurkan galeri model takal",
"membentangkan bagaimana takal berfungsi dengan justifikasi",
"Lakaran berlabel dan pembentangan dapatan takal",
"Model takal, kad rekod dan kertas poster"),
}

# Crosswalk evidence: audits/sains_y3_dskp_sp_crosswalk_20261106.json.
# These three SP are absent as primary records; candidate coverage is added
# inside existing PdP for review only, not as invented extra lesson numbers.
# The pairing and book pages remain academically unapproved (HOLD).
INTEGRATED_SP_DRAFT = {
    "3.2.1": {
        "sp": "3.2.5",
        "teacher": "meminta laporan pemerhatian hasil pengelasan kelas makanan",
        "pupil": "menulis jadual berlabel dan menyampaikan dua dapatan tentang kelas makanan",
        "pbd": "Jadual dan laporan pemerhatian kelas makanan dengan dua dapatan",
    },
    "3.3.1": {
        "sp": "3.3.3",
        "teacher": "menyoal tentang makanan yang tidak diperlukan badan selepas proses pencernaan",
        "pupil": "merumus bahan yang tidak digunakan badan dan cara sisa disingkirkan",
        "pbd": "Rumusan makanan tidak diperlukan badan berpandukan rajah pencernaan",
    },
    "3.3.2": {
        "sp": "3.3.4",
        "teacher": "meminta komunikasi pemerhatian tentang laluan dan proses pencernaan",
        "pupil": "melakar laluan makanan berlabel lalu menerangkan pemerhatian kepada pasangan",
        "pbd": "Lakaran pencernaan berlabel dan penerangan pemerhatian yang tepat",
    },
}

def source_ledgers():
    p=json.loads(LEDGER.read_text(encoding="utf-8"))
    f=json.loads(FIXES.read_text(encoding="utf-8"))
    bycode={item["pdp_code"]:item for item in p["items"]}
    fixes={item["pdp_code"]:item for item in f["changes"]}
    if len(bycode)!=45 or len(fixes)!=12 or len(BANK)!=45:
        raise RuntimeError("Science source ledger changed unexpectedly")
    if {x["sp_code"] for x in bycode.values()}!=set(BANK):
        raise RuntimeError("Missing or extra SP activity")
    return bycode,fixes

def adapt_rows(state, original):
    """Never mutate original RPH rows; reject unproven subject/year/code/SP."""
    if not isinstance(state,dict) or not isinstance(original,dict):
        return original
    if state.get("subject")!="Sains" or str(state.get("year"))!="Tahun 3":
        return original
    code=str(state.get("pdp_sequence_code") or "").strip()
    sp=str(state.get("sp_code") or "").strip()
    year=str(state.get("year_label") or state.get("year") or "")
    if year!="Tahun 3":
        return original
    pages,fixes=source_ledgers()
    item=pages.get(code)
    if not item or item["sp_code"]!=sp or item["release"]!="HOLD":
        return original
    if not re.fullmatch(r"SCI-Y3-PDP-\d{3}",code):
        return original
    if str(state.get("sk_code") or "")!=sp.rsplit(".",1)[0]:
        return original
    if item.get("visual_layout_check")!="PENDING":
        return original  # strict gate: release manifest must be implemented separately
    label=item["source_pdp_title_unverified"]
    if code in fixes:
        change=fixes[code]
        if change["sp_code"]!=sp or change["original_title"]!=label:
            return original
        label=change["ds_kpm_official_sp_text"]
    hook,a1,p1,a2,p2,pbd,materials=BANK[sp]
    extra=INTEGRATED_SP_DRAFT.get(sp)
    # Numbered actions start on separate lines; keep two distinct activities.
    main=(f"Aktiviti 1 — Penerokaan: {hook}\n"
          f"1. Guru {a1}.\n"
          f"2. Murid {p1}.\n\n"
          f"Aktiviti 2 — Aplikasi dan PBD\n"
          f"1. Guru {a2}.\n"
          f"2. Murid {p2}.")
    if extra:
        main+=(f"\n3. Guru {extra['teacher']}.\n"
               f"4. Murid {extra['pupil']}.")
    all_sp=sp+((", "+extra["sp"]) if extra else "")
    all_pbd=pbd+(("; "+extra["pbd"]) if extra else "")
    page_text=", ".join(str(x) for x in item["printed_book_page_candidates"])
    updated=dict(original)
    updated.update({
        "TAJUK":label,
        "STANDARD KANDUNGAN":sp.rsplit(".",1)[0],
        "STANDARD PEMBELAJARAN":all_sp,
        "OBJEKTIF PEMBELAJARAN":f"Pada akhir PdP, murid dapat {label[0].lower()+label[1:].rstrip('.')}.",
        "KRITERIA KEJAYAAN":all_pbd+".",
        "PENGETAHUAN SEDIA ADA":f"Murid berkongsi pengalaman berkaitan {hook.lower()}.",
        "SET INDUKSI":f"Guru menunjukkan {hook.lower()}; murid menyatakan satu ramalan/pemerhatian awal.",
        "AKTIVITI UTAMA":main,
        "PENTAKSIRAN":all_pbd+". Guru menyemak hasil individu atau pasangan.",
        "PENUTUP":f"Murid menyatakan satu dapatan tentang {hook.lower()}; guru merumus kaitan dengan SP {sp}.",
        "BAHAN BANTU MENGAJAR":f"{materials}. Buku Teks Sains Tahun 3, halaman bercetak {page_text} (petunjuk sumber; semak sebelum cetak).",
        "PEMULIHAN / PENGAYAAN":"Pemulihan: guru membimbing dengan kad/objek berlabel. Pengayaan: murid menjelaskan bukti tambahan daripada tugasan.",
    })
    return updated
