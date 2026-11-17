"""Frozen conditional zoom policy; reads image pixels, never evaluation labels."""
import base64, copy, hashlib, json, math, time, urllib.request
from datetime import datetime, timezone
from PIL import ImageChops
from benchmark_core import image_input, question

SPEC = {
    "version": "context-v1", "probability_threshold": .85, "margin_threshold": .15,
    "acceptance_gain": .05, "padding_fraction": .05, "tie_tolerance": 1e-12,
    "orange_mask": {"red_min_exclusive":190,"green_min_exclusive":80,"green_max_exclusive":170,"blue_max_exclusive":85},
    "minimum_edge_coverage": .9, "minimum_frame_side": 30,
    "primary_outcome": "Unique-top exact answer accuracy on all 16 new synthetic test examples, relative to their paired direct answers.",
    "scope": "One visible orange rectangular task frame. This is an image-derived region proposal, not learned general object grounding or optimal scale selection.",
    "selection": "Retain the initial answer unless the follow-up has a unique non-uncertain answer and its top probability exceeds the initial top by at least .05. Probabilities are uncalibrated heuristics, not correctness guarantees.",
    "input_policy": "Adaptive follow-up receives original overview plus full-frame crop. Repeat control receives the original overview again. Same final question/options; each image capped at512px. Control matches request count, not image-token budget.",
    "test_policy": "Freeze controller, prompts and test generator before any new-test inference. Do not tune on test outcomes. Keep all outcomes.",
}

def top_answer(call):
    answer=call["response"]["answers"]["answer"];ps=answer["probabilities"]
    order=sorted(ps.values(),reverse=True);top=order[0]
    tied=[k for k,p in ps.items() if abs(p-top)<=SPEC["tie_tolerance"]]
    return dict(choice=answer["choice"],probability=top,margin=top-order[1],unique=len(tied)==1)

def frame_from_pixels(image):
    """Union of orange pixels, accepted only if all four outer edges form a frame.

    Several disconnected frames normally fail the rectangular-edge check. Missing,
    clipped, small or nonrectangular cues fall back to the unchanged initial answer.
    Padding is 5% of detected outer-frame width/height per side, clipped to the image.
    """
    r,g,b=image.convert("RGB").split()
    mask=ImageChops.multiply(r.point(lambda x:255 if x>190 else 0),g.point(lambda x:255 if 80<x<170 else 0))
    mask=ImageChops.multiply(mask,b.point(lambda x:255 if x<85 else 0))
    box=mask.getbbox()
    if box is None:return None
    x,y,X,Y=box;w,h=X-x,Y-y
    if min(w,h)<30 or x==0 or y==0 or X==image.width or Y==image.height:return None
    edges=[(x,y,X,y+1),(x,Y-1,X,Y),(x,y,x+1,Y),(X-1,y,X,Y)]
    cover=[sum(mask.crop(e).histogram()[1:])/((e[2]-e[0])*(e[3]-e[1])) for e in edges]
    if min(cover)<SPEC["minimum_edge_coverage"]:return None
    pad=SPEC["padding_fraction"]
    bounds=[max(0,math.floor(x-w*pad)),max(0,math.floor(y-h*pad)),min(image.width,math.ceil(X+w*pad)),min(image.height,math.ceil(Y+h*pad))]
    if bounds==[0,0,image.width,image.height]:return None
    return dict(method="visible orange frame pixels",frame_bounds=list(box),bounds=bounds,padding_fraction=pad,edge_coverage=cover)

