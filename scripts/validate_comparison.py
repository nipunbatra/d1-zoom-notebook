"""Validate all three fresh suites and rebuild the current comparison scorecards."""
from pathlib import Path
import base64, csv, hashlib, json, statistics
from PIL import Image
from benchmark_core import outcome
from context_controller import SPEC, initialize_run, finalize_run, build_request
from record_comparison import MODELS, ROUND, recording_path, round_protocol

ROOT=Path(__file__).resolve().parents[1]
experiment=round_protocol()
rows=[];calls={};failures=[]
for split in ("development","test"):
    fixtures=json.loads((ROOT/"data"/("tasks.json" if split=="development" else "test-tasks.json")).read_text())
    for model_key,(model,label,transport) in MODELS.items():
        suite=json.loads(recording_path(split,model_key).read_text())
        assert suite["experiment"]==experiment and suite["controller_spec"]==SPEC
        assert suite["model_key"]==model_key and suite["protocol"]["model"]==model
        assert len(suite["tasks"])==len(fixtures)==16
        failures+=suite.get("request_failures",[])
        for task,fixture in zip(suite["tasks"],fixtures):
            for key,value in fixture.items():assert task[key]==value,(split,model_key,task["id"],key)
            path=ROOT/"data"/task["image_path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest()==task["image_sha256"]
            assert base64.b64decode(task["image"].split(",",1)[1])==path.read_bytes()
            original=Image.open(path).convert("RGB")
            assert set(task["runs"])=={"direct","adaptive","repeat"}
            direct=task["runs"]["direct"];assert len(direct["calls"])==1 and direct["complete"]
            initial=direct["calls"][0]
            for method in ("adaptive","repeat"):
                run=task["runs"][method];replay=initialize_run(initial,original,method)
                assert run["complete"] and replay["calls"][0]==run["calls"][0]
                assert len(run["calls"])==1+int(replay["decision"]["followup"])
                if replay["decision"]["followup"]:
                    replay["calls"].append(run["calls"][1]);finalize_run(replay)
                    if method=="adaptive":
                        x,y,X,Y=run["crop_proposal"]["bounds"];a,b,A,B=fixture["evidence"]["bounds"]
                        assert x<=a and y<=b and X>=A and Y>=B,"Evidence clipped"
                for field in ("decision","crop_proposal","selected_call","selection_reason","stop_reason"):
                    assert replay.get(field)==run.get(field),(model_key,task["id"],method,field)
            assert len(task["runs"]["adaptive"]["calls"])==len(task["runs"]["repeat"]["calls"])
            for method,run in task["runs"].items():
                for index,call in enumerate(run["calls"]):
                    role="direct" if index==0 else method
                    expected_window = (initialize_run(initial,original,"adaptive")["crop_proposal"]["bounds"]
                        if role=="adaptive" else [0,0,*original.size])
                    assert call["window"]==expected_window,(split,model_key,task["id"],role,"Wrong submitted crop")
                    body,sizes,hashes,windows=build_request(task,original,model,role,expected_window)
                    assert call["body"]==body and call["pixel_hashes"]==hashes
                    assert call["input_sizes"]==sizes and call["input_windows"]==windows
                    assert call["input_size"]==sizes[-1] and call["pixel_hash"]==hashes[-1]
                    assert call["model_requested"]==model and call["elapsed_ms"]>0
                    assert call["recorded_at"]>=experiment["started_at"]
                    assert call["endpoint"]==suite["protocol"]["endpoint"]
                    if model_key!="gemini":assert call["response"]["model"]==model
                    answer=call["response"]["answers"]["answer"];probabilities=answer["probabilities"]
                    assert answer["type"]=="choice" and set(probabilities)==set(task["choices"])
                    assert all(0<=p<=1 for p in probabilities.values()) and abs(sum(probabilities.values())-1)<1e-6
                    assert abs(probabilities[answer["choice"]]-max(probabilities.values()))<1e-12
                    identity=hashlib.sha256(json.dumps([body,call["response"],call["recorded_at"],call["elapsed_ms"]],sort_keys=True).encode()).hexdigest()
                    calls[identity]=call
                score=outcome(task,run);baseline=outcome(task,direct)
                rows.append(dict(split=split,model_key=model_key,model=label,id=task["id"],family=task["family"],method=method,
                    truth=task["truth"],**score,baseline_correct=baseline["correct"],selected_call=run.get("selected_call",0),
                    followup=run.get("decision",{}).get("followup",False)))

summary=[]
for split in ("development","test","all"):
    for key,(_,label,transport) in MODELS.items():
        for method in ("direct","adaptive","repeat"):
            group=[r for r in rows if r["model_key"]==key and r["method"]==method and (split=="all" or r["split"]==split)]
            summary.append(dict(split=split,model_key=key,model=label,transport=transport,method=method,total=len(group),
                correct=sum(r["correct"] for r in group),gains=sum(r["correct"] and not r["baseline_correct"] for r in group),
                regressions=sum(r["baseline_correct"] and not r["correct"] for r in group),
                mean_calls=statistics.mean(r["calls"] for r in group),followups=sum(r["followup"] for r in group),
                mean_http_ms=round(statistics.mean(r["elapsed_ms"] for r in group),2),
                median_http_ms=round(statistics.median(r["elapsed_ms"] for r in group),2)))
assert len(rows)==288
expected=96+sum(r["followup"] for r in rows if r["method"]!="direct")
assert len(calls)==expected
result=dict(round=ROUND,started_at=experiment["started_at"],unique_calls=len(calls),request_failures=failures,
    note="Fresh repeat evaluation on existing fixtures. Combined totals are descriptive and include development examples. Zoom and repeat share their model's fresh initial answer. HTTP times include all calls; repeat matches request count, not image tokens.",summary=summary,rows=rows)
(ROOT/f"data/comparison-{ROUND}.json").write_text(json.dumps(result,indent=2)+"\n")
with (ROOT/f"data/comparison-{ROUND}.csv").open("w") as handle:
    writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
for row in summary:
    if row["split"] in ("test","all"):print(json.dumps(row))
print(f"Validated {len(calls)} distinct fresh calls across 96 model/example pairs and 288 method outcomes; {len(failures)} failed attempts.")
