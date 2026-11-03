"""Fail-closed QA for Bahasa Melayu RPT/RPH 2027. Read-only.

    python tools/qa_bm_2027_readiness.py structure
    python tools/qa_bm_2027_readiness.py ready
"""
from pathlib import Path
import html
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {2:164, 3:165, 4:165, 5:166, 6:165}
BASE = ROOT/"rpt_2027"/"bahasa_melayu"


def audit(mode="structure"):
    if mode not in ("structure","rph","ready"):
        raise ValueError(mode)
    errors, summary = [], {}
    manifest = json.loads((BASE/"READY_GATE.json").read_text(encoding="utf-8"))
    for year, count in COUNTS.items():
        stem=BASE/"keluaran_format_english"/f"RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF"
        md=stem.with_suffix(".md").read_text(encoding="utf-8")
        page=stem.with_suffix(".html").read_text(encoding="utf-8")
        weeks=re.findall(r"^### M(\d\d)\b",md,re.M)
        if weeks != [f"{n:02d}" for n in range(1,45)]:
            errors.append(f"T{year}: weeks not M01-M44")
        rows=[]
        for line in md.splitlines():
            if not line.startswith("| **Lesson "):
                continue
            fields=[v.strip() for v in line.split("|")]
            if len(fields) != 9:
                errors.append(f"T{year}: invalid row format")
                continue
            match=re.fullmatch(rf"\*\*Lesson (\d{{3}})\*\* \(BM{year}-P(\d{{3}})\)",fields[1])
            if not match or match.group(1)!=match.group(2):
                errors.append(f"T{year}: invalid Lesson ID")
                continue
            rows.append((int(match.group(1)),*fields[2:8]))
        htmlrows=[]
        pattern=(rf'<tr><td class="id">Lesson (\d{{3}})<div class="sub">'
                 rf'BM{year}-P(\d{{3}})</div></td>((?:<td>.*?</td>){{6}})</tr>')
        for item in re.finditer(pattern,page):
            values=[html.unescape(x) for x in re.findall(r"<td>(.*?)</td>",item.group(3))]
            htmlrows.append((int(item.group(1)),*values))
        if len(rows)!=count or [r[0] for r in rows]!=list(range(1,count+1)):
            errors.append(f"T{year}: expected {count} sequenced Lessons, got {len(rows)}")
        if rows!=htmlrows:
            errors.append(f"T{year}: Markdown/HTML data differ")
        for row in rows:
            number,unit,title,sk,sp,ref,note=row
            skcode=re.match(r"([1-5]\.\d)\b",sk)
            spcode=re.match(r"([1-5]\.\d\.\d)\b",sp)
            if spcode and (not skcode or spcode.group(1)[:3]!=skcode.group(1)):
                errors.append(f"T{year}-P{number:03}: SK/SP mismatch")
            elif not spcode and not (year==2 and title.startswith("Penilaian Tema")):
                errors.append(f"T{year}-P{number:03}: missing SP")
            if re.search(r"\b(?:terhadap|secara|pelb|sesua)\s*$",sp):
                errors.append(f"T{year}-P{number:03}: truncated SP")
        rph_dir=ROOT/"rph_standalone"/"bahasa_melayu"/f"year{year}"
        rph_count=sum(1 for _ in rph_dir.glob("lesson_[0-9][0-9][0-9].md"))
        summary[year]={"rpt":len(rows),"html":len(htmlrows),"weeks":len(weeks),"rph":rph_count,
                       "rph_checked":0, "rph_hold":0, "rph_draft":0, "rph_ready":0}
        if mode in ("rph", "ready"):
            # Verify existing RPH metadata against the canonical RPT; never infer READY from presence.
            by_number = {row[0]:row for row in rows}
            required = ("Set induksi","Aktiviti 1","Aktiviti 2","Tindakan guru",
                        "Tindakan murid","Pengukuhan","PBD","Penutup","Objektif")
            for n in range(1, count+1):
                path = rph_dir/f"lesson_{n:03}.md"
                if not path.is_file():
                    continue
                content = path.read_text(encoding="utf-8")
                summary[year]["rph_checked"] += 1
                expected = by_number.get(n)
                if expected is None:
                    errors.append(f"T{year}-P{n:03}: RPH has no RPT record")
                    continue
                for label, field in (("Tajuk",2), ("SK",3), ("SP",4)):
                    match = re.search(rf"(?m)^\\*\\*{label}:\\*\\*\\s*(.+)$", content)
                    got = re.sub(r"\\s+", " ", match.group(1)).strip() if match else ""
                    want = re.sub(r"\\s+", " ", expected[field]).strip()
                    if got != want:
                        errors.append(f"T{year}-P{n:03}: RPH {label} differs from RPT")
                missing = [word for word in required if word not in content]
                if missing:
                    errors.append(f"T{year}-P{n:03}: incomplete RPH: {', '.join(missing)}")
                status = re.search(r"(?m)^\\*\\*Status(?: QA| audit)?:\\*\\*\\s*(.+)$", content)
                if not status:
                    errors.append(f"T{year}-P{n:03}: missing QA status")
                elif re.search(r"\\bHOLD\\b", status.group(1), re.I):
                    summary[year]["rph_hold"] += 1
                elif re.search(r"\\bDRAF\\b", status.group(1), re.I):
                    summary[year]["rph_draft"] += 1
                elif re.search(r"\\bREADY\\b", status.group(1), re.I):
                    summary[year]["rph_ready"] += 1
                else:
                    errors.append(f"T{year}-P{n:03}: unknown QA status")
        if mode=="ready":
            if rph_count!=count:
                errors.append(f"T{year}: RPH {rph_count}/{count}")
            for n in range(1,count+1):
                path=rph_dir/f"lesson_{n:03}.md"
                if not path.is_file():
                    continue
                text=path.read_text(encoding="utf-8")
                required=("Set induksi","Aktiviti 1","Aktiviti 2","Tindakan guru",
                          "Tindakan murid","Pengukuhan","PBD","Penutup","Objektif")
                if any(word not in text for word in required):
                    errors.append(f"T{year}-P{n:03}: incomplete RPH")
                if re.search(r"\b(?:DRAF|HOLD|BELUM READY)\b",text,re.I):
                    errors.append(f"T{year}-P{n:03}: RPH not approved")
            if "BELUM AGIH" in md:
                errors.append(f"T{year}: unallocated weeks")
            gates=manifest["year_gates"].get(str(year),{})
            for name,flag in gates.items():
                if flag is not True:
                    errors.append(f"T{year}: gate {name} is blocked")
    if mode=="ready" and (manifest.get("status")!="READY_VERIFIED" or
                          manifest.get("verified_strict_ready") is not True):
        errors.append("Global READY status has not been approved")
    return {"passed":not errors,"mode":mode,"summary":summary,"errors":errors}


if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "structure"
    result=audit(mode)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result["passed"] else 1)
