#!/usr/bin/env python3
"""Audit product code for motion assets that bypass QC."""

from __future__ import annotations

import re
import sys
from pathlib import Path


MOTION_HINTS = (
    "home-tap",
    "compose-",
    "process-",
    "splash-",
    "welcome-entry",
    "data-",
)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: audit_product_usage.py /path/to/index.html", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]).expanduser()
    text = path.read_text(encoding="utf-8")
    refs = sorted(set(re.findall(r"chars/[^'\"` )]+\.png", text)))

    motion_refs = [ref for ref in refs if any(hint in ref for hint in MOTION_HINTS)]
    suspect = [
        ref
        for ref in motion_refs
        if "-aligned" not in ref and "welcome-entry-home-aligned" not in ref
    ]

    print("Motion asset audit")
    print(f"file: {path}")
    print(f"motion refs: {len(motion_refs)}")
    for ref in motion_refs:
        status = "FAIL raw-or-unmarked" if ref in suspect else "OK"
        print(f"{status:18} {ref}")

    if suspect:
        print("\nResult: FAIL")
        print("These motion assets should pass $animation-qc before product use:")
        for ref in suspect:
            print(f"- {ref}")
        return 1

    print("\nResult: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
