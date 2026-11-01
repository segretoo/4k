"""Replay stored 34-image detections through the current fragment renderer.

No VLM/OCR inference runs here. The report labels inference timings as historical.
Keep the input manifest, photographs, and generated artifacts outside Git.
"""
import argparse
from collections import Counter
import copy
import html
import json
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ml" / "gpu_server"))
from masking import render_mask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected", type=int, default=34)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    runs = [r for r in manifest["runs"] if r["condition"].endswith("ocr_first")]
    counts = Counter(r["condition"] for r in runs)
    if len(counts) != 2 or any(count != args.expected for count in counts.values()):
        raise SystemExit(f"Expected two full {args.expected}-image sets, found {dict(counts)}")
    args.out.mkdir(parents=True, exist_ok=True)
    results, cards = [], []
    for index, run in enumerate(runs, 1):
        source_path = args.manifest.parent.parent / run["source_file"].replace("\\", "/")
        with Image.open(source_path) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
        started = time.perf_counter()
        composite = image.copy()  # simulate client compositing, never send this through an API
        fragment_dir = args.out / "fragments" / f"{index:03}"
        fragment_dir.mkdir(parents=True, exist_ok=True)
        for item_index, original_item in enumerate(run["risk_items"]):
            item = copy.deepcopy(original_item)
            location = item["location_in_image"]
            points = location.get("polygon")
            if not points:
                x1, y1, x2, y2 = location["bbox"]
                points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            xs, ys = zip(*points)
            left, top = max(0, min(xs) - 28), max(0, min(ys) - 28)
            right, bottom = min(image.width, max(xs) + 29), min(image.height, max(ys) + 29)
            crop = image.crop((left, top, right, bottom))
            location["polygon"] = [[x - left, y - top] for x, y in points]
            patch, alpha = render_mask(crop, [item], layer_only=True)
            expected, _ = render_mask(crop, [item])
            reconstructed = Image.composite(patch, crop, alpha)
            delta = np.abs(np.asarray(expected).astype(int) - np.asarray(reconstructed).astype(int))
            if delta.max() > 1:
                raise AssertionError(f"Fragment compositing differs: {run['image']}")
            composite.paste(patch, (left, top), alpha)
            patch.save(fragment_dir / f"{item_index:03}_patch.png")
            alpha.save(fragment_dir / f"{item_index:03}_alpha.png")
        elapsed = time.perf_counter() - started
        original = image.copy()
        original.thumbnail((1600, 1600))
        composite.thumbnail((1600, 1600))
        original.save(args.out / f"{index:03}_source.jpg", quality=92)
        composite.save(args.out / f"{index:03}_masked.jpg", quality=92)
        result = {"image": run["image"], "condition": run["condition"],
                  "region_count": len(run["risk_items"]), "render_and_regression_seconds": round(elapsed, 3),
                  "new_ocr_or_vlm_run": False, "fragment_pixel_test_passed": True}
        results.append(result)
        texts = " · ".join(str(item.get("text") or "판독 불확실") for item in run["risk_items"])
        cards.append(f'<article><h2>{index}. {html.escape(run["image"])} / {run["condition"]}</h2>'
                     f'<p>{len(run["risk_items"])}영역 · 렌더+픽셀검사 {elapsed:.3f}초 · {html.escape(texts)}</p>'
                     f'<div><figure><img loading="lazy" src="{index:03}_source.jpg"><figcaption>원본</figcaption></figure>'
                     f'<figure><img loading="lazy" src="{index:03}_masked.jpg"><figcaption>조각을 클라이언트 방식으로 합성</figcaption></figure></div></article>')
    summary = {"scope": "Stored OCR/VLM polygons, new masking/alpha regression only",
               "source_count_per_condition": dict(counts), "new_ocr_or_vlm_run": False,
               "all_fragment_pixel_tests_passed": True, "runs": results}
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    body = ('<!doctype html><meta charset="utf-8"><title>34장 마스킹 조각 재검증</title>'
            '<style>body{font:16px system-ui;max-width:1500px;margin:auto;padding:24px;background:#f1f4f8}'
            'article{background:white;padding:20px;margin:20px 0;border-radius:12px}article div{display:flex;gap:10px}'
            'figure{margin:0;flex:1;min-width:0}img{width:100%;max-height:900px;object-fit:contain}figcaption{text-align:center}</style>'
            '<h1>34장 전체 × 1280/2200 OCR-first 마스킹 조각 재검증</h1>'
            '<p>저장된 검출 결과로 새 마스킹 코드를 실행했습니다. 이번 실행은 OCR/VLM 재추론이나 위험도 정확도 측정이 아닙니다. '
            '두 조건 모두 34장을 처리하고, 각 조각을 합성한 픽셀이 단일 렌더 결과와 일치하는지 확인했습니다.</p>'
            '<p>검정 박스 대신 주변 평균색, 2px 확장, sigma 8 경계. 아래 시간에는 이미지 재렌더·인코딩·픽셀 검사가 포함됩니다. '
            '기존 OCR/VLM 처리시간은 별도 벤치마크 보고서의 값입니다.</p>' + "".join(cards))
    (args.out / "report.html").write_text(body, encoding="utf-8")
    print(json.dumps({"conditions": dict(counts), "runs": len(results), "fragment_pixel_tests": "passed",
                      "report": str(args.out / "report.html")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
