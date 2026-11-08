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
from rpt_2027.common.music_dskp_full_statement_staging import music_full_standard_display

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
    recovery=json.loads((ROOT/"audits/pendidikan_islam_rpt2027_6_held_source_recovery_20261107_DRAF.json").read_text(encoding="utf-8"))
    if (recovery.get("status")!="PROVISIONAL_SOURCE_RECOVERY_FOR_HELD_PI_RPT_PREVIEW_ONLY"
        or recovery.get("release_ready_count")!=0 or len(recovery.get("entries",[]))!=6):
        raise ValueError("PI held-record recovery ledger unexpectedly approved or incomplete")
    source_only={(v["year"],v["lesson"]):v for v in recovery["entries"]}
    if len(source_only)!=6:
        raise ValueError("PI source candidate Lxxx duplicated")
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
        # Only source-backed candidate weeks from the RPT Drive document are
        # assigned to the six held rows. They are *not* approved class dates.
        week=f"M{int(m.group(1)):02d}" if m else ""
        recovered=source_only.get((year,n))
        if withheld:
            held_count+=1
            if recovered is None:
                raise ValueError(f"PI T{year} L{n:03d}: unreviewed source hold")
            week=recovered["week"]
            if week not in master["A"] or week not in master["B"]:
                raise ValueError("Recovered PI source week outside verified 2027 master")
            if recovered["kind"]=="KHATAM_TASMI_OPTIONAL_NO_OFFICIAL_SK_SP_IN_SOURCE":
                # Tasmi is an elective, source-backed enrichment programme,
                # NOT a false new official DSKP SK/SP standard.
                sk="PROGRAM TASMI PILIHAN GURU — BUKAN KOD SK RASMI"
                sp="BACAAN TASMI / PBD — TIADA KOD SP RASMI DALAM RPT SUMBER"
                topic="Tasmi' / Khatam cadangan: "+recovered["focus"]
                note=("REKOD DITAHAN: RPH V5 asal tidak lengkap. "
                      "Rujukan RPT sumber "+recovered["source_lesson"]+" (hanya cadangan "
                      "tasmi' pilihan guru; tiada kod SK/SP rasmi dibekalkan). "
                      "Bacaan: "+recovered["focus"]+". "
                      "Minggu sumber calon, bukan jadual kelas yang diluluskan.")
            elif recovered["kind"]=="IBADAH_2026_RPT_STANDARD_CONFLICT_HOLD":
                sk="4.2 — Solat Ketika Sakit (DSKP Tahun 6)"
                sp=("4.2.3 / 4.2.4 / 4.2.5 — Pengukuhan dan pentaksiran "
                    "amali Solat Ketika Sakit; ulang kaji SP L059")
                topic="KONFLIK SUMBER DIBETULKAN DALAM CADANGAN: Solat Ketika Sakit — pengukuhan/PBD"
                correction=recovered.get("conflict_resolution_evidence") or {}
                if (correction.get("year6_expected_topic")!="Solat Ketika Sakit" or
                    correction.get("year5_topic_used_by_errant_rpt")!="Solat Berjemaah" or
                    correction.get("candidate_correction_approval") is not False):
                    raise ValueError("Year6 L060 cross-year collision evidence missing")
                note=("REKOD DITAHAN / CADANGAN DIPERBETULKAN: sumber RPT "+
                      recovered["source_lesson"]+
                      " tersalin Solat Berjemaah Tahun 5. DSKP Tahun 6 SK4.2 "
                      "ialah Solat Ketika Sakit. L060 menggunakan pengukuhan "
                      "situasi berbeza serta rubrik PBD; L059 telah mengajar "
                      "SP4.2.3–5. RPH V5 masih ditahan, guru tidak menerima "
                      "bahan ini sehingga audit penerbitan siap. Minggu cadangan.")
            else:
                raise ValueError("Unknown PI held recovery kind")
        else:
            sk=str(field.get("sk") or "").strip()
            sp=str(field.get("sp") or "").strip()
            topic=str(field.get("objektif") or "").strip()
            note=("Bahan: "+str(field.get("bahan") or "").strip()+
                  " | Penilaian: "+str(field.get("pentaksiran") or "").strip())
            if not sk or not sp or not note:
                raise ValueError(f"PI T{year} PdP{n:03d}: original SK/SP/notes absent")
        b=re.search(r"Bidang:\s*(.*?)\s*(?:•|$)",intro)
        unit="Bidang: "+(recovered["unit"] if withheld else
                         (b.group(1).strip() if b else "Belum dinyatakan dalam sumber"))
        rows.append(dict(
            id=f"{n:03d}",week=week,unit=unit,topic=topic[:350],
            sk=sk,sp=sp,note=note[:630],source_status=r.get("state"),
            source_held=withheld,
            held_source_proposal=bool(withheld),
            held_release_approved=False if withheld else None,
            **dates(master,week)
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
    # Every SP code has a verified original DSKP PDF page anchor.
    # A page anchor is NOT permission to invent or silently OCR its Arabic text.
    ledger=json.loads((ROOT/"audits/bahasa_arab_rpt2027_y2_y6_117_sp_pdf_page_evidence_20261107.json").read_text(encoding="utf-8"))
    if ledger.get("status")!="STAGING_117_CODE_AND_PDF_PAGE_VERIFIED_ONLY" or ledger["summary"]["full_arabic_statement_signoffs"]!=0:
        raise ValueError("Arabic source-page ledger unexpectedly promoted to approved text")
    indexed=ledger["year2"] if year==2 else next((v for v in ledger["years"] if v["year"]==year),None)
    if indexed is None:
        raise ValueError("Missing Arabic DSKP source-page index for year")
    source_pages={e["sp_code"]:e["pdf_page"] for e in indexed["entries"]}
    # Year2/3/4/5/6 original DSKP PDFs were read visually and locked to SHA + source
    # page anchors. These are strictly DRAFT transcription CANDIDATES, never
    # subject-panel-approved SK/SP or permission to publish teachers' RPT.
    visual_candidates={}
    if year in (2,3,4,5,6):
        expected_visual={
            2:(19,18,1,{"3.4.1"},
               "audits/bahasa_arab_rpt2027_t2_19_sp_visual_statement_candidates_20261108.json"),
            3:(23,20,3,{"2.3.1","2.3.2","2.3.3"},
               "audits/bahasa_arab_rpt2027_t3_23_sp_visual_statement_candidates_20261108.json"),
            4:(25,25,0,set(),
               "audits/bahasa_arab_rpt2027_t4_25_sp_visual_statement_candidates_20261108.json"),
            5:(25,25,0,set(),
               "audits/bahasa_arab_rpt2027_t5_25_sp_visual_statement_candidates_20261108.json"),
            6:(25,25,0,set(),
               "audits/bahasa_arab_rpt2027_t6_25_sp_visual_statement_candidates_20261108.json"),
        }
        count,display_count,held_count,held_codes,relative=expected_visual[year]
        visual=json.loads((ROOT/relative).read_text(encoding="utf-8"))
        entries=visual.get("entries") or []
        summary=visual.get("summary") or {}
        visual_candidates={x["sp_code"]:x for x in entries}
        actual_held={x["sp_code"] for x in entries
                     if x.get("candidate_for_staging_display") is False}
        if (visual.get("status")!="VISUAL_TRANSCRIPTION_CANDIDATE_ONLY_NOT_ACADEMIC_FINAL"
            or visual.get("source_pdf_sha256")!=indexed["pdf_sha256"]
            or visual.get("source_url")!=indexed["source_url"]
            or (year in (3,4,5,6) and visual.get("source_pdf_pages")!=indexed["pdf_page_count"])
            or len(entries)!=count or len(visual_candidates)!=count
            or set(visual_candidates)!=set(source_pages)
            or summary.get("unique_sp")!=count
            or summary.get("visual_candidates")!=count
            or summary.get("candidate_for_staging_display")!=display_count
            or summary.get("held_source_conflict")!=held_count
            or summary.get("academic_panel_signoffs")!=0
            or summary.get("sk_full_statement_signoffs")!=0
            or summary.get("rpt_release_ready") is not False
            or actual_held!=held_codes
            or sum(x["candidate_for_staging_display"] is True for x in entries)!=display_count
            or any(x["pdf_page"]!=source_pages[x["sp_code"]]
                   or x.get("academic_panel_signed_off") is not False
                   or x.get("inspected_rendered_page") is not True
                   or not x.get("visual_transcription_candidate","").startswith("القدرة على ")
                   for x in entries)):
            raise ValueError(f"Year{year} Arabic visual source evidence changed: fail closed")
        if year==3:
            # Publisher's 2.3.1-2.3.3 phrases duplicate syllable SP2.2,
            # despite SK[2.3] reading words. Keep those RPT cells on HOLD.
            for code,original in {"2.3.1":"2.2.1","2.3.2":"2.2.2",
                                  "2.3.3":"2.2.3"}.items():
                if (visual_candidates[code]["visual_transcription_candidate"]
                    !=visual_candidates[original]["visual_transcription_candidate"]):
                    raise ValueError("Year3 DSKP duplicated syllable text changed; re-audit source")
    source_pdf_url=indexed["source_url"]
    source_pdf_sha256=indexed["pdf_sha256"]
    source_page_count=indexed["pdf_pages"] if year==2 else indexed["pdf_page_count"]
    if len(source_pages)!=len(indexed["entries"]) or any(
        type(pg) is not int or pg < 1 or pg > source_page_count for pg in source_pages.values()
    ):
        raise ValueError("Invalid Arabic DSKP code-page evidence")
    if (not re.fullmatch(r"https://drive\.google\.com/file/d/[A-Za-z0-9_-]{20,}/view",
                             source_pdf_url)
        or not re.fullmatch(r"[0-9a-f]{64}",source_pdf_sha256)):
        raise ValueError("Arabic original PDF link/checksum malformed")
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
        sp_code=left["sp"].strip()
        if sp_code not in source_pages:
            raise ValueError(f"Arabic T{year} PdP{n:03d}: SP has no source DSKP page")
        # Source-page and SHA-locked DSKP transcription candidate only.
        # Held Year2/3 codes are never promoted or rewritten from context.
        # A displayed visual candidate is NOT academic-release approval.
        candidate=visual_candidates.get(sp_code)
        use_visual=bool(candidate and candidate["candidate_for_staging_display"])
        draft_sp_display=(sp_code+" — "+candidate["visual_transcription_candidate"]
                          if use_visual else
                          sp_code+" — Pernyataan penuh SP belum dipadankan")
        rows.append(dict(
            id=f"{n:03d}",week="",unit=f"Unit {no}: {titles[no]}",
            topic=left["fokus"],sk=left["sk"],sp=left["sp"],
            sk_display=left["sk"]+" — Pernyataan penuh SK belum dipadankan",
            sp_display=draft_sp_display,
            note=("BT m/s: "+(left.get("halaman_buku") or "belum disahkan")+
                  f" (calon). DSKP SP PDF hlm {source_pages[sp_code]} (kod disemak; teks belum disahkan). "+
                  "Tarikh A/B belum diperuntukkan. DRAF."),
            source_sp_dskp_pdf_page=source_pages[sp_code],
            source_sp_dskp_pdf_url=source_pdf_url,
            source_sp_dskp_pdf_sha256=source_pdf_sha256,
            source_sp_dskp_text_signoff=False,
            source_sp_visual_candidate_staging=use_visual,
            source_sp_academic_panel_signed_off=False,
            source_pdf_extraction_code_repeated_unreliable=(year==2),
            source_status=left["status_rpt"],
        ))
    validate_rows("bahasa_arab",year,rows)
    return rows

def _music_status_for_pdf(original):
    """Human-readable display only; original source status stays in source_status."""
    risk="RISIKO CALON HARI PDP 0/16 NEGERI - PDP ANJAL; JANGAN ANJAK AUTOMATIK"
    has_risk=risk in original
    display=original.replace("; "+risk,"").replace(risk,"").strip(" ;")
    labels={
        "RPT_2025_26_BELUM_BUKU_DAN_AUDIO_VERIFIED":
            "Padanan buku teks/audio sumber 2025–26 belum disahkan; DRAF",
        "DRAF_STAGING_BOOK_AND_RPT_NOT_FINAL":
            "Kandungan buku/RPT masih draf",
        "CADANGAN_PENGUKUHAN_BUKAN_PROJEK_RASMI":
            "Pengukuhan pilihan, bukan projek rasmi; DRAF",
    }
    display=labels.get(display,display)
    if has_risk:
        display+="; Slot berisiko cuti negeri — PdP anjal, jangan alih automatik"
    return display

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
        official=music_full_standard_display(year,sp)
        unit=field(r,"Unit","Unit/Tajuk").strip()
        status=field(r,"Semakan","Status tambahan","Status Semakan")
        display_status=_music_status_for_pdf(status)
        book=field(r,"BT m/s","RPT halaman BT (belum sah)","Buku Teks m/s")
        audio=r.get("Audio cetak atau RPT",r.get("Audio Tercetak",""))
        output.append(dict(
            id=f"{n:03d}",week=matches[0],unit="Unit/Tajuk: "+unit,
            topic="PdP Seni Muzik "+f"{n:03d}",
            sk=official["sk"],sk_display=official["sk_display"],
            sp=official["sp"],sp_display=official["sp_display"],
            note=("BT m/s: "+book+" (draf). " +
                  ("Audio: "+audio+". " if audio else "")+display_status+
                  (" | "+official["source_note"] if official["source_note"] else ""))[:660],
            source_rpt_sp_codes=sp,source_status_original=status,
            dskp_text_source="KPM_MUSIC_DSKP_PDF_PRINTED_SK_SP_STAGING_ONLY",
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
            # A merged week group must not exceed the landscape page height.
            # For dense BM and Jawi PI, repeat the week label on a new sub-group
            # rather than hiding/losing PdP rows across a page break.
            build_preview(sub,year,rows,file,
                          max_span_rows=(2 if sub in ("bahasa_melayu","pendidikan_islam") else None))
            results.append((sub,year,len(rows),str(file)))
    if len(results)!=20:
        raise ValueError("Incomplete 20 PDF RPT rendering")
    return results

if __name__=="__main__":
    for sub,year,n,p in build_all():
        print(f"RPT_REMAINING: {sub} year={year} rows={n} file={p}")
