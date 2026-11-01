# Image privacy pipeline architecture

## Responsibilities

| Part | Host | Work | Image retention |
|---|---|---|---|
| Mobile/web client | User device | Select a photo, send it for screening, show detected regions, let the user toggle regions, composite the returned fragments, export the final JPEG | Keeps the original and final image locally; final canvas export drops EXIF/GPS |
| Product API | CPU server `10.1.1.30` | Request validation, EXIF orientation, resize to a 2200px long edge, caption/risk rules, fair GPU admission, user-facing API and static frontend | UC2 photo bytes stay in request memory; UC1 export files use an owner-scoped private temp directory with TTL and cleanup |
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

Install the FastAPI dependencies from `backend/requirements.txt`, build the web app, set `GPU_MOCK=false`, and configure `GPU_URL=http://10.1.2.30:8080`, `SESSION_SECRET` (32+ random characters), and the same `GPU_API_KEY` as the GPU service. Run one CPU API worker: UC1 jobs and the fair queue are held in process memory, so multiple workers would disagree about job state and fairness. The CPU gateway admits one GPU request at a time, keeps a FIFO waiting line capped at four requests, and allows at most one waiting request per browser. This prevents later requests from the same browser from jumping ahead of other users already waiting. The L4 endpoint has its own single inference slot and bounded queue. A full queue receives HTTP 429 and can be retried. Set Uvicorn `--limit-concurrency 8` on the 8 GiB CPU host to bound simultaneous uploads. UC1 uses owner-scoped temporary files; UC2 does not persist application files, although multipart uploads can spool to OS temporary files closed after reading.

### GPU host

Run `ml/gpu_server` in the existing CUDA/Torch environment that can load the cached `Qwen/Qwen3.5-4B` model. Keep `LOAD_4BIT=false` for the measured BF16 configuration, `PIPELINE_ORDER=ocr_first`, `MODEL_EDGE=2200`, `OCR_EDGE=2200`, and `MAX_WAITING=4`. PaddleOCR can run in a separate CPU sidecar process so its Paddle dependencies do not replace the Torch/CUDA environment. Use one Uvicorn worker. Configure a private API key and firewall port 8080 to allow only the CPU host.

The image routes used by the product are `/gpu/v1/health`, `/gpu/v1/screen-captions`, `/gpu/v1/analyze`, and `/gpu/v1/mask`. A fifth waiting request at either bounded queue receives HTTP 429; UC1 batch workers retry CPU admission without skipping photos, while the interactive UC2 flow can show a retry message.

## User identity and data lifecycle

The prototype issues a signed, HttpOnly browser session cookie and derives a random owner ID from it; callers cannot choose their own `user_id`. UC1 uploads, thumbnails, and jobs are scoped to that owner. This distinguishes browsers, but is not an account login: use the product's authenticated principal when one is available. UC2 screening is request/response and needs no persistent user folder: discard image buffers when the request finishes. The fair queue receives only the random owner ID inside the CPU API; that identity is not sent to the GPU. The model process remains warm; do not create a GPU instance per uploaded photo.

UC1 uploads are private temporary directories, removed when a job completes/fails, when cancelled, on service restart, or after the TTL. Use an OS-managed temporary filesystem with private permissions and monitor its capacity. A tmpfs mount reduces disk persistence but consumes the CPU host's 8 GiB RAM; do not enable it at the current 1.5 GiB extracted-upload limit without measuring peak concurrent extraction and memory headroom. UC2 is already memory-only at the application layer; OS multipart spooling and crash dumps/swap still need production host policy. Deletion from an ordinary disk filesystem is not a guarantee of forensic erasure.

The product-facing GPU adapter does not save source images or OCR results. The multipart parser may spool uploads to OS temporary files; the adapter closes them immediately after reading, and request buffers become reclaimable when processing finishes. A separate benchmark/debug route may retain small output artifacts under its configured TTL; disable or firewall that route in production. Never put image samples, `.env`, API keys, or OCR logs in Git.

## UC1: Instagram export and multi-post review

