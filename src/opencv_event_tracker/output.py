"""Structured event, screenshot, and annotation output."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np

from .config import LineConfig, OutputConfig, ZoneConfig
from .models import Event, Track


class EventWriter:
    def __init__(self, directory: Path, config: OutputConfig) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.jsonl = None
        self.csv_file = None
        self.csv_writer = None
        if config.save_events:
            self.jsonl = (directory / "events.jsonl").open("x", encoding="utf-8")
        if config.csv:
            self.csv_file = (directory / "events.csv").open("x", newline="", encoding="utf-8")
            fields = [
                "event_id",
                "event_type",
                "timestamp",
                "frame_number",
                "object_id",
                "source",
                "zone",
                "line",
                "direction",
                "bbox",
                "centroid",
            ]
            self.csv_writer = csv.DictWriter(
                self.csv_file, fieldnames=fields, extrasaction="ignore"
            )
            self.csv_writer.writeheader()

    def write(self, event: Event) -> None:
        data = event.to_dict()
        if self.jsonl:
            self.jsonl.write(json.dumps(data) + "\n")
            self.jsonl.flush()
        if self.csv_writer:
            self.csv_writer.writerow(data)
            self.csv_file.flush()

    def close(self) -> None:
        if self.jsonl:
            self.jsonl.close()
        if self.csv_file:
            self.csv_file.close()

    def __enter__(self) -> EventWriter:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def next_output_directory(base: Path) -> Path:
    if not base.exists():
        return base
    index = 1
    while (candidate := base.with_name(f"{base.name}-{index:03d}")).exists():
        index += 1
    return candidate


def annotate_frame(
    frame: np.ndarray,
    tracks: list[Track],
    zones: list[ZoneConfig],
    lines: list[LineConfig],
    fps: float,
    frame_number: int,
    event_count: int,
    banner: str | None = None,
) -> np.ndarray:
    canvas = frame.copy()
    for zone in zones:
        cv2.rectangle(canvas, (zone.x1, zone.y1), (zone.x2, zone.y2), (255, 180, 0), 2)
        cv2.putText(
            canvas,
            f"ZONE: {zone.name}",
            (zone.x1, max(18, zone.y1 - 7)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 180, 0),
            2,
        )
    for line in lines:
        cv2.line(canvas, line.start, line.end, (0, 80, 255), 2)
        cv2.putText(
            canvas,
            f"LINE: {line.name}",
            line.start,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 80, 255),
            2,
        )
    for track in tracks:
        x, y, width, height = track.bbox
        color = (
            (37 * track.object_id) % 200 + 55,
            (83 * track.object_id) % 200 + 55,
            (131 * track.object_id) % 200 + 55,
        )
        cv2.rectangle(canvas, (x, y), (x + width, y + height), color, 2)
        cv2.circle(canvas, track.centroid, 4, color, -1)
        cv2.putText(
            canvas,
            f"ID {track.object_id}",
            (x, max(18, y - 7)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )
        if len(track.history) > 1:
            cv2.polylines(canvas, [np.array(track.history, dtype=np.int32)], False, color, 2)
    cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 28), (20, 20, 20), -1)
    status = f"Frame {frame_number} | FPS {fps:.1f} | Tracks {len(tracks)} | Events {event_count}"
    cv2.putText(canvas, status, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1)
    if banner:
        cv2.putText(
            canvas,
            banner,
            (8, canvas.shape[0] - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
        )
    return canvas


def save_screenshot(directory: Path, event: Event, frame: np.ndarray) -> Path:
    screenshots = directory / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    timestamp = event.timestamp.replace(":", "-").replace("+", "_")
    path = screenshots / f"{timestamp}_{event.event_type}_object_{event.object_id}.jpg"
    if not cv2.imwrite(str(path), frame):
        raise OSError(f"Unable to save event screenshot: {path}")
    return path
