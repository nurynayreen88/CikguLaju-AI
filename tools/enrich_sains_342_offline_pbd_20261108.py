"""Add eight source-locked PBD support Word/PDF sheets to the 342-RPH ZIP.

Does NOT create any official PdP or mark any drafted RPH as approved.
Runs after the existing 342-RPH offline reviewer builder has succeeded.
"""
from __future__ import annotations

from hashlib import sha256
from html import escape
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

from docx import Document
from pypdf import PdfReader

from tools.build_sains_342_offline_review_pack_20261108 import OUT, PORTAL, ZIP
from tools.render_sains_y2_3_unmapped_sp_pbd_20261107 import (
    TASKS as MISSING_Y2, doc_path, load_semantics,
)
from tools.render_sains_y2_2_sp_alternative_pbd_20261107 import (
    TASKS as ALTERNATE_Y2, doc_file,
)
from tools.render_sains_y3_3_secondary_sp_pbd_20261107 import (
    TASKS as SECONDARY_Y3, OUT as SECONDARY_OUT,
    stem as secondary_stem, verify_source as verify_y3,
)

EXPECTED_MISSING={"3.1.4","3.1.5","3.1.6"}
EXPECTED_SECONDARY={"3.2.5","3.3.3","3.3.4"}
EXPECTED_TOTAL=8


def _source_items():
    official=load_semantics()
    verify_y3()
    if (set(MISSING_Y2)!=EXPECTED_MISSING or set(official)!=EXPECTED_MISSING
            or len(ALTERNATE_Y2)!=2 or set(SECONDARY_Y3)!=EXPECTED_SECONDARY):
        raise ValueError("Supplementary SP/PBD source inventory unexpectedly changed")
    rows=[]
    for sp in sorted(MISSING_Y2):
        if official[sp]["scheduled_pdp"] is not None:
            raise ValueError("Unscheduled Year2 SP must not gain invented official PdP")
        rows.append({
            "year":2,"sp":sp,"linked_pdp":None,
            "title":MISSING_Y2[sp]["title"],
            "kind":"SP belum dijadualkan — PBD sokongan asli, BUKAN PdP rasmi",
            "source_category":"YEAR2_UNASSIGNED_DSKP_SP",
            "original_word":doc_path(sp),
        })
    for sp in sorted(ALTERNATE_Y2):
        row=ALTERNATE_Y2[sp]
        rows.append({
            "year":2,"sp":sp,"linked_pdp":row["pdp"],
            "title":row["title"],
            "kind":"PBD alternatif asli — bukan halaman Buku Aktiviti KPM",
            "source_category":"YEAR2_ALTERNATIVE_PBD",
            "original_word":doc_file(sp),
        })
    for sp in sorted(SECONDARY_Y3):
        row=SECONDARY_Y3[sp]
        rows.append({
            "year":3,"sp":sp,"linked_pdp":row["pdp"],
            "title":row["title"],
            "kind":"PBD SP tambahan pada PdP sedia ada, bukan BA rasmi",
            "source_category":"YEAR3_SECONDARY_SP_PBD",
            "original_word":SECONDARY_OUT/(secondary_stem(sp)+".docx"),
        })
    if len(rows)!=EXPECTED_TOTAL or len({(r["year"],r["sp"]) for r in rows})!=EXPECTED_TOTAL:
        raise ValueError("Eight source-specific PBD SP identities must be unique")
    return rows


def _validate_and_copy(item):
    word=Path(item["original_word"])
    pdf=word.with_suffix(".pdf")
    if any(not f.is_file() or f.is_symlink() for f in (word,pdf)):
        raise FileNotFoundError(f"Missing source PBD Word/PDF for SP {item['sp']}")
    doc=Document(str(word))
    section=doc.sections[0]
    if not doc.tables or abs(section.page_width.cm-21)>0.05 or abs(section.page_height.cm-29.7)>0.05:
        raise ValueError("Supplementary PBD Word not A4 "+item["sp"])
    reader=PdfReader(str(pdf))
    if len(reader.pages)!=1:
        raise ValueError("Supplementary PBD PDF not one page "+item["sp"])
    page=reader.pages[0]
    if abs(float(page.mediabox.width)-595.28)>2 or abs(float(page.mediabox.height)-841.89)>2:
        raise ValueError("Supplementary PBD PDF not A4 "+item["sp"])
    text=page.extract_text()
    if any(phrase not in text for phrase in (item["sp"],"Aktiviti 1","Aktiviti 2","Aktiviti 3")):
        raise ValueError("Supplementary PBD content lost exact SP/tasks "+item["sp"])
    result={key:value for key,value in item.items() if key!="original_word"}
    for kind,original in (("word",word),("pdf",pdf)):
        relative=Path("PBD_Sokongan")/f"Tahun_{item['year']}"/original.name
        destination=PORTAL/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(original,destination)
        result[kind]=relative.as_posix()
        result[kind+"_sha256"]=sha256(destination.read_bytes()).hexdigest()
    result.update({
        "academic_status":"DRAF_HOLD",
        "teacher_approved":False,
        "official_pdp_created":False,
        "official_workbook":False,
    })
    return result


