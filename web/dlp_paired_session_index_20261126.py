"""Read-only paired DLP session index; candidate integration, not live activation.

An RPH source ID can belong to multiple calendar sessions. Resolve by
subject, year, week and slot, never by a guessed or overwritten source ID.
"""
from collections import Counter
from datetime import date
from hashlib import sha256
from pathlib import Path
import json

EXPECTED = {**{f"mathematics_dlp:{y}": (101,n) for y,n in [(3,82),(4,77),(5,69),(6,54)]},
            **{f"science_dlp:{y}": (70,n) for y,n in [(2,67),(3,56),(6,61)]}}
WEEKS = set(range(1,39)) - {6,18,19}

def build_index(payload):
    result={}
    assert {x["key"] for x in payload["sets"]}==set(EXPECTED)
    for dataset in payload["sets"]:
        key=dataset["key"];count,source_count=EXPECTED[key]
        sessions=dataset["sessions"]
        assert [s["session"] for s in sessions]==list(range(1,count+1))
        assert len({i for s in sessions for i in s["source_ids"]})==source_count
        by_week={}; by_source={}
        for s in sessions:
            week=s["week"]
            assert week in WEEKS
            assert len(s["source_ids"])==len(s["source_labels"])==len(s["standards"])
            assert s["objective"]==s["evidence"] and s["objective"]
            assert sum(a["suggested_minutes"] for a in s["activities"])==s["slot_minutes"]
            assert s["slot_minutes"] in (30,60)
            slots=by_week.setdefault(week,[])
            slot=len(slots)+1
            row={"session":s["session"],"week":week,"slot":slot,"minutes":s["slot_minutes"],
                 "source_ids":s["source_ids"],"source_labels":s["source_labels"],
                 "dates":s["dates"],"titles":s["titles"],"standards":s["standards"],
                 "objective":s["objective"],"references":s["references"]}
            slots.append(row)
            for source_id in s["source_ids"]:
                by_source.setdefault(source_id,[]).append(s["session"])
        assert set(by_week)==WEEKS
        for week,slots in by_week.items():
            if key.startswith("mathematics"):
                assert len(slots)==(2 if week in (1,5,20,35) else 3)
                assert all(s["minutes"]==60 for s in slots)
            else:
                assert len(slots)==2
                assert sorted(s["minutes"] for s in slots)==([30,60] if key.endswith((":2",":3")) else [60,60])
        result[key]={"by_week":by_week,"by_source":by_source}
    return result

def resolve(index,subject,year,week,slot):
    """Internal selection only. No entitlement or live download bypass."""
    if not isinstance(slot,int) or slot<1:raise ValueError("Invalid slot")
    return index[f"{subject}:{int(year)}"]["by_week"][int(week)][slot-1]

def verified_candidate(path,expected_sha256):
    raw=Path(path).read_bytes()
    if sha256(raw).hexdigest()!=expected_sha256:
        raise ValueError("Session content checksum mismatch")
    return build_index(json.loads(raw))

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("paired",type=Path)
    args=parser.parse_args()
    raw=args.paired.read_bytes()
    index=verified_candidate(args.paired,sha256(raw).hexdigest())
    total=sum(len(rows) for d in index.values() for rows in d["by_week"].values())
    assert total==614
    print("PAIRED_SESSION_INDEX_OK",total,"QA only",flush=True)
