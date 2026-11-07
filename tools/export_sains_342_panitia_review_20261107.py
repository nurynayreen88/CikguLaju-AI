"""Export one fail-closed human academic signoff row for all 342 staged Science RPH.

Every source must have actual Word+PDF and A4 print-checked files from CI.
All rubric score columns are intentionally blank; official READY requires
external teacher evidence and authenticated Telegram/Web parity, not CI.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from pypdf import PdfReader

from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT, analyze
from tools.audit_rph80_sains_first_20261107 import EXPECTED, validated_staging_drafts
from tools.sains_buku_aktiviti_mapping_20261107 import load_activity_books,is_direct_sp_match
from tools.sains_y6_textbook_toc_20261107 import cue_for,SOURCE_URL
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import checked_book_pages as checked_year5_textbook_pages
from web.sains_y3_rph_activity_preview_20261106 import checked_book_pages as verified_year3_textbook_pages
from tools.render_sains_y3_3_secondary_sp_pbd_20261107 import TASKS as Y3_SECONDARY_PBD, OUT as Y3_SECONDARY_OUTPUT,stem as y3_secondary_stem
from tools.render_sains_y2_51_rph_draf_20261107 import Y2_SOURCE_CONFLICTS, CORRECTED_CANDIDATE_TITLE, verified_original_textbook_pages
from tools.render_sains_y2_3_unmapped_sp_pbd_20261107 import (
    load_semantics as year2_unmapped_semantics,doc_path as year2_supplement_doc_path
)

OUT=ROOT/"build/rph80_sains_20261107"
FOLDERS={
  2:ROOT/"build/sains_y2_51_rph_DRAF_20261107",
  3:ROOT/"build/sains_y3_45_rph_REVIEW_ONLY_20261106",
  4:ROOT/"build/sains_y4_79_rph_DRAF_20261107",
  5:ROOT/"build/sains_y5_83_rph_DRAF_20261107",
  6:ROOT/"build/sains_y6_84_rph_DRAF_20261107",
}

def get_review_rows():
    source,summary=analyze()
    if len(source)!=342 or summary["decision"]!="HOLD":
        raise RuntimeError("No safe 342 source roster")
    print_proofs=validated_staging_drafts()
    if sum(len(s) for s in print_proofs.values())!=297:
        raise RuntimeError("Year2,4,5,6 print QA incomplete")
    print_y3=ROOT/"build/sains_y3_word_page_count_QA"
    if len(list(print_y3.glob("SAINS_T3_PDP_*_DRAF.pdf")))!=45:
        raise RuntimeError("Year3 LibreOffice Word print proof missing")
    book_mappings=load_activity_books()
    book_year2=verified_original_textbook_pages()
    book_year3=verified_year3_textbook_pages()
    book_year5=checked_year5_textbook_pages()
    result=[]
    for row in source:
        year=int(row["tahun"])
        num=int(row["pdp_number"])
        code=row["pdp_code"]
        if year not in EXPECTED or row["keputusan"]!="HOLD":
            raise RuntimeError("Unexpected source year/status "+code)
        stem=f"SAINS_T{year}_PDP_{num:03d}_DRAF"
        folder=FOLDERS[year]
        word=folder/(stem+".docx")
        pdf=folder/(stem+".pdf")
        if not word.is_file() or not pdf.is_file():
            raise RuntimeError("Missing actual RPH Word/PDF "+code)
        reader=PdfReader(str(pdf))
        if len(reader.pages)!=1:
            raise RuntimeError("RPH PDF not one page "+code)
        page=reader.pages[0]
        if abs(float(page.mediabox.width)-595.28)>2 or abs(float(page.mediabox.height)-841.89)>2:
            raise RuntimeError("RPH PDF not A4 "+code)
        if year==3:
            actual=print_y3/(stem+".pdf")
            if not actual.is_file() or len(PdfReader(str(actual)).pages)!=1:
                raise RuntimeError("Year3 Word physical one-page check missing "+code)
        elif code not in print_proofs.get(year,set()):
            raise RuntimeError("RPH source not linked to printed A4 evidence "+code)
        sp=row["sp"]
        source_sp_tokens=[v.strip() for v in sp.split(",") if v.strip()]
        if not source_sp_tokens or len(source_sp_tokens)>2:
            raise RuntimeError("Unsupported source multi-SP scope "+code)
        multi_sp_warning=""
        book_context=""
        book_page_status="BUKU_TEKS_EXACT_SP_PAGE_NOT_VERIFIED"
        book_source=""
        book_activity=""
        activity_status=""
        pbd_alt=""
        if year in (2,3):
            ba=book_mappings[year].get(code)
            if not ba or ba["sp"] not in source_sp_tokens:
                raise RuntimeError("Workbook is not mapped to any source SP "+code)
            if len(source_sp_tokens)>1:
                secondary=[other for other in source_sp_tokens if other!=ba["sp"]]
                if len(secondary)!=1:
                    raise RuntimeError("Unrecognized source secondary SP "+code)
                extra=secondary[0]
                if extra not in Y3_SECONDARY_PBD or Y3_SECONDARY_PBD[extra]["pdp"]!=code:
                    raise RuntimeError("Year3 secondary SP missing original PBD "+code)
                extra_pdf=Y3_SECONDARY_OUTPUT/(y3_secondary_stem(extra)+".pdf")
                if not extra_pdf.is_file() or len(PdfReader(str(extra_pdf)).pages)!=1:
                    raise RuntimeError("Year3 secondary SP PBD not actually printed single A4 "+code)
                multi_sp_warning=(f"SP BA {ba['sp']} hanya satu daripada SP sumber "
                                  f"{sp}. SP kedua {extra} ada PBD asli "
                                  f"{extra_pdf.name}, DRAF untuk semakan panitia.")
                pbd_alt=str(extra_pdf.relative_to(ROOT))
            book_activity=(f"Buku Aktiviti T{year} m/s {ba['workbook_printed_page']}; "
                           f"PDF p{ba['workbook_pdf_page']}; {ba['activity_title']}")
            activity_status=("PRINTED_SP_CODE_MATCH__PEDAGOGY_APPROVAL_PENDING"
                             if is_direct_sp_match(ba) else "RELATED_DIFFERENT_SP__NOT_FOR_THIS_SP_PBD")
            if len(source_sp_tokens)>1:
                activity_status+="__MULTI_SOURCE_SP_SECONDARY_PBD_PENDING"
            if year==2 and sp in ("4.1.7","6.1.6"):
                pbd_alt=f"Original CikguLaju PBD untuk {code}, SP {sp}; bukan Buku Aktiviti rasmi"
        if year==2:
            textbook=book_year2.get(sp)
            if not textbook or textbook["teacher_academic_equivalence_approved"] is not False:
                raise RuntimeError("Year2 textbook visual review source changed "+code)
            book_context=(f"Buku Teks asal m/s bercetak {textbook['printed_page']}, "
                          f"PDF p{int(textbook['pdf_page_one_based'])}; kod SP {sp} dilihat.")
            book_source="https://drive.google.com/file/d/1LkJJWUb-zyFJ1ftpHM-4HIpIcEGLORI9/view"
            book_page_status="PRINTED_PAGE_AND_SP_LABEL_CHECKED__CONTENT_PEDAGOGY_TEACHER_HOLD"
        if year==3:
            book=book_year3.get(code)
            primary=source_sp_tokens[0]
            if not book or book["sp"]!=primary or book["teacher_pedagogical_approved"] is not False:
                raise RuntimeError("Year3 source textbook SP visual audit invalid "+code)
            pages=", ".join(map(str,book["printed_page_candidates"]))
            book_context=f"Buku Teks asal m/s {pages}; SP utama {primary} dilihat pada sekurang-kurangnya satu halaman."
            book_source="https://drive.google.com/file/d/17QNqKZjSF7V9GzzkXkz46bDJGnyKYq-F/view"
            book_page_status="ORIGINAL_BOOK_PAGE_SP_LABEL_CHECKED__TEACHER_CONTENT_SIGNOFF_PENDING"
        if year==5:
            rec=book_year5.get(sp)
            if not rec or rec["teacher_academic_approved"] is not False:
                raise RuntimeError("Year5 original book SP source not verified "+code)
            book_context=("Buku Teks T5 SK asal 2020, m/s bercetak " +
                          ", ".join(map(str,rec["printed_pages"])) +
                          "; kod SP muncul dalam teks PDF asal 3 bahagian. Semantik/PBD belum sah.")
            book_source="; ".join((
                "https://drive.google.com/file/d/1m5k8gVkNImT8QEdw6fCEVpQh_tNkUKUT/view",
                "https://drive.google.com/file/d/1xvpW8HgqrTdrl8QJCHUx0pDIiyuBLjIJ/view",
                "https://drive.google.com/file/d/1YnwPPyyLoGCzP_m3izeB_PFn3w7XGsPt/view"))
            book_page_status="83_SOURCE_SP_PDF_TEXT_CODE_MATCH__TEACHER_PEDAGOGY_HOLD"
        if year==6:
            topic=cue_for(sp)
            book_context=(f"Tajuk '{topic['topic']}', julat m/s "
                          f"{topic['range_start']}-{topic['range_end']} (TOC SAHAJA)")
            book_source=SOURCE_URL
            if topic["exact_sp_page"] is not None:
                raise RuntimeError("Fake verified Year6 textbook page "+code)
        source_anomaly=Y2_SOURCE_CONFLICTS.get(sp,"") if year==2 else ""
        candidate_title=CORRECTED_CANDIDATE_TITLE.get(sp,row["tajuk"]) if year==2 else row["tajuk"]
        result.append({
            "Tahun":year,"Kod PdP":code,"Unit":row["unit"],"SK":row["sk"],
            "SP":sp,"Tajuk PdP":row["tajuk"],
            "Tajuk calon dalam RPH":candidate_title,
            "Amaran konflik sumber asal":source_anomaly,
            "Word RPH staging":str(word.relative_to(ROOT)),
            "PDF RPH staging":str(pdf.relative_to(ROOT)),
            "QA cetakan Word/PDF":"SINGLE_A4_TECHNICAL_PASS",
            "Buku Teks — julat topik untuk carian":book_context,
            "Buku Teks — sumber":book_source,
            "Buku Teks — status muka surat SP":book_page_status,
            "Buku Aktiviti — tajuk/muka surat":book_activity,
            "Buku Aktiviti — status SP":activity_status,
            "Isu SP berganda":multi_sp_warning,
            "PBD alternatif asli (jika berkaitan)":pbd_alt,
            "Semak SP penuh DSKP":"BELUM DISAHKAN PANITIA",
            "Semak muka surat Buku Teks tepat":"BELUM",
            "Semak pelaksanaan Aktiviti 1/2":"BELUM",
            "Semak KPS dan bukti PBD individu":"BELUM",
            "Semak keselamatan dan tahap murid":"BELUM",
            "Semak RPT/2027/negeri":"BELUM",
            "Semak muat turun Web–Telegram":"BELUM",
            "Mata SK/SP (maks 25)":"",
            "Mata Buku Teks/RPT (maks 25)":"",
            "Mata Aktiviti/PBD (maks 25)":"",
            "Mata Word/PDF (maks 15)":"",
            "Mata Web/Telegram (maks 10)":"",
            "Jumlah disahkan (maks 100)":"",
            "Semakan guru/panitia": "",
            "Tarikh semakan":"",
            "Keputusan":"HOLD — AKADEMIK BELUM DISAHKAN",
            "Aktif di Telegram/Web":False,
        })
    if len(result)!=342 or {str(y):sum(x["Tahun"]==y for x in result) for y in EXPECTED}!={str(y):EXPECTED[y] for y in EXPECTED}:
        raise RuntimeError("Missing/duplicate source in academic queue")
    if sum(x["Buku Aktiviti — status SP"].startswith("RELATED") for x in result)!=2:
        raise RuntimeError("Incorrect number of mismatched workbook SP cases")
    multi=[x for x in result if x["Isu SP berganda"]]
    if len(multi)!=3 or {x["Kod PdP"] for x in multi}!={
       "SCI-Y3-PDP-006","SCI-Y3-PDP-010","SCI-Y3-PDP-011"}:
        raise RuntimeError("Year3 multi-SP curriculum source coverage changed")
    anomalies=[x for x in result if x["Amaran konflik sumber asal"]]
    if len(anomalies)!=2 or {x["SP"] for x in anomalies}!={"3.1.3","10.1.6"}:
        raise RuntimeError("Unaccounted Year2 source DSKP semantic conflicts")
    if any(x["Jumlah disahkan (maks 100)"] or x["Semakan guru/panitia"] for x in result):
        raise RuntimeError("Academic grades must not be generated by code")
    return result

def get_unassigned_year2_unit3_queue():
    """3 known KPM content SPs, intentionally NOT among 342 official source PdPs."""
    semantic=year2_unmapped_semantics()
    result=[]
    for sp in sorted(semantic):
        rec=semantic[sp]
        word=year2_supplement_doc_path(sp)
        pdf=word.with_suffix(".pdf")
        if not word.is_file() or not pdf.is_file() or len(PdfReader(str(pdf)).pages)!=1:
            raise RuntimeError("Year2 unscheduled original SP supplementary PBD not rendered: "+sp)
        result.append({
            "Tahun":2,
            "SK":"3.1","SP":sp,
            "Penyataan SP DSKP":rec["official_dskp_text"],
            "Kod PdP rasmi (jika disahkan)":"",
            "Status jadual":"SP DSKP ADA / TIADA PDP BERASINGAN DALAM 51 SUMBER ASAL",
            "BT sumber asal m/s bercetak":",".join(map(str,rec["verified_textbook_printed_pages"])),
            "BA sumber asal m/s bercetak":",".join(map(str,rec["verified_activity_book_printed_pages"])),
            "Bukti halaman & SP buku":"DILIHAT — KANDUNGAN/PBD MASIH PERLU PANITIA",
            "Adaptasi etika murid":rec["pedagogical_privacy_adaptation"],
            "Word bahan sokongan":str(word.relative_to(ROOT)),
            "PDF bahan sokongan":str(pdf.relative_to(ROOT)),
            "Sumber buku teks tepat":"BELUM DISAHKAN",
            "Semak penempatan dalam RPT 2027":"BELUM",
            "Semak kesesuaian bukti PBD dan privasi":"BELUM",
            "Guru/panitia": "",
            "Tarikh": "",
            "Keputusan":"HOLD — BUKAN PdP RASMI / BELUM DILULUSKAN",
            "Kelulusan kandungan":False
        })
    if len(result)!=3:
        raise RuntimeError("Missing one of three Year2 KPM SP supplemental tasks")
    return result

def main():
    records=get_review_rows()
    OUT.mkdir(parents=True,exist_ok=True)
    dst=OUT/"SAINS_342_PANITIA_SEMAKAN_MANUAL_HOLD.csv"
    with dst.open("w",encoding="utf-8-sig",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=list(records[0]))
        wr.writeheader();wr.writerows(records)
    supplementary=get_unassigned_year2_unit3_queue()
    supplement_file=OUT/"SAINS_TAHUN2_UNIT3_3_SP_BELUM_PDP_SEMAKAN_PANITIA_HOLD.csv"
    with supplement_file.open("w",encoding="utf-8-sig",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=list(supplementary[0]))
        wr.writeheader();wr.writerows(supplementary)
    summary={
        "year2_missing_standalone_content_sp":[x["SP"] for x in supplementary],
        "year2_original_unit3_sp_extra_review_rows":3,
        "supplementary_review_queue":supplement_file.name,
        "year2_original_pdp_source_count_unchanged":51,
        "year_counts":{str(y):EXPECTED[y] for y in EXPECTED},
        "total_word_pdf_rph":342,"technical_A4":342,
        "year2_textbook_printed_page_and_sp_visual_match":51,
        "year2_textbook_unique_original_pages_examined":43,
        "year2_textbook_content_teacher_approved":0,
        "year3_original_textbook_sp_code_page_visual_match":45,
        "year3_unique_original_book_pages_examined":54,
        "year3_supplemental_sp_textbook_labels_verified":3,
        "year3_textbook_content_teacher_approved":0,
        "year5_original_3part_printed_page_coverage":234,
        "year5_sp_pdf_text_page_matches":83,
        "year5_unique_sp_matched_printed_pages":103,
        "year5_textbook_pedagogy_teacher_approved":0,
        "year6_textbook_topic_toc_only":84,
        "year6_exact_textbook_sp_page_approved":0,
        "activity_book_y2_y3_matched_code":94,
        "activity_book_y2_y3_related_only":2,
        "year3_multiple_sp_lessons_needing_secondary_pbd":3,
        "year2_dskp_legacy_title_conflicts":2,
        "year3_original_secondary_sp_pbd_printed_a4":3,
        "teacher_approved":0,"academic_80_percent_certified":0,
        "auth_web_telegram_e2e_verified":False,
        "runtime_release":"HOLD","database_write":False,
        "filename":dst.name,
    }
    (OUT/"SAINS_342_PANITIA_APPROVAL_GATE_HOLD.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_342_PANITIA: 342 Word/PDF A4 checked, 342 human academic checks HOLD")

if __name__=="__main__":
    main()
