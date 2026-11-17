# Watch the model look closer

[Open the interactive lesson](https://nipunbatra.github.io/d1-zoom-notebook/) · [Download the companion notebook](https://nipunbatra.github.io/d1-zoom-notebook/d1_crop_walkthrough.ipynb)

Choose an example and play its recorded path. Animated zoom, pan, original and cropped inputs, exact prompts, typed questions, real answers, probabilities, and HTTP timings are included. There is nothing to type and no API key is needed. The single HTML file works offline; Python code is folded below the gallery.

## Four examples

| Example | Recorded path | Calls | Sum of HTTP times |
|---|---|---:|---:|
| Cat’s nose, natural photograph | bottom → centre | 3 | 3,079.32 ms |
| Palm island, NASA satellite comparison figure | top_left → left | 3 | 7,200.74 ms |
| Material defect, compared with a healthy reference | centre → centre | 3 | 3,042.89 ms |
| Circuit-board defects | not_visible; stop and review annotations | 2 | 2,074.71 ms |

All answers are actual `liquid/d1.2-20261116` responses recorded through OpenRouter on 17 November 2026. The natural and satellite cases were each run once without retries or selecting an answer. The material case was selected from an earlier batch because it follows the full crop path; the PCB case shows a localization miss. These four teaching cases are not a benchmark. HTTP times include networking and provider behavior.

## How the steps work

1. View the original image and the fixed target.
2. Ask whether the target is visible, or compare with a supplied healthy reference.
3. Ask for one cell of an imaginary 3 × 3 grid, or `not_visible`.
4. Pad the selected cell by half a cell on each side, clip to the image, and crop original pixels.
5. Ask for a finer cell inside the crop.
6. Add the crop origin to map that cell back to the original image.

A `not_visible` answer stops the search. The presence/defect score does not force a location. Purple boxes are deterministic grid regions, not native bounding-box predictions or tight object boundaries. Gold boxes are independent dataset annotations, withheld from the model. No ground-truth boxes are supplied for the cat or satellite cases. High choice probability is not a box-quality score.

Drag to pan, scroll or use +/− to zoom, and choose **Reset to step** to restore the camera. Those controls affect only the displayed view. The **Crop & zoom** step changes the actual input pixels for the next request. Every model step shows its precise input and prompt; raw JSON and code expand on demand.

## Companion notebook

Open `d1_crop_walkthrough.ipynb` in Jupyter and run all cells. It contains 10 code cells: embedded assets, small utilities, and one worked material-inspection example. The final cell embeds all four interactive replays. Images, records, and viewer are self-contained: no checkout, helper module, server, or image downloads. Pillow is the only extra package; setup installs it if missing. IPython comes with Jupyter. Replay otherwise works offline. Running all cells produces trusted interactive outputs; static intermediate images remain readable if a frontend disables scripts.

Leave `LIVE = False` for replay. Optionally set it to `True` for up to three billed material-example requests, using `OPENROUTER_API_KEY` or a hidden key prompt. The other three gallery examples remain recorded. Credentials are never embedded or saved. Replay rejects changed inputs or prompts rather than silently reusing mismatched answers.

This version was executed in an isolated directory with HTTP blocked and checked in JupyterLab. The material example was also checked with three fresh successful API calls. OpenRouter's multimodal Decisions endpoint supports the decision types used here; its Liquid adapter did not accept native bounding-box questions in our checks.

## Sources and scope

- Natural photograph: [Chelsea, scikit-image](https://scikit-image.org/docs/0.26.x/api/skimage.data.html#skimage.data.chelsea), Stefan van der Walt, CC0. 451 × 300 JPEG derivative.
- Satellite figure: [NASA Earth Observatory, Urbanization of Dubai](https://science.nasa.gov/earth/earth-observatory/urbanization-of-dubai-united-arab-emirates-7153/), images by Jesse Allen, data provided by Laura Rocchio, Landsat Project Science Office. Three panels show 2006, 1990, and 1973. The complete 540 × 1060 figure was resized to 522 × 1024 before inference; no panel or target-specific crop was selected beforehand. [NASA image-use guidance](https://www.nasa.gov/nasa-brand-center/images-and-media/) permits educational reuse with credit.
- Material and PCB: public `chewinggum/03.jpg`, `pcb4/01.jpg`, and healthy references from [Liquid's inspection playground](https://d1.liquid.ai/#/inspect), with box metadata from its [manifest](https://d1.liquid.ai/demos/data/inspection/index.json). Images correspond to Amazon Science's [VisA dataset](https://registry.opendata.aws/visa/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): Yang Zou, Jongheon Jeong, Latha Pemula, Dongqing Zhang, and Onkar Dabeer. Images are cropped/resized and overlays added for the walkthrough.

The crop policy has at most two grid decisions. It does not learn an optimal scale. An APERTURE extension could compare `keep this scale / inspect a child / recover wider context / unresolved` while holding its downstream concept scorer fixed; that adaptive-scale experiment remains untested.

For GitHub Pages, serve `index.html` and the notebook from the repository root. There is no build step, external JavaScript, inference backend, or credential in the page.
