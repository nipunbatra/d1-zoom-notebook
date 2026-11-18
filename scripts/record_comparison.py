"""Fresh, checkpointed three-model comparison using the unchanged context-v1 policy."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import argparse, base64, copy, hashlib, json, os
from PIL import Image
from benchmark_core import PROTOCOL, outcome
from context_controller import SPEC, initialize_run, finalize_run, call_answer
from record_context import frozen_protocol

ROOT = Path(__file__).resolve().parents[1]
ROUND = "20261118"
MODELS = {
    "d1": ("liquid/d1.2-20261116", "Liquid D1.2", "OpenRouter"),
    "ultra": ("liquid/d1.2-ultra-20261116", "Liquid D1.2 Ultra", "OpenRouter"),
    "gemini": ("gemini-decision-1", "Gemini Decision 1", "Google native API"),
}
MANIFEST = ROOT / f"data/comparison-{ROUND}-protocol.json"

def recording_path(split, key):
    return ROOT / f"recordings/comparison-{ROUND}-{split}-{key}.json"

def round_protocol():
    previous = frozen_protocol()
    files = [*previous["file_sha256"], "data/tasks.json", "scripts/record_comparison.py"]
    spec = dict(round=ROUND, controller_protocol=previous, models=MODELS,
        methods=["direct", "adaptive", "repeat"], splits={"development":16, "test":16},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
        design="Fresh initial answers for all 96 model/example pairs; shared only within each pair. Alternating adaptive/repeat order by example index. One worker per model; models run concurrently. No successful response is retried or selected by correctness.",
        scope="Repeat evaluation on the existing 32 synthetic fixtures, not a new unseen test set. No controller, prompt, threshold or fixture tuning. Repeat control matches request count, not image tokens.")
    # JSON round-trip normalizes the model tuples for an exact resume comparison.
    spec = json.loads(json.dumps(spec))
    if MANIFEST.exists():
        saved=json.loads(MANIFEST.read_text())
        assert {k:v for k,v in saved.items() if k!="started_at"}==spec,"Comparison protocol changed"
        return saved
    spec["started_at"]=datetime.now(timezone.utc).isoformat()
    MANIFEST.write_text(json.dumps(spec,indent=2)+"\n")
    return spec

def record(split, model_key, experiment):
    model,label,transport=MODELS[model_key]
    destination=recording_path(split,model_key)
    if destination.exists():
        suite=json.loads(destination.read_text())
        assert suite["experiment"]==experiment
    else:
        tasks=json.loads((ROOT/"data"/("test-tasks.json" if split=="test" else "tasks.json")).read_text())
        for task in tasks:
            task["image"]="data:image/png;base64,"+base64.b64encode((ROOT/"data"/task["image_path"]).read_bytes()).decode()
            task["runs"]={}
        protocol=copy.deepcopy(PROTOCOL)
        protocol.update(model=model,version="context-v1",max_crops=1,
            endpoint="https://generativelanguage.googleapis.com/v1beta/decisions" if model_key=="gemini" else PROTOCOL["endpoint"])
        suite=dict(protocol=protocol,model_key=model_key,model_label=label,transport=transport,
            controller_spec=SPEC,split=split,experiment=experiment,tasks=tasks,
            revision_note="Fresh run · 18 Nov 2026 · all three models, same frozen prompts and crop policy. These are the existing "+split+" fixtures, not a newly unseen test set. Each model's initial response is shared by its direct, conditional-zoom and repeat-full-view methods. Repeat matches requests, not image tokens.")
    def save():
        temporary=destination.with_suffix(".tmp")
        temporary.write_text(json.dumps(suite));temporary.replace(destination)
    key=(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")) if model_key=="gemini" else os.environ.get("OPENROUTER_API_KEY")
    assert key,"API key missing for "+model_key
    def request(task, original, method, window):
        try:
            result=call_answer(task,original,model,method,window,key)
        except Exception as error:
            suite.setdefault("request_failures",[]).append(dict(task_id=task["id"],method=method,
                recorded_at=datetime.now(timezone.utc).isoformat(),error_type=type(error).__name__))
            save()
            raise
        return result
    save()
    for i,task in enumerate(suite["tasks"]):
        path=ROOT/"data"/task["image_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==task["image_sha256"]
        original=Image.open(path).convert("RGB");full=[0,0,*original.size]
        if "direct" not in task["runs"]:
            initial=request(task,original,"direct",full);initial["purpose"]="initial answer"
            task["runs"]["direct"]=dict(calls=[initial],complete=True,stop_reason="single full-image answer")
            save()
        initial=task["runs"]["direct"]["calls"][0]
        for method in (["adaptive","repeat"] if i%2==0 else ["repeat","adaptive"]):
            run=task["runs"].setdefault(method,initialize_run(initial,original,method))
            if run.get("complete"):continue
            if run["decision"]["followup"] and len(run["calls"])==1:
                window=run["crop_proposal"]["bounds"] if method=="adaptive" else full
                run["calls"].append(request(task,original,method,window));save()
            finalize_run(run);run["complete"]=True;save()
        print(json.dumps(dict(model=model_key,split=split,task=task["id"],
            scores={m:outcome(task,r)["correct"] for m,r in task["runs"].items()})),flush=True)
    return destination

def record_model(key, experiment):
    for split in ("development","test"):record(split,key,experiment)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--model",choices=list(MODELS));args=parser.parse_args()
    experiment=round_protocol()
    selected=[args.model] if args.model else list(MODELS)
    with ThreadPoolExecutor(max_workers=len(selected)) as pool:
        for result in pool.map(lambda key:record_model(key,experiment),selected):pass
    print("Completed fresh comparison; prior recordings preserved.")
