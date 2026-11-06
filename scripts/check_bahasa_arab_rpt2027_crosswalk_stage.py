#!/usr/bin/env python3
"""Offline read-only integrity gate for BA RPT2027 *undated* A/B candidate crosswalk."""
import csv
import json
from collections import Counter
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
RPT = BASE / "rpt_2027" / "bahasa_arab"
EXPECTED = {2:60, 3:60, 4:58, 5:60, 6:60}
def rows(p):
    with p.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def main():
    meta = json.loads((RPT/"kalendar_2027_A_B_rujukan_DRAF.json").read_text(encoding="utf-8"))
    assert meta["release_authorized"] is False and meta["rpt_final_ready"] is False
    sources = [RPT/"pdp_001_012_DRAF.csv", *sorted(RPT.glob("year[2-6]_*.csv"))]
    originals = {}
    for p in sources:
        if not p.name.endswith("_DRAF.csv"): continue
        for row in rows(p):
            key=(row["tahun"],row["pdp"])
            assert key not in originals, f"duplicate source: {key}"
            originals[key]=row
    assert len(originals)==298
    # Final release-candidate QA: read every source-backed RPH and detect unsafe gaps.
    # This is a structural gate only, never teacher/DSKP/pedagogic approval.
    units = rows(RPT/"unit_sequence_DRAF_20261105.csv")
    titles = {(r["tahun"], r["unit"]):r["tajuk_arab"] for r in units}
    assert len(titles)==20
    required = ("Set induksi", "Aktiviti 1", "Aktiviti 2",
                "Penutup", "BBM", "Refleksi", "Objektif", "Kriteria kejayaan")
    complete = {2:60, 3:60, 4:58, 5:60, 6:60}
    by_year = Counter()
    problems = []
    warnings = []
    for (year, pdp), row in sorted(originals.items()):
        y, n = int(year), int(pdp)
        by_year[y] += 1
        p = BASE/"rph_standalone"/"bahasa_arab"/f"year{y}"/f"lesson_{n:03d}.md"
        if not p.is_file():
            problems.append(f"Year{y} PdP{n:03d}: missing document")
            continue
        content = p.read_text(encoding="utf-8")
        absent = [word for word in required if word not in content]
        if absent: problems.append(f"Year{y} PdP{n:03d}: missing sections {absent}")
        if (f"Bahasa Arab Tahun {y}" not in content or f"PdP {n:03d}" not in content
                or titles.get((year,row["unit"])) not in content):
            problems.append(f"Year{y} PdP{n:03d}: wrong year/unit/PdP")
        if row["sp"] not in content or row["sk"] not in content:
            problems.append(f"Year{y} PdP{n:03d}: missing proposed SK/SP")
        if "DRAF" not in content or "BELUM READY" not in content:
            problems.append(f"Year{y} PdP{n:03d}: unapproved status escaped")
        if y==6 and ("2021" not in content or "978-983-49-3300-5" not in content):
            problems.append(f"Year6 PdP{n:03d}: correct DBP 2021 book not identified")
        page = row.get("halaman_buku_teks_dicadang", "")
        if not page: warnings.append(f"Year{y} PdP{n:03d}: page provenance not populated")
        elif page not in content: warnings.append(f"Year{y} PdP{n:03d}: page {page!r} needs manual crosscheck")
    assert dict(sorted(by_year.items()))==complete, by_year
    assert len(list((BASE/"rph_standalone"/"bahasa_arab").glob("year[2-6]/lesson_*.md")))==298
    print(f"QA all 298 candidate RPH: structural_errors={len(problems)}, source_page_review_warnings={len(warnings)}")
    for item in problems[:30]: print("BLOCKER:",item)
    for item in warnings[:15]: print("SOURCE_REVIEW:",item)
    assert not problems, "Structural QA blocked. Drafts must not be released."
    # Unit 1 source pages have existing audit provenance, but are still candidates.
    unit1=[r for r in originals.values() if int(r["pdp"]) <= 12]
    assert len(unit1)==60
    assert all(r.get("halaman_buku_teks_dicadang") for r in unit1), "Missing Unit 1 candidate pages"
    assert all(r["halaman_buku_disahkan"]=="FALSE" and r["ready"]=="FALSE" for r in unit1)
    counts=Counter(int(k[0]) for k in originals)
    assert dict(sorted(counts.items()))==EXPECTED, counts
    for group in ("A","B"):
        path=RPT/f"rpt_2027_KUMPULAN_{group}_INDEKS_PDP_DRAF.csv"
        result=rows(path); assert len(result)==298
        keys=set()
        for r in result:
            key=(r["tahun"],r["pdp"]); assert key not in keys; keys.add(key)
            original=originals[key]
            assert r["kumpulan"]==group and r["unit"]==original["unit"]
            assert r["sp"]==original["sp"] and r["sk"]==original["sk"] and r["fokus"]==original["fokus"]
            assert r["halaman_buku"]==original.get("halaman_buku_teks_dicadang","")
            assert r["ready"]=="FALSE" and r["kelulusan_guru"]=="FALSE"
            assert r["status_rpt"]=="DRAF_TARIKH_BELUM_DISAHKAN"
            assert not r["tarikh_pdp_2027"] and not r["waktu_mula"] and not r["waktu_tamat"] and not r["negeri"]
            f=BASE/r["rph_staging"]; assert f.is_file(), f
            src=f.read_text(encoding="utf-8")
            assert r["sp"] in src and "BELUM READY" in src
        assert keys==set(originals)
    print("PASS: 298 unique source IDs x Group A/B = 596 entries; no duplicates/orphans, no invented dates, 0 READY")
    print("BLOCKED: KPM/state holiday audit, period quota, RPT2027 actual dates, teacher per-PdP approval and runtime parity")
if __name__=="__main__": main()
