"""Execute just the notebook in an empty directory, with network disabled."""
from pathlib import Path
import argparse, json, os, shutil, sys, tempfile
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/"d1_crop_walkthrough.ipynb"
parser=argparse.ArgumentParser();parser.add_argument("--model",choices=["d1","gemini"],default="d1");args=parser.parse_args()
nb=nbformat.read(target,as_version=4)
if args.model=="gemini":
    first=next(c for c in nb.cells if c.cell_type=="code")
    first.source=first.source.replace('MODEL_KEY = "d1"','MODEL_KEY = "gemini"')
guard=nbformat.v4.new_code_cell('import socket\ndef offline_only(*args, **kwargs): raise RuntimeError("Unexpected network access during replay")\nsocket.socket.connect = offline_only\nsocket.create_connection = offline_only')
nb.cells.insert(0,guard)
nb.cells.append(nbformat.v4.new_code_cell('assert len(runs["direct"]["calls"]) == 1 and len(runs["zoom"]["calls"]) == 4\nfor method in ("direct","zoom"):\n    assert runs[method]["calls"][-1]["response"] == task["runs"][method]["calls"][-1]["response"]\nassert viewer.count("__BENCHMARK_DATA__") == 0\nassert data["tasks"] == BUNDLE["data"]["tasks"], "Recorded benchmark was modified"\nprint("Self-contained replay and exact prompt/pixel guards passed.")'))
with tempfile.TemporaryDirectory(prefix="d1-notebook-qa-") as folder:
    kernels=Path(folder)/"jupyter/kernels/standalone";kernels.mkdir(parents=True)
    (kernels/"kernel.json").write_text(json.dumps(dict(argv=[sys.executable,"-m","ipykernel_launcher","-f","{connection_file}"],display_name="Standalone QA",language="python")))
    os.environ["JUPYTER_PATH"]=str(Path(folder)/"jupyter")
    run_dir=Path(folder)/"only-notebook";run_dir.mkdir()
    shutil.copy2(target,run_dir/target.name)
    NotebookClient(nb,timeout=120,kernel_name="standalone",resources={"metadata":{"path":str(run_dir)}}).execute()
nb.cells=nb.cells[1:-1]
for i,c in enumerate([c for c in nb.cells if c.cell_type=="code"],1):c.execution_count=i
if args.model=="gemini":
    target=ROOT/"work/gemini-notebook-qa.ipynb";target.parent.mkdir(exist_ok=True)
nbformat.validate(nb);nbformat.write(nb,target)
print(f"Executed all 9 code cells for {args.model} in isolation with network blocked.")
