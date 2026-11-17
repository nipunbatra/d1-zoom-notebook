"""Record once, checkpoint every call, resume without replacing any response.

OPENROUTER_API_KEY must already be in the environment. Never writes credentials.
"""
from pathlib import Path
import base64, hashlib, json, os
from PIL import Image
from benchmark_core import PROTOCOL, MAX_CROPS, CELLS, call_model, crop_window, outcome

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data/tasks.json"
DEST=ROOT/"recordings/mini-benchmark-v2.json"

def record():
    fingerprint=hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    if DEST.exists():
        data=json.loads(DEST.read_text())
        assert data["manifest_sha256"]==fingerprint and data["protocol"]==PROTOCOL,"Protocol or fixtures changed; use a new run file."
    elif (ROOT/"recordings/mini-benchmark-v1.json").exists():
        data=json.loads((ROOT/"recordings/mini-benchmark-v1.json").read_text())
        assert data["manifest_sha256"]==fingerprint
        data["pilot_protocol"]=data["protocol"]
        data["protocol"]=PROTOCOL
        data["revision_note"]="After the early-stop pilot chose answer_now on 15 of 16 images, the crop budget was fixed at 3. All pilot results are retained. Direct baseline requests are unchanged and reused, not rerun. This is exploratory protocol development on these fixtures, not a held-out evaluation."
        for task in data["tasks"]:
            task["runs"]["early_stop"]=task["runs"].pop("zoom")
    else:
        tasks=json.loads(MANIFEST.read_text())
        for task in tasks:
            blob=(ROOT/"data"/task["image_path"]).read_bytes()
            assert hashlib.sha256(blob).hexdigest()==task["image_sha256"]
            task["image"]="data:image/png;base64,"+base64.b64encode(blob).decode()
            task["runs"]={}
        data=dict(protocol=PROTOCOL,manifest_sha256=fingerprint,tasks=tasks)
    def save():
        temp=DEST.with_suffix(".tmp");temp.write_text(json.dumps(data));temp.replace(DEST)
    save()
    key=os.environ["OPENROUTER_API_KEY"]
    # Alternate method order to reduce a systematic first-call timing advantage.
    for index,task in enumerate(data["tasks"]):
        original=Image.open(ROOT/"data"/task["image_path"]).convert("RGB")
        for method in (["direct","zoom"] if index%2==0 else ["zoom","direct"]):
            run=task["runs"].setdefault(method,dict(calls=[]))
            if run.get("stop_reason") and run["calls"] and run["calls"][-1]["stage"]=="answer":continue
            if method=="zoom":
                while len(run["calls"])<MAX_CROPS:
                    if run["calls"]:
                        last=run["calls"][-1];choice=last["response"]["answers"]["route"]["choice"]
                        if choice not in CELLS:
                            run["stop_reason"]=choice;break
                        window=crop_window(last["window"],choice);last["next_window"]=window;save()
                    else:window=[0,0,*original.size]
                    call=call_model(task,original,window,"route",key)
                    run["calls"].append(call);save()
                    print(task["id"],method,"route",call["response"]["answers"]["route"]["choice"],call["elapsed_ms"],flush=True)
                last=run["calls"][-1];choice=last["response"]["answers"]["route"]["choice"]
                if choice in CELLS:
                    window=crop_window(last["window"],choice);last["next_window"]=window
                    run["stop_reason"]="3-crop budget reached"
                else:
                    window=last["window"];run["stop_reason"]=choice
            else:
                window=[0,0,*original.size];run["stop_reason"]="single full-image answer"
            save()
            run["calls"].append(call_model(task,original,window,"answer",key));save()
            print(task["id"],method,outcome(task,run),flush=True)
    print("Saved",DEST)

if __name__=="__main__":record()
