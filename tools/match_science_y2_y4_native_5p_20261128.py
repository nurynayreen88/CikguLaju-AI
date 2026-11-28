"""Offline only: match actual native Science source identities to 5P draft shortlist.
No source modifications, generated teaching plans, production writes or approval.
Input is parsed JSON payloads from the curriculum-only native identity audit.
"""
import argparse
import json
from pathlib import Path
from hashlib import sha1
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"audits"
COUNTS={2:58,3:54,4:85}
OPENING={2:7,3:9,4:6}

def blob(raw):
    return sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def unpack(chunks):
    grouped={y:{} for y in COUNTS}
    for chunk in chunks:
        y=chunk["year"]
        if type(y) is not int or y not in COUNTS or chunk["total"]!=COUNTS[y]:
            raise ValueError("Unexpected native year/count")
        start=chunk["start"]
        rows=chunk["records"]
        if type(start) is not int or start<0 or start%5 or not isinstance(rows,list) or len(rows)!=min(5,COUNTS[y]-start) or not rows:
            raise ValueError("Incomplete native chunk")
        if start in grouped[y]:
            if grouped[y][start]!=rows:
                raise ValueError("Conflicting duplicate chunk")
        else:
            grouped[y][start]=rows
    result={}
    for y,ch in grouped.items():
        if set(ch)!=set(range(0,COUNTS[y],5)):
            raise ValueError("Missing native source chunks")
        result[y]=[r for i in sorted(ch) for r in ch[i]]
        ids=[r["lesson_id"] for r in result[y]]
        if len(ids)!=COUNTS[y] or len(set(ids))!=COUNTS[y] or any(r["year"]!=y for r in result[y]):
            raise ValueError("Native identities not unique")
        if sum(r["opening"] is True for r in result[y])!=OPENING[y]:
            raise ValueError("Opening count changed")
    return result

def match(chunks,index,opening):
    native=unpack(chunks)
    open_map={(r["year"],r["lesson_id"]):r for r in opening["records"]}
    if len(open_map)!=22:
        raise ValueError("Opening draft count")
    report=[]
    for y,rows in native.items():
        candidates=index["years"][str(y)]
        allowed={r["candidate_id"]:r for r in candidates["records"] if not r["opening_scope"]}
        for r in rows:
            codes=sorted(set(x["sp_code"] for x in r["standards"] if x["sp_code"]))
            key=(y,r["lesson_id"])
            if not codes or not r["title"] or not r["unit"]:
                raise ValueError("Incomplete source identity")
            base={k:r[k] for k in ("year","unit","unit_title","lesson_id","title","standards","textbook_refs","minutes","opening","complete")}
            if r["opening"]:
                d=open_map.pop(key,None)
                if not d or d["title"]!=r["title"] or sorted(d["sp_codes"])!=codes:
                    raise ValueError("Opening draft identity mismatch: "+r["lesson_id"])
                # Confirm the explicitly recorded source reference; no inferred pages.
                if "Buku Teks m/s "+d["textbook_pages"] not in r["textbook_refs"]:
                    raise ValueError("Opening reference drift")
                base.update(status="EXACT_OPENING_ID_TITLE_SP_PAGES",shortlist=[],selected_candidate_id=None)
            else:
                exact=[c for c in candidates["by_exact_sp_set"].get("|".join(codes),[]) if c in allowed]
                partial=sorted({c for sp in codes for c in candidates["by_sp"].get(sp,[]) if c in allowed and c not in exact})
                base.update(status="EXACT_SP_SHORTLIST" if exact else "PARTIAL_SP_SHORTLIST" if partial else "AUTHOR_NEW_PLAN",
                            shortlist=exact,partial_shortlist=partial,selected_candidate_id=None)
            base["ready"]=False
            report.append(base)
    if open_map or len(report)!=197:
        raise ValueError("Opening/source coverage changed")
    return {"status":"NATIVE_SOURCE_IDENTITY_TRIAGE_ONLY","total":197,"opening":22,"remaining":175,
        "duration_unknown":sum(r["minutes"] is None for r in report),
        "source_incomplete":sum(not r["complete"] for r in report),
        "counts_by_status":{s:sum(r["status"]==s for r in report) for s in sorted({r["status"] for r in report})},
        "records":report,"release":False,
        "limitations":"Candidate shortlist is not approved content; verify original RPH teaching fields and actual duration before authoring. No selected candidates or production modifications."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chunks",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    index=json.loads((AUDIT/"rph_5p_science_y2_y3_y4_candidate_reuse_index_20261128.json").read_text(encoding="utf-8"))
    for path,digest in index["source_blobs"].items():
        if blob((ROOT/path).read_bytes())!=digest:
            raise ValueError("Candidate source drift")
    opening=json.loads((AUDIT/"rph_5p_science_y2_y3_y4_opening_22_drafts_20261128.json").read_text(encoding="utf-8"))
    report=match(json.loads(a.chunks.read_text(encoding="utf-8")),index,opening)
    with a.out.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!="records"},ensure_ascii=False))
if __name__=="__main__":main()
