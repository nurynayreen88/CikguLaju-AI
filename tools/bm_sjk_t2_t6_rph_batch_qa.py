"""Offline BM SJK source adapter. Never replaces RPT, SK materials or live routes."""
from pathlib import Path
from io import BytesIO
from hashlib import sha256
import json
import argparse
import re
from dlp_year2_rph import _word, _pdf

ROOT=Path(__file__).resolve().parents[1]
COUNTS={2:160,3:160,4:128,5:128,6:128}
# Git object IDs pin the approved RPT source, not generated files.
BLOBS={2:"795de6d20992e568ca6c34d32fdc4f593693115d",3:"c613ffb02d785284d4ccf81fb3ffb17f09332013",
4:"a3d4fe15e80ddc2735ad0d4111502a403c733988",5:"add74bf0fc74eccf9986eeaec97f974f612ee6a0",6:"0c7455b963aec84243b0168ce03df318000a031b"}
TONE="EDF3FA"
PROFILES={
"1.1":("Dengar dan respons","Memperdengarkan bahan bahasa daripada rujukan yang ditetapkan; ulang ujaran secara jelas tanpa memberikan jawapan tugasan.","Mendengar, mengecam maklumat yang diminta dan memberikan respons mengikut tugasan.","Semak ketepatan ujaran atau respons berdasarkan bahan asal.","Kad gambar, bahan dengar daripada teks, kad frasa"),
"1.2":("Interaksi lisan","Memodelkan ujaran santun mengikut situasi dalam tajuk dan menunjukkan cara menyambung perbualan.","Berlatih ujaran mengikut konteks bersama pasangan, bergilir sebagai penutur dan pendengar.","Memerhati respons dan penggunaan bahasa dalam interaksi sebenar.","Kad situasi, kad dialog"),
"1.3":("Penerangan lisan","Menunjukkan cara memilih maklumat penting daripada bahan rujukan sebelum menyampaikan penerangan.","Menyusun isi dan menyampaikan penerangan secara berturutan.","Memberikan maklum balas terhadap ketepatan isi dan kejelasan penyampaian.","Kad isi, bahan rangsangan"),
"2.1":("Bacaan berpandu","Membimbing bacaan bahan rujukan, menunjukkan bahagian yang perlu diberi perhatian tanpa menjawab tugasan.","Membaca bahan mengikut arahan, menandai perkataan atau maklumat berkaitan.","Menyemak bukti dalam bahan bacaan bagi jawapan atau sebutan.","Buku Teks, kad perkataan"),
"2.2":("Pemahaman bahan","Menunjukkan strategi mencari isi melalui tajuk, kata kunci dan konteks.","Meneliti bahan, memilih maklumat yang diperlukan dan menerangkan asas jawapan.","Meminta murid menunjukkan bahagian bahan yang menyokong respons.","Bahan bacaan, peta pemikiran"),
"2.3":("Bacaan dan penghayatan","Memodelkan cara membaca dan memberi perhatian kepada bentuk serta maksud bahan.","Membaca dan melaksanakan tugasan penghayatan berdasarkan bahan.","Menilai respons berdasarkan maksud dan ciri bahan.","Bahan bacaan, kad respons"),
"3.1":("Asas tulisan","Menunjukkan contoh pembentukan huruf atau tulisan yang ditetapkan pada halaman sumber.","Berlatih menulis daripada contoh sebelum menyiapkan tugasan secara individu.","Menyemak kebolehbacaan, bentuk dan ketepatan salinan.","Contoh tulisan, buku latihan"),
"3.2":("Penulisan berpandu","Membimbing murid mengenal maklumat dan menyusun isi sebelum menulis.","Menghasilkan jawapan atau ayat berdasarkan bahan dan menyemak ketepatan isi.","Meneliti hasil tulisan berdasarkan tugasan, bukan panjang tulisan semata-mata.","Bahan rangsangan, buku latihan"),
"3.3":("Hasil penulisan","Memodelkan cara merancang isi atau menyemak kesalahan mengikut jenis tugasan.","Menghasilkan atau menyunting tulisan berdasarkan fokus dan menyemak semula.","Menyemak hasil tulisan dengan merujuk keperluan tugasan.","Kad panduan, buku latihan"),
"4.1":("Persembahan bahasa","Menunjukkan penggunaan bahasa dan ekspresi yang sesuai dengan bahan seni bahasa.","Berlatih dan mempersembahkan bahan mengikut bentuk asal.","Memberikan maklum balas tentang maksud, bahasa dan persembahan.","Bahan seni bahasa, kad dialog"),
"4.2":("Penghayatan seni bahasa","Memodelkan cara menghayati teks, irama atau bentuk persembahan yang dirujuk.","Menghayati dan menyampaikan bahan mengikut tugasan sebenar.","Menilai hubungan maksud bahan dengan persembahan murid.","Bahan seni bahasa, kad rangsangan"),
"4.3":("Kreativiti bahasa","Menunjukkan ciri bahan kreatif pada halaman sumber.","Mengolah atau mempersembahkan bahan mengikut tugasan asal.","Menyemak hasil kreatif berdasarkan bentuk dan maksud yang diperlukan.","Bahan seni bahasa, kertas"),
"4.4":("Pengenalan Jawi pilihan","Menunjukkan bahan Jawi pada halaman rujukan tanpa memperluas skop kepada kemahiran lain.","Mengecam tulisan dan melaksanakan tugasan pengenalan seperti dalam sumber.","Menyemak pengecaman tulisan yang benar-benar diperkenalkan.","Bahan Jawi daripada Buku Teks"),
"5.1":("Golongan kata","Menunjukkan penggunaan kata dalam konteks pada bahan asal.","Mengecam, mengelaskan atau menggunakan kata mengikut tugasan.","Menyemak penggunaan kata berdasarkan konteks ayat.","Kad kata, kad ayat"),
"5.2":("Pembentukan kata","Menunjukkan hubungan kata dasar dan bentuk kata dalam contoh sumber.","Mengenal pasti atau membentuk kata mengikut tugasan pada bahan.","Menyemak bentuk serta penggunaan kata dalam konteks.","Kad kata dasar, kad bentuk kata"),
"5.3":("Binaan ayat","Menunjukkan pola ayat yang berkaitan menggunakan contoh daripada rujukan.","Mengenal pasti atau membina ayat mengikut fokus pembelajaran.","Menyemak jenis, binaan dan ketepatan ayat.","Kad ayat, buku latihan"),
}
ASSESS=("Pentaksiran tema","Menjelaskan arahan pentaksiran tanpa membekalkan jawapan.","Menyiapkan tugasan secara individu berdasarkan bahan yang ditetapkan.","Merekod penguasaan bagi setiap tugasan sebelum membincangkan pembetulan.","Bahan pentaksiran sumber")
RECOVER=("Pemulihan berfokus","Mengenal pasti kesalahan terdahulu dan memodelkan satu langkah pemulihan.","Mencuba semula tugasan dengan bantuan berperingkat.","Menilai percubaan selepas bantuan dan merekod kemajuan.","Bahan pemulihan sumber")
def source(year):
    path=ROOT/f"rpt_2027/sjkc/bahasa_melayu/year_{year}_kuala_lumpur.json"
    raw=path.read_bytes()
    from hashlib import sha1
    assert sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()==BLOBS[year],year
    d=json.loads(raw)
    assert d["year"]==year and len(d["lessons"])==COUNTS[year]
    assert [r["pdp"] for r in d["lessons"]]==list(range(1,COUNTS[year]+1))
    return d["lessons"]

