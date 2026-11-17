"""Execute just the notebook in an empty directory, with network disabled."""
from pathlib import Path
import argparse, json, os, re, shutil, sys, tempfile
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/"d1_crop_walkthrough.ipynb"
parser=argparse.ArgumentParser();parser.add_argument("--model",choices=["d1","gemini"],default="d1");parser.add_argument("--case",default="count-02");args=parser.parse_args()
nb=nbformat.read(target,as_version=4)
first=next(c for c in nb.cells if c.cell_type=="code")
for name, value in (("TASK_ID",args.case),("MODEL_KEY",args.model)):
    first.source,count=re.subn(rf'''(?m)^{name}\s*=\s*(?:'[^']*'|"[^"]*")''',f"{name} = {value!r}",first.source)
    assert count == 1, f"Expected one {name} assignment"
guard=nbformat.v4.new_code_cell('import socket\ndef offline_only(*args, **kwargs): raise RuntimeError("Unexpected network access during replay")\nsocket.socket.connect = offline_only\nsocket.create_connection = offline_only')
nb.cells.insert(0,guard)
nb.cells.append(nbformat.v4.new_code_cell('assert len(runs["direct"]["calls"]) == 1 and 1 <= len(runs["adaptive"]["calls"]) <= 2\nfor method in ("direct","adaptive"):\n    assert runs[method]["calls"][-1]["response"] == task["runs"][method]["calls"][-1]["response"]\nassert runs["adaptive"]["selected_call"] == task["runs"]["adaptive"]["selected_call"]\nassert viewer.count("__BENCHMARK_DATA__") == 0\nassert data["tasks"] == BUNDLE["data"]["tasks"] and data["test_suites"] == BUNDLE["data"]["test_suites"], "Recorded benchmark was modified"\nprint("Self-contained replay and exact prompt/pixel guards passed.")'))
nb.cells[-1].source+=f'\nassert TASK_ID == task["id"] == {args.case!r}\nassert MODEL_KEY == {args.model!r}\nassert ("gemini" in active["protocol"]["model"]) == {args.model == "gemini"!r}'
with tempfile.TemporaryDirectory(prefix="d1-notebook-qa-") as folder:
    kernels=Path(folder)/"jupyter/kernels/standalone";kernels.mkdir(parents=True)
    (kernels/"kernel.json").write_text(json.dumps(dict(argv=[sys.executable,"-m","ipykernel_launcher","-f","{connection_file}"],display_name="Standalone QA",language="python")))
    os.environ["JUPYTER_PATH"]=str(Path(folder)/"jupyter")
    run_dir=Path(folder)/"only-notebook";run_dir.mkdir()
    shutil.copy2(target,run_dir/target.name)
    NotebookClient(nb,timeout=120,kernel_name="standalone",resources={"metadata":{"path":str(run_dir)}}).execute()
nb.cells=nb.cells[1:-1]
for i,c in enumerate([c for c in nb.cells if c.cell_type=="code"],1):c.execution_count=i
if args.model=="gemini" or args.case!="count-02":
    target=ROOT/f"work/{args.model}-{args.case}-notebook-qa.ipynb";target.parent.mkdir(exist_ok=True)
nbformat.validate(nb);nbformat.write(nb,target)
print(f"Executed all 9 code cells for {args.model}/{args.case} in isolation with network blocked.")
