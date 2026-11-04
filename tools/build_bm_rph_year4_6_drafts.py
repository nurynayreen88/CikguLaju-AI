#!/usr/bin/env python3
"""Bina RPH BM SK T4–T6 secara non-destruktif daripada baris RPT 2027 sedia ada.

Ini melengkapkan fail calon RPH sahaja, BUKAN audit sumber buku/kelulusan READY.
"""
from pathlib import Path
import csv, io, re, json, hashlib
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"rpt_2027/bahasa_melayu/keluaran_format_english"
DEST=ROOT/"rph_standalone/bahasa_melayu"
COUNTS={4:165,5:166,6:165}

def norm(s):
    return re.sub(r"\s+"," ",s.strip().replace("**","").replace(" • ","; "))

def rows(year):
    file=BASE/f"RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF.md"
    txt=file.read_text(encoding="utf-8")
    out=[]
    week=None
    for line in txt.splitlines():
        m=re.match(r"### (M\d\d)\b",line)
        if m:week=m.group(1)
        if not line.startswith("| **PdP "):continue
        parts=[norm(x) for x in line.strip().strip("|").split("|")]
        if len(parts)!=7:raise ValueError((year,week,len(parts),line[:250]))
        match=re.fullmatch(r"PdP (\d{3}) \((BM\d-P\d{3})\)",parts[0])
        if not match:raise ValueError((year,"ID",parts[0]))
        no=int(match.group(1))
        out.append(dict(no=no,id=match.group(2),week=week,unit=parts[1],title=parts[2],sk=parts[3],sp=parts[4],books=parts[5],note=parts[6]))
    expected=COUNTS[year]
    assert [x["no"] for x in out]==list(range(1,expected+1)),(year,len(out))
    assert all(x["week"] and x["sp"] not in ("","—") and x["title"] for x in out)
    return out

def skill(sp,sk,note):
    d=(sp+" "+sk+" "+note).lower()
    if "mendengar" in d or "bertutur" in d or sp.startswith(("1.",)):
        return "lisan"
    if "membaca" in d or "menaakul" in d or sp.startswith("2."):
        return "bacaan"
    if "menulis" in d or "penulisan" in d or sp.startswith("3."):
        return "tulisan"
    if "sajak" in d or "pantun" in d or "puisi" in d or "lagu" in d or sp.startswith("4."):
        return "seni"
    if "kata " in d or "ayat" in d or sp.startswith("5."):
        return "tatabahasa"
    return "kefahaman"

