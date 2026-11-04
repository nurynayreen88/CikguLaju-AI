#!/usr/bin/env python3
"""Pembetulan teks kecil BM RPH Tahun 2–6 tanpa ubah metadata/DB/isi akademik.

Sumber RPH lama dipelihara; hanya istilah PdP dan tiga ayat draf baharu dibetulkan.
Idempotent; tiada penggantian status HOLD/DRAF atau penciptaan READY.
"""
from pathlib import Path
import re
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]/"rph_standalone/bahasa_melayu"
EXPECTED={2:164,3:165,4:165,5:166,6:165}
stats=Counter()
for year,total in EXPECTED.items():
    paths=sorted((ROOT/f"year{year}").glob("lesson_???.md"))
    assert len(paths)==total,(year,len(paths))
    for num,path in enumerate(paths,1):
        assert path.name==f"lesson_{num:03d}.md"
        old=path.read_text(encoding="utf-8")
        new=re.sub(r"\bLesson\b","PdP",old)
        if year>=4:
            new=new.replace("“Apakah idea, tindakan atau maklumat yang sesuai dengan tajuk “", "“Apakah yang dapat kamu jangka berdasarkan tajuk ")
            # Remove nested quote and retain one question mark.
            new=new.replace("”?”","?”")
            new=new.replace("Catatan tiga maklumat didengar dan dua respons tepat melalui senarai semak.",
                            "Merekod ketepatan tiga maklumat didengar dan dua respons lisan melalui senarai semak.")
            new=re.sub(r"(Merumus kemahiran [^\n]+?)\. dan meminta contoh aplikasi",r"\1 dan meminta contoh aplikasi",new)
        assert f"PdP {num:03d}" in new,(year,num)
        assert f"BM{year}-P{num:03d}" in new if year>=4 else True
        if new!=old:
            path.write_text(new,encoding="utf-8")
            stats[f"T{year}"]+=1
    print(f"Tahun {year}: {total} RPH, {stats[f'T{year}']} pembetulan label/ayat",flush=True)
print("Jumlah fail BM",sum(EXPECTED.values()),"dikekalkan; READY tidak diubah")
