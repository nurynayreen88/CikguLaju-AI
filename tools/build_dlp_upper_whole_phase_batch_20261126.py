"""Batch complete source activity phases for 474 remaining upper DLP slots.
Private review only: retain all teacher/pupil text, flag retiming, composition
and reinforcement; never publish unreviewed cross-unit sessions.
"""
import json,sys
from collections import Counter
from pathlib import Path
from functools import lru_cache
KEYS=[f'mathematics_dlp:{y}' for y in range(3,7)]+['science_dlp:6']
def build(data):
    output={}
    for key in KEYS:
        v=data['sets'][key]; phases={};sources={}
        for s in v['sessions']:
            for p in s['parts']:
                m=p['source'];sid=m['source_id'];a=p['phase']
                sources.setdefault(sid,m)
                phases[(sid,a['start'])]={'source':m,'phase':a,'minutes':a['end']-a['start']}
        blocks=list(phases.values());n=len(blocks);slots=v['sessions'];count=len(slots)
        unit=lambda x:next((t for t in x['source']['title'] if t.startswith('Unit ')),x['source']['title'][-1])
        prefix=[0]
        for x in blocks:prefix.append(prefix[-1]+x['minutes'])
        @lru_cache(None)
        def choices(i):
            options=[]
            for j in range(i+1,n+1):
                mins=prefix[j]-prefix[i]
                if mins>75:break
                seg=blocks[i:j]
                reductions=sum(min(x['minutes']//5,max(0,x['minutes']-3)) for x in seg)
                if mins>60 and mins-60>reductions:continue
                crossings=sum(a['source']['source_id']!=b['source']['source_id'] for a,b in zip(seg,seg[1:]))
                unit_cross=sum(unit(a)!=unit(b) for a,b in zip(seg,seg[1:]))
                if unit_cross and key!='mathematics_dlp:6':continue
                split=j<n and blocks[j-1]['source']['source_id']==blocks[j]['source']['source_id']
                score=2*max(0,mins-60)**2+.35*max(0,60-mins)**2+65*crossings+1500*unit_cross+20*split
                options.append((j,score))
            return options
        dp={0:(0,None)};layers=[]
        for k in range(count):
            nxt={}
            for i,(cost,_) in dp.items():
                for j,score in choices(i):
                    if n-j<count-k-1 or prefix[n]-prefix[j]>(count-k-1)*75:continue
                    val=cost+score
                    if j not in nxt or val<nxt[j][0]:nxt[j]=(val,i)
            assert nxt,(key,k)
            dp=nxt;layers.append(nxt)
        assert n in dp,key
        edges=[];j=n
        for l in reversed(layers):i=l[j][1];edges.append((i,j));j=i
        assert j==0
        rows=[];counts=Counter();used=[]
        for slot,(i,j) in zip(slots,reversed(edges),strict=True):
            seg=blocks[i:j];mins=prefix[j]-prefix[i];times=[p['minutes'] for p in seg];need=max(0,mins-60)
            while need:
                k=max((k for k,x in enumerate(seg) if times[k]>x['minutes']-min(x['minutes']//5,max(0,x['minutes']-3))),key=lambda k:times[k]/seg[k]['minutes'])
                times[k]-=1;need-=1
            ids=list(dict.fromkeys(p['source']['source_id'] for p in seg))
            exact=len(ids)==1 and mins==60 and seg[0]['phase']['start']==0 and seg[-1]['phase']['end']==seg[-1]['source']['original_minutes']
            status='EXACT_RPH' if exact else 'WHOLE_PHASE_RETIMING_REVIEW' if mins>60 else 'WHOLE_PHASE_COMPOSITION_REVIEW' if mins==60 else 'WHOLE_PHASE_REINFORCEMENT_REVIEW'
            counts[status]+=1;activities=[]
            for p,t in zip(seg,times):
                a=p['phase'];m=p['source'];used.append((m['source_id'],a['start']))
                activities.append({'source':m,'phase':a['phase'],'teacher':a['teacher'],'pupils':a['pupils'],'original_minutes':p['minutes'],'minutes':t,'original_start':a['start']})
            rows.append({'week':slot['week'],'session':slot['session'],'minutes':60,'source_ids':ids,'status':status,'cross_unit_review':len({unit(p) for p in seg})>1,'activities':activities,'reinforcement_minutes':60-sum(times)})
        assert used==list(phases)
        assert all(sum(a['minutes'] for a in s['activities'])+s['reinforcement_minutes']==60 for s in rows)
        assert sum(a['original_minutes'] for s in rows for a in s['activities'])==sum(m['original_minutes'] for m in sources.values())
        output[key]={'source_count':len(sources),'phase_count':n,'counts':dict(counts),'sessions':rows}
        print('WHOLE_PHASE_BATCH',key,len(rows),len(sources),n,dict(counts),'cross_unit',sum(s['cross_unit_review'] for s in rows),'original_minutes',prefix[-1],flush=True)
    assert sum(len(v['sessions']) for v in output.values())==474
    return {'status':'PRIVATE_WHOLE_PHASE_REVIEW','release_ready':False,'sets':output}
if __name__=='__main__':
    inp,out=sys.argv[1:]
    Path(out).write_text(json.dumps(build(json.loads(Path(inp).read_text())),indent=2,ensure_ascii=False)+'\n')
