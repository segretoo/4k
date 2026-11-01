"""OpenCV 5 masking: surrounding-colour fill, softened edges, optional inpaint."""
from __future__ import annotations

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops


def _region_polygon(item):
    loc = item.get("location_in_image", {})
    polygon = loc.get("polygon")
    if polygon:
        return [(int(x), int(y)) for x, y in polygon]
    x1, y1, x2, y2 = loc["bbox"]
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def build_mask(size, items, dilation_px=2):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for item in items:
        draw.polygon(_region_polygon(item), fill=255)
    if dilation_px:
        mask = mask.filter(ImageFilter.MaxFilter(dilation_px * 2 + 1))
    return mask


def _render_mean_blur_opencv(source: Image.Image, items: list[dict], sigma: float,
                             dilation_px: int, layer_only: bool = False) -> tuple[Image.Image, Image.Image]:
    try:
        import cv2
    except ImportError as e:
        raise RuntimeError("Install opencv-python-headless==5.0.0.93 for mean_blur mode") from e

    rgb = np.asarray(source, dtype=np.uint8)
    height, width = rgb.shape[:2]
    core_u8 = np.asarray(build_mask(source.size, items, dilation_px), dtype=np.uint8)
    protected = core_u8 > 0
    out = rgb.copy()
    composite_alpha = np.zeros((height, width), dtype=np.float32)
    ring_radius = max(6, dilation_px * 3 + 2)
    ring_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (ring_radius * 2 + 1, ring_radius * 2 + 1)
    )
    feather_radius = max(1, int(math.ceil(sigma * 3))) if sigma else 0

    for item in items:
        pts = _region_polygon(item)
        xs, ys = zip(*pts)
        pad = max(ring_radius, feather_radius) + 2
        left, top = max(0, min(xs) - pad), max(0, min(ys) - pad)
        right, bottom = min(width, max(xs) + pad + 1), min(height, max(ys) + pad + 1)
        patch_rgb = rgb[top:bottom, left:right]
        protected_roi = protected[top:bottom, left:right]

        local_core = np.zeros((bottom - top, right - left), dtype=np.uint8)
        local_pts = np.asarray([(x - left, y - top) for x, y in pts], dtype=np.int32)
        cv2.fillPoly(local_core, [local_pts], 255)
        if dilation_px:
            # Match build_mask's square 2px dilation exactly so the returned
            # polygon and the pixels replaced by the renderer describe the same region.
            dilate_kernel = np.ones((dilation_px * 2 + 1, dilation_px * 2 + 1), dtype=np.uint8)
            local_core = cv2.dilate(local_core, dilate_kernel, iterations=1)

        outer = cv2.dilate(local_core, ring_kernel, iterations=1) > 0
        ring = outer & (local_core == 0) & ~protected_roi
        samples = patch_rgb[ring]
        if samples.size == 0:
            raise ValueError("cannot estimate surrounding color: no visible outer ring")
        # Use the arithmetic mean of nearby unmasked pixels, per the selected spec.
        fill_rgb = np.clip(np.rint(samples.astype(np.float32).mean(axis=0)), 0, 255).astype(np.uint8)

        if sigma:
            alpha = cv2.GaussianBlur(local_core, (0, 0), sigmaX=float(sigma), sigmaY=float(sigma))
            alpha = np.maximum(local_core, alpha).astype(np.float32) / 255.0
        else:
            alpha = local_core.astype(np.float32) / 255.0
        composite_alpha[top:bottom, left:right] = np.maximum(
            composite_alpha[top:bottom, left:right], alpha
        )
        alpha3 = alpha[..., None]
        blended = (np.broadcast_to(fill_rgb, patch_rgb.shape) if layer_only else
                   patch_rgb.astype(np.float32) * (1.0 - alpha3) + fill_rgb.astype(np.float32) * alpha3)
        out[top:bottom, left:right] = np.clip(np.rint(blended), 0, 255).astype(np.uint8)

    alpha_u8 = np.clip(np.rint(composite_alpha * 255.0), 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode="RGB"), Image.fromarray(alpha_u8, mode="L")


def render_mask(image: Image.Image, items: list[dict], mode="mean_blur", sigma=8,
                inpaint_radius=5, dilation_px=2, layer_only=False):
    source = image.convert("RGB")
    hard_mask = build_mask(source.size, items, dilation_px)
    if mode == "black":
        out = Image.new("RGB", source.size, (0, 0, 0))
        out.paste(source, mask=ImageChops.invert(hard_mask))
    elif mode == "blur":
        if not math.isfinite(sigma) or sigma <= 0:
            raise ValueError("sigma must be finite and > 0 for blur mode")
        # Blur the source locally through a tight, feathered text mask. This
        # preserves the sign/background texture outside glyph regions and avoids
        # inventing replacement pixels inside broad rectangles.
        blurred = source.filter(ImageFilter.GaussianBlur(sigma))
        edge = max(1.0, min(7.0, sigma / 2.0))
        alpha = ImageChops.lighter(hard_mask, hard_mask.filter(ImageFilter.GaussianBlur(edge)))
        out = Image.composite(blurred, source, alpha)
    elif mode == "mean_blur":
        if not math.isfinite(sigma) or sigma < 0:
            raise ValueError("sigma must be finite and >= 0")
        return _render_mean_blur_opencv(source, items, sigma, dilation_px, layer_only)
    elif mode == "inpaint":
        if not 1 <= inpaint_radius <= 20:
            raise ValueError("inpaint_radius must be in 1..20")
        try:
            import cv2
        except ImportError as e:
            raise RuntimeError("Install opencv-python-headless to use mode=inpaint") from e
        rgb = np.asarray(source)
        m = np.asarray(hard_mask)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        restored = cv2.inpaint(bgr, m, inpaint_radius, cv2.INPAINT_TELEA)
        out = Image.fromarray(cv2.cvtColor(restored, cv2.COLOR_BGR2RGB))
    else:
        raise ValueError("mode must be black, mean_blur, or inpaint")
    return out, hard_mask
