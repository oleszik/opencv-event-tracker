"""Generate a deterministic, copyright-free motion demo."""

from __future__ import annotations

import argparse
from pathlib import Path

from opencv_event_tracker.demo import generate_demo_video


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("examples/demo.mp4"))
    parser.add_argument("--frames", type=int, default=180)
    args = parser.parse_args()
    print(generate_demo_video(args.output, args.frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
