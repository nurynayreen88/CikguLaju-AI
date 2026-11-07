"""Extra Sains 2027 DSKP appendix for 80 unique SP absent from 342 historical PdP.

No fabricated PdP or teaching dates. Contains full sourced SK/SP statements and
separates 51 crosscutting process/manipulative skills from 29 topic standards.
Standalone staging PDFs; existing 342-PdP RPT PDFs remain unchanged.
"""
from pathlib import Path

from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows
from scripts.audit_sains_rpt2027_uncovered_verified_sp_staging import audit_coverage, ROOT

OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_80_sp_not_covered_DSKP_REFERENCE_DRAF"
EXPECTED={4:(31,17,14),5:(24,17,7),6:(25,17,8)}

def supplementary_sains_rows(year:int,audit=None):
    if year not in EXPECTED:
        raise ValueError("Only Sains T4–T6 have this source SP coverage deficit")
    data=audit if audit is not None else audit_coverage()
    if data.get("status")!="STAGING_ONLY_UNCOVERED_STANDARDS_NOT_PLANNED_LESSONS" or data.get("full_2027_rpt_ready") is not False:
        raise ValueError("Unsafe DSKP source or premature academic release approval")
    section=data["years"][str(year)]
    groups=(
        ("KPS/MANIPULATIF",section["crosscutting_kps_need_per_lesson_activity_evidence"]),
        ("KANDUNGAN TOPIK",section["subject_content_requires_textbook_rph_reconciliation"]),
    )
    records=[]
    for kind,items in groups:
        for item in items:
            code=item["sp_code"]
            sk=item["sk_code"]
            text=item["sp_text"].strip()
            sk_text=item["sk_text"].strip()
            if not code or not text or not sk_text or not sk:
                raise ValueError("Missing original verified DSKP statement")
            n=len(records)+1
            category_note=("Perlu diintegrasi ke aktiviti sebenar dalam PdP lain; bukan Lesson baharu."
                           if kind=="KPS/MANIPULATIF" else
                           "SP kandungan belum diwakili dalam PdP v25.82; perlu RPH, tajuk buku teks dan urutan PdP yang dipersetujui.")
            records.append({
                "id":f"{n:03d}","unit":f"{kind} | SK {sk}: {sk_text}",
                "topic":f"SP {code} belum diwakili dalam 342 PdP sumber",
                "sk":sk,"sp":code,
                "sk_display":f"{sk} — {sk_text}",
                "sp_display":f"{code} — {text}",
                "week":"","a_start":"","a_end":"","b_start":"","b_end":"",
                "note":f"RUJUKAN DB LEGACY (bukan pengesahan KSSR2017): {category_note} Kod mesti dipadankan semula kepada DSKP asal. Lampiran audit sahaja, tiada tarikh kelas. {item['source']}.",
                "gap_kind":kind,"assigned_to_existing_pdp":False,
                "academic_signoff":False,
            })
    total,skills,content=EXPECTED[year]
    if len(records)!=total or sum(r["gap_kind"]=="KPS/MANIPULATIF" for r in records)!=skills or sum(r["gap_kind"]=="KANDUNGAN TOPIK" for r in records)!=content:
        raise ValueError("Expected exact Sains crosscutting/content SP gap partition")
    validate_rows("sains",year,records)
    return records

def build_all(out_dir=OUT):
    data=audit_coverage()
    paths=[]
    for year in EXPECTED:
        rows=supplementary_sains_rows(year,data)
        destination=Path(out_dir)/f"RPT_SAINS_TAHUN_{year}_2027_{len(rows)}_SP_DSKP_BELUM_DILIPUTI_LAMPIRAN_DRAF.pdf"
        build_preview("sains",year,rows,destination)
        paths.append((year,rows,destination))
    if sum(len(rows) for _,rows,_ in paths)!=80:
        raise ValueError("Sains gap appendix must contain 80 unique year-specific SP")
    return paths

if __name__=="__main__":
    for year,rows,path in build_all():
        print(f"SAINS YEAR {year}: {len(rows)} unrepresented original DSKP SP -> {path}")
