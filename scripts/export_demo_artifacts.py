"""Export small, review-friendly artifacts from an actual demo run."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("output/demo"))
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    args = parser.parse_args()
    events_path = args.run / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    representative = [
        event
        for event in events
        if event["event_type"] in {"zone_enter", "zone_exit", "line_cross"}
    ]
    args.docs.mkdir(parents=True, exist_ok=True)
    (args.docs / "demo-events.json").write_text(
        json.dumps(representative, indent=2) + "\n", encoding="utf-8"
    )
    screenshots = sorted((args.run / "screenshots").glob("*line_cross*.jpg"))
    if not screenshots:
        screenshots = sorted((args.run / "screenshots").glob("*.jpg"))
    if not screenshots:
        raise RuntimeError("The demo run did not produce a screenshot")
    shutil.copyfile(screenshots[0], args.docs / "demo-preview.jpg")
    print(f"Exported {len(representative)} events and {screenshots[0].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
