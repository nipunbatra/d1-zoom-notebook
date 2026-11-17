"""Build a portable notebook and static HTML from the exact recorded benchmark."""
from pathlib import Path
import base64, html, json, zlib

ROOT=Path(__file__).resolve().parents[1]
def build():
    development=json.loads((ROOT/"recordings/context-development-v1.json").read_text())
    testing=json.loads((ROOT/"recordings/context-test-v1.json").read_text())
    for experiment in (development,testing):
        assert all(t['runs'].get('adaptive',{}).get('complete') and t['runs'].get('repeat',{}).get('complete') for s in experiment['suites'] for t in s['tasks']),"Recording incomplete"
    data=development["suites"][0]
    data["model_suites"]=development["suites"][1:]
    data["test_suites"]=testing["suites"]
    data["selected_split"]="test"
    data["selected_id"]="count-02"
    template=(ROOT/"src/benchmark.html").read_text()
    cells=[]
    def md(source):cells.append(dict(cell_type="markdown",metadata={},source=source.splitlines(keepends=True)))
    def code(source,fold=False):
        cells.append(dict(cell_type="code",execution_count=None,metadata={"jupyter":{"source_hidden":True},"tags":["hide-input"]} if fold else {},source=source.splitlines(keepends=True),outputs=[]))
    md("# Look closer: preserve context, zoom when uncertain\n\nRun all cells. **Replay is offline and free.** The worked example counts cross-slot screws. The viewer includes 16 development and 16 new test examples, two models, all prompts, inputs and responses.\n\nAnswer once. If the answer is uncertain, find the **visible orange frame from image pixels**, preserve the whole panel, and answer with both overview and detail. This is a controlled framed-task experiment, not general learned grounding. All final answers are **multiple choice**.")
    code('''LIVE = False  # True reruns only this example: at most 2 billed requests.
TASK_ID = "count-02"
SPLIT = "test"  # "development" keeps the original examples and earlier policies.
MODEL_KEY = "d1"  # "gemini" selects Google's native Decisions API recordings.
import base64, copy, html, io, json, os, zlib
from IPython.display import display, HTML
try:
    from PIL import Image, ImageDraw
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow==13.0.0"])
    from PIL import Image, ImageDraw
key = ""
if LIVE:
    from getpass import getpass
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")) if MODEL_KEY == "gemini" else os.environ.get("OPENROUTER_API_KEY")
    key = key or getpass("API key for selected model: ")
''')
    packed=base64.b64encode(zlib.compress(json.dumps(dict(data=data,template=template)).encode(),9)).decode()
    code("# Embedded images, exact recordings and offline viewer. No helper files.\nBUNDLE = json.loads(zlib.decompress(base64.b64decode('"+packed+"')))\ndata = copy.deepcopy(BUNDLE['data'])\n",True)
    md("## 1. Shared instructions and task\n\nD1 uses `state`; Gemini uses `input`. Both use typed `questions`, rather than chat roles. The shared policy below plays the role of a system prompt and is **actually prepended to every question's instructions**. No ground-truth labels or coordinates are sent.")
    code('''suites = data["test_suites"] if SPLIT == "test" else [data, *data["model_suites"]]
active = suites[0 if MODEL_KEY == "d1" else 1]
policy = active["protocol"]["system_prompt"]
task = next(t for t in active["tasks"] if t["id"] == TASK_ID)
original = Image.open(io.BytesIO(base64.b64decode(task["image"].split(",", 1)[1]))).convert("RGB")
print("SHARED INSTRUCTIONS", policy, "TASK", task["question"], sep="\\n\\n")
print("Model:", active["protocol"]["model"])
print("Final response type: choice. Options:", task["choices"])
''')
    md("## 2. Frozen controller and request functions\n\nKeep a unique initial answer when top probability ≥ 0.85 and margin ≥ 0.15. Otherwise locate the complete orange frame from pixels, pad its width and height by 5% per side, and request one follow-up with overview + detail. Each image is at most 512 px. Keep the initial answer unless the follow-up is unique, non-uncertain, and raises top probability by at least 0.05. These are fixed heuristics, not calibrated correctness guarantees. No evaluation coordinates are read by the controller.")
    controller=(ROOT/"scripts/context_controller.py").read_text().replace('from benchmark_core import image_input, question\n','')
    code((ROOT/"scripts/benchmark_core.py").read_text()+'\n'+controller+'\nMODEL = active["protocol"]["model"]\n',True)
    code('''# Replay validates the current prompt and pixels; LIVE makes the same request.
runs = {name: {"calls": []} for name in ("direct", "adaptive")}
def ask(method, window):
    if LIVE:
        call = call_answer(task, original, MODEL, method, window, key)
    else:
        call = copy.deepcopy(task["runs"][method]["calls"][len(runs[method]["calls"])])
        body, sizes, digests, windows = build_request(task, original, MODEL, method, window)
        assert call["stage"] == "answer" and call["window"] == window
        assert call["body"]["questions"] == body["questions"], "Prompt changed: use LIVE=True."
        text_key = "input" if MODEL_KEY == "gemini" else "state"
        assert call["body"][text_key][0] == body[text_key][0] and call["body"]["model"] == MODEL
        assert call.get("pixel_hashes",[call["pixel_hash"]]) == digests and call["input_size"] == sizes[-1], "Image changed: use LIVE=True."
    runs[method]["calls"].append(call)
    show(call, method)
    return call

def show(call, method):
    # These annotated previews are display-only; model inputs never have these overlays.
    left = original.copy(); draw = ImageDraw.Draw(left)
    for i, previous in enumerate(runs[method]["calls"]):
        if previous.get("next_window"):
            draw.rectangle(previous["next_window"], outline="#25865c", width=7)
            draw.text(previous["next_window"][:2], str(i+1), fill="#25865c", stroke_width=2)
    draw.rectangle(call["window"], outline="#25865c", width=7)
    left.thumbnail((420,300))
    body = call["body"]
    image_url = "data:image/jpeg;base64,"+body["input"][-1]["data"] if "input" in body else body["state"][-1]["image_url"]["url"]
    right = decode(image_url)
    right.thumbnail((420,300))
    pair = Image.new("RGB",(860,320),"#eef2e9")
    pair.paste(left,(0,20)); pair.paste(right,(440,20))
    labels = ImageDraw.Draw(pair)
    labels.text((0,0),"Original + crop path",fill="#25382d")
    labels.text((440,0),"Exact submitted image (display scaled)",fill="#25382d")
    display(pair)
    q = call["body"]["questions"][call["stage"]]
    payload = {"input_text":body["input"][0] if "input" in body else body["state"][0], "question":q}
    result = call["response"]["answers"][call["stage"]]
    display(HTML("<b>"+method+" / "+call["stage"]+" · type: choice · "+str(call["elapsed_ms"])+" ms HTTP</b>"
        +"<pre>"+html.escape(json.dumps(result,indent=2))+"</pre>"
        +"<details open><summary>Exact prompt and response type</summary><pre>"+html.escape(json.dumps(payload,indent=2))+"</pre></details>"))
''',True)
    md("## 3. Direct: one image, one answer\n\nThis request contains only the final task question. It makes no crop decisions.")
    code('''full = [0, 0, *original.size]
direct = ask("direct", full)
runs["direct"]["stop_reason"] = "single full-image answer"
''')
    md("## 4. Apply the uncertainty gate and preserve the frame\n\nThis step is Python, with no API call. The model's answer probabilities drive the gate. The crop comes from the visible frame pixels, not a model-generated box or ground truth. Missing, clipped or non-rectangular frames fall back to the initial answer.")
    code('''runs["adaptive"] = initialize_run(direct, original, "adaptive")
print(json.dumps(runs["adaptive"]["decision"], indent=2))
window = full
if runs["adaptive"]["decision"]["followup"]:
    window = runs["adaptive"]["crop_proposal"]["bounds"]
    print("CROP (Python):", window)
    print("Next input: overview + detail, showing the same objects once.")
''')
    md("## 5. Final answer and independent check\n\nThe final question and options are identical to the direct request. Correct means a unique top-probability answer matches the fixture label. A tie or abstention is unresolved. Timing sums every model call; it is HTTP time, not hardware inference time.")
    code('''if runs["adaptive"]["decision"]["followup"]:
    detail = ask("adaptive", window)
finalize_run(runs["adaptive"])
print(runs["adaptive"]["selection_reason"])
print("KNOWN ANSWER:", task["truth"], "(fixture metadata, withheld from inference)")
for method in ("direct", "adaptive"):
    print(method, outcome(task, runs[method]))
print("Evidence:", task["evidence"]["facts"])
if LIVE:
    live_recording = {"task_id": TASK_ID, "protocol": active["protocol"], "runs": runs}
    download = base64.b64encode(json.dumps(live_recording).encode()).decode()
    display(HTML('<a download="live-rerun.json" href="data:application/json;base64,'+download+'">Download this live rerun</a>'))
    print("Fresh results are shown above. The gallery below preserves the original recorded benchmark.")
''')
    md("## 6. Compare models, policies and the new test set\n\nThe new test set was generated and the controller frozen before its inference. Development retains the old grid-crop and model-stop policies. The repeat-full-view control uses the same gate and selection rule but repeats the original image; it matches request count, not image tokens. The table includes all outcomes and timings.\n\nThis tests new labels/layouts within the same framed synthetic task families. It does not establish performance on natural images or learned optimal scale selection. Thermal values are illustrative, not measurements.")
    code('''data["selected_id"] = TASK_ID
data["selected_model"] = active["protocol"]["model"]
data["selected_split"] = SPLIT
viewer = BUNDLE["template"].replace("__BENCHMARK_DATA__", json.dumps(data).replace("<", "\\\\u003c"))
display({"text/html": '<iframe title="Visual mini-benchmark" sandbox="allow-scripts allow-downloads allow-popups allow-popups-to-escape-sandbox" style="width:100%;height:1150px;border:0" srcdoc="'+html.escape(viewer,quote=True)+'"></iframe>'}, raw=True)
''')
    md("[Open the standalone viewer](https://nipunbatra.github.io/d1-zoom-notebook/) · [Source and protocol](https://github.com/nipunbatra/d1-zoom-notebook) · [OpenRouter Decisions request reference](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) · [D1.2 capabilities](https://www.liquid.ai/blog/d1-2)\n\nThe optional LIVE switch reruns only the worked example. The gallery always preserves the original recorded benchmark. Live reruns are shown separately above it and can be downloaded. Installation of Pillow, if needed, requires internet; subsequent replay is offline.")
    for i,c in enumerate(cells):c["id"]=f"cell-{i:02d}"
    nb=dict(cells=cells,metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.13"}},nbformat=4,nbformat_minor=5)
    (ROOT/"d1_crop_walkthrough.ipynb").write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n")
    viewer=template.replace("__BENCHMARK_DATA__",json.dumps(data).replace("<","\\u003c"))
    links='<nav id="export-links" class="export-links" aria-label="Downloads"><a href="d1_crop_walkthrough.ipynb" download>Notebook</a><a href="#code">Code</a></nav>'
    viewer=viewer.replace('<nav id="export-links" class="export-links" aria-label="Downloads"></nav>',links)
    chunks=[]
    for i,c in enumerate([c for c in cells if c["cell_type"]=="code"],1):
        source="".join(c["source"])
        if source.startswith("# Embedded"):source="# Embedded images, recorded responses and the viewer are in cell 2 of the notebook."
        chunks.append(f'<details><summary>Python · cell {i}</summary><pre><code>'+html.escape(source)+"</code></pre></details>")
    appendix=f'<section class="app" id="code"><details><summary>Companion notebook · {len(chunks)} code cells</summary><p>Self-contained replay. Only Pillow and IPython are needed; images and recordings are included.</p>'+"".join(chunks)+"</details></section>"
    (ROOT/"index.html").write_text(viewer.replace("</main>","</main>"+appendix,1))
    print("Built standalone HTML and self-contained notebook.")

if __name__=="__main__":build()
