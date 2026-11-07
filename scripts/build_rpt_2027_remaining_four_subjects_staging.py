"""Reflow 20 sourced 2027 RPT sets into the shared five-column preview.

NO curriculum revision, published file replacement or invented dates/standards.
Sources:
- BM Year2-6: existing 44-week RPT HTML (original full SK/SP text).
- Pendidikan Islam Year2-6: original RPH JSON with native Jawi SK/SP.
- Bahasa Arab Year2-6: original 298 sourced index rows (SK/SP codes ONLY).
- Music Year2-6: original 35-PdP/year RPT CSV (SP codes ONLY).

Missing full official text is explicitly marked in the preview, not fabricated.
"""
from __future__ import annotations
import csv
import json
import re
from datetime import date
from pathlib import Path

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks, matching_master_weeks
from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "staging/rpt_2027_seragam_2026/baki_4_subjek_DRAF"

def csv_rows(p):
    with p.open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))

def dates(master, week):
    if not week:
        return {}
    if week not in master["A"] or week not in master["B"]:
        raise ValueError(f"Unverified calendar week: {week}")
    a,b=master["A"][week],master["B"][week]
    return dict(a_start=a[0],a_end=a[1],b_start=b[0],b_end=b[1])

def bm_records(year):
    from bs4 import BeautifulSoup
    path=ROOT/f"rpt_2027/bahasa_melayu/RPT_BM_Tahun_{year}_2027_Format_2026_DRAF.html"
    soup=BeautifulSoup(path.read_text(encoding="utf-8"),"html.parser")
    tables=soup.find_all("table")
    if len(tables)!=44:
        raise ValueError(f"BM T{year} needs 44 distinct original week tables")
    master=load_calendar_weeks()
    items=[]
    for wn,table in enumerate(tables,1):
        week=f"M{wn:02d}"
        source_week=table.select_one("span.wn")
        if not source_week or int(source_week.get_text(strip=True))!=wn:
            raise ValueError("BM source HTML week index changed")
        for tr in table.select("tbody tr"):
            td=tr.find_all("td",recursive=False)
            if tr.has_attr("class") and "unallocated" in tr["class"]:
                continue
            if len(td)==5 and "week" in td[0].get("class",[]):
                td=td[1:]
            if len(td)!=4:
                raise ValueError(f"BM T{year} week {wn} malformed body cells ({len(td)})")
            unit,sk,sp,notes=(x.get_text(" ",strip=True) for x in td)
            title=td[3].select_one(".ref-title")
            if not title:
                raise ValueError("BM source RPT row lacks numbered PdP")
            title_text=title.get_text(" ",strip=True)
            m=re.search(r"\bPdP\s+(\d{3})\b",title_text)
            if not m:
                raise ValueError("BM RPT source lacks PdP identifier")
            no=int(m.group(1))
            detail=title_text[m.end():].strip(" · ")
            sk_code=re.match(r"\d+(?:\.\d+)+",sk)
            sp_code=re.match(r"\d+(?:\.\d+)+",sp)
            # PBD/penilaian tema explicitly has no additional official SK/SP.
            # Preserve the printed assessment text rather than inventing codes.
            if (not sk_code or not sp_code) and not (
                sk == "Penilaian Tema / PBD"
                and "tiada kod SP baharu" in sp
            ):
                raise ValueError(f"BM T{year} PdP {no}: original SK/SP code missing")
            source_notes=td[3].get_text(" ",strip=True)
            if not source_notes:
                raise ValueError("BM source reference cell empty")
            items.append(dict(
                id=f"{no:03d}",week=week,unit=unit,topic=detail,
                sk=sk_code.group(0) if sk_code else sk,
                sp=sp_code.group(0) if sp_code else sp,
                sk_display=sk,sp_display=sp,
                note=source_notes,source_week=week,**dates(master,week)
            ))
    expected={2:164,3:165,4:165,5:166,6:165}[year]
    if len(items)!=expected:
        raise ValueError(f"BM T{year} missing PdP: {len(items)} != {expected}")
    validate_rows("bahasa_melayu",year,items)
    return items

