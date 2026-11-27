"""Offline draft QA for every BM SK KP2027 5P companion. No live route."""
import json
from hashlib import sha256
from pathlib import Path
from web import kp2027_bm_rpt_aligned as bm
from web.rph_5p_v5_layout import Palette, PHASE_KEYS, render_word

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"qa_bm_5p"
PALETTE=Palette("DBE8F5","F4F7FA","EDF3FA","BAC7D0")
DK_PAGES={"1.1":22,"1.2":23,"2.1":30,"2.2":31,"2.3":31,
          "3.1":38,"3.2":39,"4.1":44,"4.2":44}

def build():
    raw=bm.approved_source()
    batches=[]
    for i in range(1,6):
        p=ROOT/"audits"/f"rph_5p_source_adaptation_bm_t1_batch{i:02d}_20261127.json"
        batches.extend(json.loads(p.read_text())["records"])
    indexed={(x["group"],x["lesson"]):x for x in batches}
    expected={(g,n) for g,count in bm.COUNTS.items() for n in range(1,count+1)}
    if len(batches)!=len(expected) or set(indexed)!=expected:
        raise ValueError("Draft coverage mismatch")
    OUT.mkdir(exist_ok=True)
    report=[]
    for g,n in sorted(expected):
        c=indexed[g,n]
        original=raw[g][str(n)]
        if "source_record" in c and c["source_record"]!=original:
            raise ValueError(f"Original source drift {g} {n}")
        if c.get("sp_code",original["sp_code"])!=original["sp_code"]:
            raise ValueError("SP identity drift")
        r=bm.lesson(g,n)
        page=DK_PAGES[r["sk_code"]]
        if r["sp_code"] in ("1.2.3","1.2.4"):page=24
        if r["sp_code"] in ("2.3.2","2.3.3"):page=32
        phases=c["phases"]
        source={
            "subject":"BM_SK","year":1,"lesson_id":f"{g}-{n:03d}","curriculum":"KP2027",
            "topic":r["unit"]+" / "+r["title"],
            "sk":r["sk_code"]+" "+r["sk"],"sp":r["sp_code"]+" "+r["sp"],
            "objective":r["objective"],"criteria":r["criteria"],"closure":r["closure"],
            "aids_pak21_emk":r["material"]+"\nPAK21 / KBAT: Kolaborasi, komunikasi, pemikiran kritis; menerangkan sebab dan membuat pilihan yang bersesuaian.\nEMK / Nilai: Bahasa; komunikasi berhemah; kerjasama; hormat-menghormati; tanggungjawab.",
            "remedial_enrichment":"Pemulihan: "+r["remedial"]+"\nPengayaan: "+r["extension"],
            "reflection":bm._reflection(r,{}),
            "reference":f"Rujukan: DK BM SK Tahun 1 (BPK, 2026), hlm. {page}.",
        }
        data=json.dumps(source,sort_keys=True,ensure_ascii=False).encode()
        companion={**{k:source[k] for k in ("subject","year","lesson_id","curriculum")},
                   "source_sha256":sha256(data).hexdigest(),"phases":phases}
        # No fabricated textbook pages. Preserve original content and teacher reflection.
        name=f"DRAF_BM_KP2027_T1_5P_{g}_{n:03d}"
        file=OUT/(name+".docx")
        file.write_bytes(render_word(source,companion,source_bytes=data,palette=PALETTE,
                         subject_heading="BAHASA MELAYU SK\nTAHUN 1"))
        report.append({"group":g,"lesson":n,"sp":r["sp_code"],"dk_page":page,
                       "file":name,"source_sha256":companion["source_sha256"],
                       "textbook_checked":False,"academic_ready":False,"ready":False})
    (OUT/"manifest.json").write_text(json.dumps({"status":"DRAFT_QA_ONLY","records":report},ensure_ascii=False,indent=2))
    print("Draft Word files generated:",len(report))

if __name__=="__main__":
    build()
