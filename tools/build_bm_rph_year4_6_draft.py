#!/usr/bin/env python3
"""Bina RPH Standalone BM T4–T6 daripada RPT 2027 dalam staging.

Tidak memadam RPH sedia ada, tidak mengubah DB/bot, dan tidak meluluskan READY.
RPT 2026 menjadi rujukan susunan dan DSKP menjadi semakan asas kod SP.
Rujukan BT hanya calon halaman; BA/PKJR tidak diteka.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
RPT_ROOT = ROOT / "rpt_2027/bahasa_melayu/keluaran_format_english"
RPH_ROOT = ROOT / "rph_standalone/bahasa_melayu"
COUNTS = {4: 165, 5: 166, 6: 165}
SOURCES = {
    4: ("https://docs.google.com/document/d/103e8N7kZvR_tPr9TLy8TaM8Yz6VMeoQ-/edit",
        "https://drive.google.com/file/d/1gDBc4hMH3MBT9EJNzU15BB9C6dM3aTHb/view"),
    5: ("https://docs.google.com/document/d/1q0vWe8ydZonJsAohVEe121u-0A2xMrg7/edit",
        "https://drive.google.com/file/d/1YuH-xfZSJCbCVAoJUYprx4Uu5Vq8hAFO/view"),
    6: ("https://docs.google.com/document/d/1g0HR5PGuW9CMQFJZLcDbXUD0qZwlMJK1/edit",
        "https://drive.google.com/file/d/1QxObljj4PX2BikO6LYGGoVPh_-xw5Fjo/view")
}

def tidy(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).replace("PdP/PdP", "PdP")

def parse_rpt(year: int):
    path = RPT_ROOT / f"RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF.md"
    content = path.read_text(encoding="utf-8")
    rows = []
    current_week = None
    for line in content.splitlines():
        m = re.match(r"###\s+M(\d{2})", line)
        if m:
            current_week = int(m.group(1))
        if not re.match(r"\|\s*\*\*PdP\s+\d{3}\*\*", line):
            continue
        cells = [tidy(x) for x in line.split("|")[1:-1]]
        if len(cells) != 7:
            raise AssertionError((year, "expected 7 RPT columns", line))
        num = int(re.search(r"PdP (\d{3})", cells[0]).group(1))
        expected_id = f"BM{year}-P{num:03d}"
        assert expected_id in cells[0], (year, num, "RPT ID mismatch")
        assert current_week is not None, (year, num, "week missing")
        rows.append(dict(n=num, week=current_week, theme=cells[1], title=cells[2],
                         sk=cells[3], sp=cells[4], ref=cells[5], note=cells[6]))
    assert [r["n"] for r in rows] == list(range(1, COUNTS[year] + 1)), (year, "RPT sequence")
    return rows

def skill_plan(row: dict):
    """Spesifikasi tugasan terukur, berbeza mengikut kemahiran SP dan konteks tajuk."""
    sp = row["sp"].lower()
    title = row["title"].replace(" + PKJR", "")
    title = re.sub(r"\s*\+\s*pkjr\b", "", title, flags=re.I)
    theme = row["theme"]
    core = row["sp"].split("—", 1)[-1].strip()
    prefix = re.search(r"\b([1-5])\.\d\.\d\b", sp)
    domain = prefix.group(1) if prefix else "?"
    is_review = bool(re.search(r"\b(penilaian|pengukuhan|pemulihan|pengayaan|ulangkaji|ulang kaji)\b", title, re.I))
    context = f"teks atau ilustrasi bertajuk “{title}” dalam unit {theme}"
    prompt = f"Apakah idea, tindakan atau maklumat yang sesuai dengan tajuk “{title}”?"
    if domain == "1":
        if "bercerita" in sp or "menceritakan" in sp:
            focus = "Menceritakan bahan dengan urutan, sebutan dan intonasi sesuai."
            obj = "Murid menyampaikan semula sekurang-kurangnya tiga isi mengikut urutan dengan sebutan jelas."
            a1 = ("Susun isi sebelum bercerita",
                  f"Membimbing bacaan atau tontonan {context}; guru menyoal perkara awal, tengah dan akhir tanpa memberikan jawapan.",
                  "Mengesan tiga isi atau peristiwa daripada bahan sebenar dan menyusun kad isi secara berkumpulan.")
            a2 = ("Ceritakan kepada pasangan",
                  "Memberi contoh pembuka dan penanda urutan, kemudian memantau penyampaian lisan secara berpasangan.",
                  f"Menceritakan semula tiga isi daripada “{title}” menggunakan ayat sendiri dan penanda urutan.")
            assess = "Senarai semak tiga isi tersusun, suara jelas dan sebutan/intonasi yang sesuai."
        elif "bertutur" in sp or "bersoal jawab" in sp or "menjelas" in sp or "berhujah" in sp:
            focus = "Menyampaikan pendapat atau maklumat dengan alasan dan bahasa yang santun."
            obj = "Murid menyatakan dua idea berkaitan bahan dan satu alasan yang munasabah secara lisan."
            a1 = ("Kumpul idea dan alasan",
                  f"Mempamerkan {context}; mengemukakan soalan terbuka dan membezakan fakta daripada pendapat.",
                  "Menyenaraikan dua idea utama dan satu bukti atau alasan berdasarkan bahan yang benar-benar dilihat.")
            a2 = ("Dialog atau pembentangan ringkas",
                  "Menyusun perbincangan berpasangan, mengingatkan giliran bercakap dan bertanya soalan susulan.",
                  f"Menerangkan pendapat tentang “{title}”, memberi alasan dan merespons satu soalan rakan.")
            assess = "Rekod dua isi tepat, satu alasan relevan dan kesantunan berkomunikasi."
        else:
            focus = "Mendengar, memahami dan memberikan respons terhadap ujaran."
            obj = "Murid mengenal pasti tiga maklumat daripada ujaran dan memberi dua respons yang tepat."
            a1 = ("Dengar dan kesan kata kunci",
                  f"Membaca dua kali petikan atau ujaran daripada {context}; pertama tanpa teks, kedua untuk semakan.",
                  "Mendengar, mencatat tiga kata kunci dan memadankan maklumat dengan situasi yang dirujuk.")
            a2 = ("Berikan respons lisan",
                  "Mengajukan tiga soalan berasaskan ujaran dan menunjukkan contoh respons santun tanpa memberikan jawapan sebenar.",
                  f"Memberikan dua respons lisan tentang “{title}” dan menyebut semula maklumat secara bergilir.")
            assess = "Catatan tiga maklumat didengar dan dua respons tepat melalui senarai semak."
    elif domain == "2":
        if "multimedia" in sp or "grafik" in sp or "rumusan" in sp or "ramalan" in sp or "menaakul" in sp:
            focus = "Menaakul maklumat tersurat dan tersirat daripada bahan."
            obj = "Murid mengenal pasti tiga maklumat dan menghasilkan satu inferens, ramalan atau rumusan bersumberkan bahan."
            a1 = ("Baca grafik atau bahan",
                  f"Membimbing murid meneliti {context} dan menunjukkan cara mengenal pasti tajuk, label dan fakta.",
                  "Mencatat tiga maklumat yang dapat disahkan daripada teks, rajah atau gambar sebenar.")
            a2 = ("Huraikan bukti",
                  "Mencabar murid membezakan bukti daripada andaian dengan dua soalan mengapa atau bagaimana.",
                  f"Menghasilkan satu inferens, ramalan atau rumusan tentang “{title}” disertakan bukti daripada bahan.")
            assess = "Semak tiga fakta bersumber dan satu penaakulan yang disokong bukti."
        elif "mempersembah" in sp or "gaya" in sp or "mengapresiasi" in sp:
            focus = "Membaca dan mempersembahkan bahan dengan gaya dan penghayatan."
            obj = "Murid menjelaskan dua isi atau nilai dan menyampaikan satu petikan dengan gaya bersesuaian."
            a1 = ("Kenal isi dan nilai",
                  f"Memimpin pembacaan {context}, menandai dua isi atau nilai daripada petikan asal.",
                  "Membaca secara berpasangan, mencatat dua isi atau nilai dan memilih petikan pendek yang sesuai.")
            a2 = ("Persembahan bacaan",
                  "Memodelkan satu teknik intonasi dan meminta pasangan memberi maklum balas berdasarkan rubrik mudah.",
                  f"Membaca petikan “{title}” dengan sebutan, intonasi dan gaya yang sesuai serta menerangkan pilihannya.")
            assess = "Rubrik dua isi/nilai serta persembahan sebutan, intonasi dan penghayatan."
        else:
            focus = "Membaca, memahami dan menjelaskan maklumat dalam teks."
            obj = "Murid mengenal pasti tiga maklumat daripada teks dan menjawab dua soalan pemahaman dengan bukti."
            a1 = ("Bacaan berfokus",
                  f"Membimbing bacaan berpandu {context}; menunjukkan cara menandakan maklumat penting.",
                  "Membaca petikan asal, menggariskan tiga maklumat dan menulis makna kata baharu berdasarkan konteks.")
            a2 = ("Soal jawab berasaskan bukti",
                  "Mengemukakan satu soalan tersurat dan satu tersirat; meminta murid menunjukkan ayat penyokong.",
                  f"Menjawab dua soalan tentang “{title}” dan menyatakan bahagian teks yang menyokong jawapan.")
            assess = "Semak tiga maklumat dan dua jawapan yang disokong bukti daripada teks."
    elif domain == "3":
        if "mengedit" in sp or "memurnikan" in sp:
            focus = "Mengedit ejaan, tanda baca dan struktur ayat mengikut konteks."
            obj = "Murid mengesan dan membetulkan sekurang-kurangnya empat kesalahan bahasa dalam teks latihan."
            a1 = ("Jejaki kesalahan",
                  f"Menyediakan satu perenggan latihan ciptaan guru berkaitan “{title}” yang mengandungi beberapa kesalahan terancang.",
                  "Membaca perenggan, menandakan empat kesalahan serta menamakan jenis kesalahan.")
            a2 = ("Edit dan semak silang",
                  "Memimpin pembetulan ejaan, tanda baca atau struktur ayat dan mengedar senarai semak rakan.",
                  "Menulis semula perenggan yang dibaiki dan menyemak kerja pasangan mengikut empat kriteria.")
            assess = "Banding sebelum/selepas; sekurang-kurangnya empat pembetulan yang dapat dijelaskan."
        elif "imlak" in sp:
            focus = "Menulis semula teks yang diimlakkan dengan ejaan dan tanda baca tepat."
            obj = "Murid menulis empat ayat imlak berkaitan tema dengan sekurang-kurangnya tiga ayat tepat."
            a1 = ("Dengar dan pecahkan frasa",
                  f"Membacakan empat ayat latihan ciptaan guru berkaitan “{title}”, pada kadar sesuai; bahan asal menjadi konteks.",
                  "Mendengar tanpa menulis dahulu, mengenal pasti frasa dan tanda baca yang didengar.")
            a2 = ("Tulis dan sunting imlak",
                  "Mengimlak ayat secara berperingkat dan membaca sekali lagi untuk pemeriksaan akhir.",
                  "Menulis empat ayat, menyemak ejaan dan membetulkan huruf besar serta tanda baca.")
            assess = "Kira ketepatan tiga daripada empat ayat imlak dan pembetulan kendiri."
        elif "berangkai" in sp or "mekanis" in sp:
            focus = "Menulis kemas menggunakan tulisan berangkai."
            obj = "Murid menulis empat ayat atau satu rangkap ringkas dengan tulisan berangkai yang jelas."
            a1 = ("Perhatikan bentuk huruf",
                  f"Memilih empat ayat atau rangkap yang sesuai daripada {context} dan menunjukkan sambungan huruf.",
                  "Meneliti sambungan huruf, menyalin satu contoh dan membetulkan bentuk yang tidak tepat.")
            a2 = ("Salin dan semak",
                  "Membimbing posisi tulisan dan memberi maklum balas ringkas ketika murid menulis.",
                  f"Menulis semula empat ayat berkaitan “{title}” dan menandakan sambungan huruf yang baik.")
            assess = "Semak empat ayat dari segi kebolehbacaan, sambungan huruf dan kekemasan."
        elif "mencatat" in sp or "menganalisis" in sp or "maklumat" in sp:
            focus = "Mencatat dan menyusun maklumat penting secara jelas."
            obj = "Murid memilih tiga maklumat tepat dan menyusunnya dalam jadual atau peta pemikiran."
            a1 = ("Kumpul data daripada bahan",
                  f"Memimpin pemerhatian atau bacaan {context}; menunjukkan perbezaan isi utama dan butiran.",
                  "Menulis tiga isi bersumber daripada bahan pada kad atau nota ringkas.")
            a2 = ("Bina peta atau jadual",
                  "Memberi contoh dua lajur kategori dan meminta murid menjelaskan hubungan antaraisi.",
                  f"Memindahkan tiga isi tentang “{title}” ke dalam jadual dan membina satu ayat rumusan.")
            assess = "Semak ketepatan tiga isi, pengelasan dan satu rumusan."
        elif "karangan" in sp or "perenggan" in sp or "penulisan" in sp:
            focus = "Merancang dan menghasilkan perenggan yang tersusun."
            obj = "Murid menghasilkan satu perenggan sekurang-kurangnya lima ayat dengan isi dan penanda wacana sesuai."
            a1 = ("Rancang kerangka",
                  f"Menunjukkan bahan bertema “{title}” dan membimbing peta isi: idea utama, dua huraian dan contoh.",
                  "Melakar kerangka satu idea utama, dua huraian dan satu contoh yang berkaitan dengan unit.")
            a2 = ("Tulis dan tambah baik",
                  "Memodelkan ayat topik dan menyemak struktur perenggan tanpa menulis jawapan murid.",
                  f"Menulis perenggan lima ayat tentang “{title}”, menggunakan penanda wacana dan menyunting satu ayat.")
            assess = "Semak lima ayat, kesinambungan isi, ejaan dan satu pembetulan kendiri."
        else:
            focus = "Membina jawapan atau ayat yang bermakna berasaskan bahan."
            obj = "Murid menghasilkan tiga ayat lengkap serta satu alasan atau huraian yang berkaitan dengan bahan."
            a1 = ("Kenal pasti isi untuk ditulis",
                  f"Membimbing penelitian {context} dan menunjukkan beza isi dengan contoh.",
                  "Memilih tiga isi relevan dan menyebut ayat lengkap secara berpasangan sebelum menulis.")
            a2 = ("Bina jawapan beralasan",
                  "Memberi rangka isi–huraian–contoh dan memantau ejaan serta tanda baca.",
                  f"Menulis tiga ayat tentang “{title}” dan menambah satu ayat huraian sendiri.")
            assess = "Semak tiga ayat lengkap, satu huraian dan ketepatan bahasa."
    elif domain == "4":
        if "pantun" in sp or "lagu" in sp or "puisi" in sp or "melafazkan" in sp or "menyanyikan" in sp:
            focus = "Menghayati bahasa indah melalui karya sastera."
            obj = "Murid melafazkan satu petikan dengan gaya sesuai dan menerangkan dua ungkapan atau nilai."
            a1 = ("Tafsir karya",
                  f"Memimpin pembacaan karya yang dirujuk melalui {context} dan membimbing maksud dua ungkapan.",
                  "Membaca petikan dan menjelaskan maksud dua ungkapan dengan bahasa sendiri.")
            a2 = ("Latih persembahan",
                  "Menunjukkan contoh jeda, intonasi dan gerak laku yang santun bagi petikan tersebut.",
                  "Melafaz atau mempersembahkan petikan secara berkumpulan dengan irama dan intonasi sesuai.")
            assess = "Maklum balas terhadap kefahaman dua ungkapan dan persembahan bahasa; bukan TP Seni Bahasa berasingan."
        else:
            focus = "Menggunakan bahasa indah dan santun dalam dialog atau penceritaan."
            obj = "Murid menggunakan dua ungkapan atau peribahasa yang sesuai dalam satu dialog ringkas."
            a1 = ("Kenal bahasa indah",
                  f"Meneliti {context} bersama murid dan membincangkan fungsi dua ungkapan santun atau peribahasa.",
                  "Menjelaskan maksud dua ungkapan berdasarkan konteks dan mencadangkan situasi yang sesuai.")
            a2 = ("Lakonkan dialog",
                  "Membimbing pasangan membina dialog enam giliran tanpa menyalin teks asal bulat-bulat.",
                  f"Melakonkan dialog tentang “{title}” dengan dua ungkapan santun atau peribahasa.")
            assess = "Perhatikan penggunaan dua ungkapan tepat dalam dialog dan respons lisan; PBD bersepadu."
    elif domain == "5":
        subject = ("kata nama" if "kata nama" in sp else "kata ganti nama" if "kata ganti nama" in sp
                   else "kata kerja" if "kata kerja" in sp else "kata adjektif" if "kata adjektif" in sp
                   else "kata tugas" if "kata tugas" in sp else "imbuhan" if "imbuh" in sp
                   else "pembentukan kata" if "kata" in sp else "struktur ayat")
        focus = f"Memahami dan menggunakan {subject} dalam konteks ayat."
        obj = f"Murid mengenal pasti tiga contoh {subject} dan membina dua ayat yang menggunakannya dengan tepat."
        a1 = (f"Kenal pasti {subject}",
              f"Memilih ayat daripada {context}; meminta murid mengesan contoh {subject} berdasarkan fungsi, bukan rupa perkataan sahaja.",
              f"Mencatat tiga contoh {subject} daripada bahan yang dibaca dan menjelaskan fungsinya.")
        a2 = ("Bina ayat berkonteks",
              "Mengedar kad kata atau frasa ciptaan guru dan membimbing pembinaan ayat sesuai tatabahasa.",
              f"Membina dua ayat baharu bertema “{title}” menggunakan {subject}; bertukar hasil dengan pasangan untuk semakan.")
        assess = f"Senarai semak tiga contoh {subject}, fungsi yang tepat dan dua ayat gramatis."
    else:
        raise ValueError(f"Cannot classify SP: {row['sp']}")
    if is_review:
        a2 = ("Aplikasi susulan atau pentaksiran",
              "Menggunakan set soalan baharu ciptaan guru yang menilai SP sama tanpa memperkenalkan kod standard tambahan.",
              f"Menyelesaikan tugasan berbeza daripada sesi pertama tentang “{title}” dan membaiki sekurang-kurangnya satu kesilapan.")
        assess += " Catat perkembangan berbanding respons sebelum ini; bukan SP baharu."
    return dict(focus=focus, obj=obj, a1=a1, a2=a2, assess=assess, prompt=prompt, domain=domain)

def render(year: int, row: dict, repeat_count: int):
    n = row["n"]
    sk, sp, title, theme, ref, note = (row[k] for k in ("sk","sp","title","theme","ref","note"))
    plan = skill_plan(row)
    pkjr = bool(re.search(r"\bPKJR\b", title + " " + note, re.I))
    risky = pkjr or bool(re.search(r"\bSEMAK PENGULANGAN\b", note, re.I))
    status = "HOLD" if risky else "DRAF"
    rationale = ("Perlu padanan modul BAM/BPG dan HP PKJR yang sah; aktiviti PKJR rasmi tidak direka." if pkjr else
                 "RPT menandakan pengulangan yang perlu semakan akademik." if risky else
                 "Rujukan buku dan penerimaan akademik belum disahkan sepenuhnya.")
    suffix = " Sesi susulan memerlukan tugasan berbeza." if repeat_count > 1 else ""
    a1_title, a1_teacher, a1_pupil = plan["a1"]
    a2_title, a2_teacher, a2_pupil = plan["a2"]
    refs = ref if ref and ref != "—" else "Halaman buku belum disahkan"
    return f"""# RPH Standalone Bahasa Melayu Tahun {year} — PdP {n:03d}