def pi_records(year):
    path=ROOT/f"rph_standalone/pendidikan_islam_draf_2027/year{year}.json"
    doc=json.loads(path.read_text(encoding="utf-8"))
    records=doc["records"]
    counts={2:112,3:147,4:151,5:143,6:143}
    if len(records)!=counts[year]:
        raise ValueError(f"PI T{year} source count changed")
    master=load_calendar_weeks()
    rows=[]
    held_count=0
    for n,r in enumerate(records,1):
        if r.get("lesson")!=n or r.get("tahun")!=year:
            raise ValueError("PI PdP source identity mismatch")
        intro="\n".join(r.get("intro") or [])
        m=re.search(r"Minggu 2027:\s*(\d{2})",intro)
        field=r.get("fields") or {}
        withheld=bool(r.get("withheld",False))
        if not m and not withheld:
            raise ValueError(f"PI T{year} PdP{n:03d} has no sourced original week")
        # Held RPH records have no source week. Never assign their neighbours'
        # dates: teacher must decide separately if/when replacement is scheduled.
        week=f"M{int(m.group(1)):02d}" if m else ""
        if withheld:
            held_count+=1
            # The source explicitly withheld six records. Do not invent their SK/SP.
            sk="REKOD DITAHAN — SK TIDAK TERSEDIA"
            sp="REKOD DITAHAN — SP TIDAK TERSEDIA"
            topic="Kandungan asal ditahan; bukan PdP disahkan."
            note="REKOD DITAHAN: tidak boleh digunakan sebagai rancangan mengajar."
        else:
            sk=str(field.get("sk") or "").strip()
            sp=str(field.get("sp") or "").strip()
            topic=str(field.get("objektif") or "").strip()
            note=("Bahan: "+str(field.get("bahan") or "").strip()+
                  " | Penilaian: "+str(field.get("pentaksiran") or "").strip())
            if not sk or not sp or not note:
                raise ValueError(f"PI T{year} PdP{n:03d}: original SK/SP/notes absent")
        b=re.search(r"Bidang:\s*(.*?)\s*(?:•|$)",intro)
        unit="Bidang: "+(b.group(1).strip() if b else "Belum dinyatakan dalam sumber")
        rows.append(dict(
            id=f"{n:03d}",week=week,unit=unit,topic=topic[:350],
            sk=sk,sp=sp,note=note[:630],source_status=r.get("state"),
            source_held=withheld,**dates(master,week)
        ))
    if held_count!=({2:1,3:0,4:0,5:0,6:5}[year]):
        raise ValueError("PI hold records count changed")
    validate_rows("pendidikan_islam",year,rows)
    return rows

def arabic_records(year):
    base=ROOT/"rpt_2027/bahasa_arab"
    a=csv_rows(base/"rpt_2027_KUMPULAN_A_INDEKS_PDP_DRAF.csv")
    b=csv_rows(base/"rpt_2027_KUMPULAN_B_INDEKS_PDP_DRAF.csv")
    seq=csv_rows(base/"unit_sequence_DRAF_20261105.csv")
    titles={int(x["unit"]):x["tajuk_arab"] for x in seq if int(x["tahun"])==year}
    ar=[x for x in a if int(x["tahun"])==year]
    br=[x for x in b if int(x["tahun"])==year]
    expected={2:60,3:60,4:58,5:60,6:60}[year]
    if len(ar)!=expected or len(br)!=expected or len(titles)!=4:
        raise ValueError(f"Arabic Year {year} source coverage or unit index incomplete")
    rows=[]
    for n,(left,right) in enumerate(zip(ar,br),1):
        for key in ("tahun","pdp","unit","sk","sp","fokus","halaman_buku"):
            if left.get(key)!=right.get(key):
                raise ValueError(f"Arabic T{year} PdP {n} group A/B content mismatch")
        if (int(left["pdp"])!=n or left["kumpulan"]!="A" or right["kumpulan"]!="B"
            or left.get("tarikh_pdp_2027") or right.get("tarikh_pdp_2027")):
            raise ValueError("Arabic source timeline unexpectedly filled")
        no=int(left["unit"])
        if no not in titles:
            raise ValueError("Arabic source unit missing")
        # Only numeric codes exist in this repo's year-wide source index.
        # Do not turn short teacher focus labels into fictitious DSKP statements.
        rows.append(dict(
            id=f"{n:03d}",week="",unit=f"Unit {no}: {titles[no]}",
            topic=left["fokus"],sk=left["sk"],sp=left["sp"],
            sk_display=left["sk"]+" — Pernyataan penuh SK belum dipadankan",
            sp_display=left["sp"]+" — Pernyataan penuh SP belum dipadankan",
            note="BT m/s: "+(left.get("halaman_buku") or "belum disahkan")+
                 " (calon). Tarikh A/B belum diperuntukkan. DRAF.",
            source_status=left["status_rpt"],
        ))
    validate_rows("bahasa_arab",year,rows)
    return rows

