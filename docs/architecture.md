# Image privacy pipeline architecture

## Responsibilities

| Part | Host | Work | Image retention |
|---|---|---|---|
| Mobile/web client | User device | Select a photo, send it for screening, show detected regions, let the user toggle regions, composite the returned fragments, export the final JPEG | Keeps the original and final image locally; final canvas export drops EXIF/GPS |
| Product API | CPU server `10.1.1.30` | Request validation, EXIF orientation, resize to a 2200px long edge, caption/risk rules, per-request routing, user-facing API and static frontend | UC2 photo bytes stay in request memory; UC1 export files use a private temp directory with TTL and cleanup |
| Vision API | GPU server `10.1.2.30` / NVIDIA L4 24GB | PP-OCRv5 OCR, Qwen3.5-4B BF16 risk review, vector geometry, selected-region masking and OCR rescan | UC2 image/result held in memory; product routes do not write source images or OCR JSON to artifacts |

The browser talks only to the CPU API. The CPU API calls the GPU API on the private network using an API key. The GPU API is not exposed publicly. Keep one BF16 model process on the L4: the 34-image test reached 13.12 GiB peak reserved memory for one process, so two independent BF16 processes are not safe to assume on a 24 GiB card.

## UC2 request flow

1. The client sends a photo and caption to `POST /api/uc2/check`.
2. The CPU API rejects files over 20 MiB or 40 megapixels, applies EXIF orientation, converts to RGB/JPEG, and caps the long edge at 2200px. Its response includes `image_size`, box coordinates, OCR polygons, SVG paths, risk warnings, and `requires_review`.
3. The GPU API runs PP-OCRv5 at 2200px and passes the OCR candidate text plus image to Qwen3.5-4B BF16. The prompt asks Qwen to classify only person/place identifiers and return OCR IDs or narrow object regions. It does not ask the model to recognize faces.
4. The same VLM request also reviews the caption when one is supplied. It returns caption clues separately, and the server accepts only exact substrings of the supplied caption. The CPU API adds obvious caption cues (time with routine wording, age, school/class and area hashtags, name hashtags, phone and email) without another model call. It combines these with image clues and computes the risk level using deterministic rules. Empty or malformed image results carry review status.
5. The user chooses the regions to hide. The client posts only those selected region IDs/text/boxes/polygons to `POST /api/uc2/mask` along with the source photo.
6. The GPU API produces a separate crop patch and alpha mask for each polygon. The selected pixels are filled using the arithmetic mean RGB of nearby unmasked pixels; the polygon is expanded 2px and its edge is feathered with Gaussian sigma 8.
7. The GPU API OCR-rescans a transient in-memory composite for the selected text and returns only patches, alpha masks, and the result. It does not write that composite to disk.
8. The browser scales each fragment from server coordinate space to the locally decoded original image, composites each patch through its alpha mask, and creates a fresh JPEG. It blocks download if selected text is re-read. For unreadable signs, it offers download only after explicit visual confirmation by the user.

### Coordinate and image-size rules

- All region geometry is in EXIF-corrected, server-resized image pixels.
- `box` is `[x1, y1, x2, y2]`; `polygon` is an ordered list of `[x, y]`; `path` is an SVG path string in the same coordinate system.
- `CheckResponse.image_size` is `[width, height]` for that coordinate space. The client scales x and y independently when placing fragments on the original image.
- OCR polygons should cover the text itself. For a non-text sign whose text is unreadable, a narrow object box can be returned and is marked for human review.
- VLM-only whole-building boxes are rejected by the prompt/adapter. The box area must stay below 1% of the image; the model should split broad signage into text-line boxes.

## CPU/GPU deployment split

### CPU host

Install the FastAPI dependencies from `backend/requirements.txt`, build the web app, set `GPU_MOCK=false`, and configure `GPU_URL=http://10.1.2.30:8080` plus the same `GPU_API_KEY` as the GPU service. Run one CPU API worker: UC1 jobs are held in process memory, so multiple workers would disagree about job state. GPU calls are serialized by the client lock and GPU semaphore. Set Uvicorn `--limit-concurrency 8` on the 8 GiB CPU host to bound simultaneous uploads. UC1 uses temporary files; UC2 does not persist application files, although multipart uploads can spool to OS temporary files closed after reading.

### GPU host

Run `ml/gpu_server` in the existing CUDA/Torch environment that can load the cached `Qwen/Qwen3.5-4B` model. Keep `LOAD_4BIT=false` for the measured BF16 configuration, `PIPELINE_ORDER=ocr_first`, `MODEL_EDGE=2200`, `OCR_EDGE=2200`, and `MAX_WAITING=4`. PaddleOCR can run in a separate CPU sidecar process so its Paddle dependencies do not replace the Torch/CUDA environment. Use one Uvicorn worker. Configure a private API key and firewall port 8080 to allow only the CPU host.

The image routes used by the product are `/gpu/v1/health`, `/gpu/v1/screen-captions`, `/gpu/v1/analyze`, and `/gpu/v1/mask`. A fifth waiting request receives HTTP 429; the CPU layer returns a user-facing temporary-unavailable response if the internal GPU queue is unavailable.

## User identity and data lifecycle

The current prototype has no login/session provider. Do not accept a client-supplied `user_id` as authentication. In production, authenticate the client at the CPU API (for example, a signed session/JWT), derive the user ID from the verified principal, and scope any saved UC1 upload/job to that identity. UC2 screening is request/response and needs no persistent user folder: use a random request ID for tracing, do not send the user ID to the GPU, and discard image buffers when the request finishes. The model process remains warm; do not create a GPU instance per uploaded photo.

The product-facing GPU adapter does not save source images or OCR results. The multipart parser may spool uploads to OS temporary files; the adapter closes them immediately after reading, and request buffers become reclaimable when processing finishes. A separate benchmark/debug route may retain small output artifacts under its configured TTL; disable or firewall that route in production. Never put image samples, `.env`, API keys, or OCR logs in Git.

## Evaluation-backed defaults and limitations

| Setting | Selected value | 34-image evidence |
|---|---|---|
| OCR/model order | OCR-first | 30/32 positive scenes for 2200px; 34/34 valid JSON |
| OCR/model image edge | 2200px | 26.65s average; mean 4,620 input tokens; peak reserved 13.12 GiB |
| OCR/model image edge (lower-cost option) | 1280px | 29/32 positive scenes; 33/34 valid JSON; mean 2,626 tokens; average time 26.20s |
| VLM-first | Not selected as default | Tested on six positive samples only, not the full 34; 31.77s/33.76s average by size |
| Mask | mean surrounding RGB + 2px dilation + sigma 8 | 34-image result bundle contains per-image OCR, masks, and elapsed-time comparisons |

2200px missed two small bench labels (`04.jpg`, `06.jpg`). A higher resolution did not fix them. The 6/6 VLM-first result is a six-image sample, not a 100% full-dataset score. See the full 34-image report and gallery generated during evaluation; the report is outside this repository because real evaluation photos must not be committed.