**ID:** BM{year}-P{n:03d}  **Minggu RPT:** M{row['week']:02d} (cadangan; tarikh ikut negeri dan jadual sebenar)  
**Tema / Unit:** {theme}  
**Tajuk:** {title}  
**Standard Kandungan (SK):** {sk}  
**Standard Pembelajaran (SP):** {sp}  
**Rujukan RPT 2027:** {refs} — *halaman calon daripada RPT 2026; sahkan dengan Buku Teks SK asal*.  
**Buku Aktiviti:** Tiada halaman/latihan BA yang disahkan bagi PdP ini; gunakan latihan guru, jangan reka halaman.  
**Masa:** 60 minit cadangan (guru boleh laras).  
**Fokus:** {plan['focus']}  
**Objektif:** Pada akhir PdP, {plan['obj'][0].lower() + plan['obj'][1:]}  
**Kriteria kejayaan:** Murid mencapai bilangan bukti yang dinyatakan dalam objektif dan boleh menjelaskan satu pembetulan.  
**BBM:** Buku Teks pada halaman RPT (jika sepadan), kad kata/ayat atau gambar bertema {theme}, papan putih, buku latihan dan senarai semak PBD.

## Set induksi — 5 minit
**Guru:** Menunjukkan tajuk “{title}” dan bahan sumber, mengemukakan soalan rangsangan: “{plan['prompt']}”  
**Murid:** Berkongsi pengetahuan sedia ada, menyatakan satu jangkaan dan menghubungkannya dengan unit.

