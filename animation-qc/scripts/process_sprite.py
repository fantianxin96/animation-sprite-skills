#!/usr/bin/env python3
"""Process sprite sheets into aligned transparent animation assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def load_anchor_profile(path: str | None) -> dict:
    if not path:
        return {}
    profile_path = Path(path).expanduser()
    return json.loads(profile_path.read_text())


def anchor_profile_data(profile: dict | None) -> dict:
    if not profile:
        return {}
    return profile.get("anchor_profile", profile)


def uses_baseline_anchor(profile: dict | None) -> bool:
    data = anchor_profile_data(profile)
    return data.get("baseline_anchor") != "none"


def parse_frames(value: str | None) -> list[int] | None:
    if not value:
        return None
    return [int(part.strip()) for part in value.split(",") if part.strip() != ""]


def parse_durations(value: str | None) -> list[int] | None:
    if not value:
        return None
    return [int(part.strip()) for part in value.split(",") if part.strip() != ""]


def infer_grid(width: int, height: int, cols: int | None, rows: int | None) -> tuple[int, int]:
    if cols and rows:
        return cols, rows
    candidates: list[tuple[int, int]] = []
    for c in range(1, 13):
        for r in range(1, 9):
            if width % c == 0 and height % r == 0 and width // c == height // r:
                candidates.append((c, r))
    if candidates:
        preferred = [(3, 2), (4, 2), (2, 3), (6, 1), (5, 2), (4, 3), (6, 2)]
        for grid in preferred:
            if grid in candidates:
                return grid
        return max(candidates, key=lambda item: item[0] * item[1])
    raise SystemExit(
        f"Cannot infer a square-cell grid from {width}x{height}; pass --cols and --rows."
    )


def green_mask(arr: np.ndarray) -> np.ndarray:
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    return (g > 145) & (r < 170) & (b < 170) & (a > 0)


def dynamic_green_mask(arr: np.ndarray) -> np.ndarray:
    """Detect green-screen pixels relative to edge/corner samples.

    Image models often output near-green instead of exact #00FF00. The static
    threshold is kept as a fallback, but this dynamic mask prevents green
    residue from making the whole frame look like foreground.
    """
    static = green_mask(arr)
    rgb = arr[..., :3].astype(np.int16)
    alpha = arr[..., 3] > 0
    h, w = arr.shape[:2]
    band = max(4, min(h, w) // 32)
    edge = np.zeros((h, w), dtype=bool)
    edge[:band, :] = True
    edge[-band:, :] = True
    edge[:, :band] = True
    edge[:, -band:] = True
    edge &= alpha
    edge_pixels = rgb[edge]
    if len(edge_pixels) < 16:
        return static
    bg = np.median(edge_pixels, axis=0)
    # Only use dynamic masking when the sampled background is green-ish.
    if not (bg[1] > bg[0] + 35 and bg[1] > bg[2] + 35 and bg[1] > 120):
        return static
    color_distance = np.linalg.norm(rgb - bg, axis=2)
    greenish = (rgb[..., 1] > rgb[..., 0] + 25) & (rgb[..., 1] > rgb[..., 2] + 25)
    return alpha & greenish & (color_distance < 85)


def edge_connected_mask(mask: np.ndarray) -> np.ndarray:
    """Return the part of mask connected to the image border."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    stack: list[tuple[int, int]] = []
    for x in range(w):
        if mask[0, x]:
            stack.append((0, x))
        if mask[h - 1, x]:
            stack.append((h - 1, x))
    for y in range(h):
        if mask[y, 0]:
            stack.append((y, 0))
        if mask[y, w - 1]:
            stack.append((y, w - 1))
    while stack:
        y, x = stack.pop()
        if seen[y, x] or not mask[y, x]:
            continue
        seen[y, x] = True
        if y > 0:
            stack.append((y - 1, x))
        if y < h - 1:
            stack.append((y + 1, x))
        if x > 0:
            stack.append((y, x - 1))
        if x < w - 1:
            stack.append((y, x + 1))
    return seen


def clean_foreground_mask(arr: np.ndarray) -> np.ndarray:
    fg = (arr[..., 3] > 0) & (~dynamic_green_mask(arr))
    # Many generated sprite sheets include a 1-2px white grid/border. If left
    # in the mask, it makes every frame look like a full-cell subject.
    edge_fg = edge_connected_mask(fg)
    if edge_fg.sum() / fg.size < 0.12:
        fg = fg & (~edge_fg)
    return fg


def foreground_mask(img: Image.Image, profile: dict | None = None) -> np.ndarray:
    arr = np.array(img.convert("RGBA"))
    return clean_foreground_mask(arr)


def body_mask(img: Image.Image, profile: dict | None = None) -> np.ndarray:
    arr = np.array(img.convert("RGBA"))
    fg = clean_foreground_mask(arr)
    # Public default: use the visible character/object foreground. Exact
    # semantic body-part exclusion belongs to a later anchor-strategy layer or
    # a caller-provided anchor profile; do not bake in any product/IP color.
    return fg


def mask_confidence(img: Image.Image, profile: dict | None = None) -> dict:
    arr = np.array(img.convert("RGBA"))
    fg = foreground_mask(img, profile)
    body = body_mask(img, profile)
    green = dynamic_green_mask(arr)
    exact_green = (
        (arr[..., 0] == 0)
        & (arr[..., 1] == 255)
        & (arr[..., 2] == 0)
        & (arr[..., 3] > 0)
    )
    ys, xs = np.where(fg)
    if len(xs):
        fg_bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        fg_coverage = (
            ((fg_bbox[2] - fg_bbox[0] + 1) * (fg_bbox[3] - fg_bbox[1] + 1))
            / (img.width * img.height)
        )
    else:
        fg_bbox = [0, 0, 0, 0]
        fg_coverage = 0.0
    green_pixels = int(green.sum())
    exact_green_pixels = int(exact_green.sum())
    body_pixels = int(body.sum())
    fg_pixels = int(fg.sum())
    body_to_fg_ratio = body_pixels / fg_pixels if fg_pixels else 0.0
    exact_green_ratio = exact_green_pixels / green_pixels if green_pixels else 0.0
    green_coverage = green_pixels / (img.width * img.height)

    warnings = []
    if green_pixels and exact_green_ratio < 0.85:
        warnings.append("green screen not pure")
    if fg_pixels == 0:
        warnings.append("foreground mask confidence low")
    if green_coverage > 0.35 and fg_coverage > 0.92:
        warnings.append("foreground mask may include background residue")
    if body_pixels and body_to_fg_ratio < 0.18:
        warnings.append("body mask confidence low")

    confidence = "high"
    if warnings:
        confidence = "low" if len(warnings) > 1 else "medium"
    if profile and fg_pixels > 0 and body_pixels > 0:
        # With a profile we intentionally use a generic visible-body anchor.
        # Non-pure green remains a warning, but should not block alignment by itself.
        blocking = [
            warning
            for warning in warnings
            if warning
            not in {
                "green screen not pure",
                "body mask confidence low",
            }
        ]
        confidence = "high" if not blocking else "medium"
    return {
        "confidence": confidence,
        "warnings": warnings,
        "green_pixels": green_pixels,
        "exact_green_pixels": exact_green_pixels,
        "green_coverage": round(green_coverage, 4),
        "exact_green_ratio": round(exact_green_ratio, 4),
        "foreground_pixels": fg_pixels,
        "body_pixels": body_pixels,
        "body_to_foreground_ratio": round(body_to_fg_ratio, 4),
        "foreground_bbox": fg_bbox,
        "foreground_bbox_coverage": round(fg_coverage, 4),
    }


def anchors(img: Image.Image, profile: dict | None = None) -> dict:
    fg = foreground_mask(img, profile)
    body = body_mask(img, profile)
    ys, xs = np.where(fg)
    bys, bxs = np.where(body)
    if len(xs) == 0:
        return {
            "body_cx": 256.0,
            "body_cy": 256.0,
            "foot": 438,
            "bbox": [0, 0, 0, 0],
            "body_bbox": [0, 0, 0, 0],
            "foreground_pixels": 0,
            "body_pixels": 0,
        }

    arr = np.array(img.convert("RGBA"))
    dark = fg & (arr[..., 0] < 75) & (arr[..., 1] < 95) & (arr[..., 2] < 75)
    dys, _ = np.where(dark)
    lower_dark = dys[dys > img.height * 0.58]
    if profile and not uses_baseline_anchor(profile):
        foot = int(ys.max())
    else:
        foot = int(np.percentile(lower_dark, 99)) if len(lower_dark) > 8 else int(ys.max())

    has_body = len(bxs) > 20
    body_cx = float(np.median(bxs)) if has_body else float(np.median(xs))
    body_cy = float(np.median(bys)) if has_body else float(np.median(ys))
    return {
        "body_cx": body_cx,
        "body_cy": body_cy,
        "foot": foot,
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "body_bbox": (
            [int(bxs.min()), int(bys.min()), int(bxs.max()), int(bys.max())]
            if has_body
            else [0, 0, 0, 0]
        ),
        "foreground_pixels": int(len(xs)),
        "body_pixels": int(len(bxs)),
    }