from functools import lru_cache

@lru_cache(maxsize=5)
def standard_labels(year):
    path=ROOT/f"rph_standalone/sjkc/bahasa_melayu/year{year}_standard_labels_20261124.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    assert data["year"]==year and data["source_git_blob"]==BLOBS[year]
    assert data["status"]=="QA_DSKP_TOPIC_LABELS_NOT_VERBATIM"
    rows=[x for r in source(year) for x in [r]+([r["alternative"]] if r.get("alternative") else [])]
    for key in ("sk","sp"):
        assert set(data[key])=={code for r in rows for code in r[key]},(year,key)
        assert all(v.strip() for v in data[key].values())
    return data

def display_standard(year,kind,codes):
    labels=standard_labels(year)[kind]
    return "; ".join(code+" "+labels[code] for code in codes)

def workbook_text(value):
    if not value:return ""
    if isinstance(value,dict):value=[value]
    return "; ".join("Jilid "+str(x.get("volume",""))+", hlm. "+str(x.get("page",""))+
                     (", Aktiviti "+str(x["activity"]) if x.get("activity") is not None else
                      ", "+str(x["activity_label"]) if x.get("activity_label") else "") for x in value)

def profile(r):
    if r["kind"]=="pentaksiran":return ASSESS
    if r["kind"]=="pemulihan":return RECOVER
    key=r["sk"][0]
    if key in PROFILES:return PROFILES[key]
    # Unknown SK stays in the QA manifest; no fabricated official description.
    return ("Tugasan sumber","Menunjukkan bahan pada rujukan asal.","Melaksanakan fokus pembelajaran asal.","Menyemak hasil berdasarkan fokus asal.","Bahan rujukan asal")