## Aktiviti 1 — {a1_title} (15 minit)
**Guru:** {a1_teacher}  
**Murid:** {a1_pupil}

## Aktiviti 2 — {a2_title} (20 minit)
**Guru:** {a2_teacher}  
**Murid:** {a2_pupil}

## Pengukuhan dan penilaian PBD — 15 minit
**Guru:** {plan['assess']} Membimbing kumpulan sokongan dengan rangka atau kad petunjuk; murid mahir menambah satu contoh atau justifikasi.  
**Murid:** Menyerahkan atau mempersembahkan hasil individu, menerima maklum balas dan membuat satu pembetulan.

## Penutup — 5 minit
**Guru:** Merumus kemahiran {plan['focus'][0].lower()+plan['focus'][1:]} dan meminta contoh aplikasi dalam kehidupan harian.  
**Murid:** Menyatakan satu kemahiran yang dikuasai dan satu cara menggunakannya.

**Refleksi guru:** ____ / ____ murid mencapai objektif; tindakan susulan: ____________________.  
**Status semakan:** {status} — {rationale}{suffix}  
**Jejak sumber:** RPT BM SK 2026 → RPT BM 2027 → calon RPH. Teks SK/SP dipetik daripada matriks RPT, belum dianggap pengesahan akademik penuh. **Tidak READY; tidak untuk penerbitan bot.**  
**Nota RPT:** {note}
"""

def build():
    audit = []
    for year, expected in COUNTS.items():
        rows = parse_rpt(year)
        out_dir = RPH_ROOT / f"year{year}"
        out_dir.mkdir(parents=True, exist_ok=True)
        seen_titles = Counter()
        created = []
        status_counts = Counter()
        weak = []
        for row in rows:
            seen_titles[row["title"].casefold()] += 1
            md = render(year, row, seen_titles[row["title"].casefold()])
            dest = out_dir / f"lesson_{row['n']:03d}.md"  # nama dalaman kekal untuk keserasian
            if dest.exists():
                raise FileExistsError(f"Refuse to overwrite existing file: {dest}")
            dest.write_text(md, encoding="utf-8")
            status = re.search(r"\*\*Status semakan:\*\* (DRAF|HOLD)", md).group(1)
            status_counts[status] += 1
            assert f"PdP {row['n']:03d}" in md and f"BM{year}-P{row['n']:03d}" in md
            assert "**Buku Aktiviti:** Tiada halaman" in md
            for heading in ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Pengukuhan dan penilaian PBD", "Penutup"):
                assert f"## {heading}" in md, (dest, heading)
            created.append(dest.name)
            if "Semak" in row["note"] or "DRAF" in row["note"] or "PENGULANGAN" in row["note"]:
                weak.append(row["n"])
        assert len(created) == expected
        source_rpt, source_dskp = SOURCES[year]
        (out_dir / "README.md").write_text(f"""# Bahasa Melayu Tahun {year} 2027 — RPH Standalone