def remove_green(img: Image.Image) -> Image.Image:
    arr = np.array(img.convert("RGBA"))
    gm = dynamic_green_mask(arr)
    arr[gm, 3] = 0
    near = (
        (arr[..., 1] > 125)
        & (arr[..., 0] < 185)
        & (arr[..., 2] < 185)
        & (arr[..., 3] > 0)
    )
    arr[near, 3] = 0
    pale_edge = (
        (arr[..., 0] > 230)
        & (arr[..., 1] > 230)
        & (arr[..., 2] > 220)
        & (arr[..., 3] > 0)
    )
    edge_residue = edge_connected_mask(pale_edge)
    arr[edge_residue, 3] = 0
    dark_edge = (
        (arr[..., 0] < 70)
        & (arr[..., 1] < 70)
        & (arr[..., 2] < 70)
        & (arr[..., 3] > 0)
    )
    dark_edge_residue = edge_connected_mask(dark_edge)
    if dark_edge_residue.sum() / dark_edge_residue.size < 0.035:
        arr[dark_edge_residue, 3] = 0
    alpha = arr[..., 3]
    transparent = alpha == 0
    near_transparent = np.zeros_like(transparent, dtype=bool)
    near_transparent[:-1, :] |= transparent[1:, :]
    near_transparent[1:, :] |= transparent[:-1, :]
    near_transparent[:, :-1] |= transparent[:, 1:]
    near_transparent[:, 1:] |= transparent[:, :-1]
    green_spill = (
        (arr[..., 1] > arr[..., 0] + 18)
        & (arr[..., 1] > arr[..., 2] + 18)
        & (arr[..., 3] > 0)
        & near_transparent
    )
    if np.any(green_spill):
        max_rb = np.maximum(arr[..., 0], arr[..., 2])
        arr[..., 1] = np.where(green_spill, max_rb, arr[..., 1])
        weak_spill = green_spill & (alpha < 230)
        arr[..., 3] = np.where(weak_spill, (alpha * 0.55).astype(np.uint8), alpha)
    return Image.fromarray(arr, "RGBA")


