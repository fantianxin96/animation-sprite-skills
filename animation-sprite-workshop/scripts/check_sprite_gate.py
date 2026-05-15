#!/usr/bin/env python3
"""Basic sprite gate before animation-qc.

This checks whether a generated sheet can be machine-cut into equal square
cells according to the sprite geometry contract. It does not judge motion
quality; animation-qc handles drift, baseline, timing, and transparency cleanup.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description="Check sprite geometry contract")
    parser.add_argument("--input", required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--target-width", type=int)
    parser.add_argument("--target-height", type=int)
    parser.add_argument("--target-cell", type=int)
    parser.add_argument("--require-transparency", action="store_true")
    parser.add_argument("--allow-guide-background", action="store_true")
    parser.add_argument(
        "--check-visible-grid",
        action="store_true",
        help="Verify visible white divider lines are close to expected cell boundaries.",
    )
    parser.add_argument("--grid-tolerance", type=float, default=4.0)
    parser.add_argument("--out")
    args = parser.parse_args()

    path = Path(args.input).expanduser()
    img = Image.open(path).convert("RGBA")
    width, height = img.size
    failures: list[str] = []
    warnings: list[str] = []

    if args.target_width and width != args.target_width:
        failures.append(f"width {width} != target_width {args.target_width}")
    if args.target_height and height != args.target_height:
        failures.append(f"height {height} != target_height {args.target_height}")
    if width % args.cols != 0:
        failures.append(f"width {width} is not divisible by cols {args.cols}")
    if height % args.rows != 0:
        failures.append(f"height {height} is not divisible by rows {args.rows}")

    cell_w = width // args.cols if width % args.cols == 0 else None
    cell_h = height // args.rows if height % args.rows == 0 else None
    if cell_w is not None and cell_h is not None:
        if cell_w != cell_h:
            failures.append(f"cell is not square: {cell_w}x{cell_h}")
        if args.target_cell and cell_w != args.target_cell:
            failures.append(f"cell_w {cell_w} != target_cell {args.target_cell}")
        if args.target_cell and cell_h != args.target_cell:
            failures.append(f"cell_h {cell_h} != target_cell {args.target_cell}")

    ratio_expected = args.cols / args.rows
    ratio_actual = width / height
    if abs(ratio_actual - ratio_expected) > 0.002:
        failures.append(
            f"sheet aspect {ratio_actual:.4f} does not match cols:rows {ratio_expected:.4f}"
        )

    alpha = np.array(img.getchannel("A"))
    has_transparency = bool((alpha < 10).any())
    if args.require_transparency and not has_transparency and not args.allow_guide_background:
        failures.append("background is not truly transparent")
    elif not has_transparency and not args.allow_guide_background:
        warnings.append("background is opaque; may need cleanup before product use")

    visible_grid = None
    if args.check_visible_grid:
        rgb = np.array(img.convert("RGB"))
        white = (rgb[..., 0] > 235) & (rgb[..., 1] > 235) & (rgb[..., 2] > 235)
        col_frac = white.mean(axis=0)
        row_frac = white.mean(axis=1)

        def runs(indices: np.ndarray) -> list[dict]:
            if len(indices) == 0:
                return []
            out = []
            start = prev = int(indices[0])
            for raw in indices[1:]:
                value = int(raw)
                if value == prev + 1:
                    prev = value
                else:
                    out.append(
                        {
                            "start": start,
                            "end": prev,
                            "center": (start + prev) / 2,
                            "width": prev - start + 1,
                        }
                    )
                    start = prev = value
            out.append(
                {
                    "start": start,
                    "end": prev,
                    "center": (start + prev) / 2,
                    "width": prev - start + 1,
                }
            )
            return out

        vertical_runs = runs(np.where(col_frac > 0.70)[0])
        horizontal_runs = runs(np.where(row_frac > 0.70)[0])
        expected_x = [i * (width / args.cols) for i in range(args.cols + 1)]
        expected_y = [i * (height / args.rows) for i in range(args.rows + 1)]
        found_x = [run["center"] for run in vertical_runs]
        found_y = [run["center"] for run in horizontal_runs]

        def max_error(found: list[float], expected: list[float]) -> float | None:
            if len(found) != len(expected):
                return None
            return max(abs(a - b) for a, b in zip(found, expected))

        err_x = max_error(found_x, expected_x)
        err_y = max_error(found_y, expected_y)
        visible_grid = {
            "vertical_line_centers": [round(value, 2) for value in found_x],
            "horizontal_line_centers": [round(value, 2) for value in found_y],
            "expected_vertical_line_centers": [round(value, 2) for value in expected_x],
            "expected_horizontal_line_centers": [round(value, 2) for value in expected_y],
            "max_vertical_error_px": None if err_x is None else round(err_x, 2),
            "max_horizontal_error_px": None if err_y is None else round(err_y, 2),
            "tolerance_px": args.grid_tolerance,
        }
        if len(found_x) != args.cols + 1:
            failures.append(
                f"visible grid has {len(found_x)} vertical lines, expected {args.cols + 1}"
            )
        elif err_x is not None and err_x > args.grid_tolerance:
            failures.append(
                f"visible vertical grid lines deviate by up to {err_x:.1f}px"
            )
        if len(found_y) != args.rows + 1:
            failures.append(
                f"visible grid has {len(found_y)} horizontal lines, expected {args.rows + 1}"
            )
        elif err_y is not None and err_y > args.grid_tolerance:
            failures.append(
                f"visible horizontal grid lines deviate by up to {err_y:.1f}px"
            )

    result = {
        "input": str(path),
        "status": "fail" if failures else "pass",
        "route": "regenerate_or_recompose_before_qc" if failures else "split_or_qc_next",
        "cols": args.cols,
        "rows": args.rows,
        "size": [width, height],
        "cell": [cell_w, cell_h] if cell_w is not None and cell_h is not None else None,
        "target": {
            "width": args.target_width,
            "height": args.target_height,
            "cell": args.target_cell,
        },
        "has_true_transparency": has_transparency,
        "failures": failures,
        "warnings": warnings,
        "visible_grid": visible_grid,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).expanduser().write_text(text)
    print(text)
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
