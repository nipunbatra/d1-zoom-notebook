"""Validate provenance, exact submitted pixels, crop paths, prompts and scoring."""
from pathlib import Path
import base64, csv, hashlib, io, json, statistics
from PIL import Image
from benchmark_core import MODEL, PROTOCOL, CELLS, image_input, crop_window, question, outcome

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"recordings/mini-benchmark-v2.json").read_text())
pilot=json.loads((ROOT/"recordings/mini-benchmark-v1.json").read_text())
assert data["protocol"]==PROTOCOL and len(data["tasks"])==16
assert data["manifest_sha256"]==hashlib.sha256((ROOT/"data/tasks.json").read_bytes()).hexdigest()
rows=[];unique={};count=0
for task,old in zip(data["tasks"],pilot["tasks"]):
    assert task["id"]==old["id"] and task["runs"]["direct"]==old["runs"]["direct"]
    assert task["runs"]["early_stop"]==old["runs"]["zoom"]
    blob=base64.b64decode(task["image"].split(",",1)[1])
    assert hashlib.sha256(blob).hexdigest()==task["image_sha256"]
    assert blob==(ROOT/"data"/task["image_path"]).read_bytes()
    original=Image.open(io.BytesIO(blob)).convert("RGB")
    assert list(original.size)==task["size"]
    for method,run in task["runs"].items():
        calls=run["calls"];assert calls[-1]["stage"]=="answer"
        assert len(calls)==1 if method=="direct" else 2<=len(calls)<=4
        expected=[0,0,*original.size]
        for i,c in enumerate(calls):
            assert c["window"]==expected
            url,size,digest=image_input(original,expected)
            assert c["body"]["state"][1]["image_url"]["url"]==url
            assert c["input_size"]==size and c["pixel_hash"]==digest
            assert max(size)<=512 and c["elapsed_ms"]>0
            assert c["body"]["model"]==c["response"]["model"]==MODEL
            assert c["body"]["state"][0]=="Task: "+task["question"]+"\nThe image below is the current view."
            assert c["body"]["provider"]=={"allow_fallbacks":False}
            answer=c["response"]["answers"][c["stage"]]
            p=answer["probabilities"];assert answer["type"]=="choice"
            assert set(p)==set(c["body"]["questions"][c["stage"]]["criteria"])
            assert abs(sum(p.values())-1)<1e-6 and abs(p[answer["choice"]]-max(p.values()))<1e-12
            assert c["body"]["questions"][c["stage"]]["instructions"].startswith(PROTOCOL["system_prompt"])
            if c["stage"]=="answer":assert c["body"]["questions"]==question(task,"answer")
            elif method=="zoom":assert c["body"]["questions"]==question(task,"route")
            if answer["choice"] in CELLS and c["stage"]=="route":
                expected=crop_window(expected,answer["choice"]);assert c["next_window"]==expected
            elif c["stage"]=="route":assert "next_window" not in c and calls[i+1]["stage"]=="answer"
            unique[c["response"]["id"]]=c
            count+=1
        score=outcome(task,run)
        rows.append(dict(id=task["id"],family=task["family"],variant=task["variant"],method=method,truth=task["truth"],**score))
# Ground-truth values are checked against the independently stored fixture facts.
for task in data["tasks"]:
    f=task["evidence"]["facts"];name=task["id"].split("-")[0]
    expected={"text":lambda:f["UNIT"],"count":lambda:str(sum(o["kind"]=="cross-slot screw" for o in f["objects"])),
        "thermal":lambda:str(f["upper_endpoint_C"]),"chart":lambda:str(f["Cedar"]),"table":lambda:str(f["rows"]["D"][4]),
        "circuit":lambda:"broken" if f["gap"] else "continuous","gauge":lambda:str(f["needle_value"]),
        "spatial":lambda:"left" if f["triangle_centre"][0]<f["square_centre"][0] else "below"}[name]()
    assert expected==task["truth"]
summary={}
for method in ("direct","zoom","early_stop"):
    subset=[r for r in rows if r["method"]==method]
    summary[method]=dict(correct=sum(r["correct"] for r in subset),total=len(subset),calls=sum(r["calls"] for r in subset),
        mean_http_ms=round(statistics.mean(r["elapsed_ms"] for r in subset),2),median_http_ms=round(statistics.median(r["elapsed_ms"] for r in subset),2),
        total_http_ms=round(sum(r["elapsed_ms"] for r in subset),2))
cost=sum(c["response"].get("usage",{}).get("cost",0) for c in unique.values())
(ROOT/"data/scorecard.json").write_text(json.dumps(dict(summary=summary,rows=rows,unique_calls=len(unique),reported_cost_usd=cost),indent=2)+"\n")
with (ROOT/"data/scorecard.csv").open("w") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps(summary,indent=2));print(f"Verified {count} input JPEGs; {len(unique)} unique calls. Reported cost USD {cost:.6f}.")
