"""PaddleOCR 3.x adapter. Emits original-image pixel polygons and stable IDs."""
from __future__ import annotations

import base64
import json
import io
import numpy as np
import os
import shlex
import subprocess
import threading


class PaddleOCRBackend:
    def __init__(self, device: str = "cpu", lang: str = "korean", version: str = "PP-OCRv5"):
        from paddleocr import PaddleOCR

        self.engine = PaddleOCR(
            lang=lang,
            ocr_version=version,
            device=device,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    @staticmethod
    def _unwrap(result):
        if hasattr(result, "json"):
            result = result.json
        if callable(result):
            result = result()
        if isinstance(result, dict) and "res" in result:
            result = result["res"]
        return result if isinstance(result, dict) else {}

    def read(self, rgb: np.ndarray, original_size: tuple[int, int]) -> list[dict]:
        original_w, original_h = original_size
        input_h, input_w = rgb.shape[:2]
        sx, sy = original_w / input_w, original_h / input_h
        results = self.engine.predict(rgb)
        lines: list[dict] = []
        for result in results or []:
            data = self._unwrap(result)
            texts = data.get("rec_texts")
            scores = data.get("rec_scores")
            polys = data.get("rec_polys", data.get("dt_polys"))
            if texts is None or scores is None or polys is None:
                continue
            for text, score, poly in zip(texts, scores, polys):
                if not str(text).strip():
                    continue
                points = [[
                    max(0, min(original_w, round(float(x) * sx))),
                    max(0, min(original_h, round(float(y) * sy))),
                ] for x, y in np.asarray(poly).reshape(-1, 2)]
                if len(points) < 4:
                    continue
                lines.append({
                    "id": f"T{len(lines)+1}",
                    "text": str(text),
                    "score": round(float(score), 4),
                    "polygon": points,
                    "coordinate_space": "oriented_original_pixels",
                })
        return lines


class PaddleOCRProcessBackend:
    """Persistent OCR sidecar for keeping Paddle and CUDA/PyTorch environments apart."""
    def __init__(self, command: str):
        self.proc = subprocess.Popen(
            shlex.split(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=None, text=True, bufsize=1,
        )
        self.lock = threading.Lock()
        ready = self.proc.stdout.readline()
        try:
            ready_data = json.loads(ready)
        except (json.JSONDecodeError, AttributeError) as exc:
            self.proc.terminate()
            raise RuntimeError(f"OCR worker startup failed: {ready[:300]}") from exc
        if not ready_data.get("ready"):
            self.proc.terminate()
            raise RuntimeError("OCR worker did not become ready")

    def read(self, rgb: np.ndarray, original_size: tuple[int, int]) -> list[dict]:
        from PIL import Image
        buffer = io.BytesIO()
        Image.fromarray(rgb.astype(np.uint8), mode="RGB").save(buffer, format="JPEG", quality=95)
        payload = {"image_b64": base64.b64encode(buffer.getvalue()).decode("ascii"),
                   "original_size": list(original_size), "input_size": [rgb.shape[1], rgb.shape[0]]}
        with self.lock:
            if self.proc.poll() is not None:
                raise RuntimeError(f"OCR worker exited with code {self.proc.returncode}")
            self.proc.stdin.write(json.dumps(payload) + "\n")
            self.proc.stdin.flush()
            line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("OCR worker returned no response")
        result = json.loads(line)
        if "error" in result:
            raise RuntimeError(f"OCR worker error: {result['error']}")
        return result["lines"]

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def make_backend():
    command = os.getenv("OCR_WORKER_CMD", "").strip()
    if command:
        return PaddleOCRProcessBackend(command)
    return PaddleOCRBackend(
        device=os.getenv("OCR_DEVICE", "cpu"),
        lang=os.getenv("OCR_LANG", "korean"),
        version=os.getenv("OCR_VERSION", "PP-OCRv5"),
    )
