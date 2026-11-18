# Verification — 18 November 2026

## Fresh round and accuracy

- All three models ran on the same 32 existing fixtures (development16 + test16), with new initial answers for every model/example pair. This is repeat evaluation, not a newly unseen test set.
- The unchanged controller/prompt/fixture sources and new recorder were hashed before the first request at 05:03:05 UTC. All previous response records are preserved.
- **196 distinct real API calls**, zero failed attempts, 96 model/example pairs, 288 method outcomes. Baselines are shared only within their corresponding direct/adaptive/repeat comparison.
- Test16 direct / adaptive / repeat: **D1 10 / 15 / 9; Ultra 10 / 16 / 10; Gemini 14 / 15 / 14**.
- All32, including development: **D1 22 / 30 / 22; Ultra 20 / 30 / 20; Gemini 26 / 30 / 26**. Zero adaptive correct-to-wrong changes in this run. Model errors and latency outliers remain in the records.
- Alternated adaptive/repeat request order by fixture. One sequential worker per model, models concurrent. No successful response retried to improve an answer.

## Requests, crops and scoring

- Validated earlier records plus all fresh records: exact image bytes, question text, options, provider configuration, model/endpoint, hashes, input sizes/windows and timestamps.
- Submitted windows are checked against the independently replayed controller proposal; direct and repeat must use the full source image. All adaptive windows retain the complete evaluation panel.
- Evaluation coordinates are read only by validation, never by inference/controller code. Existing fallback checks cover blank, broken, disconnected and clipped frames.
- Replayed confidence gates, crop proposals, selected-call indices and acceptance reasons. A rejected follow-up cannot silently replace the initial answer in scoring.
- Correctness requires a unique top-probability option equal to both the known label and returned choice. Ties and abstentions are unresolved.
- Direct/adaptive/repeat share the same final task. Repeat matches request count and acceptance rule, not image-token budget. Adaptive follow-ups contain overview plus detail.
- HTTP totals include every request, even rejected follow-ups; different transports and network/provider delay limit speed comparisons.
- The raw recording protocol includes inherited grid-policy descriptions. Raw records remain immutable. Viewer/notebook exports use corrected context-v1 metadata, preserve the original under `legacy_protocol`, and leave all request/response bodies unchanged.

## Notebook and viewer

- All nine notebook cells executed for D1, Ultra and Gemini in an otherwise empty directory with network connections blocked. A no-follow-up example also passed.
- Replay compares the **entire rebuilt request body**, including embedded image payloads and provider options, plus image sizes/windows and pixel hashes.
- Model selection is by stable model key; Ultra cannot accidentally select Gemini. The executed notebook includes the selected model's actual responses and timings.
- Browser checks passed for three-model dropdown, direct/detail answers, shared instructions, exact two-image prompt, split switching, repeat control, per-example navigation, and the three-row comparison table. The table includes correctness, mean HTTP duration and mean calls for direct, adaptive and repeat. No browser error logs were reported.
- Independent read-only code review identified four gaps: submitted-window validation, inherited protocol metadata, complete request replay checking, and repeat timing visibility. All were addressed without changing frozen inference code or recorded responses.
- Credentials are not embedded. Publication scans include generated HTML, notebook outputs and decoded compressed notebook assets.

## Native object boxes

Both Liquid models rejected the OpenRouter `box` request with HTTP400: `Liquid does not accept box questions; question 1 is a box`. OpenRouter's documented Liquid adapter supports `noul`, `choice`, `score`; this corroborates an integration limitation, not a failure of the native model. Four additional fresh requests with identical image/state reproduced HTTP200 for choice and HTTP400 for box on both models. [Evidence page](openrouter-box-check.html) and [saved requests/responses](recordings/openrouter-box-check-20261118.json) omit authentication headers entirely. No native Liquid API was called. Real-image fixture preparation, source annotations and endpoint evidence are separate from these measured zoom results; see [NATIVE-DETECTION.md](NATIVE-DETECTION.md).

## Reproduce and limitations

Run `python3 scripts/validate.py` for old and new record checks and scorecards. Current results: [CSV](data/comparison-20261118.csv), [JSON](data/comparison-20261118.json), [frozen protocol](data/comparison-20261118-protocol.json).

These are framed, procedural, closed-choice images with shared task families/styles. Frame detection is an image-processing aid, not learned general localization or optimal scale selection. Confidence thresholds are uncalibrated heuristics. One run per model/method on 32 fixtures cannot establish a general model ranking or statistical certainty. Thermal labels are not physical measurements. COCO preparation supplies source annotations, not model-predicted boxes or an exhaustive count benchmark.
