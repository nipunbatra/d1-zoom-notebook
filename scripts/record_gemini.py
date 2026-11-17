"""Use an existing GEMINI_API_KEY/GOOGLE_API_KEY with Google's native Decisions API.

Same fixture pixels, question instructions, options and crop rules as D1.
Every successful response is checkpointed. No failed answer is retried for quality.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, time, urllib.request
from PIL import Image
from benchmark_core import CELLS, MAX_CROPS, image_input, crop_window, outcome, question

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"recordings/gemini-benchmark-v1.json"
ENDPOINT="https://generativelanguage.googleapis.com/v1beta/decisions"
MODEL="gemini-decision-1"

def call_gemini(task,original,window,stage,method,key,source_task):
    url,size,digest=image_input(original,window)
    questions=question(task,stage)
    if stage=="route" and method=="early_stop":
        questions=copy.deepcopy(source_task["runs"]["early_stop"]["calls"][0]["body"]["questions"])
    body=dict(model=MODEL,input=[{"type":"text","text":"Task: "+task["question"]+"\nThe image below is the current view."},
        {"type":"image","data":url.split(",",1)[1],"mime_type":"image/jpeg"}],questions=questions)
    request=urllib.request.Request(ENDPOINT,json.dumps(body).encode(),{"Content-Type":"application/json","x-goog-api-key":key})
    start=time.perf_counter()
    with urllib.request.urlopen(request,timeout=90) as response:result=json.load(response)
    elapsed=round((time.perf_counter()-start)*1000,2)
    answer=result["answers"][stage]
    assert answer["type"]=="choice" and answer["choice"] in questions[stage]["criteria"]
    return dict(stage=stage,body=body,response=result,elapsed_ms=elapsed,window=list(window),input_size=size,pixel_hash=digest,
        endpoint=ENDPOINT,model_requested=MODEL,recorded_at=datetime.now(timezone.utc).isoformat())

def record():
    source=json.loads((ROOT/"recordings/mini-benchmark-v2.json").read_text())
    if DEST.exists():
        data=json.loads(DEST.read_text());assert data["manifest_sha256"]==source["manifest_sha256"]
    else:
        data=copy.deepcopy(source)
        data.update(model_label="Gemini Decision 1",transport="Google native API",
            revision_note="Gemini uses the frozen D1 fixtures, prompts and both crop policies. Every method was recorded once; no D1 responses are reused for Gemini. D1 was measured through OpenRouter, Gemini through Google's native endpoint, so timings include different transports. This is a small exploratory comparison, not a general model ranking.")
        data["protocol"].update(model=MODEL,endpoint=ENDPOINT,version="gemini-mini-v1",
            system_note="Shared instructions play the role of a system prompt. This Decisions request prepends them to each typed question's instructions; the native request uses input rather than OpenRouter's state.")
        data["pilot_protocol"].update(model=MODEL,endpoint=ENDPOINT)
        for task in data["tasks"]:task["runs"]={}
    key=os.environ.get("GEMINI_API_KEY") or os.environ["GOOGLE_API_KEY"]
    def save():
        tmp=DEST.with_suffix(".tmp");tmp.write_text(json.dumps(data));tmp.replace(DEST)
    save()
    for index,(task,source_task) in enumerate(zip(data["tasks"],source["tasks"])):
        assert task["id"]==source_task["id"]
        path=ROOT/"data"/task["image_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==task["image_sha256"]
        original=Image.open(path).convert("RGB")
        order=["direct","zoom","early_stop"] if index%2==0 else ["zoom","early_stop","direct"]
        for method in order:
            run=task["runs"].setdefault(method,{"calls":[]})
            if run.get("stop_reason") and run["calls"] and run["calls"][-1]["stage"]=="answer":continue
            window=[0,0,*original.size]
            if method!="direct":
                while len(run["calls"])<MAX_CROPS:
                    if run["calls"]:
                        last=run["calls"][-1];action=last["response"]["answers"]["route"]["choice"]
                        if action not in CELLS:break
                        window=crop_window(last["window"],action);last["next_window"]=window;save()
                    call=call_gemini(task,original,window,"route",method,key,source_task)
                    run["calls"].append(call);save()
                    print(task["id"],method,"route",call["response"]["answers"]["route"]["choice"],call["elapsed_ms"],flush=True)
                last=run["calls"][-1];action=last["response"]["answers"]["route"]["choice"]
                if action in CELLS:
                    window=crop_window(last["window"],action);last["next_window"]=window;run["stop_reason"]="3-crop budget reached"
                else:window=last["window"];run["stop_reason"]=action
            else:run["stop_reason"]="single full-image answer"
            save()
            run["calls"].append(call_gemini(task,original,window,"answer",method,key,source_task));save()
            print(task["id"],method,outcome(task,run),flush=True)
    print("Saved",DEST)

if __name__=="__main__":record()
