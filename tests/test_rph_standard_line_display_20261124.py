"""Verify code line breaks for every existing source selection; no approval changes."""
import re
from types import SimpleNamespace

from web.rph_standard_line_display_20261124 import (
    standard_lines, display_rows, install, BOUNDARY, START,
)
from web.psv_2027_rph_release_bridge import load_candidate
from web.pjpk_2027_preview_runtime import _source, MAXIMUM
from web.rbt_2027_user_runtime import _lesson as rbt
from web.sejarah_2027_user_runtime import _lesson as sejarah
from staging.pendidikan_muzik.rpt_rph_2027.music_native_route_candidate import load as muzik


def test_exact_boundary():
    assert standard_lines("1.1 Membaca; 1.2 Menulis") == "1.1 Membaca\n1.2 Menulis"
    assert standard_lines("1.1.1(i) Membaca; 1.1.1(ii) Menyebut") == "1.1.1(i) Membaca\n1.1.1(ii) Menyebut"
    assert standard_lines("6.1.1 Menerangkan · K6.1.4 Menilai") == "6.1.1 Menerangkan\nK6.1.4 Menilai"
    assert standard_lines("1.1 Contoh, penerangan; bukan kod.") == "1.1 Contoh, penerangan; bukan kod."
    assert standard_lines("Bukan standard; 1.2 Contoh") == "Bukan standard; 1.2 Contoh"
    assert standard_lines("1.1.1") == "1.1.1"
    assert standard_lines("1.1 A\n1.2 B") == "1.1 A\n1.2 B"


def check(subject, sk, sp):
    state={"subject":subject,"task":"rph"}
    original={"STANDARD KANDUNGAN":sk,"STANDARD PEMBELAJARAN":sp,
              "REFLEKSI":"Catatan guru.", "AKTIVITI UTAMA":"Isi asal."}
    result=display_rows(state,original)
    for key in ("STANDARD KANDUNGAN","STANDARD PEMBELAJARAN"):
        assert result[key]==BOUNDARY.sub("\n",original[key]), (subject,key,original[key],result[key])
        assert all(START.match(line) for line in result[key].splitlines()), (subject,key,result[key])
        assert standard_lines(result[key])==result[key]
    assert result["REFLEKSI"]==original["REFLEKSI"]
    assert result["AKTIVITI UTAMA"]==original["AKTIVITI UTAMA"]
    assert display_rows({**state,"school_type":"SJKC"},original) is original
    return int(result["STANDARD PEMBELAJARAN"]!=sp)


def test_all_928_source_plans():
    total=changed=0
    for y in range(2,7):
        for n in range(1,43):
            p=load_candidate(y,n,preview=True)
            changed+=check("Pendidikan Seni Visual",p["standard_descriptions"]["sk"],p["standard_descriptions"]["sp"])
            total+=1
        for short,subject in (("pj","Pendidikan Jasmani"),("pk","Pendidikan Kesihatan")):
            for n in range(1,MAXIMUM[short][y]+1):
                p=_source(y,short,n)
                changed+=check(subject,p["standard_descriptions"]["sk"],p["standard_descriptions"]["sp"])
                total+=1
        if y>=4:
            for n in range(1,33):
                p=rbt(y,n)
                changed+=check("Reka Bentuk dan Teknologi",p["sk_description"],p["sp_description"])
                total+=1
            for n in range(1,37):
                p=sejarah(y,n)
                changed+=check("Sejarah",p["rph"]["sk"]+" "+p["rph"]["sk_title"],p["sp_text"])
                total+=1
        for n in range(1,36):
            p=muzik(y,n)
            fields={x["label"]:x["value"] for x in p["preview"]["layout"]["header"]}
            changed+=check("Pendidikan Muzik",fields["Standard Kandungan"],fields["Standard Pembelajaran"])
            total+=1
    assert total==928,total
    assert changed>0
    print(f"{total} exact source plans; {changed} multi-SP display changes")


def test_install_and_scope():
    base={"STANDARD PEMBELAJARAN":"1.1 A; 1.2 B"}
    runtime=SimpleNamespace(_rph_rows=lambda state,text:base)
    assert install(runtime)
    assert install(runtime)
    for subject in ("Bahasa Melayu","English","Matematik","Sains"):
        out=runtime._rph_rows({"task":"rph","subject":subject},"")
        assert out["STANDARD PEMBELAJARAN"]=="1.1 A\n1.2 B"
    assert runtime._rph_rows({"task":"rph","subject":"Pendidikan Islam"},"") is base
    assert runtime._rph_rows({"task":"rph","subject":"Matematik","curriculum":"KP2027"},"") is base
    assert base["STANDARD PEMBELAJARAN"]=="1.1 A; 1.2 B"
