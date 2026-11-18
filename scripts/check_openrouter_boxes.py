"""Reproduce supported choice vs unsupported Liquid box with one identical image.
Requires OPENROUTER_API_KEY in the environment. Headers are never recorded.
"""
from pathlib import Path
from datetime import datetime, timezone
import base64, copy, hashlib, json, os, time, urllib.request, urllib.error
ROOT=Path(__file__).resolve().parents[1]
ENDPOINT='https://openrouter.ai/api/alpha/decisions'

def check():
    key=os.environ['OPENROUTER_API_KEY']
    source=json.loads((ROOT/'recordings/openrouter-capabilities-20261118.json').read_text())
    image=next(r for r in source if r['check']=='choice_full')['request']['state'][1]
    image_bytes=base64.b64decode(image['image_url']['url'].split(',',1)[1])
    shared_state=['Inspect the orange-outlined fastener tray in this image.',image]
    questions={
        'choice':{'type':'choice','instructions':'Is an orange-outlined fastener tray present in the image?',
            'criteria':{'present':'An orange-outlined fastener tray is visible.','absent':'No orange-outlined fastener tray is visible.'}},
        'box':{'type':'box','instructions':'The entire orange-outlined fastener tray, including every screw and plain ring.'},
    }
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'endpoint':ENDPOINT,
        'image_sha256':hashlib.sha256(image_bytes).hexdigest(),
        'note':'Four fresh authenticated requests. Same image bytes, state, endpoint, account and provider setting; question type and instructions differ. Authorization headers never recorded. user_id omitted from successful response metadata.',
        'calls':[]}
    destination=ROOT/'recordings/openrouter-box-check-20261118.json'
    assert not destination.exists(),'Keep prior evidence immutable; choose a new filename to rerun.'
    for model in ('liquid/d1.2','liquid/d1.2-ultra'):
        for kind,q in questions.items():
            body={'model':model,'state':copy.deepcopy(shared_state),'questions':{'target':q},'provider':{'allow_fallbacks':False}}
            request=urllib.request.Request(ENDPOINT,json.dumps(body).encode(),{'Authorization':'Bearer '+key,'Content-Type':'application/json'})
            start=time.perf_counter()
            try:
                with urllib.request.urlopen(request,timeout=90) as response:
                    status=response.status;raw=response.read().decode()
            except urllib.error.HTTPError as error:
                status=error.code;raw=error.read().decode()
            elapsed=round((time.perf_counter()-start)*1000,2)
            response=json.loads(raw);response.pop('user_id',None)
            result['calls'].append({'question_type':kind,'model_requested':model,'request':body,'status':status,
                'response':response,'elapsed_ms':elapsed,'recorded_at':datetime.now(timezone.utc).isoformat()})
            destination.write_text(json.dumps(result,indent=2)+'\n')
            print(model,kind,'HTTP',status,str(elapsed)+' ms',flush=True)
    assert all(c['status']==(200 if c['question_type']=='choice' else 400) for c in result['calls'])
    assert len({json.dumps(c['request']['state'],sort_keys=True) for c in result['calls']})==1
    return destination

if __name__=='__main__':check()
