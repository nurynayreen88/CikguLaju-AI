"""Source-corrected Sains T4/T5 RPT 2027 DRAF from independent original KPM PDFs.

CLI: python -m scripts.build_rpt2027_sains_kssr2017_y4y5_staging \
 --year 4 --original-pdf 'GuruBesar_DSKP_Sains_Tahun_4.pdf' --out-dir /tmp/sains

IMPORTANT: 91/95 *SP* are official DSKP standards, NOT new PdP/lessons.
All week/date/class allocations remain blank. This does not write to DB/Web/Telegram.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

EXPECTED={
 4:("623e60d32156e1a3eeb399f856f40dc6529946445278bf4cf69aea081ad543ea",91),
 5:("e90744b28e6cc3943e8707475a911238ffc8b6a9dffb812bf742d35bcaa61ef6",95),
}
SK_TITLES={
4:{"1.1":"Kemahiran Proses Sains","2.1":"Pernafasan Manusia","2.2":"Perkumuhan dan Penyahtinjaan","2.3":"Manusia Bergerak Balas Terhadap Rangsangan","3.1":"Organ Pernafasan Haiwan","3.2":"Haiwan Vertebrata","4.1":"Tumbuhan Bergerak Balas Terhadap Rangsangan","4.2":"Fotosintesis","5.1":"Cahaya Bergerak Lurus","5.2":"Pantulan Cahaya","5.3":"Pembiasan Cahaya","6.1":"Bunyi","7.1":"Sumber dan Bentuk Tenaga","7.2":"Sumber Tenaga Boleh Dibaharui dan Sumber Tenaga Tidak Boleh Dibaharui","8.1":"Sumber Asas Bahan","8.2":"Sifat Bahan","9.1":"Graviti Bumi","9.2":"Putaran dan Peredaran Bumi","10.1":"Tuas","10.2":"Mesin Ringkas dan Mesin Kompleks"},
5:{"1.1":"Kemahiran Proses Sains","2.1":"Sistem Rangka Manusia","2.2":"Sistem Peredaran Darah Manusia","2.3":"Perkaitan antara Sistem dalam Tubuh Manusia","3.1":"Kemandirian Spesies Haiwan","3.2":"Mereka Cipta Model Haiwan","3.3":"Hubungan Makanan antara Hidupan","4.1":"Kemandirian Spesies Tumbuhan","4.2":"Pencaran Biji Benih","5.1":"Sumber Tenaga Elektrik","5.2":"Litar Bersiri dan Litar Selari","5.3":"Keselamatan Pengendalian Peralatan dan Penjimatan Elektrik","6.1":"Haba dan Suhu","7.1":"Pengaratan Bahan","8.1":"Keadaan Jirim","8.2":"Perubahan Keadaan Jirim Bagi Air","9.1":"Fasa Bulan","9.2":"Buruj","10.1":"Penggunaan Alat dalam Kehidupan"}}
SP_RE=re.compile(r"^\d+\.\d+\.\d+$")

def _ordered_lines(words):
    lines=[]
    for w in sorted(words,key=lambda z:(round(z[1]),z[0])):
        if lines and abs(w[1]-lines[-1][0])<2.5:
            lines[-1][1].append((w[0],w[4]))
        else:lines.append([w[1],[(w[0],w[4])]])
    return " ".join(" ".join(t[1] for t in sorted(l[1])) for l in lines).strip()

def extract_official_pdf(year:int,original_pdf:Path):
    if year not in EXPECTED:
        raise ValueError("Only source-checked KSSR2017 Sains Year4/5")
    p=Path(original_pdf)
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=EXPECTED[year][0]:
        raise ValueError(f"DSKP Year{year} original source SHA-256 missing or changed")
    import fitz
    output=[]
    with fitz.open(p) as doc:
        for pn,page in enumerate(doc,1):
            words=page.get_text("words")
            codes=sorted([w for w in words if SP_RE.fullmatch(w[4])],key=lambda w:w[1])
            for k,code in enumerate(codes):
                x,y,_,_,sp,*_=code
                end=codes[k+1][1]-2 if k+1<len(codes) else min(555,page.rect.height-20)
                source_words=[w for w in words if x+32 <= w[0]<420 and y-2<=w[1]<end and w[4] not in ("Murid","boleh:")]
                text=_ordered_lines(source_words)
                text=re.sub(r"\s\d{2}$","",text)
                text=re.sub(r"(?<=\s)[1-6](?=\s|$)","",text)
                text=re.sub(r"\s+"," ",text).strip()
                # Do not fill any missing PDF-extraction tail with guessed
                # words, even when the expected ending appears obvious.
                # The original page must remain the authoritative source.
                text_tail_incomplete = (
                    not text or text[-1] not in ".!?:;)"
                )
                sk=".".join(sp.split(".")[:2])
                if sk not in SK_TITLES[year] or len(text)<18:
                    raise ValueError(f"SK/text source suspect: {year}/{sp}")
                output.append({"year":year,"sk_code":sk,"sk_text":SK_TITLES[year][sk],
                               "sp_code":sp,"sp_text_source_extract_NEEDS_VISUAL_REVIEW":text,
                               "original_pdf_page":pn,
                               "extraction_tail_requires_visual_check":text_tail_incomplete,
                               "week_2027":None,"class_date":None,
                               "academic_release_approved":False})
    if len(output)!=EXPECTED[year][1] or len({r["sp_code"] for r in output})!=len(output):
        raise ValueError("Year4/5 official source unique SP count changed")
    return output

def write_source_index(year:int,original_pdf:Path,destination:Path):
    rows=extract_official_pdf(year,original_pdf)
    d=Path(destination);d.parent.mkdir(parents=True,exist_ok=True)
    d.write_text(json.dumps({"status":"KSSR2017_SOURCE_EXTRACT_TEXT_VISUAL_REVIEW_REQUIRED",
                              "source_sha256":EXPECTED[year][0],"year":year,
                              "official_sp_code_count":len(rows),
                              "note":"Source KPM original, not 91/95 independently approved PdP. No week assigned.",
                              "rows":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return d

def write_five_column_preview(year:int,rows:list,destination:Path):
    from rpt_2027.common.format_2026_layout_preview import build_preview
    draft=[]
    for i,r in enumerate(rows,1):
        if r["academic_release_approved"] or r["week_2027"]:
            raise ValueError("Source index must not be published as a teaching timetable")
        draft.append({"id":f"{i:03d}","unit":f"SK {r['sk_code']}: {r['sk_text']}",
                      "sk":r["sk_code"],"sp":r["sp_code"],
                      "sk_display":r["sk_code"]+" — "+r["sk_text"],
                      "sp_display":r["sp_code"]+" — "+r["sp_text_source_extract_NEEDS_VISUAL_REVIEW"],
                      "week":"","a_start":"","a_end":"","b_start":"","b_end":"",
                      "note":f"KSSR2017 DSKP asal PDF hlm {r['original_pdf_page']}. AYAT EKSTRAK PERLU SEMAK VISUAL. Tarikh/PdP belum sah."+
                          (" AYAT TERPOTONG — rujuk PDF sumber!" if r.get("extraction_tail_requires_visual_check") else "")})
    dest=Path(destination)
    if "DRAF" not in dest.name.upper() or dest.suffix.lower()!=".pdf":
        raise ValueError("Separate review-only DRAF filename required")
    return build_preview("sains",year,draft,dest)

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--year",type=int,choices=(4,5),required=True)
    p.add_argument("--original-pdf",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    args=p.parse_args()
    folder=Path(args.out_dir);folder.mkdir(parents=True,exist_ok=True)
    index=write_source_index(args.year,args.original_pdf,folder/f"Sains_T{args.year}_KSSR2017_DSKP_SOURCE_DRAF.json")
    rows=json.loads(index.read_text("utf-8"))["rows"]
    dest=folder/f"Sains_T{args.year}_RPT2027_5_LAJUR_KSSR2017_DRAF.pdf"
    write_five_column_preview(args.year,rows,dest)
    print("OFFICIAL DSKP CODE INDEX (not lesson approved)",args.year,len(rows),dest)
