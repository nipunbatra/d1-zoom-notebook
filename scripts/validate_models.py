"""Check native Gemini records against the same fixtures and frozen D1 prompts."""
from pathlib import Path
import csv, hashlib, json, statistics
from PIL import Image
from benchmark_core import CELLS, crop_window, image_input, outcome
import validate_benchmark  # Independently verifies all 113 D1 calls first.

ROOT=Path(__file__).resolve().parents[1]
d1=json.loads((ROOT/"recordings/mini-benchmark-v2.json").read_text())
gem=json.loads((ROOT/"recordings/gemini-benchmark-v1.json").read_text())
assert len(gem["tasks"])==16 and gem["manifest_sha256"]==d1["manifest_sha256"]
count=0;tokens=0
for task,ref in zip(gem["tasks"],d1["tasks"]):
    assert all(task[k]==ref[k] for k in ["id","question","choices","truth","evidence","image","size","image_sha256"])
    original=Image.open(ROOT/"data"/task["image_path"]).convert("RGB")
    assert set(task["runs"])=={"direct","zoom","early_stop"}
    for method,run in task["runs"].items():
        calls=run["calls"];assert calls[-1]["stage"]=="answer"
        assert len(calls)==1 if method=="direct" else 2<=len(calls)<=4
        expected=[0,0,*original.size]
        for i,c in enumerate(calls):
            assert c["window"]==expected and c["body"]["model"]=="gemini-decision-1"
            assert c["endpoint"]=="https://generativelanguage.googleapis.com/v1beta/decisions"
            url,size,digest=image_input(original,expected)
            assert c["body"]["input"]==[{"type":"text","text":ref["runs"]["direct"]["calls"][0]["body"]["state"][0]},
                {"type":"image","data":url.split(",",1)[1],"mime_type":"image/jpeg"}]
            assert c["input_size"]==size and c["pixel_hash"]==digest and c["elapsed_ms"]>0
            qref=ref["runs"]["direct"]["calls"][0] if c["stage"]=="answer" else ref["runs"][method]["calls"][0]
            assert c["body"]["questions"]==qref["body"]["questions"]
            a=c["response"]["answers"][c["stage"]];p=a["probabilities"]
            assert a["type"]=="choice" and set(p)==set(c["body"]["questions"][c["stage"]]["criteria"])
            assert abs(sum(p.values())-1)<1e-6 and abs(p[a["choice"]]-max(p.values()))<1e-12
            if c["stage"]=="route" and a["choice"] in CELLS:
                expected=crop_window(expected,a["choice"]);assert c["next_window"]==expected
            elif c["stage"]=="route":assert "next_window" not in c and calls[i+1]["stage"]=="answer"
            count+=1;tokens+=c["response"]["usage"]["total_input_tokens"]
rows=[];summary=[]
for label,transport,data in [("Liquid D1.2","OpenRouter",d1),("Gemini Decision 1","Google native API",gem)]:
    for method in ["direct","zoom","early_stop"]:
        scores=[]
        for task in data["tasks"]:
            score=outcome(task,task["runs"][method]);scores.append(score)
            rows.append(dict(model=label,transport=transport,id=task["id"],family=task["family"],method=method,truth=task["truth"],**score))
        summary.append(dict(model=label,transport=transport,method=method,correct=sum(s["correct"] for s in scores),total=len(scores),
            mean_http_ms=round(statistics.mean(s["elapsed_ms"] for s in scores),2),median_http_ms=round(statistics.median(s["elapsed_ms"] for s in scores),2),
            mean_calls=statistics.mean(s["calls"] for s in scores)))
(ROOT/"data/model-comparison.json").write_text(json.dumps(dict(summary=summary,rows=rows,gemini_calls=count,gemini_input_tokens=tokens),indent=2)+"\n")
with (ROOT/"data/model-comparison.csv").open("w") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps(summary,indent=2));print(f"Verified {count} native Gemini requests, {tokens} input tokens. No cost returned by native API.")
