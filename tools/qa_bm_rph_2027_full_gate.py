#!/usr/bin/env python3
"""Non-destructive QA gate for 825 Bahasa Melayu RPH and 2027 RPT records.

The DSKP code index was extracted on 2026-11-04 from five original SK
DSKP PDF files in the project's connected Drive. Passing this mechanical
gate DOES NOT attest to the academic correctness of source activity pages.
"""
from pathlib import Path
import json, re, collections, hashlib

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"rpt_2027/bahasa_melayu/keluaran_format_english"
RPH=ROOT/"rph_standalone/bahasa_melayu"
OUT=ROOT/"audits/bm_rph_2027_825_gate_20261104.json"
EXPECTED={2:164,3:165,4:165,5:166,6:165}
BASE_CODES="""1.1.1 1.1.2 1.1.3 1.1.4 1.2.1 1.2.2 1.2.3 1.2.4 1.2.5 1.2.6 2.1.1 2.1.2 2.2.1 2.3.1 2.3.2 3.1.1 3.2.1 3.2.2 3.2.3 3.2.4 3.3.1 3.3.2 4.1.1 4.2.1 4.2.2 4.2.3 4.3.1 4.3.2 4.3.3 5.1.1 5.1.2 5.1.3 5.1.4 5.2.1 5.2.2 5.2.3 5.3.1 5.3.2""".split()
UPPER_CODES="""1.1.1 1.1.2 1.1.3 1.1.4 1.2.1 1.2.2 1.2.3 1.2.4 1.2.5 1.2.6 1.3.1 1.3.2 2.1.1 2.2.1 2.3.1 2.3.2 3.1.1 3.2.1 3.2.2 3.2.3 3.2.4 3.3.1 3.3.2 4.1.1 4.2.1 4.2.2 4.3.1 4.3.2 4.3.3 4.4.1 4.4.2 5.1.1 5.1.2 5.1.3 5.1.4 5.2.1 5.2.2 5.2.3 5.3.1 5.3.2 5.3.3 5.3.4""".split()
DSKP={
  2:set(BASE_CODES),3:set(BASE_CODES),
  4:set(UPPER_CODES),
  5:set(UPPER_CODES+["2.1.2"]),
  6:set(UPPER_CODES+["2.1.2"]),
}
DSKP_SHA256={
2:"c842c22b745ed2c2ea4a6da9932494b97cb62e4eb3937832840fe81c66c32522",
3:"d8498c616447323d7e98c9940b369faeaab2e7e20ab499567943cb16baffa7a7",
4:"42af399fc0abae7a49d81d8a0202fa1249592326e62b92c52bad200c59986373",
5:"28683e60e201838550c760f69388bbe73fe60510e70f311aed957b5f81cb4c7d",
6:"db151ef90a7fcdd8d8b9079a32473ae54c9276d12621d369cf329cc8fe6b24d9"}
CODE=re.compile(r"\b[1-5]\.\d(?:\.\d)?\b")
def key(s):
    return re.sub(r"[\W_]+","",s.casefold().replace("**",""))
def field(text,labels):
    lines=text.splitlines()
    for label in labels:
        for line in lines:
            m=re.match(r"^\*\*"+re.escape(label)+r":\*\*\s*(.+?)\s*$",line)
            if m:return m.group(1).strip()
    return ""
def rpt_rows(year):
    t=(SRC/f"RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF.md").read_text(encoding="utf-8")
    rows={}
    week=""
    weeks=set()
    for line in t.splitlines():
        w=re.match(r"^### M(\d\d)\b",line)
        if w:week=w.group(1);weeks.add(week)
        m=re.match(r"^\| \*\*PdP (\d{3})\*\* \(BM\d-P\d{3}\) \|",line)
        if not m:continue
        fields=[v.strip().replace("**","") for v in line.strip().strip("|").split("|")]
        if len(fields)!=7:raise ValueError((year,"invalid RPT row",line))
        n=int(m.group(1))
        if n in rows:raise ValueError((year,"duplicate",n))
        rows[n]={"week":week,"title":fields[2],"sk":fields[3],"sp":fields[4],"theme":fields[1],"refs":fields[5],"notes":fields[6]}
    assert len(weeks)==44,(year,len(weeks))
    assert list(rows)==list(range(1,EXPECTED[year]+1)),(year,"missing RPT row",len(rows))
    return rows

