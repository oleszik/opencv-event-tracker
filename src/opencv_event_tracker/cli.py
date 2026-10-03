"""Command-line interface."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import __version__
from .app import run
from .config import ConfigError, load_config
from .video import VideoError, open_capture


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opencv-event-tracker", description="Motion tracking and event analytics"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Process a video or camera stream")
    source = run_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Video file")
    source.add_argument("--camera", type=int, help="Camera index")
    run_parser.add_argument("--config", type=Path, default=Path("config.example.yaml"))
    run_parser.add_argument("--output", type=Path)
    run_parser.add_argument("--display", action="store_true", default=None)
    run_parser.add_argument("--no-video", action="store_true")
    run_parser.add_argument("--max-frames", type=int)
    validate = subparsers.add_parser("validate-config", help="Validate YAML configuration")
    validate.add_argument("--config", type=Path, default=Path("config.example.yaml"))
    inspect = subparsers.add_parser("inspect", help="Inspect a video source")
    source = inspect.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path)
    source.add_argument("--camera", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-config":
            load_config(args.config)
            print(f"Configuration is valid: {args.config}")
            return 0
        if args.command == "inspect":
            capture, source = open_capture(args.input, args.camera)
            try:
                print(f"Source: {source}")
                print(f"Resolution: {int(capture.get(3))}x{int(capture.get(4))}")
                print(f"FPS: {capture.get(5):.2f}")
                print(f"Frames: {int(capture.get(7))}")
            finally:
                capture.release()
            return 0
        config = load_config(args.config)
        summary = run(
            config,
            args.input,
            args.camera,
            args.output,
            args.display,
            False if args.no_video else None,
            args.max_frames,
        )
        print("Processing complete")
        print(f"Frames processed: {summary.frames_processed}")
        print(f"Average FPS: {summary.average_fps:.1f}")
        print(f"Objects tracked: {summary.objects_tracked}")
        print(f"Events recorded: {summary.events_recorded}")
        print(f"Zone entries: {summary.event_counts.get('zone_enter', 0)}")
        print(f"Line crossings: {summary.event_counts.get('line_cross', 0)}")
        print(f"Output: {summary.output_directory}")
        return 0
    except (ConfigError, VideoError, RuntimeError, OSError) as exc:
        logging.error("%s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
