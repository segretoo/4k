"""Run all 34 images through each live API profile, restoring the service afterwards.

Run on the GPU host as the service owner. Uses sudo only to restart its own API
service. The API must be private and have no other users during this benchmark.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, action="append", required=True)
    parser.add_argument("--url", default="http://10.1.1.30:8000")
    args = parser.parse_args()
    images = sorted({p.resolve() for folder in args.image_dir for p in folder.rglob("*")
                     if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and p.name != "contact.jpg"})
    if len(images) != 34:
        raise SystemExit(f"All 34 originals are required; found {len(images)}")
    env_path = args.root / "ml/gpu_server/.env"
    original = env_path.read_text(encoding="utf-8-sig")
    args.out.mkdir(parents=True, exist_ok=True)
    progress = {"status": "running", "source_count": len(images), "conditions": []}

    def save():
        (args.out / "matrix.json").write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")

    def restart(edge, order):
        filtered = [line for line in original.splitlines()
                    if not line.startswith(("MODEL_EDGE=", "PIPELINE_ORDER="))]
        filtered += [f"MODEL_EDGE={edge}", f"PIPELINE_ORDER={order}"]
        env_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")
        subprocess.run(["sudo", "-n", "systemctl", "restart", "kkokkok-gpu"], check=True)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            try:
                if httpx.get("http://127.0.0.1:8080/healthz", timeout=3).json().get("ready"):
                    return
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(2)
        raise RuntimeError("GPU API did not become ready")

    try:
        for edge, order in ((2200, "ocr_first"), (1280, "ocr_first"),
                            (1280, "vlm_first"), (2200, "vlm_first")):
            label = f"edge_{edge}_{order}"
            row = {"condition": label, "status": "running"}
            progress["conditions"].append(row)
            save()
            print(f"START {label}: all 34 images", flush=True)
            restart(edge, order)
            started = time.perf_counter()
            with images[0].open("rb") as image:
                response = httpx.post(args.url + "/api/uc2/check", files={"file": (images[0].name, image)},
                                      timeout=300)
            response.raise_for_status()
            row["warmup_seconds"] = round(time.perf_counter() - started, 3)
            command = [sys.executable, str(args.root / "scripts/evaluate_api.py"), "--url", args.url,
                       "--out", str(args.out / label), "--expected", "34"]
            for folder in args.image_dir:
                command += ["--image-dir", str(folder)]
            completed = subprocess.run(command, check=False)
            row["status"] = "completed" if completed.returncode == 0 else "failed"
            row["exit_code"] = completed.returncode
            save()
            print(f"END {label}: {row['status']}", flush=True)
        progress["status"] = "completed" if all(row["status"] == "completed" for row in progress["conditions"]) else "failed"
    except Exception as error:
        progress.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        # Always restore the measured production default and keep one warm model.
        try:
            restart(2200, "ocr_first")
            progress["restored_default"] = True
        finally:
            save()


if __name__ == "__main__":
    main()
