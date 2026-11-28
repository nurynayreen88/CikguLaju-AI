"""Compare 205 draft records to actual pinned native exporter build_source output.

Read-only, no rendering or source modification. Never authorize release.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tools.audit_science_native_5p_documents_20261128 import inventory, support_inventory, fields

PIN = "207317c6d092561e2ffd07a6d2fb4ef604797030"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    root = args.native_root.resolve()
    commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if commit != PIN:
        raise ValueError("Incorrect native source commit")
    args.out.mkdir(parents=True, exist_ok=False)
    issues = []
    summary = []
    for year in (5, 6):
        # Isolate native imports from QA branch imports. Run real build_source;
        # source itself performs DSKP, calendar, identity and duration checks.
        cmd = ("import json; from staging.sains.tahun%d.eksport_2027 import build_source; "
               "weeks, rows = build_source(); print(json.dumps(rows, ensure_ascii=False))") % year
        raw = subprocess.check_output([sys.executable, "-c", cmd], cwd=root, text=True)
        source = json.loads(raw)
        drafts = inventory(year)
        additions = support_inventory(year, drafts)
        if len(source) != len(drafts):
            raise ValueError("Native source count mismatch")
        full = []
        before = len(issues)
        for r in drafts:
            cid = r["lesson_id"]
            native = source[str(int(cid.rsplit("-", 1)[-1]))]
            s, companion, _ = fields(year, r, additions[cid])
            expected_sp = (native["sp"] + " " + native["sp_text"] if year == 5 else
                " · ".join(code + " " + value for code, value in zip(native["standards"], native["sp_texts"], strict=True)))
            expected = {"sk": native["sk"] + " " + native["sk_text"], "sp": expected_sp,
                        "objective": native["objective"]}
            for key, value in expected.items():
                if s[key] != value:
                    issues.append({"id":cid, "field":key, "native":value, "draft":s[key]})
            for key, draft_key in (("title","title"), ("unit","unit"), ("minutes","minutes"), ("pages","textbook_pages")):
                if native[key] != r[draft_key]:
                    issues.append({"id":cid, "field":key, "native":native[key], "draft":r[draft_key]})
            original_pbd = r["original_pbd"] if year == 5 else r["original"]["pbd"]
            original_materials = r["original_materials"] if year == 5 else r["original"]["materials"]
            if native["pbd"] != original_pbd:
                issues.append({"id":cid,"field":"pbd","native":native["pbd"],"draft":original_pbd})
            if native["materials"] != original_materials:
                issues.append({"id":cid,"field":"materials","native":native["materials"],"draft":original_materials})
            if native["safety"] and native["safety"] not in s["aids_pak21_emk"]:
                issues.append({"id":cid,"field":"safety","native":native["safety"]})
            if year == 6 and cid.endswith("-014"):
                # Special source exporter defers the full PBD until PdP 016.
                effective = native["phases"][3][2]
                if s["criteria"] != effective or companion["phases"]["evaluation"] != effective:
                    issues.append({"id":cid,"field":"deferred_PBD","native":effective})
            elif s["criteria"] != native["pbd"] or companion["phases"]["evaluation"] != native["pbd"]:
                issues.append({"id":cid,"field":"rendered_pbd","native":native["pbd"]})
            full.append({"id":cid,"native_objective":native["objective"],"native_pbd":native["pbd"],
                         "native_materials":native["materials"],"native_safety":native["safety"],
                         "native_closure":native["phases"][-1],"draft_closure":s["closure"],
                         "draft_digest":companion["source_sha256"]})
        summary.append({"year":year,"count":len(full),"issues":len(issues)-before})
        (args.out / f"native_y{year}_comparison.json").write_text(json.dumps(full,ensure_ascii=False,indent=2),encoding="utf-8")
    report = {"status":"PINNED_NATIVE_EXPORTER_FIELD_QA_ONLY","source_commit":commit,"years":summary,
              "issues":issues,"academic_approved":False,"release":False}
    (args.out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return 1 if issues else 0

if __name__ == "__main__":
    raise SystemExit(main())
