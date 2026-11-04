#!/usr/bin/env python3
"""Refine specific oral/seni/ayat objectives against recorded DSKP SP verbs.

Operates ONLY on existing BM Y4–Y6 RPH drafts. Retains SP, SK, titles,
all source caveats and DRAF/HOLD status; does not approve curriculum.
"""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1]/"rph_standalone/bahasa_melayu"
record={}
def field(t,label):
    m=re.search(r"(?m)^\*\*"+re.escape(label)+r":\*\*\s*(.*)$",t)
    if not m:raise AssertionError(label)
    return m.group(1).strip()
def edit(t,heading,new_text):
    pattern=r"(?m)^## "+re.escape(heading)+r".*?(?=\n## |\n\*\*Nota RPT asal:|\Z)"
    match=re.search(pattern,t,re.S)
    if match is None:raise AssertionError("Missing section "+heading)
    return t[:match.start()]+new_text.rstrip()+"\n"+t[match.end():]
def field_change(t,oldfield,newval):
    patt=r"(?m)^(\*\*"+re.escape(oldfield)+r":\*\*).*$"
    new,count=re.subn(patt,lambda m:m.group(1)+" "+newval,t)
    if count!=1:raise AssertionError((oldfield,count))
    return new
for year in (4,5,6):
    changed=[]
    for f in sorted((ROOT/f"year{year}").glob("lesson_*.md")):
        original=f.read_text(encoding="utf-8")
        sp=field(original,"Standard Pembelajaran (SP)")
        topic=field(original,"Tajuk aktiviti")
        t=original
        if re.match(r"1\.3\.[12]\b",sp):
            retell=sp.startswith("1.3.2")
            act="menceritakan semula perkara yang didengar, ditonton atau dibaca" if retell else "bercerita"
            obj=f"Murid dapat {act} berkaitan '{topic}' dengan sekurang-kurangnya tiga isi/peristiwa tersusun serta sebutan dan intonasi yang jelas."
            t=field_change(t,"Objektif PdP",obj)
            t=edit(t,"Aktiviti 1",f"""## Aktiviti 1 — Susun jalan cerita (15 minit)
**Guru:** Menyampaikan bahan bertajuk '{topic}' (teks/audio/gambar sesuai sumber); memodelkan urutan permulaan, perkembangan dan pengakhiran serta intonasi yang sesuai SP.
**Murid:** Mendengar, membaca atau meneliti bahan; menyusun sekurang-kurangnya tiga isi/peristiwa mengikut urutan berdasarkan bukti bahan.""")
            t=edit(t,"Aktiviti 2",f"""## Aktiviti 2 — Persembahan cerita (20 minit)
**Guru:** Membimbing murid bercerita dengan kad urutan; memberikan maklum balas tentang sebutan, intonasi, gaya dan kesinambungan isi.
**Murid:** Bercerita semula secara bergilir tentang '{topic}' menggunakan tiga isi/peristiwa serta intonasi dan gaya yang sesuai; rakan mencatat satu kekuatan dan cadangan.""")
            t=edit(t,"Pengukuhan / Pentaksiran Bilik Darjah",f"""## Pengukuhan / Pentaksiran Bilik Darjah (15 minit)
**Guru:** Mentaksir persembahan setiap murid melalui senarai semak: tiga isi tersusun, sebutan jelas dan intonasi/gaya tepat mengikut SP ({sp}). Beri peluang persembahan semula sebagai pemulihan.
**Murid:** Menyampaikan ringkasan lisan dan membaiki satu aspek sebutan, urutan atau intonasi selepas maklum balas.""")
        elif sp.startswith("4.1.1") and ("dialog" in sp.lower() or "peribahasa" in sp.lower()):
            obj=f"Murid dapat mengujarkan dialog atau bercerita tentang '{topic}' dengan menggunakan sekurang-kurangnya dua ungkapan/peribahasa yang tepat mengikut konteks."
            t=field_change(t,"Objektif PdP",obj)
            t=edit(t,"Aktiviti 1",f"""## Aktiviti 1 — Fahami penggunaan peribahasa (15 minit)
**Guru:** Menunjukkan petikan atau dialog berkaitan '{topic}' dalam bahan yang dirujuk; mengajak murid meneliti maksud peribahasa berdasarkan situasi.
**Murid:** Mengenal pasti dua peribahasa/ungkapan dan menerangkan maksudnya melalui contoh situasi dalam tajuk.""")
            t=edit(t,"Aktiviti 2",f"""## Aktiviti 2 — Dialog dan persembahan (20 minit)
**Guru:** Membimbing murid membina dialog empat hingga enam ujaran dengan peribahasa yang digunakan pada konteks yang sesuai; memodelkan intonasi santun.
**Murid:** Berpasangan membina dialog bertema '{topic}', menggunakan dua ungkapan yang relevan, kemudian mempersembahkannya secara lisan.""")
            t=edit(t,"Pengukuhan / Pentaksiran Bilik Darjah",f"""## Pengukuhan / Pentaksiran Bilik Darjah (15 minit)
**Guru:** Merekod ketepatan makna dua peribahasa dan penggunaan dalam dialog/cerita serta kelancaran ujaran, menurut SP ({sp}).
**Murid:** Menjelaskan mengapa ungkapan dipilih dan membetulkan sekurang-kurangnya satu penggunaan jika tidak tepat.""")
        elif sp.startswith("5.3.1") and "ayat tunggal" in sp.lower() and "ayat majmuk" in sp.lower():
            obj=f"Murid dapat membina dua ayat tunggal dan dua ayat majmuk bertema '{topic}', termasuk peluasan subjek atau predikat apabila disyaratkan dalam SP."
            t=field_change(t,"Objektif PdP",obj)
            t=edit(t,"Aktiviti 1",f"""## Aktiviti 1 — Analisis binaan ayat (15 minit)
**Guru:** Menunjukkan contoh ayat daripada bahan '{topic}' dan menjelaskan perbezaan ayat tunggal, ayat majmuk serta bahagian subjek dan predikat.
**Murid:** Mengelaskan sekurang-kurangnya empat ayat mengikut struktur; menandakan subjek, predikat dan kata hubung yang berkaitan.""")
            t=edit(t,"Aktiviti 2",f"""## Aktiviti 2 — Bina dan peluaskan ayat (20 minit)
**Guru:** Menyediakan rangka ayat berkaitan '{topic}'; membimbing murid membina dan meluaskan subjek/predikat atau menggabungkan klausa dengan betul.
**Murid:** Membina dua ayat tunggal dan dua ayat majmuk bertema '{topic}', menyatakan bentuk peluasan yang dibuat serta menyemak ayat dengan pasangan.""")
            t=edit(t,"Pengukuhan / Pentaksiran Bilik Darjah",f"""## Pengukuhan / Pentaksiran Bilik Darjah (15 minit)
**Guru:** Menanda empat ayat: struktur tunggal/majmuk, hubungan subjek-predikat dan penggunaan peluasan mengikut SP ({sp}).
**Murid:** Membetulkan satu ayat yang tidak gramatis serta menerangkan pembetulannya.""")
        if t!=original:
            assert "DRAF" in t and ("HOLD" in t or "BELUM disahkan" in t)
            assert field(t,"Standard Pembelajaran (SP)")==sp
            assert field(t,"Tajuk aktiviti")==topic
            f.write_text(t,encoding="utf-8")
            changed.append(f.name)
    record[year]=changed
    print("Year",year,"skill-aligned drafts",len(changed),flush=True)
assert sum(map(len,record.values()))>=30
print("TOTAL",sum(map(len,record.values())))
