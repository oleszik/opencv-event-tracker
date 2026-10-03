"""Application orchestration for the video analytics pipeline."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import cv2

from .config import AppConfig
from .detection import MotionDetector
from .events import EventEngine
from .models import Event
from .output import EventWriter, annotate_frame, next_output_directory, save_screenshot
from .tracking import CentroidTracker
from .video import create_writer, open_capture

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RunSummary:
    frames_processed: int
    average_fps: float
    objects_tracked: int
    events_recorded: int
    event_counts: dict[str, int]
    output_directory: Path


def run(
    config: AppConfig,
    input_path: Path | None = None,
    camera: int | None = None,
    output_override: Path | None = None,
    display_override: bool | None = None,
    save_video_override: bool | None = None,
    max_frames: int | None = None,
) -> RunSummary:
    capture, source = open_capture(input_path, camera)
    output_dir = next_output_directory(output_override or Path(config.output.directory))
    output_dir.mkdir(parents=True, exist_ok=False)
    display = config.output.display if display_override is None else display_override
    save_video = config.output.save_video if save_video_override is None else save_video_override
    detector = MotionDetector(config.detection)
    tracker = CentroidTracker(
        config.tracking.max_distance,
        config.tracking.max_missing_frames,
        config.tracking.history_length,
    )
    engine = EventEngine(config.events, config.zones, config.lines)
    fps_source = capture.get(cv2.CAP_PROP_FPS) or 25.0
    writer = None
    frames = 0
    event_counts: Counter[str] = Counter()
    started = perf_counter()
    recent_banner: str | None = None
    try:
        with EventWriter(output_dir, config.output) as event_writer:
            while max_frames is None or frames < max_frames:
                ok, frame = capture.read()
                if not ok:
                    break
                frames += 1
                detections, _ = detector.detect(frame)
                tracks, created, lost = tracker.update(detections, frames)
                clock = frames / fps_source
                events: list[Event] = []
                for track in created:
                    event = engine.object_event("object_detected", track, frames, clock, source)
                    if event:
                        events.append(event)
                for track in tracks:
                    events.extend(engine.process_track(track, frames, clock, source))
                for track in lost:
                    event = engine.object_event("object_lost", track, frames, clock, source)
                    if event:
                        events.append(event)
                for event in events:
                    event_writer.write(event)
                    event_counts[event.event_type] += 1
                elapsed = max(perf_counter() - started, 1e-9)
                if events:
                    recent_banner = " | ".join(event.event_type for event in events)
                annotated = annotate_frame(
                    frame,
                    tracks,
                    config.zones,
                    config.lines,
                    frames / elapsed,
                    frames,
                    sum(event_counts.values()),
                    recent_banner,
                )
                for event in events:
                    if (
                        config.events.screenshots
                        and event.event_type in config.events.screenshot_types
                    ):
                        save_screenshot(output_dir, event, annotated)
                if save_video:
                    if writer is None:
                        height, width = annotated.shape[:2]
                        writer = create_writer(
                            output_dir / "annotated.mp4", fps_source, width, height
                        )
                    writer.write(annotated)
                if display:
                    cv2.imshow("OpenCV Event Tracker", annotated)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if display:
            cv2.destroyAllWindows()
    elapsed = max(perf_counter() - started, 1e-9)
    if frames == 0:
        raise RuntimeError(f"No frames could be read from source: {source}")
    return RunSummary(
        frames,
        frames / elapsed,
        tracker.total_created,
        sum(event_counts.values()),
        dict(event_counts),
        output_dir,
    )