1. The CPU API accepts an Instagram export ZIP, validates archive paths/expanded size, reads only `posts_*.json` and the referenced photo members, normalizes each image, and writes a short-lived owner-scoped working set. The ZIP is removed after extraction; unrelated export folders are not parsed.
2. Before any vision inference, CPU rules scan each post caption and hashtags for possible name, age/class, school/affiliation, location, time/routine, and contact clues. The upload response includes the original post grouping, photo thumbnails, the extracted hashtags, and stable candidate IDs with clue type/source. This first pass does not occupy the GPU or send text to a hosted model.
3. The frontend lets the user add/remove photos and toggle caption candidates. Directly added text must occur in that post's caption; it is not treated as a model-confirmed image finding.
4. `POST /api/uc1/jobs` carries selected photo IDs plus the per-post candidate-ID selection and manually added caption clues. The CPU job worker calls the existing OCR/VLM pipeline only for selected photos, one image at a time through the fair GPU queue. Caption-derived entities that the user switched off are omitted from the final risk aggregation; photo-derived findings remain independently visible.
5. The job response keeps the aggregate risk/cleanup fields used by the existing UI and adds `post_results[]`, grouped by original post. Each post row has its timestamp, caption, hashtags, confirmed candidate IDs, and `photos[]`; each photo row has its own detector entities, geometry, risk level, and failure flag. This is the JSON array the result screen can expand and inspect.
6. The private upload folder, extracted photos, and enriched post JSON are deleted after success/failure/cancel/TTL. The JSON result is held only in the in-process job state until its TTL; durable database storage is not enabled.

## External access: direct data path with rendezvous signaling

The current CPU and GPU addresses are private VPC addresses. Do not expose the GPU API or its model port to the public internet. For an initial reliable public web launch, terminate HTTPS at an NCP load balancer/WAF or an outbound Cloudflare Tunnel to the CPU API; the browser talks to CPU, and CPU remains the only caller of GPU. This is the simplest operational choice, but HTTP traffic traverses that edge/tunnel.

If the requirement is that the external server only pairs sessions and never carries image/API payloads, add a separate **signaling/rendezvous service** and a WebRTC DataChannel transport:

1. The browser and CPU agent each open outbound WSS connections to the rendezvous service. The user authenticates at the product API; the CPU agent authenticates with a device credential. A short-lived, single-use pairing token binds one browser session to one CPU session.
2. The rendezvous server exchanges only SDP/ICE connection metadata and the pairing state, with a short TTL and no photo, caption, OCR, or inference data.
3. Browser and CPU agent negotiate ICE using STUN. When the network permits, WebRTC selects a direct UDP path secured by DTLS/SCTP; the rendezvous server is then absent from the data path. The CPU agent bridges authenticated DataChannel calls to the local CPU API, which continues to use the private GPU API.
4. Some carrier-grade/symmetric NATs and enterprise firewalls cannot establish a direct peer path. A TURN server must relay traffic for those users, or the session must fail if the product forbids relayed payloads. Direct-only mode is therefore not universally reachable. Keep TURN as an explicit, metered fallback unless the no-relay requirement outweighs reachability.

The rendezvous option is a later network feature, not part of the current API process. Before implementation, measure direct-ICE success across mobile carriers and office networks, decide the TURN fallback policy, and add authenticated pairing, token expiry/replay protection, per-session byte/time limits, audit-safe logs, and disconnect cleanup. Never put the pairing token or user ID in GPU metadata.

## Evaluation-backed defaults and limitations

| Setting | Selected value | 34-image evidence |
|---|---|---|
| OCR/model order | OCR-first | 30/32 positive scenes at 2200px; 28/32 at 1280px |
| OCR/model image edge | 2200px | 26.06s mean check; 4,613 mean input tokens; 11.94 GiB peak reserved; 33/34 VLM JSON parses |
| OCR/model image edge (lower-memory option) | 1280px | 26.89s mean check; 2,619 mean input tokens; 10.93 GiB peak reserved; 32/34 VLM JSON parses |
| VLM-first | Not selected | Full 34-image tests: 40.72s/41.19s mean check; 24/32 and 19/32 positive scenes by size |
| Mask | mean surrounding RGB + 2px dilation + sigma 8 | OCR rescan found residual characters in 7/34–8/34 images; product export blocks those cases |

2200px missed two small bench labels (`04.jpg`, `06.jpg`). OCR stays at 2200px in all four tests, and OCR output was identical across the four profiles; OCR recognition loss/CER cannot be inferred because no exact transcription ground truth exists. VLM-first was slower and found fewer labeled scenes, so OCR-first 2200px is the default. See the private 34-image report and gallery; evaluation photos must not be committed.
