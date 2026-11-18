# Look closer: when does zoom help?

[Open the walkthrough](https://nipunbatra.github.io/d1-zoom-notebook/) · [Self-contained notebook](https://nipunbatra.github.io/d1-zoom-notebook/d1_crop_walkthrough.ipynb)

Choose an example and model in **Look closer**. Follow the initial answer, uncertainty check, crop, detail answer and final selection. The original stays beside the crop, with the crop path marked. Each model step shows its actual prompt, typed response and HTTP time; Python operations are labeled separately. **Benchmark** compares the models. Everything is precomputed: visitors need no key and make no API calls.

## Fresh three-model comparison · 18 November 2026

All three models were rerun on the same 32 existing procedural fixtures: 16 development and 16 test. The controller, prompts and fixtures are unchanged. These are repeat evaluations, **not a newly unseen test set**. All successful responses and failures of the models are retained; no response was retried for a better answer.

**Existing test split — 16 examples:**

| Model | Direct | Context + conditional zoom | Repeat full view | Mean HTTP: direct → zoom |
|---|---:|---:|---:|---:|
| Liquid D1.2 / OpenRouter | 10/16 | **15/16** | 9/16 | 1.04 → 1.67 s |
| Liquid D1.2 Ultra / OpenRouter | 10/16 | **16/16** | 10/16 | 1.14 → 1.79 s |
| Gemini Decision 1 / Google native | 14/16 | **15/16** | 14/16 | 1.51 → 2.11 s |

Each model requested detail on 8/16 test examples. Zoom had zero correct-to-wrong changes in this run.

**All 32 examples, including development — descriptive totals:**

| Model | Direct | Context + conditional zoom | Repeat full view | Mean HTTP: direct → zoom |
|---|---:|---:|---:|---:|
| D1.2 | 22/32 | **30/32** | 22/32 | 1.10 → 1.79 s |
| D1.2 Ultra | 20/32 | **30/32** | 20/32 | 1.51 → 2.13 s |
| Gemini Decision 1 | 26/32 | **30/32** | 26/32 | 1.30 → 1.91 s |

This round made **196 distinct real API calls**, with zero failed requests: 96 fresh initial answers plus 100 follow-ups. Each initial answer is shared only between its own direct, adaptive and repeat methods. Adaptive/repeat order alternates by example; the three models ran concurrently, with one sequential worker per model. Timings sum every request, including rejected follow-ups, network and provider delay. Different transports and internal preprocessing prevent a pure model-speed comparison.

The repeat control uses the same gate, acceptance rule and request count, but repeats the full image. It does **not** match the two-image method's image-token budget. These results do not isolate every effect of cropping, duplicated context and extra image tokens.

[Every outcome and timing](data/comparison-20261118.csv) · [Summary and rows](data/comparison-20261118.json) · [Frozen sources and run protocol](data/comparison-20261118-protocol.json)

## Exact policy

1. Ask the final multiple-choice question on a full-image JPEG capped at 512 px.
2. Keep a unique, non-`uncertain` answer when top probability is at least **0.85** and its margin over the next option is at least **0.15**.
3. Otherwise, locate the **visible orange frame from image pixels**. Require a complete rectangular frame and pad its width/height by **5% per side**. Crop original pixels and cap the detail at 512 px. Missing, clipped, small or nonrectangular frames fall back to the initial answer.
4. Send overview **and** detail with the same final question/options. Identify them as two views of the same objects, counted once.
5. Accept the follow-up only if its answer is unique, non-uncertain, and its top probability is at least **0.05 higher** than the initial top. Otherwise retain the initial answer. Charge every call to total HTTP time.

The thresholds are uncalibrated heuristics. Remaining failures are visible: D1 confidently misreads test `R582` as `R852` and skips detail; Gemini still miscounts the difficult screw example; Ultra misses two development counting examples despite 16/16 on the test split.

The frame is a task-provided cue. Detecting it from pixels avoids evaluation-coordinate access but does **not** demonstrate learned object grounding or optimal scale selection. Model probabilities drive a Python gate; image processing proposes a region. APERTURE is not implemented. The earlier grid policy sometimes removed evidence and stopped too soon; its original records are preserved in the repository.

## Prompts, tasks and evidence

Eight families: small text, fastener counting, thermal colorbars, charts, tables, circuit continuity, spatial relations and analog gauges. Each split has two examples per family. All 32 are procedural fixtures, not natural images or measurements. Thermal values are display labels. Splits share styles and families, so this small benchmark cannot establish general-world performance.

D1 uses OpenRouter `state`; Gemini uses native Google `input`. Both use typed `questions`. Shared instructions serve the system-prompt role by being **prepended to each question**, without an invented chat-role field. Exact request bodies and unmodified response content are inspectable. Multiple choice supplies answer candidates and `uncertain`; this is not open-ended OCR. Evaluation labels/coordinates never enter inference or controller decisions.

Correctness requires a unique highest-probability option matching the known label and returned choice. Ties and abstentions are unresolved. `selected_call` identifies the final answer, including when a follow-up is rejected. Gold regions are evaluation overlays; green windows are actual crops, **not native detector boxes**.

The controller, generator and test manifest were frozen on 17 November before the first test run. This repeat round additionally froze its recorder and development manifest at **2026-11-18 05:03:05 UTC**, before its first request. Raw recording `protocol.policy` and `route_instructions` are inherited legacy metadata; the operative policy is `controller_spec`, `experiment`, and the exact request bodies. Those raw records remain immutable.

## Native single and multiple bounding boxes

[Key-free evidence page: working choice vs rejected box](openrouter-box-check.html). Four additional matched-image requests confirmed HTTP200 for choice and HTTP400 for box on both Liquid models; timestamps and measured HTTP times are shown together.

Liquid documents native `box` / `boxes` outputs. The chosen OpenRouter route currently does not expose them for Liquid: both D1.2 and Ultra returned HTTP 400, **“Liquid does not accept box questions; question 1 is a box”**, on `/api/alpha/decisions`. OpenRouter's adapter guide lists Liquid question types as `noul`, `choice`, `score`; `box` requires a TypeSafe endpoint. This is a provider integration limitation, not evidence that Liquid's model cannot ground objects. [Exact capability probes, responses and timings](recordings/openrouter-capabilities-20261118.json).

We are keeping Liquid access **OpenRouter only**. Image-based numeric estimates work, but counts cannot be presented as predicted boxes. [Prepared COCO fixtures and capability notes](NATIVE-DETECTION.md) · [Native Liquid object localization](https://docs.liquid.ai/lfm/models/d1#locate-objects) · [OpenRouter endpoint support](https://openrouter.ai/docs/guides/community/multimodal-decisions#what-each-endpoint-accepts) · [Question posted to Liquid](https://x.com/nipun_batra/status/2122919961417154708)

## Run and edit

Open the notebook in Jupyter and run all **nine code cells**. Images, records, functions and viewer are embedded; after installing Pillow, replay runs offline without a checkout. Change `MODEL_KEY` to `"d1"`, `"ultra"` or `"gemini"`, and `SPLIT` to `"test"` or `"development"`. Trust/run the notebook to enable HTML output.

`LIVE=True` reruns only the worked example, making at most two billed requests. Both Liquid models use `OPENROUTER_API_KEY`; Gemini uses `GEMINI_API_KEY` / `GOOGLE_API_KEY`. Keys are requested privately if absent. Fresh results can be downloaded separately; aggregate scores preserve the recordings. Replay rejects changed prompts or pixels.

```sh
python3 -m pip install -r requirements.txt
python3 scripts/build_site.py
python3 scripts/execute_notebook.py
python3 scripts/execute_notebook.py --model ultra
python3 scripts/execute_notebook.py --model gemini
python3 scripts/execute_notebook.py --case spatial-01
python3 scripts/validate.py
python3 -m http.server 8788
```

- `src/benchmark.html`: static viewer, no frontend dependencies.
- `scripts/context_controller.py`: frozen controller and exact provider request functions.
- `scripts/record_comparison.py`: resumable three-model recorder; completed calls are reused and source changes refused. Keys stay out of records.
- `recordings/comparison-20261118-{split}-{model}.json`: six complete current recordings.
- `scripts/validate_comparison.py`: exact requests, images, selection, frozen-source hashes and paired scores.
- `scripts/make_benchmark.py`, `scripts/make_heldout.py`: original fixture generators, unchanged.

Across historical and current benchmark versions there are **526 distinct API calls** (330 earlier + 196 fresh). Separate endpoint-capability probes are not benchmark results. Gemini does not return a dated resolved build, so its requested alias `gemini-decision-1` is reported. Liquid resolves to `liquid/d1.2-20261116` and `liquid/d1.2-ultra-20261116`.

[Validation report](VALIDATION.md) · [Previous frozen experiment](https://github.com/nipunbatra/d1-zoom-notebook/tree/39a8071) · [Earlier policies and recordings](recordings/context-development-v1.json)

## Sources and history

[Google Decisions API](https://aistudio.google.com/docs/decisions-api) · [OpenRouter Decisions reference](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) · [Liquid D1.2](https://www.liquid.ai/blog/d1-2)

The earlier real-image cat/satellite/material gallery is preserved in [revision 1885a2f](https://github.com/nipunbatra/d1-zoom-notebook/tree/1885a2f). Its cat localization was a failure, not ground truth. The older two-model synthetic benchmark is in [revision 6ba1951](https://github.com/nipunbatra/d1-zoom-notebook/tree/6ba1951).
