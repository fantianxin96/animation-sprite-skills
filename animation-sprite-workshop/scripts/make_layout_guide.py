#!/usr/bin/env python3
"""Create sprite layout helper images.

The guide helps image generation respect exact sprite geometry. It is not a
final asset and should not appear in generated output.

The raw-template mode creates a chroma-green, machine-cuttable sprite template
that can be requested as the visible structure of a generated source sheet.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def parse_labels(value: str | None, rows: int) -> list[str]:
    if not value:
        return [f"row {i + 1}" for i in range(rows)]
    labels = [part.strip() for part in value.split(",")]
    if len(labels) != rows:
        raise SystemExit(f"--labels must have exactly {rows} comma-separated labels")
    return labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a sprite-sheet layout guide")
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cell", type=int, default=256)
    parser.add_argument("--out", required=True)
    parser.add_argument("--labels", help="Comma-separated row or sequence labels")
    parser.add_argument("--actions", help=argparse.SUPPRESS)
    parser.add_argument("--baseline-ratio", type=float, default=0.84)
    parser.add_argument("--safe-padding-ratio", type=float, default=0.12)
    parser.add_argument(
        "--mode",
        choices=["guide", "raw-template"],
        default="guide",
        help="guide is input-only; raw-template is the visible source-sheet structure",
    )
    args = parser.parse_args()

    width = args.cols * args.cell
    height = args.rows * args.cell
    labels = parse_labels(args.labels or args.actions, args.rows)

    if args.mode == "raw-template":
        img = Image.new("RGBA", (width, height), (0, 255, 0, 255))
        draw = ImageDraw.Draw(img)
        divider = (255, 255, 255, 255)
        for row in range(args.rows):
            for col in range(args.cols):
                x0 = col * args.cell
                y0 = row * args.cell
                x1 = x0 + args.cell
                y1 = y0 + args.cell
                draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=divider, width=3)
        out = Path(args.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out)
        return

    img = Image.new("RGBA", (width, height), (250, 248, 252, 255))
    draw = ImageDraw.Draw(img)

    grid = (124, 98, 158, 190)
    safe = (160, 132, 190, 120)
    center = (92, 83, 130, 170)
    baseline = (198, 84, 108, 185)
    text = (90, 70, 120, 255)

    pad = round(args.cell * args.safe_padding_ratio)
    base_y = round(args.cell * args.baseline_ratio)

    for row in range(args.rows):
        for col in range(args.cols):
            x0 = col * args.cell
            y0 = row * args.cell
            x1 = x0 + args.cell
            y1 = y0 + args.cell
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=grid, width=2)
            draw.rectangle((x0 + pad, y0 + pad, x1 - pad, y1 - pad), outline=safe, width=1)
            cx = x0 + args.cell // 2
            draw.line((cx, y0 + pad, cx, y1 - pad), fill=center, width=1)
            draw.line((x0 + pad, y0 + base_y, x1 - pad, y0 + base_y), fill=baseline, width=1)
            draw.text((x0 + 8, y0 + 8), f"{labels[row]} {col + 1}", fill=text)

    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


if __name__ == "__main__":
    main()
