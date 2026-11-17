# D1 crop walkthrough

A self-contained Jupyter notebook and static interactive walkthrough of a real Liquid D1.2 inspection run.

- [Open the interactive page](https://nipunbatra.github.io/d1-zoom-notebook/)
- [Download the notebook](https://nipunbatra.github.io/d1-zoom-notebook/d1_crop_walkthrough.ipynb)

## Use it

In Jupyter, open `d1_crop_walkthrough.ipynb` and run all cells. It embeds its images, real responses and viewer: no repository checkout, helper modules, server or data download is needed. Pillow is the only extra package; the first cell installs it if absent. IPython is provided by Jupyter. Replay is otherwise offline. Trust the notebook if the frontend blocks interactive output; running the cells also produces trusted outputs.

Leave `LIVE = False` to replay the included real responses. Set `LIVE = True` for up to three new billed requests using `OPENROUTER_API_KEY`, or a hidden key prompt. Credentials are never embedded in the notebook. Inputs changed in replay are rejected rather than silently matched with an old response.

The page is a standalone `index.html`; download it to use offline. It includes the same animated path, pan/zoom controls, images, prompts, responses and foldable Python cells. It makes no API calls and needs no key or backend.

## Six steps

1. Original specimen.
2. Compare with the healthy reference.
3. Choose one of nine grid cells or `not_visible`.
4. Crop original pixels with context padding.
5. Choose a finer cell inside the crop.
6. Map that cell back to the original and compare dataset annotations.

Purple boxes are deterministic grid regions derived from actual model choices. They are not native bounding-box predictions. Gold boxes are dataset annotations, never sent to D1. Pan/zoom controls affect only the displayed view; the input thumbnail shows the pixels used for the corresponding request.

The worked example was chosen because its saved choices traverse the full crop path. It is not an accuracy benchmark. Fresh calls may return different answers or stop at `not_visible`. The APERTURE connection is a proposed extension, not a tested satellite-image experiment.

## Provenance

Responses were recorded on 17 November 2026 through OpenRouter, resolving to `liquid/d1.2-20261116` (provider Liquid). The three saved HTTP calls total 3,042.89 ms and $0.000053 in API-reported usage. Both include network/provider behavior and should not be treated as a general latency or cost benchmark. The complete prompt, typed questions, answers and usage are embedded.

Images and reference are the public `chewinggum/03.jpg` and `chewinggum/ref.jpg` files from [Liquid's inspection playground](https://d1.liquid.ai/#/inspect). Its [manifest](https://d1.liquid.ai/demos/data/inspection/index.json) supplies the displayed annotations. Images correspond to Amazon Science's [VisA dataset](https://registry.opendata.aws/visa/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): Yang Zou, Jongheon Jeong, Latha Pemula, Dongqing Zhang and Onkar Dabeer, *SPot-the-Difference Self-Supervised Pre-training for Anomaly Detection and Segmentation*. Liquid supplies this sample selection and box metadata. Images are cropped/resized and overlays added for the walkthrough.
