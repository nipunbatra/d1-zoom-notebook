"""Independent recorded-input, controller-replay, provenance and paired-score checks."""
from pathlib import Path
import copy, csv, hashlib, json, statistics
from PIL import Image,ImageDraw
from context_controller import SPEC,frame_from_pixels,initialize_run,finalize_run,build_request
from benchmark_core import outcome
from record_context import frozen_protocol

ROOT=Path(__file__).resolve().parents[1];frozen=frozen_protocol()
summaries=[];rows=[];unique={};detail_inputs=0
originals=[json.loads((ROOT/"recordings"/f).read_text()) for f in ['mini-benchmark-v2.json','gemini-benchmark-v1.json']]
for split in ['development','test']:
    experiment=json.loads((ROOT/f"recordings/context-{split}-v1.json").read_text())
    assert experiment['frozen_protocol']==frozen
    for si,suite in enumerate(experiment['suites']):
        assert len(suite['tasks'])==16
        model=suite['protocol']['model']
        for task in suite['tasks']:
            path=ROOT/'data'/task['image_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==task['image_sha256']
            original=Image.open(path).convert('RGB')
            if split=='development':
                old=next(t for t in originals[si]['tasks'] if t['id']==task['id'])
                for method in old['runs']:assert task['runs'][method]==old['runs'][method]
            direct=task['runs']['direct']['calls'][0]
            for method in ['adaptive','repeat']:
                run=task['runs'][method];assert run['complete']
                replay=initialize_run(direct,original,method)
                assert replay['decision']==run['decision'] and replay.get('crop_proposal')==run.get('crop_proposal')
                assert replay['calls'][0]==run['calls'][0]
                if run['decision']['followup']:
                    assert len(run['calls'])==2
                    replay['calls'].append(run['calls'][1]);finalize_run(replay)
                    if method=='adaptive':
                        b=task['evidence']['bounds'];w=run['crop_proposal']['bounds']
                        assert w[0]<=b[0] and w[1]<=b[1] and w[2]>=b[2] and w[3]>=b[3],"Clipped evaluation panel"
                else:assert len(run['calls'])==1
                assert replay['selected_call']==run['selected_call'] and replay['selection_reason']==run['selection_reason']
            assert task['runs']['adaptive']['decision']['followup']==task['runs']['repeat']['decision']['followup']
            for method in ['direct','adaptive','repeat']:
                run=task['runs'][method]
                for i,c in enumerate(run['calls']):
                    role='direct' if i==0 else method
                    body,sizes,hashes,windows=build_request(task,original,model,role,c['window'])
                    # Rebuild exact image bytes for every submitted view, including the overview.
                    assert c['body']==body
                    assert c.get('pixel_hashes',[c['pixel_hash']])==hashes
                    assert c['input_size']==sizes[-1] and c['elapsed_ms']>0
                    if role=='adaptive':assert len(windows)==2;detail_inputs+=2
                    if split=='test' or i>0:assert c['recorded_at']>=frozen['frozen_at']
                    a=c['response']['answers']['answer'];p=a['probabilities']
                    assert a['type']=='choice' and set(p)==set(task['choices']) and abs(sum(p.values())-1)<1e-6
                    assert abs(p[a['choice']]-max(p.values()))<1e-12
                    ident=hashlib.sha256(json.dumps([c['body'],c['response'],c['recorded_at'],c['elapsed_ms']],sort_keys=True).encode()).hexdigest()
                    unique[ident]=c
                score=outcome(task,run);base=outcome(task,task['runs']['direct'])
                rows.append(dict(split=split,model=suite['model_label'],id=task['id'],family=task['family'],method=method,
                    truth=task['truth'],**score,baseline_correct=base['correct'],selected_call=run.get('selected_call',0),
                    followup=run.get('decision',{}).get('followup',False)))
        for method in ['direct','adaptive','repeat']:
            subset=[r for r in rows if r['split']==split and r['model']==suite['model_label'] and r['method']==method]
            summaries.append(dict(split=split,model=suite['model_label'],method=method,correct=sum(r['correct'] for r in subset),total=len(subset),
                gains=sum(r['correct'] and not r['baseline_correct'] for r in subset),regressions=sum(r['baseline_correct'] and not r['correct'] for r in subset),
                followups=sum(r['followup'] for r in subset),mean_calls=statistics.mean(r['calls'] for r in subset),
                mean_http_ms=round(statistics.mean(r['elapsed_ms'] for r in subset),2),median_http_ms=round(statistics.median(r['elapsed_ms'] for r in subset),2)))
# Fallbacks: no cue, broken cue, multiple disjoint frames, and clipped cue.
for kind in ['blank','broken','multiple','clipped']:
    im=Image.new('RGB',(400,300),'white');d=ImageDraw.Draw(im)
    if kind=='broken':d.rectangle((50,50,250,200),outline='#d58127',width=5);d.rectangle((45,80,60,150),fill='white')
    if kind=='multiple':
        d.rectangle((20,30,130,140),outline='#d58127',width=5);d.rectangle((240,170,370,280),outline='#d58127',width=5)
    if kind=='clipped':d.rectangle((-10,50,250,200),outline='#d58127',width=5)
    assert frame_from_pixels(im) is None,kind+' must safely fall back'
result=dict(frozen_at=frozen['frozen_at'],summary=summaries,rows=rows,unique_calls_in_paired_experiments=len(unique),
    note='Development includes32 reused direct calls; new test and all follow-ups are newly recorded. Adaptive vs repeat matches requests, not image tokens.')
(ROOT/'data/context-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
with (ROOT/'data/context-comparison.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
for row in summaries:print(json.dumps(row))
print(f'Validated {len(unique)} distinct calls in paired experiments; all crop panels retained, both input images checked; four safe-fallback cases passed.')
