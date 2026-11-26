"""Audit candidate continuation points against actual pinned RPH phase durations and text.
Executed with the verified RPH production snapshot as cwd.
No changes to any source RPH or live routing.
"""
import json,re,sys
from collections import defaultdict
from pathlib import Path
from tools.verify_dlp_rph_workload_20261126 import plans,phase_rows,minutes,TIME

def main(path):
    data=json.loads(Path(path).read_text())
    count=0;exact=0;inside=0;issues=[];seen=set()
    for (subject,year),rows in plans():
        key=f"{'mathematics' if subject=='math' else 'science'}_dlp:{year}"
        p=data["sets"][key];seen.add(key)
        segments=defaultdict(list)
        for w in p["weeks"]:
            for l in w["lessons"]:segments[l["id"]].append((w["week"],l))
        assert len(rows)==len(segments)==p["source_lessons"],(key,len(rows),len(segments))
        review=0;actual={}
        for identifier,label,phases,duration in rows:
            # The verified renderer returns numbered lesson labels and review labels.
            m=re.search(r"\bLesson\s+(\d+)\b",label,re.I)
            if m:k=f"L{int(m[1]):02d}"
            else:
                assert re.search(r"review|revision|consolidation",label,re.I),(key,identifier,label)
                review+=1;k=f"R{review:02d}"
            assert k not in actual,(key,k,label)
            actual[k]=(identifier,label,phase_rows(phases),duration)
        assert set(actual)==set(segments),(key,set(actual)^set(segments))
        for k,parts in segments.items():
            identifier,label,phases,duration=actual[k]
            assert duration==parts[0][1]["original_minutes"],(key,k,duration,parts)
            if len(parts)==1:continue
            count+=1
            cursor=0;blocks=[]
            for name,teacher,pupils in phases:
                m=TIME.search(name)
                assert m,(key,k,name)
                length=int(m[1])
                blocks.append({"phase":name[:m.start()],"start":cursor,"end":cursor+length,"teacher":teacher,"pupils":pupils})
                cursor+=length
            assert cursor==duration,(key,k,cursor,duration)
            boundaries={b["end"] for b in blocks}
            cuts=[l["to_minute"] for _,l in parts[:-1]]
            aligned=all(c in boundaries for c in cuts)
            if aligned:exact+=1
            else:inside+=1
            record={"set":key,"lesson":k,"id":identifier,"label":label,"duration":duration,
                    "parts":[{"week":w,**l} for w,l in parts],"cuts":cuts,"phase_aligned":aligned,
                    "blocks":blocks}
            print("RPH_CONTINUATION_AUDIT",json.dumps(record,ensure_ascii=False),flush=True)
        print("RPH_CONTINUATION_SET_OK",key,len(rows),flush=True)
    assert seen==set(data["sets"]) and count==52 and exact+inside==count
    print("RPH_CONTINUATION_SUMMARY",json.dumps({"audited":count,"exact_phase_boundaries":exact,"inside_phase":inside,"release_ready":False}),flush=True)

if __name__=="__main__":main(sys.argv[1])
