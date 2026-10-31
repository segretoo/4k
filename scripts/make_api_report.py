"""Build a private image/OCR/time report from evaluate_matrix/evaluate_api evidence."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import html
import json
import math
from pathlib import Path
import statistics

from PIL import Image, ImageOps

CONDITIONS = [f"edge_{edge}_{order}" for order in ("ocr_first", "vlm_first") for edge in (1280, 2200)]


def read_json(path, fallback=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return fallback


def norm(text):
    return "".join(c.lower() for c in text if c.isalnum())


def mean(values):
    return round(statistics.mean(values), 3) if values else None


def display(value):
    return "—" if value is None else str(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, action="append", required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    assets = args.out / "assets"
    assets.mkdir(exist_ok=True)
    ground_truth = read_json(args.ground_truth)
    labels = {item["image"]: item for item in ground_truth["images"]}
    sources = {p.name: p for folder in args.source_dir for p in folder.rglob("*")
               if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"} and p.name in labels}
    records, summaries, csv_rows = {}, [], []
    for condition in CONDITIONS:
        base = args.evidence / condition
        rows = read_json(base / "progress.json", [])
        records[condition] = {}
        for row in rows:
            folder = base / f"{row['index']:03}"
            checked = read_json(folder / "check.json", {})
            masked = read_json(folder / "mask.json", {})
            row = dict(row, checked=checked, masked=masked, folder=folder)
            records[condition][row["image"]] = row
            metrics = row.get("pipeline_metrics") or checked.get("pipeline_metrics", {})
            csv_rows.append({"condition": condition, "image": row["image"], "status": row["status"],
                             "check_seconds": row.get("check_seconds"), "mask_seconds": row.get("mask_seconds"),
                             "total_seconds": row.get("total_seconds"), "regions": row.get("region_count"),
                             "requires_review": row.get("requires_review"), "rescan_passed": row.get("rescan_passed"),
                             "leaked": " | ".join(row.get("leaked", [])),
                             "gpu_peak_allocated_bytes": metrics.get("gpu_peak_allocated_bytes"),
                             "gpu_peak_reserved_bytes": metrics.get("gpu_peak_reserved_bytes"),
                             "input_tokens": metrics.get("vlm_input_token_count"), "json_valid": metrics.get("json_valid"),
                             "ocr": " | ".join(t["text"] for t in checked.get("ocr_texts", [])),
                             "selected_text": " | ".join(r["text"] for r in checked.get("regions", [])),
                             "error": row.get("error", "")})
        values = list(records[condition].values())
        predicted = {r["image"] for r in values if any(region["type"] != "unreadable"
                     for region in r["checked"].get("regions", []))}
        positives = {name for name, label in labels.items() if label["positive"]}
        negatives = set(labels) - positives
        complete = [r for r in values if r["status"] == "completed"]
        peak = [r.get("pipeline_metrics", {}).get("gpu_peak_reserved_bytes") for r in values]
        total = sorted(r["total_seconds"] for r in complete)
        ocr_rows = [text for row in values for text in row["checked"].get("ocr_texts", [])]
        ocr_conf = [text.get("conf") for text in ocr_rows
                    if isinstance(text.get("conf"), (int, float))]
        summaries.append({"condition": condition, "attempted": len(values), "completed": len(complete),
            "positive_hits": len(predicted & positives), "positive_total": len(positives),
            "false_positive_scenes": len(predicted & negatives),
            "ocr_text_lines": len(ocr_rows),
            "mean_ocr_lines_per_image": mean([len(r["checked"].get("ocr_texts", [])) for r in values]),
            "mean_ocr_confidence": mean(ocr_conf),
            "mean_check_seconds": mean([r["check_seconds"] for r in values if "check_seconds" in r]),
            "mean_mask_seconds": mean([r["mask_seconds"] for r in values if "mask_seconds" in r]),
            "mean_total_seconds": mean(total),
            "p95_total_seconds": total[min(len(total)-1, math.ceil(len(total)*.95)-1)] if total else None,
            "peak_reserved_gib": round(max((p for p in peak if p is not None), default=0)/1024**3, 3),
            "valid_json_count": sum(r.get("pipeline_metrics", {}).get("json_valid") is True for r in values),
            "rescan_leak_images": [r["image"] for r in values if r.get("leaked")],
            "missed_positive_scenes": sorted(positives - predicted)})
    baseline = records.get("edge_2200_ocr_first", {})
    for summary_row in summaries:
        current = records[summary_row["condition"]]
        paired = sorted(set(baseline) & set(current))
        exact = sum({norm(t["text"]) for t in baseline[name]["checked"].get("ocr_texts", [])}
                    == {norm(t["text"]) for t in current[name]["checked"].get("ocr_texts", [])}
                    for name in paired)
        summary_row["ocr_output_exact_match_vs_2200_ocr_first"] = f"{exact}/{len(paired)}" if paired else "baseline"
    matrix = read_json(args.evidence / "matrix.json", {})
    complete = all(s["attempted"] == 34 and s["completed"] == 34 for s in summaries)
    summary = {"generated_kst": datetime.now(timezone(timedelta(hours=9))).isoformat(),
               "complete_four_by_34": complete, "matrix": matrix, "conditions": summaries}
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if csv_rows:
        with (args.out / "image_comparison.csv").open("w", newline="", encoding="utf-8-sig") as out:
            writer = csv.DictWriter(out, fieldnames=list(csv_rows[0]))
            writer.writeheader()
            writer.writerows(csv_rows)
    header = '<table><thead><tr><th>조건</th><th>API 완료</th><th>양성 장면 단서</th><th>음성 오탐</th><th>OCR 줄 수(평균/장)</th><th>평균 OCR 신뢰도</th><th>OCR 출력 일치(2200 OCR 우선 대비)</th><th>점검 평균</th><th>마스킹·재검사 평균</th><th>전체 평균 / p95</th><th>최대 예약 VRAM</th><th>유효 JSON</th></tr></thead><tbody>'
    for s in summaries:
        header += (f'<tr><td>{s["condition"]}</td><td>{s["completed"]}/34</td>'
                   f'<td>{s["positive_hits"]}/{s["positive_total"]}</td><td>{s["false_positive_scenes"]}</td>'
                   f'<td>{s["ocr_text_lines"]} ({display(s["mean_ocr_lines_per_image"])})</td>'
                   f'<td>{display(s["mean_ocr_confidence"])}</td><td>{s["ocr_output_exact_match_vs_2200_ocr_first"]}</td>'
                   f'<td>{display(s["mean_check_seconds"])}s</td><td>{display(s["mean_mask_seconds"])}s</td>'
                   f'<td>{display(s["mean_total_seconds"])} / {display(s["p95_total_seconds"])}s</td>'
                   f'<td>{s["peak_reserved_gib"]} GiB</td><td>{s["valid_json_count"]}/34</td></tr>')
    header += '</tbody></table>'
    cards = []
    for image_index, name in enumerate(sorted(labels), 1):
        label = labels[name]
        if name not in sources:
            cards.append(f'<article><h2>{html.escape(name)}: 원본 파일 없음</h2></article>')
            continue
        with Image.open(sources[name]) as opened:
            original = ImageOps.exif_transpose(opened).convert("RGB")
        preview = original.copy()
        preview.thumbnail((1400, 1400))
        preview.save(assets / f"{image_index:02}_original.jpg", quality=92)
        card = (f'<article><h2>{image_index}. {html.escape(name)}</h2><p>기존 비전 라벨: '
                f'{"위치·인물 단서 있음" if label["positive"] else "대상 단서 없음"} · '
                f'{html.escape(" / ".join(label.get("expected_targets", [])))}</p><div class="grid">'
                f'<figure><img loading="lazy" src="assets/{image_index:02}_original.jpg"><figcaption>원본</figcaption></figure>')
        for condition in CONDITIONS:
            row = records[condition].get(name)
            if not row:
                card += f'<section><h3>{condition}</h3><p>측정 대기</p></section>'
                continue
            checked, masked = row["checked"], row["masked"]
            has_fragments = bool(masked.get("fragments"))
            composition = original.copy()
            if has_fragments:
                width, height = checked["image_size"]
                sx, sy = original.width / width, original.height / height
                for idx, fragment in enumerate(masked["fragments"]):
                    left, top, right, bottom = fragment["crop_box_original_pixels"]
                    size = (max(1, round((right-left)*sx)), max(1, round((bottom-top)*sy)))
                    with Image.open(row["folder"] / f"{idx:03}_patch.png") as patch_image, Image.open(row["folder"] / f"{idx:03}_alpha.png") as alpha_image:
                        patch = patch_image.convert("RGB").resize(size, Image.Resampling.BILINEAR)
                        alpha = alpha_image.convert("L").resize(size, Image.Resampling.BILINEAR)
                        composition.paste(patch, (round(left*sx), round(top*sy)), alpha)
            composition.thumbnail((1400, 1400))
            filename = f"{image_index:02}_{condition}.jpg"
            composition.save(assets / filename, quality=92)
            status = "실패" if row["status"] != "completed" else "마스킹 조각 합성" if has_fragments else "후보 없음 · 원본 그대로"
            card += f'<section><h3>{condition}</h3><img loading="lazy" src="assets/{filename}"><p><b>{status}</b> · {row.get("region_count", 0)}곳</p>'
            card += f'<p>점검 {display(row.get("check_seconds"))}s · 마스킹/재검사 {display(row.get("mask_seconds"))}s · 전체 {display(row.get("total_seconds"))}s</p>'
            card += f'<p>검토 필요: {bool(row.get("requires_review"))} · 다시 읽힌 글자: {html.escape(" / ".join(row.get("leaked", []))) or "없음"}</p>'
            if row.get("error"):
                card += f'<p class="error">{html.escape(row["error"])}</p>'
            ocr = '\n'.join(f'{t["text"]} ({t.get("conf")})' for t in checked.get("ocr_texts", []))
            selected = '\n'.join(f'{r["type"]}: {r["text"]}' for r in checked.get("regions", []))
            card += f'<details><summary>OCR 원문 / 선택된 후보</summary><h4>OCR</h4><pre>{html.escape(ocr)}</pre><h4>마스킹 후보</h4><pre>{html.escape(selected)}</pre></details></section>'
        card += '</div></article>'
        cards.append(card)
    page = ('<!doctype html><meta charset="utf-8"><title>NCP 실제 API 34장 비교</title>'
            '<style>body{font:15px system-ui;max-width:1800px;margin:auto;padding:24px;background:#edf2f7;color:#172033}'
            'table{border-collapse:collapse;background:white;width:100%;font-size:13px}td,th{border:1px solid #cbd5e1;padding:10px}'
            'article{background:white;border-radius:14px;padding:20px;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:15px}'
            'figure{margin:0}img{width:100%;max-height:700px;object-fit:contain;background:#e2e8f0}pre{white-space:pre-wrap;overflow-wrap:anywhere}.error{color:#b91c1c}</style>'
            '<h1>NCP 실제 API: 34장 × 4조합</h1>'
            f'<p><b>{"전체 136건 완료" if complete else "측정 진행 중 — 부분 결과"}</b> · 생성 시각 {summary["generated_kst"]}</p>'
            '<p>CPU 10.1.1.30 → GPU 10.1.2.30의 실제 OCR·VLM·마스킹 API 결과입니다. 모든 조건에서 OCR 긴 변은 2200px이며 VLM 입력 크기와 순서를 비교합니다. '
            '평가에서는 반환된 후보를 모두 선택해 마스킹했습니다. 전체 시간에는 두 번의 이미지 업로드·OCR 재검사가 포함되고 모델 로딩/별도 워밍업은 제외합니다.</p>'
            '<p>장면 단위 단서 발견은 기존 에이전트 비전 라벨 32개 양성/2개 음성을 기준으로 했습니다. 한 사진의 모든 단서를 찾았다는 뜻은 아닙니다. '
            '전수 문자 전사 정답이 없어 전체 OCR 오타율(CER)은 계산하지 않았습니다. 아래 실제 OCR 원문과 마스킹을 확인할 수 있습니다.</p>'
            '<p>마스크는 주변 평균 RGB, 2px 확장, sigma 8입니다. 서버는 patch와 alpha만 응답하며 아래 이미지는 보고서 생성기가 클라이언트 방식으로 합성한 미리보기입니다. '
            'API 오류, 검토 필요, 재검사에서 다시 읽힌 글자는 통과와 구분해서 표시합니다.</p>' + header + ''.join(cards))
    (args.out / "report.html").write_text(page, encoding="utf-8")
    print(json.dumps({"report": str(args.out / "report.html"), "complete": complete,
                      "conditions": summaries}, ensure_ascii=False))


if __name__ == "__main__":
    main()
