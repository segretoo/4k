"""Run every image through the real CPU→GPU check/mask API and save per-image evidence."""
import argparse
import base64
import json
from pathlib import Path
import time

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-dir", type=Path, action="append", required=True)
    parser.add_argument("--url", default="http://10.1.1.30:8000")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected", type=int, default=34)
    parser.add_argument("--exclude", action="append", default=["contact.jpg"],
                        help="Generated contact sheet excluded by the approved evaluation manifest")
    args = parser.parse_args()
    images = sorted({path.resolve() for folder in args.image_dir for path in folder.rglob("*")
                     if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
                     and path.name not in args.exclude})
    if len(images) != args.expected:
        raise SystemExit(f"Expected {args.expected} images, found {len(images)}; refusing partial-set evaluation")
    results = []
    with httpx.Client(base_url=args.url.rstrip("/"), timeout=300) as client:
        status = client.get("/api/status")
        status.raise_for_status()
        state = status.json()
        if state.get("gpu_mock") is not False or not state.get("gpu_ok"):
            raise SystemExit("Real GPU API is not ready; refusing to report mock data as model evidence")
        args.out.mkdir(parents=True, exist_ok=True)
        for index, path in enumerate(images, 1):
            folder = args.out / f"{index:03}"
            folder.mkdir(exist_ok=True)
            row = {"image": path.name, "index": index, "status": "failed"}
            try:
                started = time.perf_counter()
                with path.open("rb") as file:
                    response = client.post("/api/uc2/check", files={"file": (path.name, file)},
                                           data={"meta": json.dumps({"caption": ""})})
                response.raise_for_status()
                checked = response.json()
                row["check_seconds"] = round(time.perf_counter() - started, 3)
                row["region_count"] = len(checked["regions"])
                row["requires_review"] = checked["requires_review"]
                row["pipeline_metrics"] = checked.get("pipeline_metrics", {})
                (folder / "check.json").write_text(json.dumps(checked, ensure_ascii=False, indent=2), encoding="utf-8")
                if checked["regions"]:
                    mask_started = time.perf_counter()
                    with path.open("rb") as file:
                        response = client.post("/api/uc2/mask", files={"file": (path.name, file)},
                                               data={"meta": json.dumps({"regions": checked["regions"]})})
                    response.raise_for_status()
                    masked = response.json()
                    assert "image_base64" not in masked
                    assert len(masked["fragments"]) == len(checked["regions"])
                    row.update(mask_seconds=round(time.perf_counter() - mask_started, 3),
                               rescan_passed=masked["rescan_passed"], leaked=masked["leaked"],
                               mask_requires_review=masked["requires_review"])
                    for fragment_index, fragment in enumerate(masked["fragments"]):
                        for kind in ("patch", "alpha"):
                            (folder / f"{fragment_index:03}_{kind}.png").write_bytes(
                                base64.b64decode(fragment[f"{kind}_base64"]))
                        fragment.pop("patch_base64")
                        fragment.pop("alpha_base64")
                    (folder / "mask.json").write_text(json.dumps(masked, ensure_ascii=False, indent=2), encoding="utf-8")
                row.update(status="completed", total_seconds=round(time.perf_counter() - started, 3))
            except Exception as error:
                row["error"] = f"{type(error).__name__}: {error}"
            results.append(row)
            (args.out / "progress.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(row, ensure_ascii=False), flush=True)
    summary = {"expected": args.expected, "attempted": len(results),
               "completed": sum(row["status"] == "completed" for row in results),
               "mode": "real HTTP API; no recognition accuracy score without ground truth", "runs": results}
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if summary["completed"] != args.expected:
        raise SystemExit("One or more images failed; see summary.json")


if __name__ == "__main__":
    main()
