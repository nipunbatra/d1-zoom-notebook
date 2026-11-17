# Verification — 17 November 2026

## Records and comparison

- 16 fixtures, eight families, two examples per family; generated and visually checked before inference. All labels checked against the generating values/object lists/geometry.
- 113 unique real OpenRouter responses: 16 direct, 64 fixed-budget crop, 33 early-stop pilot. Resolved model was `liquid/d1.2-20261116` in every call. No provider fallbacks or response replacement.
- Rebuilt **all 113 submitted JPEGs byte for byte** from the recorded original image, crop window, 512 px cap and quality 95. Checked image hashes, dimensions, crop geometry, response schema/probabilities, prompts and model IDs.
- Every final question and candidate set is identical across methods for its fixture. Shared instructions are prepended to the typed question. Ground-truth labels/coordinates are not sent as metadata; candidate answers are supplied in this closed-choice task.
- All pilot recordings are preserved exactly. Direct responses are reused unchanged in the second experiment. The second crop protocol was developed after observing the pilot; this is explicitly not a held-out evaluation.
- Scores recomputed from unique top-probability matches: direct **12/16**, fixed crop **12/16**, early-stop **11/16**. Fixed cropping gains four and loses four. Ties and abstentions count as unresolved, not correct. No claim of overall accuracy improvement.
- Times sum recorded HTTP durations across every model call. Mean per-example HTTP time is **856.67 ms**, **3246.42 ms**, and **1721.53 ms**, respectively. API-reported cost for the 113 unique calls is **$0.001178**.

## Gemini native API

- Existing Gemini environment key authenticated successfully. Recorded 115 real native Decisions calls on the same 16 images and three methods. All 115 request JPEGs were rebuilt byte for byte; instructions, options and crop paths were checked against the frozen D1 protocol.
- Native responses are preserved unchanged, with their actual `input` requests. No invented model build IDs or API-reported costs. The requested alias is `gemini-decision-1`; native responses omit a dated resolved version.
- Gemini direct **12/16**, fixed crop **11/16**, early-stop **12/16**. Mean total HTTP times: **1108.07 ms**, **5397.64 ms**, **2425.21 ms**. All latency outliers are retained.
- 228 requests across both models, 96 method/example runs. `data/model-comparison.csv` contains all results. These APIs have different transports and possibly different internal preprocessing, so latency is not a pure model comparison.

## Notebook and interface

- All **nine notebook code cells** executed successfully for **both model selections** in an isolated temporary directory containing only the notebook, with network connections blocked. Replay validates prompt and input-pixel identity. No helper files are required.
- Notebook setup uses Pillow only if already installed, otherwise installs the pinned package. Installation and optional live inference require internet; recorded replay does not.
- Browser checks: model dropdown preserves the selected task; cross-model table matches all six model/method aggregates; both policy selections, direct versus crop traces, full sequence including deterministic crops, counting improvement, counting regression, score table, exact prompts, tied choices, image pan/zoom/reset and source-region coverage.
- The full original remains fixed beside the exact submitted JPEG. Three numbered crop windows are visible on the original at the final step. Region coverage is labeled as evaluation geometry, not accuracy.
- Shared instructions, task question, final answers and total time are visible together; raw request/response and notebook code are expandable. Final task answers are distinct from intermediate routing choices.
- All media, code and records are embedded in the static page. No runtime network requests or API credentials are needed.

Run `python3 scripts/validate.py` to regenerate `data/scorecard.json` and `data/scorecard.csv`. Run `python3 scripts/execute_notebook.py` to repeat isolated notebook execution. The page can be served directly by GitHub Pages or opened as a standalone HTML file.

## Scope

These are generated, multiple-choice teaching fixtures with a marked target panel. They are not natural-image, satellite, medical, or industrial test sets. The thermal image is non-radiometric. The crop controller selects a location under a fixed padding and budget rule; it does not demonstrate learned optimal scale selection or APERTURE. A 16-item development set and single samples cannot establish general model performance or reliable latency distributions.

Independent read-only review found two provenance issues, both fixed: LIVE reruns now stay separate from immutable recorded scores, and protocol-development/direct-reuse disclosure is rendered in the standalone benchmark panel.