def initialize_run(initial,original,method):
    run=dict(calls=[copy.deepcopy(initial)],selected_call=0)
    run["calls"][0]["purpose"]="initial answer"
    a=top_answer(initial)
    confident=a["unique"] and a["choice"]!="uncertain" and a["probability"]>=SPEC["probability_threshold"] and a["margin"]>=SPEC["margin_threshold"]
    proposal=None if confident else frame_from_pixels(original)
    followup=not confident and proposal is not None
    reason="Keep initial answer: unique top probability and margin pass the fixed thresholds." if confident else "Inspect more evidence: the initial answer did not pass both fixed thresholds." if followup else "Keep initial answer: no complete orange frame was detected; no safe crop proposed."
    run["decision"]=dict(zoom=followup and method=="adaptive",followup=followup,reason=reason,
        initial_probability=a["probability"],initial_margin=a["margin"],threshold_probability=SPEC["probability_threshold"],threshold_margin=SPEC["margin_threshold"])
    if proposal is not None:run["crop_proposal"]=proposal
    if followup and method=="adaptive":run["calls"][0]["next_window"]=proposal["bounds"]
    run["stop_reason"]="additional evidence requested" if followup else "initial answer retained"
    run["selection_reason"]=reason
    return run

def finalize_run(run):
    if len(run["calls"])==1:return run
    initial,detail=map(top_answer,run["calls"])
    accept=detail["unique"] and detail["choice"]!="uncertain" and detail["probability"]>=initial["probability"]+SPEC["acceptance_gain"]
    run["selected_call"]=1 if accept else 0
    run["selection_reason"]="Use the follow-up: unique non-uncertain answer, with top probability at least .05 higher." if accept else "Keep the initial answer: follow-up did not satisfy the fixed acceptance rule."
    run["stop_reason"]="one follow-up budget used"
    return run

def build_request(task,original,model,method,window):
    full=[0,0,*original.size];overview,overview_size,overview_hash=image_input(original,full)
    state_text="Task: "+task["question"]+"\nThe image below is the current view."
    urls=[overview];sizes=[overview_size];hashes=[overview_hash];windows=[full]
    if method=="adaptive":
        detail,size,digest=image_input(original,window);urls.append(detail);sizes.append(size);hashes.append(digest);windows.append(window)
        state_text="Task: "+task["question"]+"\nImage 1 is the full overview. Image 2 is a magnified view of the SAME orange-outlined panel. Use image 2 to read details and image 1 for context. These are the same objects, not separate sets: count each requested object only once."
    questions=question(task,"answer")
    if model.startswith("gemini"):
        body=dict(model=model,input=[{"type":"text","text":state_text}]+[{"type":"image","data":u.split(",",1)[1],"mime_type":"image/jpeg"} for u in urls],questions=questions)
    else:body=dict(model=model,state=[state_text]+[{"type":"image_url","image_url":{"url":u}} for u in urls],questions=questions,provider={"allow_fallbacks":False})
    return body,sizes,hashes,windows

def call_answer(task,original,model,method,window,key):
    body,sizes,hashes,windows=build_request(task,original,model,method,window)
    native=model.startswith("gemini")
    endpoint="https://generativelanguage.googleapis.com/v1beta/decisions" if native else "https://openrouter.ai/api/alpha/decisions"
    auth={"x-goog-api-key":key} if native else {"Authorization":"Bearer "+key}
    request=urllib.request.Request(endpoint,json.dumps(body).encode(),{"Content-Type":"application/json",**auth})
    start=time.perf_counter()
    with urllib.request.urlopen(request,timeout=90) as response:result=json.load(response)
    elapsed=round((time.perf_counter()-start)*1000,2);result.pop("user_id",None)
    if not native:assert result["model"]==model
    answer=result["answers"]["answer"]
    assert answer["type"]=="choice" and answer["choice"] in task["choices"]
    return dict(stage="answer",purpose="detail answer" if method=="adaptive" else "follow-up answer",body=body,response=result,
        elapsed_ms=elapsed,window=list(window),input_windows=windows,input_size=sizes[-1],input_sizes=sizes,
        pixel_hash=hashes[-1],pixel_hashes=hashes,endpoint=endpoint,model_requested=model,recorded_at=datetime.now(timezone.utc).isoformat())
