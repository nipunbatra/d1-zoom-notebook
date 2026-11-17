# Look closer: a visual mini-benchmark

[Open the interactive walkthrough](https://nipunbatra.github.io/d1-zoom-notebook/) · [Download the notebook](https://nipunbatra.github.io/d1-zoom-notebook/d1_crop_walkthrough.ipynb)

**16 controlled examples, eight task families.** Choose a model and example; compare its final answers; then play through every prompt, routing decision, crop and response. The full original stays beside the exact submitted image, with the crop path marked. Prompts, answer types, probabilities and HTTP times are visible. Everything is precomputed and works offline; no typing or API key is needed.

Tasks: small text, cross-slot screw counting, thermal colorbar reading, chart reading, table lookup, circuit continuity, spatial relations and analog gauges. Every image is procedurally generated. Thermal colors and units are illustrative display labels, not physical measurements. The two examples per family differ in content and panel size; they are not a paired size-only ablation.

## What the recorded runs show

| Model / API | Method | Correct | Mean HTTP time | Mean calls |
|---|---|---:|---:|---:|
| D1.2 / OpenRouter | Direct | 12/16 | 0.86 s | 1.00 |
| D1.2 / OpenRouter | Up to 3 crops | 12/16 | 3.25 s | 4.00 |
| D1.2 / OpenRouter | Model decides when to stop | 11/16 | 1.72 s | 2.06 |
| Gemini Decision 1 / Google native | Direct | 12/16 | 1.11 s | 1.00 |
| Gemini Decision 1 / Google native | Up to 3 crops | 11/16 | 5.40 s | 4.00 |
| Gemini Decision 1 / Google native | Model decides when to stop | 12/16 | 2.43 s | 2.19 |

For D1.2, cropping fixes four direct errors: the smaller counting and table tasks, and both gauges. It also introduces four errors: the larger counting and chart tasks, and both circuit tasks. **There is no overall accuracy improvement in this set.** Crop windows can remove essential context. Spatial tasks and the text examples are useful controls where extra calls are unnecessary.

The 113 D1 requests used `liquid/d1.2-20261116` through OpenRouter on 17 November 2026. Their total API-reported cost was $0.001178. Each response is retained; none was retried to obtain a preferred answer. Times are single HTTP durations including network/provider delay, not model-only latency. The two methods have unequal compute budgets, intentionally reported.

Gemini uses the existing `GEMINI_API_KEY` through the native `POST /v1beta/decisions` endpoint. Its 115 real requests use the same fixtures, final questions, choice sets and crop policies. The API returns no dated model build identifier or cost, so the requested `gemini-decision-1` alias and full native responses are preserved. Its results are not OpenRouter responses or chat-completion approximations. [Cross-model scorecard](data/model-comparison.csv).

The APIs use different transports and may preprocess images differently internally. Submitted JPEGs follow the same 512 px cap. These times include transport/network variation; Gemini had an 11.76 s routing call, retained in the results. They are not pure model-speed measurements. Both models score 12/16 directly; neither shows an overall gain from the fixed crop policy.

The initial D1 controller chose `answer_now` on 15/16 full images, including incorrect cases. We then changed to a fixed three-crop budget on the same fixtures. **The early-stop pilot remains selectable in the viewer.** Direct requests were unchanged and their original responses were reused. This is exploratory protocol development, not held-out evaluation. Repeated identical full-image answer requests in the pilot sometimes differ; those changes are not crop effects.

## Prompts and comparison

The shared instructions are displayed in full. D1's Decisions API uses `state`; Gemini uses `input`. Both requests use typed `questions`, rather than a chat-role system field. The shared policy serves the system-prompt function by being prepended to each question's `instructions`. Exact requests can be downloaded, and raw responses expand in place.

Both methods use the same final question, answer options, model and maximum 512 px image edge. **Answers are closed-choice**, including an `uncertain` option; this is not free-form OCR or arbitrary-number extraction. Routing calls contain no final answer question. Their choices select a 3 × 3 grid cell or `not_visible`. Python pads the selected cell by half a cell on each side, clips to the current view and crops the original pixels. Each crop is separately shown as a deterministic operation. A final request answers the original task.

The fixed policy makes at most three location calls and three crops. It stops early at `not_visible`. The pilot additionally offers `answer_now`. Neither policy implements APERTURE or learns an optimal crop scale. Green boxes are crop windows, not native detector boxes. Gold reference regions and known answers are evaluation metadata, excluded from requests. Reference-region retention is geometric coverage, not an accuracy score.

Correctness requires a unique highest-probability option matching the known answer and returned choice. Ties and abstentions are unresolved and count as not correct. Labels come from the generated fixture specification; counting checks the object list, charts/tables check their source values, and circuit/gauge/spatial labels check the generating geometry. The fixtures were also visually inspected before inference. See the [full scorecard](data/scorecard.csv), [recordings](recordings/mini-benchmark-v2.json), and [validation report](VALIDATION.md).

## Notebook and source

Open `d1_crop_walkthrough.ipynb` in Jupyter and run all **nine code cells**. It includes the images, recordings, crop functions and interactive viewer. The worked counting example shows each actual input and complete prompt, including shared instructions. No checkout or helper file is needed. Pillow is installed if absent; replay otherwise needs no network. Trust or run the notebook to enable interactive HTML output.

Set `MODEL_KEY` to `"d1"` or `"gemini"` for the worked notebook example. Both paths are verified offline. `LIVE=True` reruns only that example, with up to five billed calls, using `OPENROUTER_API_KEY` for D1 or `GEMINI_API_KEY` / `GOOGLE_API_KEY` for Gemini, or a hidden prompt. Fresh results and a download are shown separately; the gallery and aggregate scores always preserve the original recordings. Replay refuses changed prompts or pixels rather than attaching old answers to new inputs.

The repository uses Python, Pillow and vanilla HTML/CSS/JS. No frontend dependencies or build service are required.

```sh
python3 -m pip install -r requirements.txt
python3 scripts/build_site.py          # builds HTML and an unexecuted notebook
python3 scripts/execute_notebook.py    # D1 replay with network blocked
python3 scripts/execute_notebook.py --model gemini  # Gemini replay in work/
python3 scripts/validate.py            # checks all inputs, paths and scores
python3 -m http.server 8788            # preview the repository root
```

Edit `src/benchmark.html` for the viewer. `scripts/benchmark_core.py` defines the shared prompts, request schema and crop rule. `scripts/make_benchmark.py` creates all 16 images and their labels; Pillow 13.0.0 is pinned for fixture reproduction. `scripts/record_benchmark.py` (D1) and `scripts/record_gemini.py` (Google native) checkpoint each response and resumes without replacing it. Inference needs an existing environment key; the browser never receives credentials. Changing an existing fixture or protocol causes a recording-resume mismatch instead of silently mixing experiments.

The earlier cat/satellite/material gallery is preserved in [revision 1885a2f](https://github.com/nipunbatra/d1-zoom-notebook/tree/1885a2f). Its cat localisation was a failure, not ground truth; the new scored suite uses explicit generated labels.

## API references

- [Google Decisions API documentation](https://aistudio.google.com/docs/decisions-api) and [official announcement](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/)

- [OpenRouter Decisions request schema](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)
- [OpenRouter's Decisions reference](https://github.com/OpenRouterTeam/skills/blob/main/skills/openrouter-decisions/references/decisions-api.md)
- [Liquid D1.2 model](https://openrouter.ai/liquid/d1.2) and [Liquid's capability announcement](https://www.liquid.ai/blog/d1-2)

Only the choice interface actually verified through OpenRouter is used here. Liquid's newer native extraction/box capabilities are not implied by the display overlays.