def music_records(year):
    base=ROOT/"staging/pendidikan_muzik/rpt_rph_2027"
    rows=csv_rows(base/f"year{year}"/f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv")
    if len(rows)!=35:
        raise ValueError(f"Music T{year}: no complete 35-PdP CSV")
    master=load_calendar_weeks()
    output=[]
    def field(row,*names):
        for k in names:
            if k in row:
                return row[k]
        raise ValueError(f"Music T{year} missing columns {names}")
    def parse_slot(text):
        text=text.strip()
        m=re.fullmatch(r"(\d{2})/(\d{2})\s*[–-]\s*(\d{2})/(\d{2})",text)
        if not m:
            raise ValueError(f"Music source 2027 A/B slot invalid: {text}")
        a,b,c,d=map(int,m.groups())
        return f"2027-{b:02d}-{a:02d}",f"2027-{d:02d}-{c:02d}"
    for n,r in enumerate(rows,1):
        if r["PdP ID"]!=f"MZ-Y{year}-{n:02d}" or int(r["PdP"])!=n:
            raise ValueError("Music PdP ID/order mismatch")
        slot_a=parse_slot(field(r,"Slot A","Kumpulan A slot 2027","Slot Kumpulan A"))
        slot_b=parse_slot(field(r,"Slot B","Kumpulan B slot 2027","Slot Kumpulan B"))
        candidate=dict(a_start=slot_a[0],a_end=slot_a[1],
                       b_start=slot_b[0],b_end=slot_b[1])
        matches=matching_master_weeks(candidate,master)
        if len(matches)!=1:
            raise ValueError(f"Music Year {year} PdP {n}: week range not in 2027 master")
        sp=field(r,"SP DSKP","SP","Kod SP")
        if not sp.strip():
            raise ValueError("Music source SP blank")
        unit=field(r,"Unit","Unit/Tajuk").strip()
        status=field(r,"Semakan","Status tambahan","Status Semakan")
        book=field(r,"BT m/s","RPT halaman BT (belum sah)","Buku Teks m/s")
        audio=r.get("Audio cetak atau RPT",r.get("Audio Tercetak",""))
        output.append(dict(
            id=f"{n:03d}",week=matches[0],unit="Unit/Tajuk: "+unit,
            topic="PdP Seni Muzik "+f"{n:03d}",
            sk="Kod SK belum dibekalkan dalam CSV",
            sp=sp.replace(";", " / "),
            sp_display=sp.replace(";", " / ")+" — Pernyataan penuh SP belum dipadankan",
            note=("BT m/s: "+book+" (draf). " +
                  ("Audio: "+audio+". " if audio else "")+status)[:440],
            **candidate
        ))
    validate_rows("muzik",year,output)
    return output

SPECS=(
    ("bahasa_melayu",range(2,7),bm_records),
    ("pendidikan_islam",range(2,7),pi_records),
    ("bahasa_arab",range(2,7),arabic_records),
    ("muzik",range(2,7),music_records),
)

def build_all(destination=OUT):
    target=Path(destination)
    results=[]
    for sub,years,reader in SPECS:
        for year in years:
            rows=reader(year)
            filename=f"CIKGULAJU_RPT_{sub.upper()}_TAHUN_{year}_2027_LIMA_LAJUR_DRAF.pdf"
            file=target/filename
            build_preview(sub,year,rows,file)
            results.append((sub,year,len(rows),str(file)))
    if len(results)!=20:
        raise ValueError("Incomplete 20 PDF RPT rendering")
    return results

if __name__=="__main__":
    for sub,year,n,p in build_all():
        print(f"RPT_REMAINING: {sub} year={year} rows={n} file={p}")