**Status: DRAF KERJA, BUKAN READY**. Fail lengkap {expected}/{expected} (PdP 001–{expected:03d}).

- DRAF: {status_counts['DRAF']}; HOLD: {status_counts['HOLD']}; READY: 0.
- Semua RPH mempunyai guru/murid, objektif terukur, set induksi, 2 aktiviti, PBD, penutup dan refleksi.
- Halaman Buku Teks datang daripada RPT 2026 yang dipadankan kepada RPT 2027; **belum dibuktikan sah** melalui pemeriksaan semua buku asal.
- **Buku Aktiviti BM Tahun {year} belum disahkan**; tidak ada arahan atau halaman BA yang direka.
- PKJR dan sesi ulangan yang diragui ditanda HOLD. PBD Seni Bahasa secara bersepadu, bukan TP tambahan.
- RPT Tahun {year}: ../../rpt_2027/bahasa_melayu/keluaran_format_english/RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF.md
- RPT SK 2026: {source_rpt}
- DSKP BM SK Tahun {year}: {source_dskp}

Pintu READY belum lulus: ketepatan buku asal, teks dan subkod DSKP penuh, padanan BA, BAM/BPG PKJR, pengulangan, tarikh/cuti negeri 2027, kebolehbacaan A4 satu halaman, ujian runtime serta kelulusan guru.

Ini bukan pemasangan produksi; data lama, main, DB, Telegram dan Web tidak diubah.
""", encoding="utf-8")
        record = dict(year=year,expected=expected,files=len(created),DRAF=status_counts["DRAF"],
                      HOLD=status_counts["HOLD"],READY=0,flags_for_human_review=len(weak),
                      verified_BA=False,verified_BT_full=False,verified_DSKP_text=False)
        audit.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    assert sum(x["files"] for x in audit) == 496
    result_path = ROOT / "rpt_2027/bahasa_melayu/AUDIT_RPH_BM_T4_T6_BATCH_20261104.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps({"status":"DRAF_NOT_PUBLISHED","date":"2026-11-04","records":audit},
                                     indent=2,ensure_ascii=False)+"\n", encoding="utf-8")

if __name__ == "__main__":
    build()