def make_steps(x):
    title=x["title"].replace(" + PKJR","").replace("+ PKJR","").strip()
    focus=skill(x["sp"],x["sk"],x["note"])
    desc=x["sp"].split(" — ",1)[-1].strip().rstrip(".")
    if len(desc)>160:desc=desc[:157].rsplit(" ",1)[0]+"…"
    if focus=="lisan":
        obj=f"Murid dapat memberikan sekurang-kurangnya tiga respons lisan yang relevan tentang '{title}' mengikut kemahiran {x['sp'].split(' — ')[0]}."
        a=("Membacakan/menyampaikan maklumat atau dialog berpandukan bahan bertajuk '"+title+"' dan meminta murid mengenal pasti isi serta sebutan penting.",
           "Mendengar/meneliti bahan '"+title+"'; mencatat tiga maklumat dan menjawab soalan guru secara lisan.")
        b=("Mengendalikan simulasi komunikasi berpasangan berdasarkan situasi sebenar dalam '"+title+"'; mengemukakan soalan susulan dan membetulkan sebutan/laras bahasa.",
           "Berbual atau memainkan peranan berpandukan tajuk; memberikan tiga respons yang jelas dan sopan serta membaiki jawapan hasil maklum balas.")
        assessment="Senarai semak tiga respons lisan: tepat, jelas dan sesuai konteks."
    elif focus=="bacaan":
        obj=f"Murid dapat membaca petikan bertajuk '{title}' dengan sesuai dan mengenal pasti sekurang-kurangnya tiga maklumat/idea yang disokong teks."
        a=("Menunjukkan bahagian bacaan '"+title+"' pada sumber yang dinyatakan, memodelkan intonasi atau strategi mencari maklumat tersurat/tersirat.",
           "Membaca petikan '"+title+"' dan menanda sekurang-kurangnya tiga isi atau bukti daripada bahan.")
        b=("Membimbing pembacaan berpasangan; meminta murid menjawab soalan isi, sebab dan bukti berdasarkan petikan, bukan berdasarkan tekaan.",
           "Menyatakan idea utama dan dua maklumat sokongan, kemudian menjawab soalan dengan merujuk bukti dalam petikan.")
        assessment="Bacaan dan tiga jawapan pemahaman disemak berdasarkan teks asal."
    elif focus=="tulisan":
        obj=f"Murid dapat menghasilkan sekurang-kurangnya tiga ayat berkaitan '{title}' yang menepati kemahiran penulisan dalam SP."
        a=("Menunjukkan contoh ayat/perenggan yang relevan dengan '"+title+"' dan memodelkan langkah menyusun isi serta menulis mengikut "+desc+".",
           "Mengenal pasti kata kunci dan membina rangka/ayat berdasarkan maklumat tajuk '"+title+"'.")
        b=("Membimbing penulisan individu berdasarkan gambar atau petikan sumber; meminta semakan kandungan, tanda baca dan ejaan.",
           "Menulis tiga ayat atau perenggan pendek yang bersesuaian dengan SP, kemudian menyuntingnya berdasarkan senarai semak.")
        assessment="Hasil penulisan: isi menepati tajuk/SP, ayat jelas dan ejaan/tanda baca betul."
    elif focus=="seni":
        obj=f"Murid dapat mempersembahkan satu respons atau hasil seni bahasa yang berkaitan '{title}' serta menjelaskan maksudnya dengan tepat."
        a=("Memperdengarkan atau membacakan contoh karya dalam '"+title+"'; memimpin pengesanan ungkapan, maksud dan ciri bahasa.",
           "Membaca/mendengar karya berkaitan '"+title+"' dan menandakan dua ungkapan atau unsur bahasa yang bermakna.")
        b=("Membimbing persembahan/hasil seni bahasa mengikut jenis karya sebenar dalam sumber dan menghubungkannya dengan situasi tema.",
           "Melafazkan, bercerita, menyampaikan dialog atau menghasilkan respons kreatif sesuai SP; menjelaskan maksud dua ungkapan.")
        assessment="Semakan respons/persembahan: sebutan, makna dan penggunaan bahasa mengikut SP."
    elif focus=="tatabahasa":
        obj=f"Murid dapat menggunakan sekurang-kurangnya empat contoh bentuk bahasa yang ditetapkan SP dalam ayat berkaitan '{title}'."
        a=("Menunjukkan ayat daripada bahan '"+title+"'; membimbing murid mengenal pasti unsur bahasa yang dinyatakan dalam "+desc+".",
           "Mengenal pasti dan mengelaskan empat contoh bentuk bahasa daripada tajuk '"+title+"'.")
        b=("Memberikan tugasan bina ayat bertema '"+title+"' menggunakan bentuk bahasa sasaran; membimbing pembetulan mengikut konteks.",
           "Membina empat ayat yang mengandungi unsur bahasa sasaran dan menyunting contoh yang kurang tepat.")
        assessment="Empat ayat disemak: pilihan perkataan betul dan penggunaan sesuai konteks."
    else:
        obj=f"Murid dapat menyatakan tiga maklumat tepat tentang '{title}' mengikut SP."
        a=("Memperkenalkan bahan '"+title+"' dan memodelkan kemahiran dalam SP menggunakan contoh daripada sumber.",
           "Memerhati dan mengenal pasti tiga maklumat berkaitan '"+title+"'.")
        b=("Memimpin tugasan berpasangan menggunakan maklumat daripada bahan sumber serta membuat pembetulan.",
           "Menghasilkan respons bertulis/lisan dan membandingkannya dengan petikan asal.")
        assessment="Tiga respons dipadankan kepada SP dan kandungan bahan."
    return obj,a,b,assessment,focus

