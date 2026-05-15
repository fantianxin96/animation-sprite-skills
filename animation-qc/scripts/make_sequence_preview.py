#!/usr/bin/env python3
"""Stitch processed sprite sheets into one preview GIF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def parse_frames(value):
    if isinstance(value, list):
        return [int(v) for v in value]
    return [int(part.strip()) for part in str(value).split(",") if part.strip()]


def natural_durations(count: int, final_hold: int = 900) -> list[int]:
    if count <= 0:
        return []
    if count == 1:
        return [final_hold]
    if count == 2:
        return [260, final_hold]
    durations = [170] * count
    durations[0] = 240
    if count >= 4:
        durations[1] = 150
        durations[-2] = 260
    durations[-1] = final_hold
    return durations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="JSON manifest with ordered segments.")
    parser.add_argument("--out", required=True, help="Output GIF path.")
    parser.add_argument("--bg", default="#FCFAF6", help="Preview background color.")
    parser.add_argument("--loop", type=int, default=0)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser()
    out_path = Path(args.out).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text())
    segments = manifest["segments"] if isinstance(manifest, dict) else manifest

    gif_frames = []
    durations = []
    for segment in segments:
        sheet = Image.open(Path(segment["src"]).expanduser()).convert("RGBA")
        cols = int(segment.get("cols", 3))
        rows = int(segment.get("rows", 2))
        cell_w, cell_h = sheet.width // cols, sheet.height // rows
        frames = parse_frames(segment.get("frames", list(range(cols * rows))))
        durs = segment.get("durs") or natural_durations(len(frames), int(segment.get("final_hold", 900)))
        if len(durs) < len(frames):
            durs = list(durs) + [durs[-1] if durs else 150] * (len(frames) - len(durs))
        for frame, dur in zip(frames, durs):
            col = frame % cols
            row = frame // cols
            crop = sheet.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
            bg = Image.new("RGBA", (cell_w, cell_h), args.bg)
            bg.alpha_composite(crop)
            gif_frames.append(bg.convert("P", palette=Image.Palette.ADAPTIVE))
            durations.append(int(dur))

    if not gif_frames:
        raise SystemExit("Manifest produced no frames.")

    gif_frames[0].save(
        out_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=durations,
        loop=args.loop,
        disposal=2,
    )
    print(out_path)


if __name__ == "__main__":
    main()