def payload(year,r,alternative=False):
    source_row=r
    if alternative:
        assert r.get("optional_jawi") and r.get("alternative")
        r={**r,**r["alternative"],"kind":"unit","optional_jawi":False}
        # No original printed Jawi workbook or cross-curricular reference is
        # attached to an alternative unless its own source explicitly supplies it.
        for k in ("workbook","pkjr","sivik"):
            r[k]=r["alternative"].get(k)
    name,model,practice,assessment,bbm=profile(r)
    focus=r["focus"]
    page=r.get("textbook_page")
    wb=workbook_text(r.get("workbook"))
    references=[]
    if page:references.append("Buku Teks hlm. "+str(page))
    if wb:references.append("Buku Aktiviti "+wb)
    details=[("PdP",f"{r['pdp']:03d}"+(" (Alternatif)" if alternative else "")),
        ("Tema / Unit",r["theme"]+(" / Unit "+str(r["unit_number"])+": "+r["unit"] if r.get("unit_number") else "")),
        ("Standard Kandungan",display_standard(year,"sk",r["sk"])),
        ("Standard Pembelajaran",display_standard(year,"sp",r["sp"])),
        ("Objektif Pembelajaran",focus),
        ("Kriteria Kejayaan","Murid melaksanakan tugasan berikut dengan tepat mengikut bahan: "+focus),
        ("BBM",bbm+("; "+"; ".join(references) if references else "")),
        ("EMK / Nilai","Bahasa, nilai murni dan kesantunan."),
        ("PAK21","Komunikasi, pembelajaran kolaboratif mengikut kesesuaian tugasan."),
        ("PBD",assessment),
        ("Pemulihan / Pengayaan","Guru membimbing semula aspek yang belum dikuasai. Murid yang menguasai menggunakan kemahiran sama pada contoh lain yang sesuai.")]
    if r.get("pkjr"):
        pk=r["pkjr"];details.append(("PKJR",f"Aktiviti {pk.get('activity','')} • hlm. {pk.get('pages','')} • HP {pk.get('hp','')}. "+str(pk.get("focus") or pk.get("topic") or "")))
    if r.get("sivik"):
        sv=r["sivik"];details.append(("Sivik",str(sv.get("value") or "")+" — "+str(sv.get("focus") or "")))
    if source_row.get("optional_jawi") and not alternative:
        details.append(("Pilihan Jawi","Pengenalan Jawi adalah pilihan sekolah; RPH alternatif disimpan berasingan."))
    activities=[("Fasa","Guru","Murid"),
      ("Set Induksi","Menunjukkan bahan berkaitan "+r["topic"]+" dan mengemukakan soalan berdasarkan bahan tersebut.","Memerhati atau mendengar bahan dan memberikan respons awal."),
      ("Aktiviti 1 – "+name,model,"Meneliti contoh dan mengenal pasti perkara yang perlu dilakukan."),
      ("Aktiviti 2 – Pelaksanaan Tugasan","Membimbing pelaksanaan tugasan daripada sumber dan memberikan bantuan mengikut tahap murid.",practice+" "+focus),
      ("Aktiviti 3 – Pengukuhan dan Pentaksiran",assessment,"Menunjukkan hasil kerja dan membetulkan kesalahan berdasarkan maklum balas."+(" Melengkapkan "+wb+" mengikut arahan yang sepadan." if wb else "")),
      ("Penutup","Merumuskan fokus pembelajaran dan mengenal pasti tindakan susulan.","Menyatakan satu perkara yang dikuasai dan membuat pembetulan jika perlu.")]
    # Retain embedded PKJR/Sivik in existing slot. Do not add duration or new PdP.
    heading=("Rancangan Pengajaran Harian",f"Bahasa Melayu (SJK) · Tahun {year}",r["topic"])
    footer=[("Refleksi","    orang murid mencapai kriteria kejayaan;     orang murid belum mencapai. Tindakan susulan berdasarkan hasil tugasan: "+focus)]
    return heading,details,activities,footer

