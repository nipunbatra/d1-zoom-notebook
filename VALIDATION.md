# Validation · 17 November 2026

- Reconstructed and byte-compared all **20 displayed model-input JPEGs** against their source crops, including the 512 px preprocessing.
- Checked every crop against the preceding grid choice, every selected cell's original-image coordinates, and all `not_visible` stopping branches.
- Checked the reading answer against the generated code **B742**, and localization against the exact orange-outline centre. Tied scores are displayed as ties.
- Executed all **10 notebook code cells** with HTTP blocked in an isolated directory. The notebook embeds every displayed image and response.
- Checked both image panes, numbered crop paths, per-step prompt/answer/time, example switching, deeper paths and stop states in the browser. Also checked the viewer inside JupyterLab.

## Findings

| Case | Finding | Treatment |
|---|---|---|
| Cat | Final cell is above the nose. Earlier cells also clip it. | Visual-review warning; presented as a control/failure. |
| Satellite | Third location decision is left of the island centre; next crop clips its right side. | Drift and truncation warnings. |
| Material | The second crop returns `not_visible`. | Stop; retain independent annotation overlays. |
| PCB | Location call returns `not_visible` despite dataset labels. | Stop; no fabricated predicted region. |
| Reading | Capped full view ties B742/B174 at 23.5% each. Crop 2 assigns B742 99.7%, while its location cell still misses the outline centre. | Separate reading correctness from localization correctness. |

[Native-resolution reading trace](recordings/reading-native.json) and [512 px reading trace](recordings/reading-512px.json) preserve both experiments, including exact submitted images. The native-resolution experiment was run first and read B742 correctly at every level; its first call assigned B742 97.7%. The capped experiment demonstrates resolution of uncertainty for one image under a stated pixel budget. It is not evidence of a general accuracy gain or a calibrated probability.

The material and PCB annotations are dataset references. Cat/satellite judgments are visual reviews, not invented numeric ground truth. Crops and canvas overlays were corrected to clip at the image boundary. The browser's manual zoom changes only the display; model paths are recorded.

Re-run the data checks with `python scripts/validate.py` (Pillow required). Rebuild and sync the HTML viewer with `python scripts/build_site.py` (standard library only).
