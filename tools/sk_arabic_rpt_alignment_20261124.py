"""Read-only gate: compare all revised Arabic SK RPT rows against current RPH files."""
import json
import re
import hashlib
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits/sk_arabic_rpt_index_revision_delta_20261124.json"
COUNTS = {2:60,3:60,4:58,5:60,6:60}
FIELDS = ("sk","sp","fokus","halaman_buku")

def main():
    delta = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert delta["status"] == "QA_ONLY_NOT_PUBLISHED"
    evidence = []
    errors = []
    for group in ("A", "B"):
        data = delta["groups"][group]
        with (ROOT / data["source_path"]).open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        index = {(int(r["tahun"]),r["pdp"]):r for r in rows}
        assert len(index) == len(rows) == 298
        assert all(sum(int(r["tahun"])==y for r in rows)==n for y,n in COUNTS.items())
        assert len(data["changes"]) == 64
        for change in data["changes"]:
            key = (change["tahun"],change["pdp"])
            row = index[key]
            assert row["kumpulan"] == group
            assert all(row[k] == change["current"][k] for k in FIELDS)
            path = ROOT / change["rph"]
            raw = path.read_bytes()
            content = raw.decode("utf-8")
            sp = re.search(r"\*\*DSKP SK/SP:\*\*\s*(\d+\.\d+)\s*/\s*(\d+\.\d+\.\d+)(?:\s*[—–-]\s*([^\n]+))?",content)
            present = {field: bool(re.search(r"\*\*"+re.escape(field)+r":\*\*\s*\S",content)) for field in
                       ("Objektif pembelajaran","Kriteria kejayaan","Pengukuhan / Penilaian (PBD)")}
            ok = bool(sp and sp[1]==row["sk"] and sp[2]==row["sp"] and all(present.values()))
            record = {"group":group,"year":key[0],"pdp":key[1],"rph":change["rph"],
                      "sha256":hashlib.sha256(raw).hexdigest(),"expected_sk":row["sk"],"expected_sp":row["sp"],
                      "actual_sk":sp[1] if sp else None,"actual_sp":sp[2] if sp else None,
                      "short_statement":sp[3].strip() if sp and sp[3] else None,
                      "required_sections":present,"pass":ok}
            evidence.append(record)
            if not ok: errors.append(record)
    assert len(evidence)==128
    assert len({(r["year"],r["pdp"]) for r in evidence})==64
    dest=ROOT/"qa-arabic-rpt"
    dest.mkdir(exist_ok=True)
    (dest/"alignment.json").write_text(json.dumps({"status":"QA_ONLY_NOT_DSKP_APPROVAL",
        "passed":sum(r["pass"] for r in evidence),"total":len(evidence),"errors":errors,
        "rows":evidence},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Matched",sum(r["pass"] for r in evidence),"of 128 A/B records (64 unique PdP)")
    if errors:
        print(json.dumps(errors,ensure_ascii=False))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