def _html(supplements):
    safe=lambda value:escape(str(value),quote=True)
    output=[]
    for row in supplements:
        pdp=row["linked_pdp"] or "Belum dijadualkan; tiada PdP baharu"
        search=f'{row["year"]} {row["sp"]} {row["title"]} {pdp}'.casefold()
        output.append(
            f'<tr data-year="{row["year"]}" data-search="{safe(search)}">'
            f'<td><strong>SP {safe(row["sp"])}</strong><small>Tahun {row["year"]}</small></td>'
            f'<td>{safe(row["title"])}<small>{safe(row["kind"])}</small></td>'
            f'<td><span class="hold">DRAF/HOLD</span><small>{safe(pdp)}</small></td>'
            f'<td class="downloads"><a href="{safe(row["word"])}" download>Word</a>'
            f'<a href="{safe(row["pdf"])}" download>PDF</a></td></tr>'
        )
    return (
        '<section class="notice"><h2>8 bahan PBD sokongan Tahun 2–3</h2>'
        '<p>Tiga SP Tahun 2 belum mempunyai PdP tersendiri dalam 51 PdP asal, '
        'dua bahan alternatif Tahun 2 dan tiga SP tambahan Tahun 3. '
        '<strong>Bukan Buku Aktiviti rasmi, bukan 8 RPH atau PdP baharu.</strong> '
        'Semua lembaran ini menunggu semakan guru/panitia.</p></section>'
        '<div class="table"><table><thead><tr><th>SP/Tahun</th><th>Aktiviti PBD</th>'
        '<th>Status / PdP</th><th>Muat turun</th></tr></thead>'
        '<tbody id="support-rows">'+ "\n".join(output) + '</tbody></table></div>'
    )


def enrich():
    index=PORTAL/"index.html"
    manifest=PORTAL/"MANIFEST_SHA256.json"
    if not ZIP.is_file() or not index.is_file() or not manifest.is_file():
        raise FileNotFoundError("Original 342 RPH review pack must finish successfully first")
    data=json.loads(manifest.read_text(encoding="utf-8"))
    if (len(data.get("items",[]))!=342 or data.get("approved")!=0
        or data.get("status")!="ACADEMIC_HOLD"
        or data.get("supplements") is not None):
        raise ValueError("Original 342-RPH archive is incomplete or already enriched")

    # Validate source and document integrity before writing index/manifest.
    supplements=[_validate_and_copy(x) for x in _source_items()]
    if len(supplements)!=EXPECTED_TOTAL or sum(x["linked_pdp"] is None for x in supplements)!=3:
        raise ValueError("Incomplete Year2 original SP coverage")
    html=index.read_text(encoding="utf-8")
    anchor='<footer>Disediakan daripada sumber RPH CikguLaju'
    if html.count(anchor)!=1 or html.count('document.querySelectorAll(\'tbody tr\')')!=1:
        raise ValueError("Offline portal HTML selector drift")
    html=html.replace('<tbody>\n', '<tbody id="main-pdp-rows">\n',1)
    html=html.replace(anchor,_html(supplements)+'\n'+anchor,1)
    html=html.replace(
        "const rows=[...document.querySelectorAll('tbody tr')];function filter(){",
        "const rows=[...document.querySelectorAll('#main-pdp-rows tr')],support=[...document.querySelectorAll('#support-rows tr')];function filter(){",
        1,
    )
    html=html.replace(
        "counter.textContent=shown+' daripada 342 RPH';}",
        "let shownSupport=0;for(const row of support){const ok=(!v||row.dataset.year===v)&&(!t||row.dataset.search.includes(t));row.hidden=!ok;if(ok)shownSupport++;}"
        "counter.textContent=shown+' daripada 342 RPH · '+shownSupport+' PBD sokongan';}",
        1,
    )
    if 'id="main-pdp-rows"' not in html or 'id="support-rows"' not in html:
        raise ValueError("Offline portal search filters incomplete")
    index.write_text(html,encoding="utf-8")
    data["supplements"]=supplements
    data["supplementary_sp_total"]=EXPECTED_TOTAL
    data["year2_official_missing_sp_supported"]=sorted(EXPECTED_MISSING)
    data["no_new_official_pdp"]=True
    manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    guide=PORTAL/"PANDUAN_SEMAKAN.txt"
    with guide.open("a",encoding="utf-8") as fp:
        fp.write("\n8 BAHAN PBD SOKONGAN: tiga SP T2 (3.1.4–3.1.6) "
                 "belum dijadualkan, dua PBD alternatif T2 dan tiga SP tambahan T3. "
                 "Tiada PdP baharu diwujudkan, semuanya DRAF/HOLD dan bukan Buku Aktiviti KPM.\n")
    with ZipFile(ZIP,"w",ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(PORTAL.rglob("*")):
            if path.is_file():
                archive.write(path,str(Path(PORTAL.name)/path.relative_to(PORTAL)))
    with ZipFile(ZIP) as archive:
        names=set(archive.namelist())
        if len(names)!=342*2+EXPECTED_TOTAL*2+4:
            raise ValueError("Unexpected RPH/PBD ZIP archive file count")
        for row in supplements:
            for kind in ("word","pdf"):
                archive_path=(Path(PORTAL.name)/row[kind]).as_posix()
                if archive_path not in names:
                    raise ValueError("PBD link missing from portable ZIP "+archive_path)
                if sha256(archive.read(archive_path)).hexdigest()!=row[kind+"_sha256"]:
                    raise ValueError("PBD file checksum failed "+archive_path)
    print("SAINS_342_OFFLINE_PBD: 342 RPH Word + 342 PDF and "
          "8 source-locked supplementary Word/PDF (16 docs); "
          "3 Year2 official SP coverage gaps visible with no invented PdP; "
          "0 teacher approvals; all HOLD; offline ZIP "+str(ZIP.stat().st_size)+" bytes")


if __name__=="__main__":
    enrich()
