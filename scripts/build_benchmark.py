"""Build a portable notebook and static HTML from the exact recorded benchmark."""
from pathlib import Path
import base64, html, json, zlib

ROOT=Path(__file__).resolve().parents[1]
def build():
    data=json.loads((ROOT/"recordings/mini-benchmark-v2.json").read_text())
    data.update(model_label="Liquid D1.2",transport="OpenRouter")
    gemini_path=ROOT/"recordings/gemini-benchmark-v1.json"
    if gemini_path.exists():
        gemini=json.loads(gemini_path.read_text())
        assert all(len(t["runs"])==3 and all(r["calls"][-1]["stage"]=="answer" for r in t["runs"].values()) for t in gemini["tasks"]),"Gemini recording incomplete"
        data["model_suites"]=[gemini]
    data["selected_id"]="count-02"
    template=(ROOT/"src/benchmark.html").read_text()
    cells=[]
    def md(source):cells.append(dict(cell_type="markdown",metadata={},source=source.splitlines(keepends=True)))
    def code(source,fold=False):
        cells.append(dict(cell_type="code",execution_count=None,metadata={"jupyter":{"source_hidden":True},"tags":["hide-input"]} if fold else {},source=source.splitlines(keepends=True),outputs=[]))
    md("# Look closer: direct answer or crop first?\n\nRun all cells. This notebook includes every image, prompt, response and the interactive benchmark. **Replay is offline and free.** The worked example counts cross-slot screws; the final viewer has 16 examples in eight task families.\n\nThe comparison uses the same selected model, answer choices and 512 px input limit. Only the crop method gets extra calls. All answers are **multiple choice**, not open-ended extraction.")
    code('''LIVE = False  # True reruns only the worked example: at most 5 billed requests.
TASK_ID = "count-02"
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
    code('''active = data if MODEL_KEY == "d1" else data["model_suites"][0]
policy = active["protocol"]["system_prompt"]
task = next(t for t in active["tasks"] if t["id"] == TASK_ID)
original = Image.open(io.BytesIO(base64.b64decode(task["image"].split(",", 1)[1]))).convert("RGB")
print("SHARED INSTRUCTIONS", policy, "TASK", task["question"], sep="\\n\\n")
print("Model:", active["protocol"]["model"])
print("Final response type: choice. Options:", task["choices"])
''')
    md("## 2. Image, request and crop functions\n\nEach request sends one JPEG at most 512 px on its longest edge. A location choice selects a 3 × 3 grid cell; Python adds half a cell of padding on every side, clips the window, and crops the **original pixels**. The budget is three crops. This tests location decisions with a fixed scale rule.")
    code((ROOT/"scripts/benchmark_core.py").read_text()+'\nMODEL = active["protocol"]["model"]\n',True)
    code('''# Replay validates the current prompt and pixels; LIVE makes the same request.
runs = {name: {"calls": []} for name in ("direct", "zoom")}
def ask(method, stage, window):
    if LIVE:
        call = call_model(task, original, window, stage, key)
    else:
        call = copy.deepcopy(task["runs"][method]["calls"][len(runs[method]["calls"])])
        body, size, digest = request_body(task, original, window, stage)
        assert call["stage"] == stage and call["window"] == window
        assert call["body"]["questions"] == body["questions"], "Prompt changed: use LIVE=True."
        text_key = "input" if MODEL_KEY == "gemini" else "state"
        assert call["body"][text_key][0] == body[text_key][0] and call["body"]["model"] == MODEL
        assert call["pixel_hash"] == digest and call["input_size"] == size, "Image changed: use LIVE=True."
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
    image_url = "data:image/jpeg;base64,"+body["input"][1]["data"] if "input" in body else body["state"][1]["image_url"]["url"]
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
direct = ask("direct", "answer", full)
runs["direct"]["stop_reason"] = "single full-image answer"
''')
    md("## 4. Decide where to look, crop, repeat\n\nRouting responses are **actions**, not answers. Each printed window is a deterministic crop operation with no model call or invented reasoning. A final, separate request will answer the original question.")
    code('''window = full
for depth in range(MAX_CROPS):
    route = ask("zoom", "route", window)
    action = route["response"]["answers"]["route"]["choice"]
    if action == "not_visible":
        runs["zoom"]["stop_reason"] = "not_visible"
        break
    window = crop_window(window, action)
    route["next_window"] = window
    print(f"CROP {depth+1} (Python): {action} -> source window {window}")
else:
    runs["zoom"]["stop_reason"] = "3-crop budget reached"
''')
    md("## 5. Final answer and independent check\n\nThe final question and options are identical to the direct request. Correct means a unique top-probability answer matches the fixture label. A tie or abstention is unresolved. Timing sums every model call; it is HTTP time, not hardware inference time.")
    code('''final = ask("zoom", "answer", window)
print("KNOWN ANSWER:", task["truth"], "(fixture metadata, withheld from inference)")
for method in ("direct", "zoom"):
    print(method, outcome(task, runs[method]))
print("Evidence:", task["evidence"]["facts"])
if LIVE:
    live_recording = {"task_id": TASK_ID, "protocol": active["protocol"], "runs": runs}
    download = base64.b64encode(json.dumps(live_recording).encode()).decode()
    display(HTML('<a download="live-rerun.json" href="data:application/json;base64,'+download+'">Download this live rerun</a>'))
    print("Fresh results are shown above. The gallery below preserves the original recorded benchmark.")
''')
    md("## 6. Explore the whole mini-benchmark\n\nChoose a task, then step through its prompts and crops. Compare the final answers at the top. Switch the zoom policy to inspect the retained early-stop pilot. The expanded score table includes every example, including failures. The fixtures are controlled illustrations; the thermal image is not a physical measurement.\n\nThe early-stop pilot was followed by a fixed crop-budget experiment on the same fixtures, with the unchanged direct responses reused. These are exploratory development results, not a held-out benchmark or evidence of general accuracy gains.")
    code('''data["selected_id"] = TASK_ID
data["selected_model"] = active["protocol"]["model"]
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