def render(year,x,prev=None):
    n=x["no"]
    obj,a,b,assess,focus=make_steps(x)
    topic=x["title"].replace("+ PKJR","").strip()
    pkjr=bool(re.search(r"\bPKJR\b",x["title"]+" "+x["note"],re.I))
    duplicate=bool("PENGULANGAN" in x["note"].upper()) or (prev is not None and prev["title"]==x["title"])
    has_ba=bool(re.search(r"\bBA\d?\b",x["books"],re.I))
    note_pkjr=("**Catatan PKJR:** RPT menyebut PKJR. Jangan mencipta HP/BAM atau melaksanakan penilaian PKJR sebagai hasil rasmi sebelum modul, aktiviti dan halaman disahkan.\n\n" if pkjr else "")
    note_repeat=("**Catatan sesi susulan:** Tajuk berulang dalam sumber; bezakan objektif sebenar daripada PdP terdahulu melalui semakan guru, bukan reka SP baharu.\n\n" if duplicate else "")
    caveat=("**Buku Aktiviti:** RPT tidak memberikan halaman BA yang disahkan untuk PdP ini. Jangan menyuruh murid membuka BA pada halaman yang diteka.\n\n" if not has_ba else "**Buku Aktiviti:** Rujukan BA masih perlu disemak dengan naskhah asal sebelum latihan ditetapkan.\n\n")
    status="HOLD_SEMAKAN_SUMBER" if pkjr or duplicate or not has_ba else "DRAF_SEMAKAN_AKADEMIK"
    materials="Buku Teks/bahan asal berdasarkan rujukan RPT, papan putih, kad perkataan/soalan bertema, buku latihan dan senarai semak PBD."
    return f"""# RPH Standalone Bahasa Melayu Tahun {year} — PdP {n:03d}

**ID:** {x['id']}  
**Minggu RPT 2027:** {x['week']} (tarikh PdP sebenar ditentukan oleh jadual sekolah)  
**Tema/Unit:** {x['unit']}  
**Tajuk aktiviti:** {x['title']}  
**Standard Kandungan (SK):** {x['sk']}  
**Standard Pembelajaran (SP):** {x['sp']}  
**Sumber BT/BA seperti RPT (BELUM disahkan menyeluruh):** {x['books']}  
**Fokus:** {focus} — {topic}  
**Objektif PdP:** {obj}  
**Bahan:** {materials}  
**Masa cadangan:** 60 minit (laras mengikut jadual kelas).

## Set induksi (5 minit)
**Guru:** Memaparkan judul/ilustrasi '{topic}' daripada bahan yang dinyatakan, meminta ramalan kandungan berdasarkan dua petunjuk dan mengaitkan dengan tema {x['unit']}.  
**Murid:** Membuat ramalan berdasarkan tajuk atau ilustrasi serta memberikan satu contoh pengalaman/perkataan berkaitan.

## Aktiviti 1 — Teliti sumber dan contoh kemahiran (15 minit)
**Guru:** {a[0]}  
**Murid:** {a[1]}

## Aktiviti 2 — Aplikasi berpandu {focus} (20 minit)
**Guru:** {b[0]}  
**Murid:** {b[1]}

## Pengukuhan / Pentaksiran Bilik Darjah (15 minit)
**Guru:** Menilai berdasarkan SP ({x['sp']}) menggunakan bukti hasil tugasan: {assess} Memberikan satu maklum balas khusus untuk pembetulan.  
**Murid:** Menunjukkan hasil/menjawab tugasan, membetulkan sekurang-kurangnya satu kesilapan dan menyatakan bukti daripada bahan.

## Penutup (5 minit)
**Guru:** Merumuskan kemahiran {focus} yang digunakan dalam '{topic}' dan menghubungkannya dengan SP tanpa menambah standard baharu.  
**Murid:** Menyebut satu perkara dipelajari dan satu contoh daripada tugasan.

**Nota RPT asal:** {x['note']}

{note_pkjr}{note_repeat}{caveat}**Status QA:** {status} — fail DRAF kandungan calon, belum lulus audit lengkap DSKP, BT/BA, pemetaan PKJR, cetakan A4 dan ujian Telegram.  
**Kawalan:** Bukan READY. Jangan aktifkan automatik di bot; kekalkan sumber asal dan buat semakan satu demi satu sebelum penerbitan.
"""

def main():
    manifest={"subject":"Bahasa Melayu SK","year":2027,"status":"DRAFT_NOT_PUBLISHED","years":{}}
    for year,count in COUNTS.items():
        dest=DEST/f"year{year}"
        dest.mkdir(parents=True,exist_ok=True)
        data=rows(year)
        stat=Counter()
        for i,x in enumerate(data):
            fname=dest/f"lesson_{x['no']:03d}.md"
            if fname.exists():raise RuntimeError(f"NO OVERWRITE: {fname}")
            content=render(year,x,data[i-1] if i else None)
            assert all(v in content for v in ["Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan","Penutup","**Guru:**","**Murid:**","Status QA"])
            fname.write_text(content,encoding="utf-8")
            stat["hold" if "HOLD_SEMAKAN_SUMBER" in content else "draft"]+=1
        files=sorted(dest.glob("lesson_*.md"))
        assert len(files)==count
        manifest["years"][str(year)]={"pdp":count,"rph_files":len(files),"draft":stat["draft"],"hold_source":stat["hold"],"ready":0}
        (dest/"README.md").write_text(
            f"# RPH Bahasa Melayu Tahun {year} — 2027\n\n**{count}/{count} calon fail RPH dalam staging; 0 READY.**\n\n"
            f"Disediakan berdasarkan RPT BM 2027 PdP 001–{count:03d}; tidak menukar nombor atau SK/SP daripada RPT. "
            "Mempunyai arahan guru dan murid, objektif, dua aktiviti, PBD dan rujukan sumber, tetapi "
            "**belum diverifikasi sepenuhnya terhadap naskhah BT/BA/DSKP**. Semua bahagian yang memerlukan "
            "pengesahan dibiarkan berstatus DRAF/HOLD; jangan publish ke Telegram atau Web.\n\n"
            f"**DRAF:** {stat['draft']}; **HOLD sumber:** {stat['hold']}; **READY:** 0.\n",
            encoding="utf-8")
        print(f"Tahun {year}: {count} fail, {stat['draft']} DRAF, {stat['hold']} HOLD",flush=True)
    path=ROOT/"rpt_2027/bahasa_melayu/BM_RPH_T4_T6_GENERATION_MANIFEST.json"
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    assert sum(v["rph_files"] for v in manifest["years"].values())==496

if __name__=="__main__":main()