def check():
    report={"scope":"BM SK 2027 Years 2–6","dsdkp_source_hashes":DSKP_SHA256,
            "ready":False,"checks":"DSKP code presence, parent SK consistency, RPT/RPH metadata, RPH structure and source-release barriers",
            "years":{},"unresolved_source_types":[
            "BT page-to-task verification","Buku Aktiviti pages and exercises","DSKP full text and Roman-subcode semantics",
            "PKJR/BPG/BAM source mapping","RPH factual lesson-specificity","2027 state calendar",
            "complete visual Word/PDF proof and real Telegram runtime"
            ]}
    for year,expected in EXPECTED.items():
        rows=rpt_rows(year);errors=[];warnings=[];counts=collections.Counter()
        files=sorted((RPH/f"year{year}").glob("lesson_*.md"))
        if len(files)!=expected:errors.append({"type":"missing_rph_files","expected":expected,"actual":len(files)})
        for n in range(1,expected+1):
            p=RPH/f"year{year}/lesson_{n:03d}.md"
            if not p.exists():errors.append({"pdp":n,"type":"file_missing"});continue
            text=p.read_text(encoding="utf-8")
            row=rows[n]
            sk=field(text,["SK","Standard Kandungan (SK)"])
            sp=field(text,["SP","Standard Pembelajaran (SP)"])
            title=field(text,["Tajuk","Tajuk aktiviti"])
            codesk=CODE.search(sk);codesp=CODE.search(sp)
            if not codesk or not codesp:
                # Three Year 2 thematic assessments have no new official SP in the source.
                if year==2 and n in (23,47,94) and "Penilaian Tema" in sp:
                    counts["thematic_pbd_no_new_sp"]+=1
                else:errors.append({"pdp":n,"type":"no_SK_SP_code","sk":sk[:90],"sp":sp[:90]})
            else:
                s=codesk.group();t=codesp.group()
                if t not in DSKP[year]:errors.append({"pdp":n,"type":"sp_not_in_original_dskp","sp":t})
                if not t.startswith(s+"."):errors.append({"pdp":n,"type":"sk_sp_prefix_conflict","sk":s,"sp":t})
                source_sk=CODE.search(row["sk"]);source_sp=CODE.search(row["sp"])
                if source_sk and source_sk.group()!=s:errors.append({"pdp":n,"type":"rpt_rph_sk_conflict","rpt":source_sk.group(),"rph":s})
                if source_sp and source_sp.group()!=t:errors.append({"pdp":n,"type":"rpt_rph_sp_conflict","rpt":source_sp.group(),"rph":t})
                counts["coded_sp"]+=1
            if title and key(title)!=key(row["title"]):
                # Some earlier RPHs intentionally use clarifying parentheticals; flag for review.
                warnings.append({"pdp":n,"type":"rpt_title_variation","rph":title[:100],"rpt":row["title"][:100]})
            if not all(patt in text for patt in ["Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan","Penutup"]):
                errors.append({"pdp":n,"type":"missing_pedagogical_section"})
            if len(re.findall(r"\*\*(?:Guru|Tindakan guru):\*\*",text))<3 or len(re.findall(r"\*\*(?:Murid|Tindakan murid):\*\*",text))<3:
                errors.append({"pdp":n,"type":"teacher_pupil_actions_missing"})
            if len(text)<700:errors.append({"pdp":n,"type":"too_short"})
            if re.search(r"\bLesson\b",text):warnings.append({"pdp":n,"type":"english_lesson_label"})
            if "Imenulis" in text:errors.append({"pdp":n,"type":"typo_Imenulis"})
            if re.search(r"HOLD",text):counts["contains_hold"]+=1
            if "DRAF" in text:counts["contains_draft"]+=1
            if "PKJR" in row["title"] or "PKJR" in row["notes"]:counts["rpt_pkjr"]+=1
            if year in (4,5,6) and ("BELUM disahkan" in text or "halaman calon" in text):
                counts["needs_full_source_review"]+=1
            if re.search(r"(?m)^\*\*(?:Status QA|Status semakan|Status audit):\*\* READY\b",text):
                errors.append({"pdp":n,"type":"premature_ready"})
            counts["files_seen"]+=1
        report["years"][str(year)]={"expected":expected,"counts":dict(counts),
            "hard_errors":len(errors),"review_warnings":len(warnings),
            "errors":errors,"warnings":warnings}
    gate=ROOT/"rpt_2027/bahasa_melayu/READY_GATE.json"
    state=json.loads(gate.read_text())
    assert state["verified_strict_ready"] is False,"Academic READY requires human evidence, cannot be auto-granted"
    assert sum(r["counts"]["files_seen"] for r in report["years"].values())==825
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for year,r in report["years"].items():
        print("Tahun",year,": files",r["counts"]["files_seen"],"mechanical errors",r["hard_errors"],
              "warnings",r["review_warnings"],r["counts"],flush=True)
    # Fail structural gate, but unresolved academic-source warnings are reported not falsely passed as FINAL READY.
    assert sum(r["hard_errors"] for r in report["years"].values())==0,"BM RPH mechanical integrity failed"
if __name__=="__main__":check()