def remove_near_edge_rule_lines(
    img: Image.Image,
    margin: int = 32,
    min_coverage: float = 0.55,
) -> Image.Image:
    """Remove long straight divider residue near a frame edge.

    White grid lines can survive keying and then get shifted inward during
    alignment. A normal outer-border crop will miss them because they are no
    longer at x/y = 0 after the frame is moved.
    """
    arr = np.array(img.convert("RGBA"))
    h, w = arr.shape[:2]
    margin = max(0, min(margin, h // 3, w // 3))
    if margin <= 0:
        return Image.fromarray(arr, "RGBA")

    alpha = arr[..., 3] > 0
    rgb = arr[..., :3].astype(np.int16)
    brightness = rgb.mean(axis=2)
    channel_spread = rgb.max(axis=2) - rgb.min(axis=2)
    pale_neutral = alpha & (brightness > 165) & (channel_spread < 42)
    dark_line = alpha & (brightness < 80)
    green_line = (
        alpha
        & (arr[..., 1] > arr[..., 0] + 18)
        & (arr[..., 1] > arr[..., 2] + 18)
        & (arr[..., 1] > 100)
    )
    candidates = pale_neutral | green_line | dark_line

    for x in list(range(margin)) + list(range(max(margin, w - margin), w)):
        coverage = candidates[:, x].sum() / h
        if coverage >= min_coverage:
            x0 = max(0, x - 1)
            x1 = min(w, x + 2)
            arr[:, x0:x1, 3] = np.where(candidates[:, x0:x1], 0, arr[:, x0:x1, 3])

    for y in list(range(margin)) + list(range(max(margin, h - margin), h)):
        coverage = candidates[y, :].sum() / w
        if coverage >= min_coverage:
            y0 = max(0, y - 1)
            y1 = min(h, y + 2)
            arr[y0:y1, :, 3] = np.where(candidates[y0:y1, :], 0, arr[y0:y1, :, 3])

    return Image.fromarray(arr, "RGBA")


def edge_artifact_report(
    frames: list[Image.Image],
    border: int = 3,
    line_margin: int = 32,
    line_min_coverage: float = 0.55,
) -> dict:
    outer_issues: list[dict] = []
    near_line_issues: list[dict] = []
    for idx, frame in enumerate(frames):
        arr = np.array(frame.convert("RGBA"))
        checks = {
            "left": arr[:, :border],
            "right": arr[:, -border:],
            "top": arr[:border, :],
            "bottom": arr[-border:, :],
        }
        for side, sl in checks.items():
            alpha = sl[..., 3] > 0
            dark = (
                (sl[..., 0] < 70)
                & (sl[..., 1] < 70)
                & (sl[..., 2] < 70)
                & alpha
            )
            green = (
                (sl[..., 1] > sl[..., 0] + 18)
                & (sl[..., 1] > sl[..., 2] + 18)
                & alpha
            )
            opaque = int(alpha.sum())
            dark_count = int(dark.sum())
            green_count = int(green.sum())
            if dark_count > 4 or green_count > 4:
                outer_issues.append(
                    {
                        "frame": idx,
                        "side": side,
                        "opaque_px": opaque,
                        "dark_px": dark_count,
                        "green_px": green_count,
                    }
                )
        alpha = arr[..., 3] > 0
        rgb = arr[..., :3].astype(np.int16)
        brightness = rgb.mean(axis=2)
        channel_spread = rgb.max(axis=2) - rgb.min(axis=2)
        pale_neutral = alpha & (brightness > 165) & (channel_spread < 42)
        h, w = alpha.shape
        margin = max(0, min(line_margin, h // 3, w // 3))
        for x in list(range(margin)) + list(range(max(margin, w - margin), w)):
            coverage = pale_neutral[:, x].sum() / h
            if coverage >= line_min_coverage:
                near_line_issues.append(
                    {
                        "frame": idx,
                        "side": "near_left" if x < margin else "near_right",
                        "type": "long_pale_divider_line",
                        "x": int(x),
                        "coverage": round(float(coverage), 3),
                    }
                )
        for y in list(range(margin)) + list(range(max(margin, h - margin), h)):
            coverage = pale_neutral[y, :].sum() / w
            if coverage >= line_min_coverage:
                near_line_issues.append(
                    {
                        "frame": idx,
                        "side": "near_top" if y < margin else "near_bottom",
                        "type": "long_pale_divider_line",
                        "y": int(y),
                        "coverage": round(float(coverage), 3),
                    }
                )
    issues = outer_issues + near_line_issues
    return {
        "status": "warning" if issues else "pass",
        "outer_border_clean": not outer_issues,
        "near_edge_long_line_clean": not near_line_issues,
        "border_px": border,
        "line_margin_px": line_margin,
        "outer_issues": outer_issues,
        "near_line_issues": near_line_issues,
        "issues": issues,
    }


def clear_frame_border(img: Image.Image, border: int) -> Image.Image:
    if border <= 0:
        return img
    arr = np.array(img.convert("RGBA"))
    border = min(border, arr.shape[0] // 2, arr.shape[1] // 2)
    if border <= 0:
        return Image.fromarray(arr, "RGBA")
    arr[:border, :, 3] = 0
    arr[-border:, :, 3] = 0
    arr[:, :border, 3] = 0
    arr[:, -border:, 3] = 0
    return Image.fromarray(arr, "RGBA")


def split_frames(img: Image.Image, cols: int, rows: int) -> list[Image.Image]:
    cell_w, cell_h = img.width // cols, img.height // rows
    frames = []
    for row in range(rows):
        for col in range(cols):
            frames.append(img.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)))
    return frames


def clamp_shift(value: int, limit: int) -> int:
    return max(-limit, min(limit, value))


def alpha_bbox(img: Image.Image) -> dict | None:
    arr = np.array(img.convert("RGBA"))
    mask = arr[..., 3] > 0
    return mask_bbox(img, mask)


def mask_bbox(img: Image.Image, mask: np.ndarray) -> dict | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    x1, y1, x2, y2 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    return {
        "bbox": [x1, y1, x2, y2],
        "center": [round((x1 + x2) / 2, 2), round((y1 + y2) / 2, 2)],
        "width": x2 - x1 + 1,
        "height": y2 - y1 + 1,
        "padding": {
            "top": y1,
            "bottom": img.height - y2 - 1,
            "left": x1,
            "right": img.width - x2 - 1,
        },
        "area_ratio": round(((x2 - x1 + 1) * (y2 - y1 + 1)) / (img.width * img.height), 4),
    }


def composition_audit(frames: list[Image.Image], profile: dict | None = None) -> dict:
    if not frames:
        return {
            "status": "warning",
            "warnings": ["composition_uncertain"],
            "suggested_position_strategy": "manual_review",
            "reason": "no frames provided",
        }
    cell_w, cell_h = frames[0].size
    cell_center = {"x": round(cell_w / 2, 2), "y": round(cell_h / 2, 2)}
    boxes = [mask_bbox(frame, foreground_mask(frame, profile)) for frame in frames]
    valid = [box for box in boxes if box]
    if not valid:
        return {
            "status": "warning",
            "cell_center": cell_center,
            "warnings": ["composition_uncertain"],
            "suggested_position_strategy": "manual_review",
            "reason": "no visible subject after background cleanup",
        }

    avg_cx = sum(box["center"][0] for box in valid) / len(valid)
    avg_cy = sum(box["center"][1] for box in valid) / len(valid)
    avg_width = sum(box["width"] for box in valid) / len(valid)
    avg_height = sum(box["height"] for box in valid) / len(valid)
    avg_area = sum(box["area_ratio"] for box in valid) / len(valid)
    avg_padding = {
        side: round(sum(box["padding"][side] for box in valid) / len(valid), 2)
        for side in ("top", "bottom", "left", "right")
    }
    offset_x = avg_cx - cell_w / 2
    offset_y = avg_cy - cell_h / 2
    warnings: list[str] = []
    threshold_x = cell_w * 0.1
    threshold_y = cell_h * 0.1
    if offset_y > threshold_y:
        warnings.append("overall_subject_low")
    elif offset_y < -threshold_y:
        warnings.append("overall_subject_high")
    if offset_x > threshold_x:
        warnings.append("overall_subject_right")
    elif offset_x < -threshold_x:
        warnings.append("overall_subject_left")

    vertical_gap = abs(avg_padding["top"] - avg_padding["bottom"])
    horizontal_gap = abs(avg_padding["left"] - avg_padding["right"])
    if vertical_gap > cell_h * 0.18 or horizontal_gap > cell_w * 0.18:
        warnings.append("unbalanced_padding")
    if avg_width < cell_w * 0.22 and avg_height < cell_h * 0.22:
        warnings.append("subject_too_small")
    if avg_width > cell_w * 0.88 or avg_height > cell_h * 0.88:
        warnings.append("subject_too_large")
    min_padding = {
        side: min(box["padding"][side] for box in valid)
        for side in ("top", "bottom", "left", "right")
    }
    crop_margin = max(2, round(min(cell_w, cell_h) * 0.025))
    if min_padding["top"] <= crop_margin:
        warnings.append("possible_crop_top")
    if min_padding["bottom"] <= crop_margin:
        warnings.append("possible_crop_bottom")
    if min_padding["left"] <= crop_margin or min_padding["right"] <= crop_margin:
        warnings.append("possible_crop_side")

    if not warnings:
        suggested = "none"
        status = "pass"
    elif any(warning.startswith("possible_crop") for warning in warnings):
        suggested = "manual_review"
        status = "warning"
    elif any(warning in warnings for warning in ("subject_too_small", "subject_too_large")):
        suggested = "manual_review"
        status = "warning"
    else:
        suggested = "global_recenter_suggested"
        status = "warning"

    return {
        "status": status,
        "cell_center": cell_center,
        "average_subject_center": {"x": round(avg_cx, 2), "y": round(avg_cy, 2)},
        "average_offset_from_cell_center": {"x": round(offset_x, 2), "y": round(offset_y, 2)},
        "average_subject_size": {"width": round(avg_width, 2), "height": round(avg_height, 2)},
        "average_area_ratio": round(avg_area, 4),
        "average_padding": avg_padding,
        "min_padding": min_padding,
        "warnings": list(dict.fromkeys(warnings)),
        "suggested_position_strategy": suggested,
        "suggested_global_shift": {
            "x": int(round(-offset_x)) if suggested == "global_recenter_suggested" else 0,
            "y": int(round(-offset_y)) if suggested == "global_recenter_suggested" else 0,
        },
        "note": "Composition audit only. No global recenter is applied in this P0 implementation.",
    }


def checker(size: tuple[int, int]) -> Image.Image:
    img = Image.new("RGBA", size, (246, 246, 246, 255))
    draw = ImageDraw.Draw(img)
    step = max(16, size[0] // 16)
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if (x // step + y // step) % 2:
                draw.rectangle((x, y, x + step - 1, y + step - 1), fill=(230, 230, 230, 255))
    return img


def save_sheet(frames: list[Image.Image], cols: int, rows: int, path: Path) -> None:
    w, h = frames[0].size
    sheet = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))
    for idx, frame in enumerate(frames):
        sheet.alpha_composite(frame, ((idx % cols) * w, (idx // cols) * h))
    sheet.save(path)


def save_audit(
    raw_frames: list[Image.Image],
    aligned_frames: list[Image.Image],
    raw_metrics: list[dict],
    aligned_metrics: list[dict],
    shifts: list[tuple[int, int]],
    target_cx: float,
    target_y: float,
    vertical_anchor_kind: str,
    cols: int,
    path: Path,
) -> None:
    w, h = raw_frames[0].size
    thumb = 256
    rows = int(np.ceil(len(raw_frames) / cols))
    contact = Image.new("RGB", (cols * thumb, rows * thumb * 2), "white")
    draw = ImageDraw.Draw(contact)
    scale_x = thumb / w
    scale_y = thumb / h

    for section, frames, metrics in (
        (0, raw_frames, raw_metrics),
        (rows, aligned_frames, aligned_metrics),
    ):
        for idx, frame in enumerate(frames):
            bg = checker(frame.size) if section else Image.new("RGBA", frame.size, "white")
            bg.alpha_composite(frame.convert("RGBA"))
            small = bg.resize((thumb, thumb), Image.Resampling.LANCZOS).convert("RGB")
            x = (idx % cols) * thumb
            y = (idx // cols + section) * thumb
            contact.paste(small, (x, y))
            draw.line((x + target_cx * scale_x, y, x + target_cx * scale_x, y + thumb), fill=(0, 80, 255), width=2)
            horizontal_color = (255, 0, 0) if vertical_anchor_kind == "contact_baseline" else (190, 0, 220)
            draw.line((x, y + target_y * scale_y, x + thumb, y + target_y * scale_y), fill=horizontal_color, width=2)
            if section == 0:
                vertical_value = metrics[idx]["foot"] if vertical_anchor_kind == "contact_baseline" else metrics[idx]["body_cy"]
                vertical_label = "foot" if vertical_anchor_kind == "contact_baseline" else "cy"
                label = f"raw f{idx} cx={metrics[idx]['body_cx']:.1f} {vertical_label}={vertical_value:.1f}"
            else:
                label = f"aligned f{idx} shift={shifts[idx]}"
            draw.text((x + 8, y + 8), label, fill=(0, 0, 0))
    contact.save(path)


def natural_durations(count: int, final_hold: int) -> list[int]:
    return natural_durations_for("once", count, final_hold)


def frame_roles(count: int, playback: str) -> list[dict]:
    if count <= 0:
        return []
    if playback == "loop":
        if count == 1:
            roles = ["loop_hold"]
        elif count == 2:
            roles = ["loop_start", "loop_return"]
        elif count == 3:
            roles = ["loop_start", "loop_peak", "loop_return"]
        else:
            roles = ["loop_start"]
            for idx in range(1, count - 1):
                if idx == count // 2:
                    roles.append("loop_peak")
                elif idx < count // 2:
                    roles.append("loop_motion")
                else:
                    roles.append("loop_return")
            roles.append("loop_end")
    elif count == 1:
        roles = ["end_hold"]
    elif count == 2:
        roles = ["start_hold", "end_hold"]
    elif count == 3:
        roles = ["start_hold", "key_pose", "end_hold"]
    elif count == 4:
        roles = ["start_hold", "motion_in", "key_pose", "end_hold"]
    elif count == 5:
        roles = ["start_hold", "anticipation", "key_pose", "recovery", "end_hold"]
    elif count == 6:
        roles = ["start_hold", "transition", "motion_in", "key_pose", "recovery", "end_hold"]
    elif count == 8:
        roles = [
            "start_hold",
            "anticipation",
            "motion_in",
            "motion_in",
            "key_pose",
            "recovery",
            "settle",
            "end_hold",
        ]
    else:
        roles = ["start_hold"]
        peak = max(1, count // 2)
        for idx in range(1, count - 1):
            if idx == peak:
                roles.append("key_pose")
            elif idx < peak:
                roles.append("motion_in")
            elif idx < count - 2:
                roles.append("recovery")
            else:
                roles.append("settle")
        roles.append("end_hold")
    return [{"frame": idx, "role": role} for idx, role in enumerate(roles)]


def natural_durations_for(playback: str, count: int, final_hold: int) -> list[int]:
    if count <= 0:
        return []
    if playback == "loop":
        if count == 1:
            return [220]
        if count == 2:
            return [210, 210]
        durations = [180] * count
        durations[0] = 200
        durations[count // 2] = 210
        durations[-1] = 190
        return durations
    if count == 1:
        return [final_hold]
    if count == 2:
        return [260, final_hold]
    durations = [160] * count
    durations[0] = 240
    if count >= 4:
        durations[1] = 140
        durations[count // 2] = 260
        durations[-2] = 160
    durations[-1] = final_hold
    return durations


def frame_difference_score(a: Image.Image, b: Image.Image) -> float:
    small_a = a.convert("RGBA").resize((96, 96), Image.Resampling.BILINEAR)
    small_b = b.convert("RGBA").resize((96, 96), Image.Resampling.BILINEAR)
    arr_a = np.array(small_a).astype(np.float32) / 255.0
    arr_b = np.array(small_b).astype(np.float32) / 255.0
    alpha_a = arr_a[..., 3:4]
    alpha_b = arr_b[..., 3:4]
    premult_a = np.concatenate([arr_a[..., :3] * alpha_a, alpha_a], axis=2)
    premult_b = np.concatenate([arr_b[..., :3] * alpha_b, alpha_b], axis=2)
    return float(np.mean(np.abs(premult_a - premult_b)))


def frame_distance_score(a: Image.Image, b: Image.Image) -> float:
    small_a = a.convert("RGBA").resize((96, 96), Image.Resampling.BILINEAR)
    small_b = b.convert("RGBA").resize((96, 96), Image.Resampling.BILINEAR)
    arr_a = np.array(small_a).astype(np.float32) / 255.0
    arr_b = np.array(small_b).astype(np.float32) / 255.0
    alpha_a = arr_a[..., 3:4]
    alpha_b = arr_b[..., 3:4]
    premult_a = np.concatenate([arr_a[..., :3] * alpha_a, alpha_a], axis=2)
    premult_b = np.concatenate([arr_b[..., :3] * alpha_b, alpha_b], axis=2)
    return float(np.mean(np.abs(premult_a - premult_b)))


def timing_review(
    frames: list[Image.Image],
    indices: list[int],
    playback: str,
    final_hold: int,
) -> dict:
    selected = [frames[idx] for idx in indices]
    count = len(selected)
    base = natural_durations_for(playback, count, final_hold)
    if count == 0:
        return {
            "method": "frame_difference_timing_v1",
            "recommended": {"durations_ms": [], "reason": "no frames selected"},
            "frame_roles": [],
            "adjacent_change_scores": [],
            "distance_from_first_scores": [],
            "notes": [],
        }
    if count == 1:
        role = "loop_hold" if playback == "loop" else "end_hold"
        return {
            "method": "frame_difference_timing_v1",
            "recommended": {"durations_ms": base, "reason": "single frame hold"},
            "frame_roles": [{"frame": indices[0], "role": role, "local_index": 0}],
            "adjacent_change_scores": [],
            "distance_from_first_scores": [0.0],
            "notes": ["Only one frame exists, so timing is a hold."],
        }

    adjacent = [frame_difference_score(selected[i], selected[i + 1]) for i in range(count - 1)]
    distance_from_first = [frame_distance_score(selected[0], frame) for frame in selected]
    max_adjacent = max(adjacent) if adjacent else 0.0
    max_distance = max(distance_from_first) if distance_from_first else 0.0
    peak_local = int(max(range(count), key=lambda idx: distance_from_first[idx])) if count else 0
    if playback == "once" and peak_local == 0 and count > 1:
        peak_local = count - 1

    durations = list(base)
    roles: list[dict] = []

    if playback == "loop":
        for i in range(count):
            incoming = adjacent[i - 1] if i > 0 else adjacent[-1]
            outgoing = adjacent[i] if i < count - 1 else adjacent[-1]
            local_change = max(incoming, outgoing)
            if i == 0:
                role = "loop_start"
            elif i == peak_local:
                role = "loop_peak"
            elif i == count - 1:
                role = "loop_return"
            else:
                role = "loop_motion"
            if max_adjacent and local_change > max_adjacent * 0.78:
                durations[i] = 210
            elif max_adjacent and local_change < max_adjacent * 0.35:
                durations[i] = 155
            else:
                durations[i] = 180
            roles.append({"frame": indices[i], "local_index": i, "role": role})
        if count > 2:
            durations[0] = max(durations[0], 190)
            durations[-1] = min(max(durations[-1], 170), 210)
    else:
        for i in range(count):
            if i == 0:
                role = "start_read"
                durations[i] = max(base[i], 220)
            elif i == peak_local:
                role = "peak_hold"
                durations[i] = max(base[i], 260)
            elif i == count - 1:
                role = "end_hold"
                durations[i] = final_hold
            else:
                incoming = adjacent[i - 1]
                if max_adjacent and incoming > max_adjacent * 0.72:
                    role = "big_change_breathe"
                    durations[i] = 180
                elif max_adjacent and incoming < max_adjacent * 0.35:
                    role = "small_transition"
                    durations[i] = 120
                else:
                    role = "transition"
                    durations[i] = 145
            roles.append({"frame": indices[i], "local_index": i, "role": role})
        if peak_local == count - 1:
            roles[-1]["role"] = "peak_end_hold"
            durations[-1] = final_hold
        elif 0 < peak_local < count - 1:
            durations[-1] = max(520, int(final_hold * 0.72))

    notes = [
        "Durations were derived from real frame differences, not only from frame count.",
        "Large visual changes are allowed more read time; small transition frames move faster.",
    ]
    if playback == "loop":
        notes.append("Loop timing avoids a long final hold so the last frame can return to the first.")
    else:
        notes.append("Once timing keeps the final or peak pose readable.")

    return {
        "method": "frame_difference_timing_v1",
        "playback": playback,
        "recommended": {
            "durations_ms": durations,
            "reason": "Frame-difference reviewer selected readable holds and faster transitions.",
        },
        "frame_roles": roles,
        "peak_frame": indices[peak_local],
        "peak_local_index": peak_local,
        "adjacent_change_scores": [round(score, 5) for score in adjacent],
        "distance_from_first_scores": [round(score, 5) for score in distance_from_first],
        "max_adjacent_change": round(max_adjacent, 5),
        "max_distance_from_first": round(max_distance, 5),
        "notes": notes,
    }


def scale_deltas(metrics: list[dict]) -> dict:
    widths = []
    heights = []
    for metric in metrics:
        bbox = metric.get("body_bbox") or [0, 0, 0, 0]
        if metric.get("body_pixels", 0) <= 20:
            continue
        widths.append(max(0, int(bbox[2]) - int(bbox[0]) + 1))
        heights.append(max(0, int(bbox[3]) - int(bbox[1]) + 1))
    if len(widths) < 2 or len(heights) < 2:
        return {"width_range": None, "height_range": None, "width_ratio": None, "height_ratio": None}
    min_w, max_w = min(widths), max(widths)
    min_h, max_h = min(heights), max(heights)
    return {
        "width_range": int(max_w - min_w),
        "height_range": int(max_h - min_h),
        "width_ratio": round(max_w / min_w, 3) if min_w else None,
        "height_ratio": round(max_h / min_h, 3) if min_h else None,
    }


def status_from_quality(
    aligned_cx_range: float,
    aligned_vertical_range: float,
    max_shift_x: int,
    max_shift_y: int,
    cell: tuple[int, int],
    scale_change: dict,
    warnings: list[str],
    failures: list[str],
    baseline_required: bool = True,
    allow_scale_change: bool = False,
) -> str:
    if aligned_cx_range > 12:
        failures.append(f"Aligned body center drift is {aligned_cx_range}px, above 12px.")
    if baseline_required and aligned_vertical_range > 6:
        failures.append(f"Aligned foot baseline drift is {aligned_vertical_range}px, above 6px.")
    if not baseline_required and aligned_vertical_range > 12:
        failures.append(f"Aligned visual center Y drift is {aligned_vertical_range}px, above 12px.")
    width_ratio = scale_change.get("width_ratio")
    height_ratio = scale_change.get("height_ratio")
    if failures:
        return "fail"
    if not allow_scale_change and width_ratio and width_ratio > 1.22:
        warnings.append(
            f"Character body width changes across frames: ratio {width_ratio}; this may be intended squash/stretch, but inspect before use."
        )
    if not allow_scale_change and height_ratio and height_ratio > 1.22:
        warnings.append(
            f"Character body height changes across frames: ratio {height_ratio}; this may be intended squash/stretch, but inspect before use."
        )
    if aligned_cx_range > 4:
        warnings.append(f"Aligned body center drift is {aligned_cx_range}px; inspect at product size.")
    if baseline_required and aligned_vertical_range > 2:
        warnings.append(f"Aligned foot baseline drift is {aligned_vertical_range}px; inspect at product size.")
    if not baseline_required and aligned_vertical_range > 4:
        warnings.append(f"Aligned visual center Y drift is {aligned_vertical_range}px; inspect at product size.")
    if max_shift_x > cell[0] * 0.14 or max_shift_y > cell[1] * 0.14:
        warnings.append("Large correction shifts may indicate source pose jumps or layout drift; QC cannot fully repair bad action continuity.")
    elif not allow_scale_change and width_ratio and width_ratio > 1.12:
        warnings.append(f"Character body width changes across frames: ratio {width_ratio}; inspect for scale inconsistency.")
    if not allow_scale_change and height_ratio and 1.12 < height_ratio <= 1.22:
        warnings.append(f"Character body height changes across frames: ratio {height_ratio}; inspect for scale inconsistency.")
    return "warning" if warnings else "pass"


def delivery_gate_for(
    status: str,
    alignment_applied: bool,
    align_mode: str,
    raw_cx_range: float,
    raw_vertical_range: float,
    aligned_cx_range: float,
    aligned_vertical_range: float,
    proposed_max_shift_x: int,
    proposed_max_shift_y: int,
    max_shift_x: int,
    max_shift_y: int,
    cell: tuple[int, int],
    composition: dict,
    scale_change: dict,
    warnings: list[str],
    baseline_required: bool = True,
    allow_scale_change: bool = False,
    vertical_anchor_kind: str = "contact_baseline",
) -> dict:
    reasons: list[str] = []
    blockers: list[str] = []
    cell_w, cell_h = cell
    proposed_large = proposed_max_shift_x > cell_w * 0.12 or proposed_max_shift_y > cell_h * 0.12
    applied_large = max_shift_x > cell_w * 0.16 or max_shift_y > cell_h * 0.16
    raw_large = raw_cx_range > 12 or raw_vertical_range > (6 if baseline_required else 12)
    aligned_unstable = aligned_cx_range > 12 or aligned_vertical_range > (6 if baseline_required else 12)
    composition_warnings = composition.get("warnings", [])
    crop_risk = any(str(warning).startswith("possible_crop") for warning in composition_warnings)
    width_ratio = scale_change.get("width_ratio")
    height_ratio = scale_change.get("height_ratio")
    scale_large = not allow_scale_change and (
        (width_ratio and width_ratio > 1.32) or (height_ratio and height_ratio > 1.32)
    )

    if status == "fail":
        blockers.append("qc_status_fail")
    if aligned_unstable:
        blockers.append("aligned_anchor_still_unstable")
    if not alignment_applied and raw_large and proposed_large:
        blockers.append("large_raw_drift_without_normalization")
    if align_mode == "audit_only" and raw_large:
        blockers.append("audit_only_large_drift_needs_anchor_policy_or_normalization")
    if crop_risk:
        reasons.append("composition_crop_risk")
    if scale_large:
        reasons.append("large_scale_or_pose_size_change")
    if applied_large:
        reasons.append("large_normalization_shift_inspect_for_pose_jump")
    if warnings:
        reasons.append("qc_warnings_present")

    if blockers:
        state = "blocked"
        action = "regenerate_or_run_suitable_per_frame_normalization"
    elif reasons:
        state = "needs_review"
        action = "inspect_audit_and_gif_before_delivery"
    else:
        state = "pass"
        action = "deliver_transparent_outputs"

    return {
        "state": state,
        "action": action,
        "blockers": blockers,
        "reasons": list(dict.fromkeys(reasons)),
        "summary": {
            "raw_body_cx_range": raw_cx_range,
            "raw_vertical_anchor_range": raw_vertical_range,
            "aligned_body_cx_range": aligned_cx_range,
            "aligned_vertical_anchor_range": aligned_vertical_range,
            "vertical_anchor_kind": vertical_anchor_kind,
            "proposed_max_shift": {"x": proposed_max_shift_x, "y": proposed_max_shift_y},
            "applied_max_shift": {"x": max_shift_x, "y": max_shift_y},
            "composition_warnings": composition_warnings,
            "scale_change": scale_change,
        },
    }


def timing_suggestions(playback: str, count: int, final_hold: int) -> dict:
    recommended = natural_durations_for(playback, count, final_hold)
    if playback == "loop":
        lively = [max(80, int(duration * 0.78)) for duration in recommended]
        soft = [int(duration * 1.28) for duration in recommended]
        return {
            "recommended": {
                "name": "自然循环",
                "use_for": "默认循环动效 / idle / loading",
                "durations_ms": recommended,
                "reason": "首尾不长停，便于自然接回第一帧。",
            },
            "lively": {
                "name": "轻快循环",
                "use_for": "轻快反馈 / 装饰动效",
                "durations_ms": lively,
                "reason": "整体更快，循环存在感更强。",
            },
            "soft": {
                "name": "柔和循环",
                "use_for": "治愈陪伴 / 低干扰待机",
                "durations_ms": soft,
                "reason": "整体更慢，循环更柔和。",
            },
        }
    lively = [max(80, int(duration * 0.72)) for duration in recommended]
    if lively:
        lively[-1] = max(360, int(final_hold * 0.58))
    soft = [int(duration * 1.28) for duration in recommended]
    if soft:
        soft[-1] = int(final_hold * 1.22)
    slow_cute = [max(260, int(duration * 2.15)) for duration in recommended]
    if len(slow_cute) >= 6:
        slow_cute = [
            max(slow_cute[0], 520),
            max(slow_cute[1], 360),
            max(slow_cute[2], 460),
            max(slow_cute[3], 680),
            max(slow_cute[4], 460),
            max(slow_cute[5], 1500),
            *slow_cute[6:],
        ]
    if slow_cute:
        slow_cute[-1] = max(slow_cute[-1], int(final_hold * 1.65))
    return {
        "recommended": {
            "name": "自然版",
            "use_for": "默认 UI 动效",
            "durations_ms": recommended,
            "reason": "起始稍停，关键姿势稍停，结束长停。",
        },
        "lively": {
            "name": "活泼版",
            "use_for": "轻快反馈 / 表情包",
            "durations_ms": lively,
            "reason": "整体更快，反馈更轻。",
        },
        "soft": {
            "name": "治愈版",
            "use_for": "治愈陪伴 / 情绪类动作",
            "durations_ms": soft,
            "reason": "停顿更长，观感更柔和。",
        },
        "slow_cute": {
            "name": "慢萌版",
            "use_for": "呆萌表演 / 小动物动作",
            "durations_ms": slow_cute,
            "reason": "每个姿势都有读秒，中段变化和最后笑点都留住。",
        },
    }


def rhythm_advice(
    playback: str,
    review: dict,
    suggestions: dict,
    selected_durations: list[int],
) -> dict:
    roles = review.get("frame_roles", [])
    adjacent = review.get("adjacent_change_scores", [])
    frame_count = review.get("frame_count") or len(roles)
    peak_local = review.get("peak_local_index")
    if peak_local is None and roles:
        peak_local = len(roles) - 1

    if playback == "loop":
        summary = "这版适合看循环是否顺，但不要在最后一帧长停。"
        focus = [
            "看首尾衔接是否有顿一下的感觉。",
            "如果循环存在感太强，整体放慢一点；如果像卡住，缩短最后一帧。",
        ]
        recommendation_key = "soft" if frame_count >= 4 else "recommended"
    else:
        summary = "这版动作读得出来，但角色表演类动图通常需要比 UI 点击反馈更慢一点。"
        focus = [
            "第一帧给一点读秒，让用户先看清角色状态。",
            "变化最大的中段需要多停一下，让摘帽动作被看见。",
            "最后定格可以停久一点，保留呆萌表情的笑点。",
        ]
        recommendation_key = "slow_cute"

    if adjacent:
        biggest_change_index = int(max(range(len(adjacent)), key=lambda idx: adjacent[idx]))
        focus.insert(
            1,
            f"第 {biggest_change_index + 1} 到第 {biggest_change_index + 2} 帧变化最大，后一帧不宜太快闪过。",
        )

    recommended = suggestions.get(recommendation_key) or suggestions.get("recommended") or {}
    selected_total = sum(selected_durations)
    recommended_total = sum(recommended.get("durations_ms", []))
    if recommended_total and selected_total and recommended_total > selected_total:
        delta = recommended_total - selected_total
        summary += f" 建议下一版整体慢约 {delta}ms。"

    return {
        "summary": summary,
        "focus_points": focus,
        "recommended_next": {
            "key": recommendation_key,
            "name": recommended.get("name", recommendation_key),
            "use_for": recommended.get("use_for"),
            "durations_ms": recommended.get("durations_ms"),
            "reason": recommended.get("reason"),
        },
        "selected_durations_ms": selected_durations,
        "selected_total_ms": selected_total,
        "recommended_total_ms": recommended_total,
        "user_facing": [
            "先看默认 GIF 的动作是否成立。",
            "如果觉得太快，优先试推荐的慢一点版本。",
            "如果觉得拖沓，再回到自然版或轻快版。",
        ],
    }


def save_gif(
    frames: list[Image.Image],
    indices: list[int],
    path: Path,
    durations: list[int],
    loop: int,
) -> None:
    gif_frames = []
    for idx in indices:
        bg = Image.new("RGBA", frames[idx].size, (252, 250, 246, 255))
        bg.alpha_composite(frames[idx])
        gif_frames.append(bg.convert("P", palette=Image.Palette.ADAPTIVE))
    gif_frames[0].save(path, save_all=True, append_images=gif_frames[1:], duration=durations, loop=loop, disposal=2)


def save_transparent_gif(
    frames: list[Image.Image],
    indices: list[int],
    path: Path,
    durations: list[int],
    loop: int,
) -> None:
    gif_frames = []
    transparency_index = 255
    for idx in indices:
        rgba = frames[idx].convert("RGBA")
        alpha = rgba.getchannel("A")
        paletted = rgba.convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        palette = paletted.getpalette() or []
        palette = palette[: 255 * 3]
        palette.extend([0, 255, 0] * (256 - len(palette) // 3))
        paletted.putpalette(palette[: 768])
        transparent_mask = alpha.point(lambda a: 255 if a <= 0 else 0)
        paletted.paste(transparency_index, transparent_mask)
        paletted.info["transparency"] = transparency_index
        gif_frames.append(paletted)
    gif_frames[0].save(
        path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=durations,
        loop=loop,
        disposal=2,
        transparency=transparency_index,
        background=transparency_index,
        optimize=False,
    )


def transparent_gif_export_report(path: Path, expected_transparency_index: int = 255) -> dict:
    img = Image.open(path)
    transparency = img.info.get("transparency")
    background = img.info.get("background")
    return {
        "transparent_index": transparency,
        "background_index": background,
        "transparent_index_ok": transparency == expected_transparency_index,
        "gif_background_index_ok": background == transparency,
        "expected_transparency_index": expected_transparency_index,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scene", default="qc")
    parser.add_argument("--action", default="action")
    parser.add_argument("--frames", help="Comma-separated preview frame indices, e.g. 0,1,2,4,5")
    parser.add_argument("--durations", help="Comma-separated GIF frame durations in ms, matching preview frames.")
    parser.add_argument("--playback", choices=["once", "loop"], default="once")
    parser.add_argument("--base", help="Optional reference sprite sheet or single frame used for anchor targets.")
    parser.add_argument("--anchor-profile", help="Optional character/object anchor_profile JSON from animation-sprite-workshop.")
    parser.add_argument("--cols", type=int)
    parser.add_argument("--rows", type=int)
    parser.add_argument(
        "--align-mode",
        choices=["auto", "audit_only", "light_align", "force_align"],
        default="auto",
        help="auto applies full high-confidence anchor shifts and flags review risks; audit_only never moves frames; light_align clamps shifts; force_align applies full shifts.",
    )
    parser.add_argument("--max-shift", type=int, default=20, help="Maximum automatic shift in px before alignment is skipped or limited.")
    parser.add_argument("--max-shift-ratio", type=float, default=0.05, help="Maximum automatic shift as a ratio of cell size.")
    parser.add_argument(
        "--position-mode",
        choices=["center", "source"],
        default="center",
        help="center places the anchor at the center of each cell; source preserves the first/base frame position.",
    )
    parser.add_argument("--target-cx", type=float, help="Override target body center x in each cell.")
    parser.add_argument("--target-foot", type=int, help="Override target foot baseline y in each cell.")
    parser.add_argument("--final-hold", type=int, default=900, help="Final GIF frame hold duration in ms.")
    parser.add_argument(
        "--gif-loop",
        type=int,
        default=None,
        help="GIF loop count. Defaults to 1 for once playback and 0 forever for loop playback.",
    )
    parser.add_argument(
        "--clear-border",
        type=int,
        default=4,
        help="Make the outer N pixels of every exported frame transparent to remove grid/divider edge residue.",
    )
    parser.add_argument(
        "--line-clean-margin",
        type=int,
        default=32,
        help="Scan this many pixels near each edge for long divider-line residue after keying/alignment.",
    )
    parser.add_argument(
        "--allow-scale-change",
        action="store_true",
        help="Allow intentional object/icon scale changes such as pop-in reward animations without blocking delivery.",
    )
    args = parser.parse_args()

    src = Path(args.input).expanduser()
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    anchor_profile = load_anchor_profile(args.anchor_profile)
    anchor_data = anchor_profile_data(anchor_profile)
    baseline_required = uses_baseline_anchor(anchor_profile)
    anchor_strategy = (
        f"profile:{anchor_data.get('center_anchor', 'body_visual_center')}"
        if anchor_profile
        else "generic_foreground"
    )

    img = Image.open(src).convert("RGBA")
    cols, rows = infer_grid(img.width, img.height, args.cols, args.rows)
    grid_remainder = {"width": img.width % cols, "height": img.height % rows}
    raw_frames = split_frames(img, cols, rows)
    cleaned = [
        remove_near_edge_rule_lines(
            clear_frame_border(remove_green(frame), args.clear_border),
            margin=args.line_clean_margin,
        )
        for frame in raw_frames
    ]

    if args.base:
        base_img = Image.open(Path(args.base).expanduser()).convert("RGBA")
        try:
            base_cols, base_rows = infer_grid(base_img.width, base_img.height, None, None)
            base_frame = split_frames(base_img, base_cols, base_rows)[0]
        except SystemExit:
            base_frame = base_img
        target = anchors(base_frame, anchor_profile)
    else:
        target = anchors(cleaned[0], anchor_profile)
    source_target_cx = target["body_cx"]
    source_target_cy = target["body_cy"]
    source_target_foot = target["foot"]
    cell_w, cell_h = raw_frames[0].size
    if args.target_cx is not None:
        target_cx = args.target_cx
    elif args.position_mode == "center":
        target_cx = cell_w / 2
    else:
        target_cx = source_target_cx

    if args.target_foot is not None:
        target_foot = args.target_foot
    else:
        target_foot = source_target_foot
    if baseline_required:
        target_y = float(target_foot)
        vertical_anchor_kind = "contact_baseline"
    elif args.position_mode == "center":
        target_y = cell_h / 2
        vertical_anchor_kind = "center_cross"
    else:
        target_y = source_target_cy
        vertical_anchor_kind = "center_cross"

    raw_metrics = [anchors(frame, anchor_profile) for frame in raw_frames]
    mask_confidences = [mask_confidence(frame, anchor_profile) for frame in raw_frames]
    confidence_levels = [entry["confidence"] for entry in mask_confidences]
    if "low" in confidence_levels:
        anchor_confidence = "low"
    elif "medium" in confidence_levels:
        anchor_confidence = "medium"
    else:
        anchor_confidence = "high"

    proposed_shifts: list[tuple[int, int]] = []
    for metric in raw_metrics:
        dx = int(round(target_cx - metric["body_cx"]))
        vertical_value = metric["foot"] if baseline_required else metric["body_cy"]
        dy = int(round(target_y - vertical_value))
        proposed_shifts.append((dx, dy))

    shift_limit = max(1, min(args.max_shift, int(round(min(cell_w, cell_h) * args.max_shift_ratio))))
    proposed_max_shift_x = max(abs(dx) for dx, _ in proposed_shifts) if proposed_shifts else 0
    proposed_max_shift_y = max(abs(dy) for _, dy in proposed_shifts) if proposed_shifts else 0
    proposed_exceeds_gate = proposed_max_shift_x > shift_limit or proposed_max_shift_y > shift_limit

    alignment_reasons = []
    alignment_warnings = []
    if grid_remainder["width"] or grid_remainder["height"]:
        alignment_warnings.append(
            f"sprite sheet size is not evenly divisible by grid: remainder {grid_remainder['width']}px x {grid_remainder['height']}px"
        )
    for idx, entry in enumerate(mask_confidences):
        for warning in entry["warnings"]:
            alignment_warnings.append(f"frame {idx}: {warning}")
    if proposed_exceeds_gate:
        alignment_warnings.append(
            f"proposed shift exceeds review threshold: max ({proposed_max_shift_x}px, {proposed_max_shift_y}px), threshold {shift_limit}px"
        )

    if args.align_mode == "audit_only":
        alignment_applied = False
        alignment_reasons.append("align_mode=audit_only; frames were not moved")
        shifts = [(0, 0) for _ in cleaned]
    elif args.align_mode == "force_align":
        alignment_applied = True
        alignment_reasons.append("align_mode=force_align; full proposed shifts were applied")
        shifts = proposed_shifts
    elif args.align_mode == "light_align":
        alignment_applied = any(dx or dy for dx, dy in proposed_shifts)
        if proposed_exceeds_gate:
            alignment_reasons.append("align_mode=light_align; shifts were clamped to the conservative gate")
        else:
            alignment_reasons.append("align_mode=light_align; proposed shifts were within the conservative gate")
        shifts = [(clamp_shift(dx, shift_limit), clamp_shift(dy, shift_limit)) for dx, dy in proposed_shifts]
    else:
        if anchor_confidence == "high":
            alignment_applied = any(dx or dy for dx, dy in proposed_shifts)
            if proposed_exceeds_gate:
                alignment_reasons.append(
                    "align_mode=auto; high confidence, so proposed shifts were applied and marked for review"
                )
            else:
                alignment_reasons.append("align_mode=auto; high confidence, so proposed shifts were applied")
            shifts = proposed_shifts
        else:
            alignment_applied = False
            if anchor_confidence != "high":
                alignment_reasons.append(
                    f"align_mode=auto; alignment skipped because anchor confidence is {anchor_confidence}"
                )
            shifts = [(0, 0) for _ in cleaned]

    aligned: list[Image.Image] = []
    for frame, (dx, dy) in zip(cleaned, shifts):
        canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        canvas.alpha_composite(frame, (dx, dy))
        canvas = clear_frame_border(canvas, args.clear_border)
        canvas = remove_near_edge_rule_lines(canvas, margin=args.line_clean_margin)
        aligned.append(canvas)

    aligned_metrics = [anchors(frame, anchor_profile) for frame in aligned]
    composition = composition_audit(aligned, anchor_profile)
    edge_artifacts = edge_artifact_report(aligned)
    preview_indices = parse_frames(args.frames) or list(range(len(aligned)))

    stem = f"{args.scene}-{args.action}"
    sheet_path = out / f"{stem}-aligned-transparent.png"
    audit_path = out / f"{stem}-audit.png"
    gif_path = out / f"{stem}-preview.gif"
    transparent_gif_path = out / f"{stem}-transparent.gif"
    timing_path = out / f"{stem}-timing.json"
    timing_review_path = out / f"{stem}-timing-review.json"
    timing_suggestions_path = out / f"{stem}-timing-suggestions.json"
    rhythm_advice_path = out / f"{stem}-rhythm-advice.json"
    report_path = out / f"{stem}-report.json"

    save_sheet(aligned, cols, rows, sheet_path)
    save_audit(raw_frames, aligned, raw_metrics, aligned_metrics, shifts, target_cx, target_y, vertical_anchor_kind, cols, audit_path)
    role_entries = frame_roles(len(preview_indices), args.playback)
    for role, frame_idx in zip(role_entries, preview_indices):
        role["frame"] = frame_idx
    suggestions = timing_suggestions(args.playback, len(preview_indices), args.final_hold)
    review = timing_review(aligned, preview_indices, args.playback, args.final_hold)
    selected_timing = "custom" if args.durations else "timing_review"
    output_frame_roles = review["frame_roles"]
    preview_durations = parse_durations(args.durations) or review["recommended"]["durations_ms"]
    if len(preview_durations) < len(preview_indices):
        preview_durations += [preview_durations[-1] if preview_durations else 170] * (
            len(preview_indices) - len(preview_durations)
        )
    preview_durations = preview_durations[: len(preview_indices)]
    advice = rhythm_advice(args.playback, review, suggestions, preview_durations)
    gif_loop = args.gif_loop if args.gif_loop is not None else (0 if args.playback == "loop" else 1)
    save_gif(aligned, preview_indices, gif_path, preview_durations, gif_loop)
    save_transparent_gif(aligned, preview_indices, transparent_gif_path, preview_durations, gif_loop)
    transparent_gif_export = transparent_gif_export_report(transparent_gif_path)

    raw_cx = [m["body_cx"] for m in raw_metrics]
    raw_cy = [m["body_cy"] for m in raw_metrics]
    raw_foot = [m["foot"] for m in raw_metrics]
    aligned_cx = [m["body_cx"] for m in aligned_metrics]
    aligned_cy = [m["body_cy"] for m in aligned_metrics]
    aligned_foot = [m["foot"] for m in aligned_metrics]
    raw_cx_range = round(max(raw_cx) - min(raw_cx), 2)
    raw_cy_range = round(max(raw_cy) - min(raw_cy), 2)
    raw_foot_range = int(max(raw_foot) - min(raw_foot))
    aligned_cx_range = round(max(aligned_cx) - min(aligned_cx), 2)
    aligned_cy_range = round(max(aligned_cy) - min(aligned_cy), 2)
    aligned_foot_range = int(max(aligned_foot) - min(aligned_foot))
    raw_vertical_anchor_range = raw_foot_range if baseline_required else raw_cy_range
    aligned_vertical_anchor_range = aligned_foot_range if baseline_required else aligned_cy_range
    max_shift_x = max(abs(dx) for dx, _ in shifts) if shifts else 0
    max_shift_y = max(abs(dy) for _, dy in shifts) if shifts else 0
    scale_change = scale_deltas(raw_metrics)
    warnings = list(dict.fromkeys(alignment_warnings))
    if edge_artifacts["status"] != "pass":
        warnings.append("edge artifact risk: outer border or near-edge divider-line residue remains")
    if not transparent_gif_export["transparent_index_ok"]:
        warnings.append("transparent GIF export risk: transparency index is not the expected transparent slot")
    if not transparent_gif_export["gif_background_index_ok"]:
        warnings.append("transparent GIF export risk: background index does not match the transparent index")
    failures = []
    if raw_cx_range > raw_frames[0].width * 0.08 or (
        raw_vertical_anchor_range > raw_frames[0].height * 0.08
    ):
        warnings.append(
            "Source frames have large anchor drift. Alignment can stabilize placement, but inspect action continuity; bad frames may need to be dropped or regenerated."
        )
    if max_shift_x > raw_frames[0].width * 0.18 or max_shift_y > raw_frames[0].height * 0.18:
        warnings.append(
            "Large correction shifts were applied. Check for cropping, pose discontinuity, or a sprite sheet that contains unrelated poses."
        )
    if alignment_applied:
        status = status_from_quality(
            aligned_cx_range,
            aligned_vertical_anchor_range,
            max_shift_x,
            max_shift_y,
            raw_frames[0].size,
            scale_change,
            warnings,
            failures,
            baseline_required,
            args.allow_scale_change,
        )
    else:
        status = "warning" if warnings or proposed_exceeds_gate or anchor_confidence != "high" else "pass"
        width_ratio = scale_change.get("width_ratio")
        height_ratio = scale_change.get("height_ratio")
        if not args.allow_scale_change and width_ratio and width_ratio > 1.12:
            warnings.append(
                f"Character body width changes across frames: ratio {width_ratio}; inspect as possible squash/stretch, not automatic fail."
            )
        if not args.allow_scale_change and height_ratio and height_ratio > 1.12:
            warnings.append(
                f"Character body height changes across frames: ratio {height_ratio}; inspect as possible squash/stretch, not automatic fail."
            )
        if warnings and status == "pass":
            status = "warning"

    if status == "fail":
        decision = "regenerate_or_drop_frames"
        alignment_recommendation = "regenerate"
    elif not alignment_applied:
        decision = "keep_raw_layout"
        alignment_recommendation = "keep_raw"
    elif args.align_mode == "force_align":
        decision = "inspect_force_aligned_output"
        alignment_recommendation = "force_align"
    else:
        decision = "inspect_light_aligned_output" if status == "warning" else "use_recommended_timing"
        alignment_recommendation = "light_align"
    recommendations = []
    if status == "pass":
        if alignment_applied:
            recommendations.append("Use the lightly aligned transparent sprite and timing_review timing by default.")
        else:
            recommendations.append("Use the raw-layout transparent sprite and timing_review timing by default.")
    elif status == "warning":
        recommendations.append("Inspect GIF preview and audit image before product use.")
        if not alignment_applied:
            recommendations.append("Automatic alignment was skipped or limited; keep raw layout unless visual drift is obvious.")
        recommendations.append("If pose discontinuity is visible, drop bad frames or regenerate with stronger continuity constraints.")
    else:
        recommendations.append("Do not treat QC output as fixed. Regenerate, drop bad frames, or manually repair the source animation.")

    delivery_gate = delivery_gate_for(
        status,
        alignment_applied,
        args.align_mode,
        raw_cx_range,
        raw_vertical_anchor_range,
        aligned_cx_range,
        aligned_vertical_anchor_range,
        proposed_max_shift_x,
        proposed_max_shift_y,
        max_shift_x,
        max_shift_y,
        raw_frames[0].size,
        composition,
        scale_change,
        warnings,
        baseline_required,
        args.allow_scale_change,
        vertical_anchor_kind,
    )
    if delivery_gate["state"] == "blocked":
        recommendations.insert(0, "Do not present this as a finished animation asset; use the audit/report to regenerate or normalize frames first.")
    elif delivery_gate["state"] == "needs_review":
        recommendations.insert(0, "Treat this as a review candidate, not an automatically approved delivery.")

    timing_payload = {
        "playback": args.playback,
        "loop": args.playback == "loop",
        "selected": selected_timing,
        "gif_loop": gif_loop,
        "frame_count": len(preview_indices),
        "frames": preview_indices,
        "durations_ms": preview_durations,
        "frame_roles": output_frame_roles,
        "notes": [
            "QC timing can improve playback rhythm, but it cannot repair broken action continuity or character deformation."
        ],
    }
    suggestions_payload = {
        "playback": args.playback,
        "loop": args.playback == "loop",
        "frame_count": len(preview_indices),
        "frames": preview_indices,
        "frame_roles": output_frame_roles,
        "suggestions": suggestions,
        "default_selection": "timing_review",
        "show_to_user_when": [
            "user asks for timing adjustment",
            "QC status is warning or fail",
            "preview feels too fast, too slow, mechanical, ghosty, or abrupt",
        ],
    }
    review_payload = {
        "playback": args.playback,
        "loop": args.playback == "loop",
        "frame_count": len(preview_indices),
        "frames": preview_indices,
        **review,
        "selected_for_output": selected_timing == "timing_review",
        "custom_durations_override": parse_durations(args.durations) if args.durations else None,
    }
    timing_path.write_text(json.dumps(timing_payload, ensure_ascii=False, indent=2))
    timing_review_path.write_text(json.dumps(review_payload, ensure_ascii=False, indent=2))
    timing_suggestions_path.write_text(json.dumps(suggestions_payload, ensure_ascii=False, indent=2))
    rhythm_advice_path.write_text(json.dumps(advice, ensure_ascii=False, indent=2))

    report = {
        "input": str(src),
        "scene": args.scene,
        "action": args.action,
        "status": status,
        "decision": decision,
        "recommendation": alignment_recommendation,
        "playback": args.playback,
        "align_mode": args.align_mode,
        "anchor_strategy": anchor_strategy,
        "anchor_profile": anchor_profile if anchor_profile else None,
        "baseline_required": baseline_required,
        "allow_scale_change": args.allow_scale_change,
        "vertical_anchor_kind": vertical_anchor_kind,
        "anchor_confidence": anchor_confidence,
        "mask_confidence": {
            "overall": anchor_confidence,
            "frames": mask_confidences,
        },
        "whether_frames_shifted": alignment_applied,
        "alignment_applied": alignment_applied,
        "alignment_reason": alignment_reasons,
        "alignment_gate": {
            "max_shift_px": args.max_shift,
            "max_shift_ratio": args.max_shift_ratio,
            "effective_limit_px": shift_limit,
            "proposed_exceeds_gate": proposed_exceeds_gate,
        },
        "composition": composition,
        "edge_artifacts": edge_artifacts,
        "gif_export": transparent_gif_export,
        "clear_border_px": args.clear_border,
        "line_clean_margin_px": args.line_clean_margin,
        "delivery_gate": delivery_gate,
        "grid": {"cols": cols, "rows": rows, "cell": raw_frames[0].size, "remainder": grid_remainder},
        "source_target": {
            "body_cx": round(source_target_cx, 2),
            "body_cy": round(source_target_cy, 2),
            "foot": source_target_foot,
        },
        "target": {
            "body_cx": round(target_cx, 2),
            "body_cy": round(target_y, 2) if not baseline_required else None,
            "foot": target_foot,
            "vertical_anchor_y": round(target_y, 2),
            "vertical_anchor_kind": vertical_anchor_kind,
            "position_mode": args.position_mode,
        },
        "raw": {
            "body_cx_range": raw_cx_range,
            "body_cy_range": raw_cy_range,
            "foot_range": raw_foot_range,
            "vertical_anchor_range": raw_vertical_anchor_range,
        },
        "aligned": {
            "body_cx_range": aligned_cx_range,
            "body_cy_range": aligned_cy_range,
            "foot_range": aligned_foot_range,
            "vertical_anchor_range": aligned_vertical_anchor_range,
        },
        "max_shift": {"x": max_shift_x, "y": max_shift_y},
        "proposed_max_shift": {"x": proposed_max_shift_x, "y": proposed_max_shift_y},
        "quality": {
            "raw_body_cx_range": raw_cx_range,
            "raw_body_cy_range": raw_cy_range,
            "raw_foot_range": raw_foot_range,
            "raw_vertical_anchor_range": raw_vertical_anchor_range,
            "aligned_body_cx_range": aligned_cx_range,
            "aligned_body_cy_range": aligned_cy_range,
            "aligned_foot_range": aligned_foot_range,
            "aligned_vertical_anchor_range": aligned_vertical_anchor_range,
            "max_shift_x": max_shift_x,
            "max_shift_y": max_shift_y,
            "proposed_max_shift_x": proposed_max_shift_x,
            "proposed_max_shift_y": proposed_max_shift_y,
            "scale_change": scale_change,
        },
        "proposed_shifts": proposed_shifts,
        "shifts": shifts,
        "preview_frames": preview_indices,
        "preview_durations": preview_durations,
        "frame_roles": output_frame_roles,
        "warnings": warnings,
        "failures": failures,
        "recommendations": recommendations,
        "timing": {
            "selected": selected_timing,
            "durations_ms": preview_durations,
            "timing_file": str(timing_path),
            "timing_review_file": str(timing_review_path),
            "suggestions_file": str(timing_suggestions_path),
            "rhythm_advice_file": str(rhythm_advice_path),
        },
        "outputs": {
            "sprite": str(sheet_path),
            "audit": str(audit_path),
            "gif": str(gif_path),
            "transparent_gif": str(transparent_gif_path),
            "timing": str(timing_path),
            "timing_review": str(timing_review_path),
            "timing_suggestions": str(timing_suggestions_path),
            "rhythm_advice": str(rhythm_advice_path),
            "report": str(report_path),
        },
        "note": "Inspect GIF first. QC can stabilize placement and timing, but it cannot fully repair bad source action continuity.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
