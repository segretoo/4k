# NCP deployment, 2026-11-01

The product has been installed on the user's private NCP hosts. Source is in `/home1/ncloud/4k` on both hosts. Original test images and model caches are outside this folder and are preserved.

| Component | Host | Runtime | Service |
|---|---|---|---|
| Frontend + CPU API | `10.1.1.30:8000` | `/home1/ncloud/4k/backend/.venv/bin/python`, Python 3.12 | `kkokkok-cpu.service`, one worker, concurrency limit 8 |
| Vision API | `10.1.2.30:8080` | Existing `/home1/ncloud/torch-env/bin/python`, Torch 2.15.0+cu132, Transformers 5.22.1 | `kkokkok-gpu.service`, one worker |
| Paddle sidecar | GPU host CPU | Existing `/home1/ncloud/paddle-ocr-kit/.venv/bin/python`, Paddle/PaddleOCR 3.2.0 | Child of the vision service |

Both services are registered with systemd and restart on failure. Their private `.env` files are mode 600. A randomly generated internal API key is shared only by the two hosts. The existing Torch environment has no pip; optional HTTP evaluation dependencies were installed with the server's existing uv, without changing Torch.

Observed startup checks: CPU frontend HTTP 200, `/api/status` reports `gpu_mock=false` and `gpu_ok=true`, GPU `/healthz` reports `ready=true`. Warm model memory before requests was 8,892 MiB as reported by nvidia-smi. This is not inference peak memory or proof that two instances fit.

Windows-created tar archives carried restrictive directory modes and Windows metadata. `scripts/package_release.py` now packages committed source and the built frontend with portable 755 directories and 644 files. The server installer is `scripts/install_service.py`; it uses an existing Python environment and does not create a second model worker.

## Operations

```bash
sudo systemctl status kkokkok-cpu     # CPU host
sudo systemctl status kkokkok-gpu     # GPU host
sudo journalctl -u kkokkok-gpu -n 30 --no-pager
```

The full real-API matrix runs as `kkokkok-evaluation.service` on the GPU host. Its private evidence directory is `/home1/ncloud/4k/evaluation/20261101`. It checks 34 distinct originals per condition, excludes only the approved generated `contact.jpg` contact sheet, warms up separately, and restores 2200px OCR-first after finishing. Each condition saves check/mask JSON, OCR strings, fragments, model-stage times, token counts, and VRAM peaks. Progress and final success must be read from `matrix.json`; starting the service does not mean all tests passed.

The API remains a prototype without account login. The latest branch adds a signed HttpOnly browser session and scopes UC1 uploads/jobs to that session. It also adds a CPU-side FIFO GPU queue with one running call, at most four waiting calls globally, and at most one waiting call per browser. UC1 batches retry queue admission; UC2 returns HTTP 429 when the bounded line is full. The browser session ID stays in the CPU gateway and is not sent to the GPU. Configure a private `SESSION_SECRET` (32+ random characters) before deploying this commit and enable `SESSION_COOKIE_SECURE=true` once HTTPS is terminated at the API.

The CPU host has 7.8 GiB RAM and no swap. Do not move UC1's 1.5 GiB extracted-file allowance to tmpfs without limiting concurrent extraction and measuring peak memory. UC1 files use private session folders and are deleted at completion, cancellation, TTL, and restart; ordinary filesystem deletion is not secure erasure. UC2 image bytes remain in application memory and are not persisted by product routes.

All four real NCP API conditions now have 34/34 completed rows. Two interrupted rows (one HTTP 503 during masking and eleven connection refusals during a CPU service restart) were retried under their original profiles. Final gallery and evidence archive are in the user's local `outputs/followup/ncp_34_comparison_20261101` folder; actual test photos and OCR evidence remain outside Git. The latest API/frontend code was deployed to CPU at commit `0d4d7e2`; Edge verified frontend, session, check, mask-fragment, rescan, and download end to end with the live GPU. GitHub CI passed, and 18 CPU-host pytest cases passed. The replacement temporary SSH key expires at 2026-11-02 12:00 UTC.

The final comparison selected OCR-first at a 2200px VLM edge: 30/32 labeled positive scenes, 26.06s mean check, 33.16s mean check+mask time, 4,613 VLM input tokens, and 11.94 GiB peak reserved VRAM. The 1280px OCR-first option found 28/32, averaged 33.85s total, and used 10.93 GiB peak reserved VRAM. VLM-first averaged 47.62–48.65s total and found 24/32 or 19/32. OCR resolution stayed at 2200px in all conditions; OCR output was identical on all 34 photos, so no recognition loss was measured. Exact character error rate is unavailable without transcript ground truth. The visual comparison report marks residual OCR after masking in 7–8 images per condition; the product UI blocks export when that happens.

Keep the API on the authorized private network. The GPU benchmark routes may retain private artifacts; the product adapter does not persist original images or OCR JSON.
