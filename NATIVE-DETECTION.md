# Grounding capability and annotated counting fixtures

Prepared 18 November 2026. **Liquid access remains OpenRouter-only.** The separate Gemini comparison uses the previously authorized native Google API. No native Liquid runner was created, no native Liquid credentials were accessed, and this fixture preparation made no model calls. There are no predictions or measured detection results in this fixture set.

## What the two API routes expose

OpenRouter's current [provider capability table](https://openrouter.ai/docs/guides/community/multimodal-decisions#what-each-endpoint-accepts) lists `LiquidDecisionsAdapter` with `noul`, `choice`, and `score` questions. Its general Decisions schema includes `box`, but the guide restricts that capability to a TypeSafe endpoint. Liquid's native `boxes` is not exposed through this Decisions route. This is a transport limitation, not evidence that the Liquid model lacks grounding.

Numeric estimation is separate: [OpenRouter's Extractions documentation](https://openrouter.ai/docs/guides/community/extractions#supported-models) lists both Liquid models with image input for `estimate` fields on `/api/alpha/extractions`. Separate project probes succeeded for both models. Those probes are outside this fixture preparation. Do not generalize the box limitation to numeric estimates or confuse the Extractions `fields` schema with Decisions `questions`.

Fresh 18 November probes confirmed the same box rejection for both D1.2 and Ultra; [exact requests, responses and timings](recordings/openrouter-capabilities-20261118.json). Earlier project probes also agree: `box` returned HTTP 400 with “Liquid does not accept box questions; question 1 is a box”; `boxes` failed the gateway's type discriminator. Their original timestamps, model, status, timing, and exact error responses are preserved in [transport-evidence.json](data/detection/transport-evidence.json). These are excerpts of the earlier 17 November probes, not new tests.

Liquid's [native Locate Objects documentation](https://docs.liquid.ai/lfm/models/d1#locate-objects) describes POST `https://api.liquid.ai/decisions/v1/systemone` with exactly one image when requesting `box` or `boxes`. A question fragment for multiple instances is:

```json
{"type": "boxes", "instructions": "Every individual banana.", "max": 16}
```

This is an unexecuted schema example. Native `box` answers contain `box`, `found`, and `confidence`; normalized edges are `left`, `top`, `right`, and `bottom`. Native `boxes` adds an array of these entries, `count`, `at_least`, and `presence`. The optional `max` accepts 1–64 and defaults to 16. `found < 0.5` means no box, represented by `null`. Saturated answer slots need attention through `at_least`. These documented native features were not tested here.

The earlier grid-choice crops and current pixel-derived frame crops are application-derived regions. They must not be relabeled as native object detections or scored as though the model returned object boxes.

## Four real images, five queries

The [manifest](data/detection/manifest.json) is the entry point. Its `images` entries contain unmodified image paths, dimensions, SHA-256 hashes, original COCO/Flickr URLs, download URLs, and the license records supplied by COCO. Its `queries` entries contain target categories and **dataset annotation boxes**, with original annotation IDs plus pixel and normalized coordinates.

| Query | COCO val2017 image ID | Target | COCO noncrowd annotation count |
|---|---:|---|---:|
| `banana-single` | 13004 | banana | 1 |
| `banana-few` | 79651 | banana | 2 |
| `banana-many` | 78959 | banana | 13 |
| `cats-pair` | 333772 | cat | 2 |
| `banana-absent` | 333772 | banana | 0 |

All 28 instance annotations for these four images are preserved unchanged in [coco-val2017-subset.json](data/detection/coco-val2017-subset.json), including segmentation, original `[x, y, width, height]` boxes, areas, category IDs, and crowd flags. This allows independent checking of the target-category filtering.

Counts mean **COCO annotation instances**. They do not establish exhaustive labeling of every visible object. The banana-plant example has overlap and occlusion; its annotation count should not be treated as a verified literal count of all visible bananas. The absent-target query means zero banana annotations in that image, not proof of an exhaustive negative label. These four purposively selected images are a smoke-test fixture, not a representative benchmark.

## Source and attribution

Images and annotations come from the [COCO 2017 validation release](https://cocodataset.org/#download). The original archive member was retrieved using HTTPS byte ranges from the [COCO S3 annotation archive](https://s3.amazonaws.com/images.cocodataset.org/annotations/annotations_trainval2017.zip). Its size, SHA-256, CRC32, and archive metadata are recorded in the manifest. The four JPEGs were downloaded unchanged from the same COCO S3 bucket.

COCO assigns all four source images license ID 4, [Creative Commons Attribution 2.0](https://creativecommons.org/licenses/by/2.0/). Original per-image license records and Flickr source URLs are retained. COCO's image metadata does not supply photographer names; none have been invented. The image bytes have not been resized, cropped, or annotated. The annotation source is COCO; any future visual overlays should be labeled as COCO annotations.

## How to use this preparation

Inspect the images and JSON locally; no key or API connection is needed:

```python
import json
from pathlib import Path

root = Path("data/detection")  # run from the repository root
fixtures = json.loads((root / "manifest.json").read_text())
for query in fixtures["queries"]:
    print(query["id"], query["target"], query["annotation_count"])
```

For a future OpenRouter counting experiment, use an Extractions `estimate` field for numeric estimation, or a fixed Decisions `choice` question over count options for count classification. These are distinct request schemas and neither returns object boxes through the Liquid adapter. Send only the image and task instructions in the route's supported image envelope; keep annotation IDs, boxes, and counts out of every model request. There are no ready-made fixture model outputs to replay here.

If actual model boxes later become available, match predictions to target annotations one-to-one at IoU ≥ 0.5, maximizing the number of valid matches. Report matched instances (TP), unmatched predictions (FP), and unmatched annotations (FN); derive precision and recall separately from count error. For the zero-annotation query, recall is undefined and should be `null`, while predicted boxes are false positives. This tiny, single-threshold check would not be COCO AP.

The manifest intentionally keeps `predictions` empty, each `model_result` null, and evaluation status `not_run`. Future records should retain exact requests, raw responses, requested/resolved model IDs, timestamps, per-call wall-clock latency, and image hashes before adding any scores.
