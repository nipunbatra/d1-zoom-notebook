# D1 visual search

[Open the viewer](https://nipunbatra.github.io/d1-zoom-notebook/) · [Download the notebook](https://nipunbatra.github.io/d1-zoom-notebook/d1_crop_walkthrough.ipynb)

Full image and current crop side by side. Numbered crop windows stay on the original. Prompt, answer, and HTTP time are visible together. Everything is precomputed; no key or typing is needed. Play, step, pan, or zoom. Code and raw probabilities expand on demand.

## Examples and correctness

| Example | What the recorded calls show |
|---|---|
| Small text, 512 px input cap | Full-image reading is tied between B742 and B174 (23.5% each). Crop 2 returns the known code B742 at 99.7%. Some location decisions still miss the outline centre; these are flagged. |
| Cat, control | The nose is already visible without zoom. The final selected cell is above it. A failure/control, not a successful zoom example. |
| Satellite, drift | Later routing moves left of the island; the next crop cuts off its right side. Both are marked. |
| Material, context loss | centre → centre → not_visible. The deeper crop stops the search. |
| Circuit board, miss | not_visible despite independent defect annotations. No predicted region is invented. |

The small-text test asks **the same reading question at every level** and caps each submitted image at 512 pixels on its longest edge. The known code and orange-outline coordinates come from the generated fixture; they are not supplied as answer metadata to the model. Candidate answers are supplied in the choice question. The initial returned choice was B742, but it tied exactly with B174, so the UI shows the tie. This is uncertainty reduction in one controlled example, not an accuracy benchmark. A separate, uncapped full-resolution call already read B742 correctly at 97.7%; zoom was unnecessary under that condition.

Cat and satellite errors are visual-review findings, not scored against invented ground-truth boxes. The fixture's answer and centre-in-cell checks use exact generated labels. Material and PCB gold boxes are independent dataset annotations, withheld from inference. Purple boxes are grid-derived regions, not native detector boxes or object outlines.

Questions worth testing with zoom are detail-dependent: small text, tiny component attributes, or a local count **under a specified image-resolution budget**. Recognizing a large visible object is a weak zoom demonstration. A higher model probability alone does not establish an accuracy improvement. Cropping can discard context or part of the target.

## Crop rule

A location call chooses a cell in a 3 × 3 grid, or `not_visible`. Pad the selected cell by half a cell on every side, clip to the current image, then crop the original pixels. Repeat for at most four location calls, stopping at `not_visible` or before a proposed crop smaller than 32 pixels. No upsampling. The cat, satellite, and reading examples each include three actual crops. Original-view coordinates are preserved throughout. The right panel uses the exact submitted JPEG, including downsampling in the reading test; source-crop and submitted-image dimensions are displayed separately.

Manual pan/zoom affects only the right-hand view. The left stays fixed. **Result** shows the last model call beside the final overlays; it does not imply an extra request. The viewer combines each crop transition with its ensuing model call; the notebook also retains separate crop images.

## Run or edit

Open `d1_crop_walkthrough.ipynb` in Jupyter and run all cells. Images, recordings, and the viewer are embedded. There are 10 code cells; the worked Python example is material inspection, and the final gallery contains all five examples. Pillow is installed by setup if missing; otherwise replay is offline. No helper files or project checkout are needed. Trust or execute the notebook to enable its interactive output.

Optional `LIVE=True` reruns only the worked material example, making up to five billed OpenRouter requests using an environment key or a hidden prompt. Other gallery examples remain recorded. Modified replay inputs are rejected instead of silently reusing old answers.

The standalone `index.html` works offline. To edit the interface, change `src/viewer.html`, then run:

```sh
python3 scripts/build_site.py
```

This uses only the Python standard library, rebuilds the page from the executed notebook, and syncs the viewer into the notebook's embedded assets and output. `scripts/validate.py` checks the embedded geometry and recorded input images with Pillow. GitHub Pages serves the repository root; no backend or external JavaScript is used.

[Validation report](VALIDATION.md) · [native-resolution reading trace](recordings/reading-native.json) · [512 px reading trace](recordings/reading-512px.json)

## Sources

- All inference responses: actual `liquid/d1.2-20261116` through OpenRouter, 17 November 2026. New continuations were recorded once without retries or replacing misses. Times are HTTP durations, including network/provider behavior.
- Small-text register: generated teaching fixture, fixed seed 29; code B742, Menlo 12 px, original 2000 × 1400. The full-resolution and 512 px experiments are distinct conditions. An analogous portable fixture generator is included in `scripts/make_fixture.py`; the exact recorded image is embedded in the notebook.
- [Chelsea / scikit-image](https://scikit-image.org/docs/0.26.x/api/skimage.data.html#skimage.data.chelsea): Stefan van der Walt, CC0; 451 × 300 JPEG derivative.
- [Dubai / NASA Earth Observatory](https://science.nasa.gov/earth/earth-observatory/urbanization-of-dubai-united-arab-emirates-7153/): Jesse Allen, data provided by Laura Rocchio, Landsat Project Science Office. Panels are 2006, 1990, and 1973. The complete 540 × 1060 figure was resized to 522 × 1024 before inference. [NASA image-use guidance](https://www.nasa.gov/nasa-brand-center/images-and-media/) permits educational reuse with credit.
- Material and PCB: `chewinggum/03.jpg`, `pcb4/01.jpg`, and healthy references from [Liquid's playground](https://d1.liquid.ai/#/inspect), with boxes from its [manifest](https://d1.liquid.ai/demos/data/inspection/index.json). Images correspond to Amazon Science [VisA](https://registry.opendata.aws/visa/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): Yang Zou, Jongheon Jeong, Latha Pemula, Dongqing Zhang, and Onkar Dabeer. Crops and overlays are added for this lesson.

This uses a fixed crop policy. Learned or optimal scale selection, including the proposed APERTURE extension, remains untested.
