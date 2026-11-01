"""Persistent newline-JSON PaddleOCR 3.x worker; launch in Paddle's own venv."""
import base64
import json
import sys
import contextlib

import cv2
import numpy as np
from paddleocr import PaddleOCR

with contextlib.redirect_stdout(sys.stderr):
    ocr = PaddleOCR(
        lang="korean", ocr_version="PP-OCRv5", device="cpu",
        use_doc_orientation_classify=False, use_doc_unwarping=False,
        use_textline_orientation=False,
    )
print(json.dumps({"ready": True}), flush=True)


def normalize(results, original_size, input_size):
    ow, oh = original_size
    iw, ih = input_size
    sx, sy = ow / iw, oh / ih
    lines = []
    for result in results or []:
        data = getattr(result, "json", result)
        if callable(data):
            data = data()
        if isinstance(data, dict) and "res" in data:
            data = data["res"]
        if not isinstance(data, dict):
            continue
        texts = data.get("rec_texts")
        scores = data.get("rec_scores")
        polygons = data.get("rec_polys", data.get("dt_polys"))
        if texts is None or scores is None or polygons is None:
            continue
        for text, score, poly in zip(texts, scores, polygons):
            if not str(text).strip():
                continue
            points = [[max(0, min(ow, round(float(x)*sx))),
                       max(0, min(oh, round(float(y)*sy)))]
                      for x, y in np.asarray(poly).reshape(-1, 2)]
            if len(points) >= 4:
                lines.append({"id": f"T{len(lines)+1}", "text": str(text),
                              "score": round(float(score), 4), "polygon": points,
                              "coordinate_space": "oriented_original_pixels"})
    return lines


for raw in sys.stdin:
    try:
        item = json.loads(raw)
        encoded = np.frombuffer(base64.b64decode(item["image_b64"]), np.uint8)
        bgr = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        with contextlib.redirect_stdout(sys.stderr):
            lines = normalize(ocr.predict(rgb), item["original_size"], item["input_size"])
        print(json.dumps({"lines": lines}, ensure_ascii=False), flush=True)
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False), flush=True)
