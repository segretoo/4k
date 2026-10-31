# 34-image pipeline evaluation (2026-10-31)

The visual reference labels were manually reviewed by the agent for 34 images: 32 positive scenes and 2 negative scenes. The set contains 15 images from the GPU server and 19 Drive images; generated contact-sheet material was excluded. Metrics below are scene-level, not character error rate or polygon IoU.

## Full-set comparison: OCR-first

| VLM long edge | Positive scenes found | Valid JSON | Average end-to-end | Mean input tokens | Mean / peak allocated VRAM | Peak reserved VRAM |
|---|---:|---:|---:|---:|---:|---:|
| 1280px | 29/32 (90.6%) | 33/34 | 26.20s | 2,626 | 9.24 / 9.47 GiB | 10.88 GiB |
| 2200px | 30/32 (93.8%) | 34/34 | 26.65s | 4,620 | 9.83 / 10.05 GiB | 13.12 GiB |

The 2200px configuration is the default because it found one more positive scene and avoided the one truncated JSON response seen at 1280px. Mean inference time differed by 0.45s. The lower edge reduced mean input tokens by about 43% and peak reserved VRAM by 2.24 GiB, but one more positive scene was missed.

## Six-image subset: VLM-first

| VLM long edge | Scene result | Valid JSON | Average end-to-end | Mean input tokens | Peak reserved VRAM |
|---|---:|---:|---:|---:|---:|
| 1280px | 6/6 positive scenes returned | 6/6 | 31.77s | 4,274 | 11.48 GiB |
| 2200px | 6/6 positive scenes returned | 6/6 | 33.76s | 7,606 | 12.20 GiB |

These are six positive examples only. They are not the full-set recall result and do not establish a 100% accuracy claim. Candidate count and location quality varied between the two sizes; 2200px returned only one candidate for `10.jpg` where the 1280px run returned six.

## Errors and limits

- At 2200px OCR-first, two small bench labels (`04.jpg`, `06.jpg`) were missed. Raising image edge did not fix them.
- At 1280px, an additional restaurant sign was missed and one output for another restaurant sign was truncated at the 768-token response limit.
- Both sizes treated a small OCR fragment in `image.png` as a location sign; only two negative scenes were available, so false-positive rates are not generalizable.
- OCR-first took 26.20s and 26.65s on average. OCR averaged 6.85s, VLM averaged 19.10s and 19.55s, masking averaged about 0.06s. Masking is not the throughput bottleneck.
- One BF16 inference process reached 13.12 GiB peak reserved VRAM. Two simultaneous BF16 processes, multi-request GPU throughput, NF4 quality, and exhaustive character error rate were not measured.
- The comparison used 2200px OCR in each condition. The 1280/2200 setting changes VLM image size; it does not change the OCR input size.

## Decision

Default to PP-OCRv5 at 2200px → Qwen3.5-4B BF16 OCR-first risk review → OpenCV surrounding-mean fill with 2px dilation and sigma 8 edge feather. Keep one model process on the L4 and serialize inference. Use 1280px only as an explicitly lower-cost profile after product owners accept the measured recall and JSON tradeoff. Add an explicit human-review state for empty, malformed, or rejected detection output.

Per-image OCR/mask/time artifacts and the full rendered gallery are stored outside Git because they include real evaluation images. The working report is `qwen35_vision_ground_truth_report.md`; the image-by-image CSV/HTML/gallery are in the same private `outputs/followup` folder.
