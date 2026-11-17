# Look closer: when does zoom help?

[Open the walkthrough](https://nipunbatra.github.io/d1-zoom-notebook/) · [Self-contained notebook](https://nipunbatra.github.io/d1-zoom-notebook/d1_crop_walkthrough.ipynb)

The **Look closer** tab lets you choose an example and model, then follow one step at a time: initial answer, uncertainty check, crop, detail answer and final selection. Every model step exposes its actual prompt, typed response and HTTP time. The original stays beside the crop. Python operations are labeled separately. The **Benchmark** tab contains the comparisons and experiment details. Everything is precomputed; the browser needs no key and makes no API calls.

## The controller is now better

The previous grid policy repeatedly shrank the view. Some failed runs kept only 23–35% of the task panel, removing objects or labels. The earlier readiness question also stopped too soon: D1 chose `answer_now` on 15/16 full images, including wrong answers. These recordings remain available under **Development**.

The replacement answers first, preserves context and requests more detail only when needed. Its rules were frozen before inference on 16 new synthetic examples.

**New test set — 16 examples per model:**

| Model | Direct | Repeat full view | Keep context + zoom if uncertain |
|---|---:|---:|---:|
| Liquid D1.2 | 9/16 | 9/16 | **15/16** |
| Gemini Decision 1 | 14/16 | 14/16 | **15/16** |

D1 gains six correct answers and Gemini gains one, with **zero correct-to-wrong changes** on this test. The repeat control uses the same uncertainty gate, acceptance rule and number of requests, but repeats the full image. It does not match the two-image method's image-token budget. This supports the revised intervention on these fixtures; it does not isolate every effect of crop, duplicated context and additional image tokens.

| New-test model | Mean direct / revised HTTP time | Mean revised calls | Examples receiving detail |
|---|---:|---:|---:|
| D1.2 / OpenRouter | 0.87 / 1.42 s | 1.56 | 9/16 |
| Gemini / Google native API | 2.53 / 3.76 s | 1.50 | 8/16 |

Times include every call, network and provider delay. Gemini's direct median is 1.25 s and revised median is 2.10 s; its 16.41 s baseline outlier is retained in both paired methods. Different transports and internal image preprocessing prevent a pure model-speed comparison.

On the original development examples, the revised policy scores D1 **16/16** and Gemini **15/16**, versus **12/16** directly for each. These development results informed the design and are not held-out evidence. [All paired outcomes and timings](data/context-comparison.csv) · [Frozen protocol and hashes](data/context-protocol-v1.json).

## Exact policy

1. Ask the original multiple-choice question on a full-image JPEG capped at 512 px.
2. Keep a unique, non-`uncertain` answer if its top probability is at least **0.85** and its margin over the next option is at least **0.15**.
3. Otherwise, locate the **visible orange frame from image pixels**. Require a complete rectangular frame; pad the detected width/height by **5% on every side**. Crop original pixels and cap this detail image at 512 px. Missing, clipped, small or nonrectangular frames fall back to the initial answer.
4. Send the original overview **and** detail crop with the same final question/options. Explicitly identify them as two views of the same objects, counted once.
5. Use the follow-up only if it has a unique, non-uncertain answer and top probability at least **0.05 higher** than the initial top. Otherwise retain the initial answer. Charge all calls to the method's total time, including rejected follow-ups.

These thresholds and probability comparisons are heuristics, not calibrated guarantees. The remaining D1 test error is a confident `R852` misread of `R582`, so the controller skips detail. Gemini still counts 13 cross-slot screws as 11 after seeing detail. Neither failure was removed or retried for a better result.

The visible frame is a task-provided cue. Detecting it from pixels avoids evaluation-coordinate access, but does **not** demonstrate learned general object grounding or optimal scale selection. This is a hybrid controller: model answer probabilities drive a Python gate; image processing proposes the context-preserving region. APERTURE is not implemented.

## Tasks, prompts and evidence

Eight families: small text, fastener counting, thermal colorbars, charts, tables, circuit continuity, spatial relations and analog gauges. Each split contains two examples per family. All 32 images are procedural fixtures, not natural images or measurements. Thermal values are display labels. Test labels/layouts differ from development, but share rendering styles and task families; this is a small within-family transfer test, not a general benchmark.

The test generator (seed `2026111703`), generated test manifest, controller and prompt code were hashed and frozen at **2026-11-17 10:03:19 UTC**, before every test request. The original 16 images still regenerate byte for byte. Original responses are immutable; all new test baselines were recorded fresh, then shared between their paired methods. No test outcome was used to adjust the controller or test fixtures.

D1 uses OpenRouter `state`; Gemini uses native Google `input`. Both use typed `questions`. Shared instructions serve the system-prompt role by being prepended to each question; there is no invented chat-role system field. Exact requests and unmodified response content are available in the viewer. Multiple choice includes the answer candidates and `uncertain`; this is not open-ended OCR. Evaluation labels and coordinates are excluded from inference and controller decisions.

Correctness requires a unique maximum-probability option matching the known label and returned choice. Ties and abstentions are unresolved. `selected_call` explicitly identifies the final answer when a follow-up is rejected; scoring never silently uses the last call. Gold regions are evaluation overlays; green windows are actual crops, not native detector boxes.

## Run and edit

Open the notebook in Jupyter and run all **nine code cells**. Images, responses, functions and viewer are embedded. It runs offline after Pillow installation; no checkout or helper files are needed. The worked example uses the new test counting task. Change `MODEL_KEY` between `"d1"` and `"gemini"`, or `SPLIT` between `"test"` and `"development"`. Trust/run the notebook to enable its HTML output.

`LIVE=True` reruns only the worked example, making at most two billed calls. It uses the existing `OPENROUTER_API_KEY` for D1 or `GEMINI_API_KEY` / `GOOGLE_API_KEY` for Gemini, or asks privately. Fresh results can be downloaded separately; the gallery and aggregate scores preserve the recordings. Replay rejects changed prompts or pixels.

```sh
python3 -m pip install -r requirements.txt
python3 scripts/build_site.py
python3 scripts/execute_notebook.py
python3 scripts/execute_notebook.py --model gemini
python3 scripts/execute_notebook.py --case spatial-01   # verifies no-follow-up path
python3 scripts/validate.py
python3 -m http.server 8788
```

- `src/benchmark.html`: static viewer; no frontend dependencies.
- `scripts/context_controller.py`: frozen controller, native requests and image-derived crop.
- `scripts/record_context.py --split development|test`: checkpointed, one-run recording. It refuses changed frozen code/data. Keys stay in the process, never in records.
- `scripts/make_benchmark.py`: original generators; default images remain unchanged.
- `scripts/make_heldout.py`: new test generator; refuses to overwrite an existing test manifest.
- `scripts/validate_context.py`: exact pixels/requests, selection, frame fallback, complete evidence retention, freeze provenance and paired scores.

There are **330 distinct recorded API calls** across all versions: the original 228 plus 102 new calls for this experiment. Development reuses 32 initial answers; those are not double-counted. Native Gemini responses omit a dated resolved model build and price, so the requested `gemini-decision-1` alias is reported honestly. D1 resolves to `liquid/d1.2-20261116`.

[Validation report](VALIDATION.md) · [New test recordings](recordings/context-test-v1.json) · [Development recordings, including old policies](recordings/context-development-v1.json)

## Sources and previous versions

[Google Decisions API](https://aistudio.google.com/docs/decisions-api) · [OpenRouter Decisions](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) · [Liquid D1.2](https://www.liquid.ai/blog/d1-2)

The earlier real-image cat/satellite/material gallery is preserved in [revision1885a2f](https://github.com/nipunbatra/d1-zoom-notebook/tree/1885a2f). Its cat localisation was a failure, not ground truth. The old two-model synthetic benchmark is preserved in [revision6ba1951](https://github.com/nipunbatra/d1-zoom-notebook/tree/6ba1951) and remains accessible through the development split's original policies.
