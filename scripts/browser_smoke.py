"""Opt-in end-to-end check against a running local CPU API in GPU_MOCK mode.

Install playwright separately. Use a synthetic fixture only; writes output outside Git.
"""
import argparse
import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--browser", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    photo = Path(__file__).resolve().parents[1] / "data" / "demo" / "uc2_demo.jpg"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=str(args.browser), headless=True)
        page = browser.new_page(viewport={"width": 450, "height": 950}, accept_downloads=True)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url + "/uc2")
        for checkbox in page.get_by_role("checkbox").all():
            checkbox.check()
        page.get_by_role("button", name="동의하고 시작하기", exact=True).click()
        page.locator('input[type="file"]').set_input_files(photo)
        page.locator("textarea").fill("오늘도 8시 40분에 등원 완료 #하늘이")
        with page.expect_response("**/api/uc2/check") as response:
            page.get_by_role("button", name="진단하기", exact=True).click()
        checked = response.value.json()
        assert checked["regions"]
        page.get_by_role("button", name="가리고 수정하기", exact=True).click()
        with page.expect_download() as download, page.expect_response("**/api/uc2/mask") as response:
            page.get_by_role("button", name="가린 사진 저장하기", exact=True).click()
        payload = response.value.json()
        assert payload["fragments"] and "image_base64" not in payload
        assert payload["rescan_passed"]
        saved = args.out / "browser_composite.jpg"
        download.value.save_as(saved)
        page.get_by_text("재검사 통과", exact=True).wait_for()
        page.screenshot(path=str(args.out / "browser_result.png"), full_page=True)
        expected = Image.open(photo).convert("RGB")
        for fragment in payload["fragments"]:
            patch = Image.open(io.BytesIO(base64.b64decode(fragment["patch_base64"]))).convert("RGB")
            alpha = Image.open(io.BytesIO(base64.b64decode(fragment["alpha_base64"]))).convert("L")
            left, top, _, _ = fragment["crop_box_original_pixels"]
            expected.paste(patch, (left, top), alpha)
        actual = Image.open(saved).convert("RGB")
        assert actual.size == expected.size
        difference = np.abs(np.asarray(actual).astype(float) - np.asarray(expected).astype(float))
        assert difference.mean() < 3, f"Browser alpha compositing differs: {difference.mean()}"
        assert not errors, errors
        result = {"check_http": 200, "mask_http": 200, "region_count": len(checked["regions"]),
                  "fragment_count": len(payload["fragments"]), "download_size": list(actual.size),
                  "mean_pixel_error_after_jpeg": round(float(difference.mean()), 4),
                  "browser_errors": errors, "mode": "GPU_MOCK with synthetic fixture"}
        (args.out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        browser.close()


if __name__ == "__main__":
    main()