def export(year,out):
    from docx import Document
    import fitz
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    files=[];rows=source(year);alternatives=0
    for r in rows:
        for variant in ([False,True] if r.get("optional_jawi") and r.get("alternative") else [False]):
            alternatives+=int(variant)
            h,d,a,foot=payload(year,r,variant)
            expected=(r["alternative"] if variant else r)
            for fmt,fn in (("docx",_word),("pdf",_pdf)):
                stream=BytesIO()
                fn(stream,h,d,a,foot,compact=True,label_fill=TONE)
                data=stream.getvalue()
                name=f"CIKGULAJU_BMSJK_T{year}_PDP{r['pdp']:03d}"+("_ALTERNATIF" if variant else "")+"_QA."+fmt
                if fmt=="docx":
                    doc=Document(BytesIO(data));text=" ".join(c.text for t in doc.tables for row in t.rows for c in row.cells)
                    assert expected["focus"] in text
                    assert all(" ".join((x+" "+standard_labels(year)[kind][x]).split()) in " ".join(text.split()) for kind in ("sk","sp") for x in expected[kind])
                    assert all(any(run.bold and run.text.startswith("Aktiviti "+str(i)) for t in doc.tables for row in t.rows for c in row.cells for p in c.paragraphs for run in p.runs) for i in (1,2,3))
                else:
                    with fitz.open(stream=data,filetype="pdf") as pdf:
                        assert len(pdf)==1,(year,r["pdp"],variant,len(pdf))
                        text=" ".join(pdf[0].get_text().split())
                        assert all(" ".join((x+" "+standard_labels(year)[kind][x]).split()) in " ".join(text.split()) for kind in ("sk","sp") for x in expected[kind])
                        assert all(x in text for x in ("Aktiviti 1","Aktiviti 2","Aktiviti 3","Refleksi"))
                (out/name).write_bytes(data)
                files.append({"name":name,"sha256":sha256(data).hexdigest(),"bytes":len(data)})
    assert len(files)==2*(COUNTS[year]+alternatives)
    (out/"manifest.json").write_text(json.dumps({"status":"QA_NOT_READY","ready":0,"year":year,
      "source_git_blob":BLOBS[year],"pdp":len(rows),"alternatives":alternatives,
      "pending":["Independent SK/SP full official wording verification and pedagogical review (editorial topic labels included)","Calendar alignment","Production authorization"],"files":files},indent=2),encoding="utf-8")
    print("BM SJK QA",year,"PdP",len(rows),"alternatives",alternatives,"files",len(files))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--year",type=int,choices=COUNTS,required=True);p.add_argument("--out",required=True)
    a=p.parse_args();export(a.year,a.out)
