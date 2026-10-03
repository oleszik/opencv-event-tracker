"""Deterministic synthetic video generation."""

from pathlib import Path

import cv2
import numpy as np


def generate_demo_video(path: Path, frames: int = 180, fps: int = 30) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 640, 480
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Unable to create demo video: {path}")
    try:
        for index in range(frames):
            frame = np.full((height, width, 3), 28, dtype=np.uint8)
            cv2.putText(
                frame,
                "Synthetic Motion Analytics Demo",
                (14, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (170, 170, 170),
                2,
            )
            x = -60 + index * 4
            cv2.rectangle(frame, (x, 175), (x + 55, 235), (50, 210, 80), -1)
            y = 500 - index * 3
            cv2.circle(frame, (440, y), 28, (220, 100, 40), -1)
            writer.write(frame)
    finally:
        writer.release()
    return path
