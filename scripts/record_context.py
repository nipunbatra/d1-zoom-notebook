"""One recorded evaluation of a frozen controller on development or new test data."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, base64, copy, hashlib, json, os
from PIL import Image
from context_controller import SPEC, initialize_run, finalize_run, call_answer
from benchmark_core import outcome

ROOT=Path(__file__).resolve().parents[1]
FREEZE=ROOT/"data/context-protocol-v1.json"
FILES=["scripts/context_controller.py","scripts/benchmark_core.py","scripts/make_benchmark.py","scripts/make_heldout.py","data/test-tasks.json"]

def frozen_protocol():
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}
    if FREEZE.exists():
        frozen=json.loads(FREEZE.read_text());assert frozen["file_sha256"]==hashes and frozen["controller"]==SPEC,"Frozen protocol changed. Start a new experiment."
    else:
        frozen=dict(frozen_at=datetime.now(timezone.utc).isoformat(),controller=SPEC,file_sha256=hashes)
        FREEZE.write_text(json.dumps(frozen,indent=2)+"\n")
    return frozen

def record(split):
    frozen=frozen_protocol();dest=ROOT/f"recordings/context-{split}-v1.json"
    if dest.exists():
        data=json.loads(dest.read_text());assert data["frozen_protocol"]==frozen
    else:
        suites=[json.loads((ROOT/"recordings"/f).read_text()) for f in ["mini-benchmark-v2.json","gemini-benchmark-v1.json"]]
        suites[0].update(model_label="Liquid D1.2",transport="OpenRouter")
        for suite in suites:
            suite["controller_spec"]=SPEC;suite["split"]=split
            if split=="test":
                tasks=json.loads((ROOT/"data/test-tasks.json").read_text())
                for task in tasks:
                    task["image"]="data:image/png;base64,"+base64.b64encode((ROOT/"data"/task["image_path"]).read_bytes()).decode();task["runs"]={}
                suite["tasks"]=tasks
                suite["revision_note"]="New synthetic test set:16 new answers/layouts in the same eight task families. Controller, prompt code and generator were frozen before any test inference. Direct, conditional zoom and repeat-full-view control are paired on the same initial response. This tests transfer within framed synthetic tasks, not general grounding; different API transports affect timings."
            else:
                suite["revision_note"]+=" The new context controller was designed using these development failures; its development score is not a held-out result. It uses the visible orange frame, not evaluation coordinates."
        data=dict(frozen_protocol=frozen,split=split,suites=suites)
    def save():
        temp=dest.with_suffix(".tmp");temp.write_text(json.dumps(data));temp.replace(dest)
    save()
    for suite in data["suites"]:
        model=suite["protocol"]["model"]
        key=(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")) if model.startswith("gemini") else os.environ.get("OPENROUTER_API_KEY")
        assert key,"Selected model's API key is missing"
        for i,task in enumerate(suite["tasks"]):
            path=ROOT/"data"/task["image_path"];assert hashlib.sha256(path.read_bytes()).hexdigest()==task["image_sha256"]
            original=Image.open(path).convert("RGB");full=[0,0,*original.size]
            if "direct" not in task["runs"]:
                initial=call_answer(task,original,model,"direct",full,key)
                task["runs"]["direct"]=dict(calls=[initial],stop_reason="single full-image answer");save()
                print(split,model,task["id"],"direct",outcome(task,task["runs"]["direct"]),flush=True)
            initial=task["runs"]["direct"]["calls"][0]
            for method in (["adaptive","repeat"] if i%2==0 else ["repeat","adaptive"]):
                run=task["runs"].setdefault(method,initialize_run(initial,original,method))
                if run.get("complete"):continue
                if run["decision"]["followup"] and len(run["calls"])==1:
                    save()
                    window=run["crop_proposal"]["bounds"] if method=="adaptive" else full
                    run["calls"].append(call_answer(task,original,model,method,window,key));save()
                finalize_run(run);run["complete"]=True;save()
                print(split,model,task["id"],method,outcome(task,run),flush=True)
    print("Saved",dest)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--split",choices=["development","test"],required=True)
    record(parser.parse_args().split)
