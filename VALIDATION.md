# Verification — 17 November 2026

## Frozen experiment and accuracy

- Original 16 development images regenerate byte for byte unchanged. Old D1 and Gemini response records are preserved exactly.
- Generated 16 new test images across the same eight families with new labels/layouts, fixed seed 2026111703. The controller, prompt code, generator and test manifest were hashed at 10:03:19 UTC before any test inference. No test-driven retuning.
- New-test exact accuracy: D1 direct **9/16**, repeated full view **9/16**, revised controller **15/16**. Gemini direct **14/16**, repeat **14/16**, revised **15/16**. D1 gains six and Gemini gains one, with zero regressions in this sample.
- Development: D1 direct 12 → revised 16; Gemini direct 12 → revised 15. Repeat controls remain 12. These are development scores and clearly separated from the new test set.
- Selection replay reproduces every `selected_call`, confidence gate, fallback, crop proposal and acceptance reason from the saved inputs. A rejected follow-up does not replace the selected initial answer in scoring.
- Correctness means a unique highest-probability answer matching the label; ties and abstentions do not count as correct. Remaining failures are retained: a confident D1 code misread and a Gemini counting error.

## Inputs and comparisons

- All 228 previous requests were validated. The new paired experiments contain 134 distinct calls: 32 reused development baselines and 102 newly recorded calls. Total across all versions: 330.
- Every new request was rebuilt exactly from source pixels, including both overview and detail JPEGs. Full input text, instructions, choices, pixel hashes, dimensions and image bytes match the records.
- Every image-derived crop contains the complete evaluation panel. Evaluation coordinates are consulted only by validation, never by the controller or request builder.
- Frame detection fallback checks pass for blank images, broken frames, multiple disconnected frames and clipped frames.
- The repeat control has the same initial answer, gate, request count and acceptance rule as adaptive zoom. It matches requests, **not** image tokens; the adaptive follow-up has two images. No claim that every intervention component is independently isolated.
- All timings include the initial answer and every follow-up, even rejected ones. API latency outliers are retained. D1/OpenRouter and Gemini/Google native use different transports.

## Artifact verification

- Notebook has nine code cells, all assets/functions/records embedded. Both provider paths and the no-follow-up path are executed in an otherwise empty directory with network connections blocked.
- Replay checks actual prompts and pixels. LIVE reruns remain separate from immutable recorded benchmark scores.
- Viewer distinguishes initial/model-detail answers from Python gate, pixel crop and final selection. Both images sent on a detail request remain inspectable.
- Standalone browser and live Jupyter checks passed for the separate Look closer/Benchmark tabs, model/example switching, frame crop, exact two-image prompt and benchmark-to-walkthrough navigation. Browser error logs were empty.
- Tables use `selected_call`, selected model and selected split. Earlier policies remain available only where actually recorded; unsupported policies are not silently substituted.
- Source code, raw API responses and exact requests are available without exposing credentials. Published content and decoded notebook assets are scanned for credentials, account IDs and local paths.

Run `python3 scripts/validate.py` for the complete checks and regenerated scorecards. The new paired scorecard is `data/context-comparison.csv`; `data/context-protocol-v1.json` stores the frozen hashes and primary outcome.

## Limits

These are marked, procedural, closed-choice images. Orange-frame detection is a task-specific image-processing aid; the controller does not learn general object localization or optimal scale. Confidence thresholds are uncalibrated heuristics. Sixteen new within-family examples, one run per model/method and synthetic thermal labels cannot establish general-world performance, statistical certainty or physical measurement accuracy.
