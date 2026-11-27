"""Build 249 optional Math KP2027 5P QA Word files. Never overwrite originals."""
import json
from hashlib import sha256
from pathlib import Path
from web.rph_5p_v5_layout import MATH_V5, PHASE_KEYS, render_word

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"audits"
OUT=ROOT/"qa_math_5p"
def load(name):return json.loads((AUDIT/name).read_text(encoding="utf-8"))
SK={"1.1":"Nilai Nombor","1.2":"Ikatan Nombor",
    "2.1":"Tambah dalam Lingkungan 30","2.2":"Tolak dalam Lingkungan 30",
    "3.1":"Wang Kertas dan Duit Syiling","3.2":"Nilai Wang",
    "4.1":"Bentuk Dua Dimensi","5.1":"Masa dalam Sehari",
    "5.2":"Tarikh, Hari, Minggu, Bulan dan Tahun",
    "6.1":"Unit Bukan Piawai","6.2":"Unit Piawai","7.1":"Piktograf"}

def build():
    source=load("rph_5p_math_kp2027_source_fields_20261127.json")["records"]
    original=json.loads((ROOT/"web/kp2027_math_v11_catalog.json").read_text())
    audit=load("rph_5p_math_kp2027_t1_individual_source_audit_20261127.json")
    companions=[]
    for i in range(1,4):
        companions.extend(load(f"rph_5p_math_kp2027_t1_batch{i:02d}_20261127.json")["records"])
    key=lambda x:(x["group"],x["lesson"])
    drafts={key(x):x for x in companions}
    reviews={key(x):x for x in audit["records"]}
    expected={(g,n) for g,count in (("A",125),("B",124)) for n in range(1,count+1)}
    assert len(companions)==len(reviews)==249 and set(drafts)==set(reviews)==expected
    assert len(source)==30
    OUT.mkdir(exist_ok=True)
    manifest=[]
    for g,n in sorted(expected):
        row,review=drafts[g,n],reviews[g,n]
        code=row["sp_code"]
        cat=original[g][str(n)]
        assert cat["sp"]==code==review["sp_code"] and cat["word"]==row["source_word_sha256"] and cat["pdf"]==row["source_pdf_sha256"]
        fields=dict(source[code])
        # Normalize only the two known PDF extraction artifacts. Do not change math.
        if code=="2.2.1":
            fields["bbm"]=fields["bbm"].replace("kad simbol dan =, kad gambar.−","kad simbol − dan =, kad gambar.")
        if code=="2.2.2":
            fields["pbd"]="Lima item: 8 − 3, 9 − 5, 18 − 5, 24 − 7 dan 21 − 6; guru catat strategi dan ketepatan."
        correction=review.get("correction")
        phases=dict(correction["phases"] if correction else row["phases"])
        if correction:
            for k in ("objective","criteria","bbm","pbd","closure","remedial","extension"):
                fields[k]=correction[k]
        # Preserve quantitative criteria and source PBD. The correction's proposed
        # assessment may repeat the criteria; keep the shorter explicit PBD instead.
        phases["evaluation"]=fields["pbd"]
        sk_code=code.rsplit(".",1)[0]
        data={
            "subject":"MATEMATIK_SK","year":1,"lesson_id":f"{g}-{n:03d}","curriculum":"KP2027",
            "topic":fields["sk"]+" / "+fields["topic"],
            "sk":sk_code+" "+SK[sk_code],"sp":fields["sp"],
            "objective":fields["objective"],"criteria":fields["criteria"],
            "closure":fields["closure"].removesuffix(" Tindakan pemulihan dan pengayaan dilaksanakan mengikut keperluan."),
            "aids_pak21_emk":"BBM: "+fields["bbm"]+"\nPAK21 / KBAT: "+fields["pak"]+"\nEMK / Nilai: "+fields["emk"],
            "remedial_enrichment":"Pemulihan: "+fields["remedial"]+"\nPengayaan: "+fields["extension"],
            "reflection":"Kriteria: "+fields["criteria"]+"\nBilangan murid menguasai:    Belum menguasai:\nTindakan susulan:",
            "reference":"Rujukan: DK Matematik Tahun 1 (BPK, 2026) • RPT 2027 Kumpulan "+g+".",
        }
        raw=json.dumps(data,sort_keys=True,ensure_ascii=False).encode()
        companion={**{k:data[k] for k in ("subject","year","lesson_id","curriculum")},
                    "source_sha256":sha256(raw).hexdigest(),"phases":phases}
        name=f"DRAF_MATEMATIK_KP2027_T1_5P_{g}_{n:03d}"
        output=render_word(data,companion,source_bytes=raw,palette=MATH_V5,subject_heading="MATEMATIK SK\nTAHUN 1")
        (OUT/(name+".docx")).write_bytes(output)
        manifest.append({"group":g,"lesson":n,"sp_code":code,"filename":name,
                         "original_word_sha256":cat["word"],"original_pdf_sha256":cat["pdf"],
                         "source_sha256":companion["source_sha256"],"dk_scope_correction":bool(correction),
                         "source":data,"phases":phases,"ready":False})
    (OUT/"manifest.json").write_text(json.dumps({"status":"DRAFT_QA_ONLY","records":manifest},ensure_ascii=False,indent=2),encoding="utf-8")
    assert sum(x["dk_scope_correction"] for x in manifest)==40
    print("Generated",len(manifest),"Word drafts")
if __name__=="__main__":build()
