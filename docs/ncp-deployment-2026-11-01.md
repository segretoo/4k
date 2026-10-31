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

The API remains a prototype: user authentication and ownership checks for persistent UC1 jobs still need a product identity provider. Keep the API on the authorized private network. The GPU benchmark routes may retain private artifacts; the product adapter does not persist original images or OCR JSON.
